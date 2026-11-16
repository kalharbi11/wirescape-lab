// SPDX-License-Identifier: GPL-3.0-only
// Devices-off FakeEngine UI profile: CDP CPU sampler + Chromium Performance trace.
// Raw traces are CI artifacts only; never stage or commit them as facts.
'use strict';
const {chromium}=require('../../apps/studio/node_modules/playwright');
const {spawn,execFileSync}=require('node:child_process');
const {mkdirSync,writeFileSync}=require('node:fs');
const path=require('node:path');
const os=require('node:os');
const {patch,previewCommand}=require('./ui_frames.cjs');
const {aggregateTrials,cpuSummary,traceSummary}=require('./ui_profile_parse.cjs');
const ROOT=path.resolve(__dirname,'../..');
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const BROWSER=process.env.WIRESCAPE_CHROMIUM || chromium.executablePath();
const VIEWPORT={width:1920,height:1080};
const CATEGORIES='devtools.timeline,disabled-by-default-devtools.timeline,blink.user_timing,blink.console,toplevel,v8.execute';
function cli(argv=process.argv.slice(2)){
  const args={output:path.join(ROOT,'build_reports/ui-profile'),repeats:6};
  for(let i=0;i<argv.length;i++){
    if(argv[i]==='--output' && argv[i+1])args.output=path.resolve(argv[++i]);
    else if(argv[i]==='--repeats' && argv[i+1])args.repeats=Number(argv[++i]);
    else throw new Error('unsupported flag '+argv[i]+'; only --output and --repeats are allowed (devices off)');
  }
  if(!Number.isInteger(args.repeats)||args.repeats<3||args.repeats>12)
    throw new Error('--repeats must be 3..12');
  return args;
}
async function readTrace(session, stream){
  const chunks=[];
  try{
    while(true){
      const part=await session.send('IO.read',{handle:stream,size:1048576});
      chunks.push(part.base64Encoded?Buffer.from(part.data,'base64').toString('utf8'):part.data||'');
      if(part.eof)break;
    }
  }finally{await session.send('IO.close',{handle:stream}).catch(()=>{});}
  return chunks.join('');
}
async function point(page,id){
  const rect=await page.getByTestId(id).boundingBox();
  if(!rect)throw new Error('Target not visible: '+id);
  return {x:rect.x+rect.width/2,y:rect.y+rect.height/2};
}
async function gesture(page,action){
  if(action==='knob'){
    const box=await page.getByTestId('knob-2-cutoff').locator('.dial-wrap').boundingBox();
    if(!box)throw new Error('Knob not visible');
    const x=box.x+box.width/2,y=box.y+box.height/2;
    await page.mouse.move(x,y);await page.mouse.down();
    await page.mouse.move(x,y-80,{steps:30});await page.mouse.up();
  }else if(action==='cable'){
    const a=await point(page,'port-1-output-audio');
    const b=await point(page,'port-2-input-audio');
    await page.mouse.move(a.x,a.y);await page.mouse.down();
    await page.mouse.move(b.x,b.y,{steps:30});await page.mouse.up();
  }else throw new Error('Unknown action '+action);
}
async function runTrial(context,dir,n,action,repeat){
  const trial={modules:n,action,repeat,interactions:0,frame_intervals_ms:[],
    observed_duration_ms:0, cpu:{status:'unavailable',reason:'not captured'},
    trace:{status:'unavailable',reason:'not captured'}};
  const page=await context.newPage();
  let session;
  const label=`${n}-${action}-r${repeat}`;
  try{
    await page.goto('http://127.0.0.1:4173');
    await page.waitForFunction(()=>document.body.dataset.ready==='true');
    await page.evaluate(graph=>{
      window.__wirescapeTest.clearAutosave();
      window.__wirescapeTest.load(graph,'L4');
    },patch(n));
    await page.evaluate(()=>new Promise(done=>requestAnimationFrame(()=>requestAnimationFrame(done))));
    session=await context.newCDPSession(page);
    await session.send('Profiler.enable');
    await session.send('Profiler.setSamplingInterval',{interval:1000});
    const tracingComplete=new Promise(resolve=>session.once('Tracing.tracingComplete',resolve));
    await session.send('Tracing.start',{categories:CATEGORIES,transferMode:'ReturnAsStream'});
    await session.send('Profiler.start');
    const started=Date.now();
    await page.evaluate(()=>{
      performance.mark('WS_UI_PROFILE_START');console.timeStamp('WS_UI_PROFILE_START');
      const intervals=[];let previous=0,active=true;
      function tick(now){
        if(!active)return;
        if(previous)intervals.push(now-previous);
        previous=now;
        requestAnimationFrame(tick);
      }
      window.__wsProfileFrames={stop:()=>{active=false;return intervals;}};
      requestAnimationFrame(tick);
    });
    await sleep(100);
    await gesture(page,action);
    trial.interactions=1; // completed mouse down/move/up gesture (not semantic graph assertion).
    await sleep(350);
    trial.frame_intervals_ms=await page.evaluate(()=>{
      performance.mark('WS_UI_PROFILE_END');console.timeStamp('WS_UI_PROFILE_END');
      return window.__wsProfileFrames.stop();
    });
    trial.observed_duration_ms=Date.now()-started;
    const {profile}=await session.send('Profiler.stop');
    writeFileSync(path.join(dir,label+'.cpuprofile'),JSON.stringify(profile));
    trial.cpu=cpuSummary(profile);
    await session.send('Tracing.end');
    const completion=await Promise.race([tracingComplete,
      sleep(20000).then(()=>{throw new Error('Tracing.tracingComplete timeout');})]);
    if(!completion?.stream)throw new Error('Chromium returned no trace stream');
    const raw=await readTrace(session,completion.stream);
    writeFileSync(path.join(dir,label+'.trace.json'),raw);
    trial.trace=traceSummary(JSON.parse(raw));
  }catch(error){
    trial.error=String(error.message||error).slice(0,500);
    if(trial.cpu.status!=='measured')trial.cpu={status:'unavailable',reason:trial.error};
    if(trial.trace.status!=='measured')trial.trace={status:'unavailable',reason:trial.error};
  }finally{
    if(session)await session.detach().catch(()=>{});
    await page.close();
  }
  return trial;
}
async function main(argv=process.argv.slice(2)){
  const options=cli(argv); // Validate before any browser, child process or socket.
  const out=options.output;
  mkdirSync(out,{recursive:true});mkdirSync(path.join(out,'raw'),{recursive:true});
  const server=spawn(previewCommand().executable,previewCommand().args,
                     {cwd:path.join(ROOT,'apps/studio'),stdio:'ignore'});
  server.on('error',error=>console.error('Vite preview:',error.message));
  let browser;
  try{
    let ready=false;
    for(let k=0;k<80;k++){
      try{
        const response=await fetch('http://127.0.0.1:4173');
        if(response.ok){ready=true;break;}
      }catch(_){}
      await sleep(250);
    }
    if(!ready)throw new Error('Vite preview not available on localhost:4173');
    browser=await chromium.launch({executablePath:BROWSER,headless:true,args:['--no-sandbox']});
    const context=await browser.newContext({viewport:VIEWPORT});
    const records=[],trials=[];
    for(const n of [50,100,200])for(const action of ['knob','cable']){
      const group=[];
      for(let repeat=1;repeat<=options.repeats;repeat++){
        const t=await runTrial(context,path.join(out,'raw'),n,action,repeat);
        group.push(t);trials.push(t);
        console.log(`profile ${n} ${action} ${repeat}/${options.repeats}: `+
          `frames=${t.frame_intervals_ms.length} cpu=${t.cpu.status} trace=${t.trace.status}`+
          (t.error?' error='+t.error:''));
      }
      records.push({modules:n,action,...aggregateTrials(group)});
    }
    await context.close();
    const summary={
      schema:2,source_commit:execFileSync('git',['rev-parse','HEAD'],{cwd:ROOT,encoding:'utf8'}).trim(),
      date_et:new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York'}).format(new Date()),
      machine:{runner:process.env.RUNNER_NAME||'local',os:os.platform(),arch:os.arch(),
        cpu:os.cpus()[0]?.model||'unknown',runner_image:process.env.ImageOS||null,
        runner_image_version:process.env.ImageVersion||null,devices:'audio/MIDI not opened',
        network:'127.0.0.1 only'},
      chromium_version:browser.version(),viewport:VIEWPORT,workloads:{module_counts:[50,100,200],
        actions:['knob','cable'],repetitions:options.repeats,
        mouse_steps:30, completed_interaction:'one full drag from mouse down to up per repetition'},
      method:{frames:'rAF interval nearest-rank percentiles, measured during instrumented drag window',
        cpu:'Chromium CDP Profiler 1ms statistical positive-duration CPU samples; all per-trial function/source self times merged before top-10 truncation; missing or empty samples unavailable',
        performance:'Chromium CDP Tracing renderer CrRendererMain nested duration categories',
        separate_from_playwright_trace:true,
        caveats:'Sampling bias, minified JS, overlapping tasks, profiler overhead, compositor/GPU excluded; unobserved time is not necessarily idle'},
      results:records,
      raw_artifacts:'raw/*.cpuprofile and raw/*.trace.json; CI upload only, never commit'};
    writeFileSync(path.join(out,'summary.json'),JSON.stringify(summary,null,2)+'\n');
    writeFileSync(path.join(out,'trials.json'),JSON.stringify(trials,null,2)+'\n');
    console.log('WS_PROFILE_FACTS_JSON='+JSON.stringify(summary));
    // A finished mouse gesture without valid CPU/timeline evidence is NOT a
    // successful attribution. Keep summary/artifacts for diagnosis, fail the
    // advisory job, and never publish an unavailable capture as measured.
    if(records.some(r=>r.completed_interactions!==options.repeats
      || r.cpu_attribution.status!=='measured'
      || r.trace_attribution.status!=='measured'
      || r.frame.sample_count<options.repeats))
      process.exitCode=1;
  }finally{
    if(browser)await browser.close();
    server.kill('SIGTERM');
  }
}
module.exports={cli,gesture,runTrial,main};
if(require.main===module)main().catch(e=>{console.error(e);process.exitCode=1;});
