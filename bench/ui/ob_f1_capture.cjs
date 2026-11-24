// SPDX-License-Identifier: GPL-3.0-only
// OB-f1: read-only device-off Studio + actual null-audio sidecar UI facts.
// Raw observations are uploaded by a dedicated advisory workflow, not committed.
'use strict';
const {chromium}=require('../../apps/studio/node_modules/playwright');
const {spawn,execFileSync}=require('node:child_process');
const {createInterface}=require('node:readline');
const {mkdirSync,mkdtempSync,rmSync,writeFileSync,readFileSync,existsSync}=require('node:fs');
const path=require('node:path');
const os=require('node:os');
const {chooseHeaviest,rankIdleCpu,hash,applyGesture,consolidate}=require('./ob_f1_metrics.cjs');
const {previewCommand}=require('../offline/ui_frames.cjs');
const ROOT=path.resolve(__dirname,'../..');
const OUT=path.join(ROOT,'build_reports/ob-f1');
const URL='http://127.0.0.1:4173';
const BINARY=path.join(ROOT,'build/native/wirescape-engine');
const CLI=path.join(ROOT,'build/native/wirescape_cli');
const ACTIONS=['knob','module','cable','telemetry'];
const VIEWPORT={width:1920,height:1080};

function sha(){return execFileSync('git',['rev-parse','HEAD'],{cwd:ROOT,encoding:'utf8'}).trim();}
function metadata() {
  return {source_commit:sha(), date_et:new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York'}).format(new Date()),
    runner:process.env.RUNNER_NAME||'local', image:process.env.ImageOS||null,
    cpu:os.cpus()[0]?.model||'unavailable', architecture:os.arch(), os:os.platform(),
    node:process.version, devices:'no audio or MIDI devices opened', transport:'native --null-audio, stdin/stdout only; Vite preview 127.0.0.1'};
}
async function readyPreview(proc) {
  for(let n=0;n<80;n++){
    if(proc.exitCode!==null)throw new Error('Vite preview exited before ready');
    try{const response=await fetch(URL);if(response.ok)return;}catch{}
    await new Promise(resolve=>setTimeout(resolve,250)); // bounded local app startup only
  }
  throw new Error('local Vite preview not available');
}
async function frameStart(page) {
  await page.evaluate(()=>{
    const intervals=[];let prior=0,active=true;
    const tick=t=>{if(!active)return;if(prior)intervals.push(t-prior);prior=t;requestAnimationFrame(tick);};
    window.__obf1Frames={stop:()=>{active=false;return intervals;}};
    window.__obf1Bridge.start();
    requestAnimationFrame(tick);
  });
}
async function settleFrames(page,n=10) {
  await page.evaluate(async count=>{
    for(let i=0;i<count;i++)await new Promise(resolve=>requestAnimationFrame(resolve));
  },n);
}
async function frameStop(page) {
  return page.evaluate(()=>{
    const frames=window.__obf1Frames.stop();
    const capture=window.__obf1Bridge.stop();
    return {frames,...capture};
  });
}
async function visible(page,selector) {
  const candidates=page.locator(selector);
  for(let i=0;i<Math.min(await candidates.count(),180);i++) {
    const item=candidates.nth(i),b=await item.boundingBox();
    if(b&&b.width>5&&b.height>5&&b.x+b.width/2>=8&&b.y+b.height/2>=8&&
       b.x+b.width/2<VIEWPORT.width-8&&b.y+b.height/2<VIEWPORT.height-8)
      return {item,b};
  }
  return null;
}
function center(b){return {x:b.x+b.width/2,y:b.y+b.height/2};}
async function mouseMove(page,item,dx,dy){
  const c=center(item.b);
  await page.mouse.move(c.x,c.y);await page.mouse.down();
  await page.mouse.move(Math.min(VIEWPORT.width-10,Math.max(10,c.x+dx)),
                        Math.min(VIEWPORT.height-10,Math.max(10,c.y+dy)),{steps:30});
  await page.mouse.up();
}
async function gesture(page,action,patch) {
  if(action==='knob'){
    const knob=await visible(page,'[data-testid^="knob-"] .dial-wrap');
    if(!knob)throw new Error('no in-viewport knob dial on selected bundled patch');
    await mouseMove(page,knob,0,-85);
    return {target:await knob.item.getAttribute('class'),completed:true};
  }
  if(action==='module'){
    const header=await visible(page,'[data-testid^="module-header-"]');
    if(!header)throw new Error('no in-viewport module header');
    const before=await page.evaluate(()=>window.__wirescapeTest.state().ui.positions);
    await mouseMove(page,header,35,25);
    const after=await page.evaluate(()=>window.__wirescapeTest.state().ui.positions);
    return {target:'native module header',position_changed:JSON.stringify(before)!==JSON.stringify(after),
      completed:true};
  }
  if(action==='cable'){
    // Use an actual pre-existing bundled graph signal path; its endpoints are
    // known compatible. Duplicate/no-op remains a drawing gesture, not an
    // assertion that the graph successfully acquired a second edge.
    const links=patch.connections.filter(c=>c.kind==='signal');
    for(const edge of links){
      const sid='port-'+edge.from.module+'-output-'+edge.from.port;
      const tid='port-'+edge.to.module+'-input-'+edge.to.port;
      const from=await visible(page,'[data-testid="'+sid+'"]');
      const to=await visible(page,'[data-testid="'+tid+'"]');
      if(!from||!to)continue;
      const p=center(from.b),q=center(to.b);
      await page.mouse.move(p.x,p.y);await page.mouse.down();
      await page.mouse.move(q.x,q.y,{steps:30});await page.mouse.up();
      return {target:sid+' -> '+tid,semantic_new_edge:'not_claimed (existing bundled path)',
        completed:true};
    }
    throw new Error('no visible original compatible bundled cable endpoint pair');
  }
  if(action==='telemetry'){
    await settleFrames(page,75); // rAF observation window, not synthetic telemetry
    return {target:'native-sidecar telemetry',completed:true};
  }
  throw new Error('unsupported action');
}

// A20: source-pinned, idle/default-state-only offline engine cost ranking.
// The real Release CLI measures app_engine_render_channels, not WAV output time.
function captureCpuRanking(proxy) {
  const rate=48000,block=128,seconds=10,periodUs=block/rate*1e6;
  if(!existsSync(CLI))throw new Error('Release wirescape_cli absent: cannot rank actual CPU');
  const temp=mkdtempSync(path.join(os.tmpdir(),'ob-f1-idle-cpu-'));
  const rows=[];
  try {
    for(const fixture of proxy.inventory) {
      const relative='apps/studio/patches/'+fixture.name;
      const wav=path.join(temp,fixture.name+'.wav');
      const args=['play',relative,'--rate',String(rate),'--block',String(block),
        '--seconds',String(seconds),'--output',wav];
      const item={name:fixture.name,sha256:fixture.sha256,bytes:fixture.bytes,
        module_count:fixture.module_count,connection_count:fixture.connection_count,
        args:['play',relative,'--rate','48000','--block','128','--seconds','10',
          '--output','<distinct temporary WAV>'],status:'unavailable',
        metrics:null,render_period_cpu_ratio_p95:null,error:null};
      try {
        const stdout=execFileSync(CLI,args,{cwd:ROOT,encoding:'utf8',
          timeout:120000,maxBuffer:1024*1024});
        const observation=JSON.parse(stdout.trim().split(/\r?\n/).at(-1));
        const names=['p50_us','p95_us','p99_us','worst_us','overruns','blocks'];
        if(observation.offline!==true||observation.rate!==rate||
           observation.block!==block||observation.frames!==rate*seconds||
           observation.blocks!==Math.ceil(rate*seconds/block)||
           names.some(k=>typeof observation[k]!=='number'||!Number.isFinite(observation[k]))||
           observation.p50_us<=0||observation.p95_us<=0||observation.p99_us<=0||
           observation.worst_us<=0||observation.overruns<0||
           !(observation.p50_us<=observation.p95_us&&
             observation.p95_us<=observation.p99_us&&
             observation.p99_us<=observation.worst_us))
          throw new Error('CLI offline JSON missing, incomplete or inconsistent');
        item.status='measured';
        item.metrics=observation; // Preserve exact CLI JSON, not just derived percentiles.
        item.raw_stdout=stdout.trim();
        item.render_period_cpu_ratio_p95=observation.p95_us/periodUs;
      }catch(error) {
        item.status='unavailable';
        item.error=String(error.message||error).slice(0,900);
        item.exit_code=Number.isInteger(error.status)?error.status:null;
        if(error.stdout)item.raw_stdout=String(error.stdout).slice(-1600);
        if(error.stderr)item.raw_stderr=String(error.stderr).slice(-1600);
      }finally {
        rmSync(wav,{force:true}); // WAVs are disposable; never commit audio or patches.
      }
      rows.push(item);
      console.log('OBF1_CPU '+fixture.name+' '+item.status+
        (item.status==='measured'?' p95_us='+item.metrics.p95_us:''));
    }
  }finally {rmSync(temp,{recursive:true,force:true});}
  const sorted=rankIdleCpu(rows);
  const report={schema:'wirescape/ob-f1-idle-cpu-rank/1',provenance:metadata(),
    cli_executable_sha256:hash(readFileSync(CLI)),
    method:'actual default-state offline wirescape_cli play; 48k Hz, 128-frame blocks, 10 s per patch; no --confirm-* or --pace; measures render only, not WAV I/O',
    scope:'idle-only; input-gated/silent graph active CPU is unresolved; one run per patch on shared hosted runner, not Pi/device/audio performance',
    period_us:periodUs,expected_patches:24,observed_patches:rows.length,
    measured_count:sorted.length,unavailable_count:rows.length-sorted.length,
    sort:'descending observed p95_us / render period, then p50_us, then lexical filename',
    graph_proxy_original:proxy.chosen.name,
    winner:sorted.length?sorted[0].name:null,
    rank:sorted.map((r,i)=>({rank:i+1,name:r.name,
      p50_us:r.metrics.p50_us,p95_us:r.metrics.p95_us,
      render_period_cpu_ratio_p95:r.render_period_cpu_ratio_p95})),
    rows};
  writeFileSync(path.join(OUT,'cpu-ranking.json'),JSON.stringify(report,null,2)+'\n');
  if(rows.length!==24)throw new Error('CPU ranking inventory expected 24 original bundled patches, got '+rows.length);
  if(!sorted.length)throw new Error('CPU ranking has no actually measured patches');
  return report;
}

async function main() {
  mkdirSync(OUT,{recursive:true});mkdirSync(path.join(OUT,'raw'),{recursive:true});
  const proxy=chooseHeaviest(path.join(ROOT,'apps/studio/patches'));
  const cpuRanking=captureCpuRanking(proxy);
  const chosen=proxy.inventory.find(x=>x.name===cpuRanking.winner);
  if(!chosen)throw new Error('CPU-winning patch missing from source-pinned inventory');
  const patch=JSON.parse(readFileSync(path.join(ROOT,'apps/studio/patches',chosen.name)));
  const selection={chosen,inventory:proxy.inventory,
    selection_rule:'actual default-state idle-only offline CPU p95_us / 2666.6667 us, p50 tie, lexical tie'};
  writeFileSync(path.join(OUT,'patch-selection.json'),JSON.stringify({
    selection_rule:selection.selection_rule,chosen,inventory:selection.inventory,
    original_graph_proxy:{name:proxy.chosen.name,rule:proxy.selection_rule},
    cpu_rank_file:'cpu-ranking.json',source_commit:sha()
  },null,2)+'\n');
  if(!existsSync(BINARY))throw new Error('native Release --null-audio sidecar missing, build headless first');
  const engine=spawn(BINARY,['--null-audio'],{cwd:ROOT,stdio:['pipe','pipe','pipe']});
  const preview=previewCommand();
  const server=spawn(preview.executable,preview.args,{cwd:path.join(ROOT,'apps/studio'),stdio:'ignore'});
  const engineLog=[];let page,browser,bridgeReady=false;
  let delivery=Promise.resolve();
  const queued=[];
  engine.stderr.on('data',chunk=>{
    const s=String(chunk);engineLog.push(s.slice(-3000));
    if(engineLog.length>80)engineLog.shift();
  });
  const rli=createInterface({input:engine.stdout,crlfDelay:Infinity});
  async function deliver(msg) {
    if(!page||!bridgeReady){queued.push(msg);return;}
    delivery=delivery.then(()=>page.evaluate(m=>window.__obf1Dispatch(m),msg))
      .catch(e=>{engineLog.push('browser native-reply delivery: '+String(e).slice(0,400));});
    await delivery;
  }
  rli.on('line',line=>{
    try{const msg=JSON.parse(line);if(msg&&msg.v===0)void deliver(msg);}
    catch{engineLog.push('non-JSON sidecar line: '+line.slice(0,300));}
  });
  const records=[];
  try{
    await readyPreview(server);
    browser=await chromium.launch({headless:true,args:['--no-sandbox']});
    const context=await browser.newContext({viewport:VIEWPORT});
    page=await context.newPage();
    await page.exposeBinding('__obf1Send',async(_source,command)=>{
      if(engine.exitCode!==null || !engine.stdin.writable)
        throw new Error('native sidecar stdin unavailable');
      engine.stdin.write(JSON.stringify(command)+'\n');
    });
    await page.addInitScript(()=>{
      const listeners=new Set();
      const buffered=[],pending=new Map();
      let retainedHello=null;
      const observations={sent:[],acks:[],telemetry:0,down_at_ms:null};
      let active=false;
      document.addEventListener('pointerdown',()=>{if(active&&observations.down_at_ms===null)
        observations.down_at_ms=performance.now();},{capture:true});
      window.__obf1Dispatch=msg=>{
        if(msg.type==='hello')retainedHello=msg;
        if(msg.type==='telemetry'&&active)observations.telemetry++;
        if(typeof msg.re==='string'){
          const prior=pending.get(msg.re);
          if(prior&&active)observations.acks.push({
            id:msg.re,type:prior.type,ok:msg.ok===true,
            gen:msg.gen,code:msg.code||null,received_at_ms:performance.now()});
          pending.delete(msg.re);
        }
        if(!listeners.size)buffered.push(msg);
        else for(const cb of listeners)cb(msg);
      };
      window.wirescape={
        send(command){
          if(active){
            observations.sent.push({...command,sent_at_ms:performance.now()});
            pending.set(command.id,{type:command.type});
          }
          void window.__obf1Send(command).catch(error=>{
            window.__obf1Bridge.transport_errors.push(String(error).slice(0,300));
          });
        },
        onMessage(callback){
          listeners.add(callback);
          // The menu listener subscribes before RealEngine. Both must see
          // the native boot hello, even when it arrived before either one.
          if(retainedHello)callback(retainedHello);
          for(const msg of buffered.splice(0))if(msg!==retainedHello)callback(msg);
          return ()=>listeners.delete(callback);
        },
        openPatch:async()=>null,
        savePatch:async()=>({name:'benchmark-only; unsaved'}),
        platform:'linux',
      };
      window.__obf1Bridge={
        transport_errors:[],
        start(){
          observations.sent=[];observations.acks=[];observations.telemetry=0;
          observations.down_at_ms=null;pending.clear();active=true;
        },
        stop(){
          active=false;
          return {sent:observations.sent.slice(),acks:observations.acks.slice(),
            telemetry_count:observations.telemetry,
            down_at_ms:observations.down_at_ms,
            transport_errors:this.transport_errors.slice()};
        },
        allAcked(){
          return observations.sent.filter(x=>x.type==='setParam').every(s=>
            observations.acks.some(a=>a.id===s.id));
        }
      };
    });
    await page.goto(URL,{waitUntil:'domcontentloaded'});
    await page.waitForFunction(()=>typeof window.__obf1Dispatch==='function');
    bridgeReady=true;
    for(const msg of queued.splice(0))await deliver(msg);
    await page.waitForFunction(()=>document.body.dataset.ready==='true',null,{timeout:25000});
    await page.evaluate(p=>{
      window.__wirescapeTest.clearAutosave();
      window.__wirescapeTest.load(p,'OB-f1 read-only heaviest bundled patch');
      window.__wirescapeTest.fit();
    },patch);
    await page.waitForFunction(()=>document.querySelector('[data-testid="status-engine"]')?.textContent?.includes('real'),null,{timeout:25000});
    await settleFrames(page,15);
    for(const action of ACTIONS){
      const record={action,gesture_completed:false,frames:[],sent:[],acks:[],
        telemetry_count:0,error:null};
      try{
        await frameStart(page);
        const gestureRecord=await gesture(page,action,patch);
        applyGesture(record,gestureRecord);
        await settleFrames(page,10);
        if(action==='knob'){
          await page.waitForFunction(()=>window.__obf1Bridge.allAcked(),{timeout:15000})
            .catch(()=>{record.error='one or more native parameter ACKs not observed';});
        }
        Object.assign(record,await frameStop(page));
      }catch(err){
        record.error=String(err.message||err).slice(0,900);
        try{Object.assign(record,await frameStop(page));}catch{}
      }
      record.raw_file='raw/'+action+'.json';
      writeFileSync(path.join(OUT,record.raw_file),JSON.stringify(record,null,2)+'\n');
      records.push(record);
      console.log('OBF1 '+action+': '+(record.error||'capture recorded')+
        ', frames='+record.frames.length+', engine ACKs='+record.acks.length);
    }
    const summary={
      schema:'wirescape/ob-f1-ui-facts/1',provenance:{...metadata(),
        chromium:browser.version(),sidecar_executable_sha256:hash(readFileSync(BINARY)),
        selector_script_sha256:hash(readFileSync(__filename)),
        metrics_script_sha256:hash(readFileSync(path.join(__dirname,'ob_f1_metrics.cjs')))},
      method:{selection:selection.selection_rule,
        frame:'browser requestAnimationFrame interval over actual mouse drag / native telemetry activity; nearest-rank p50/p95/max',
        acknowledgements:'RealEngine bridge sent setParam, native --null-audio sidecar v0 correlated ok reply; browser monotonic send/reply clock, not audio-output application time',
        device_scope:'no hardware audio/MIDI; native sidecar --null-audio, stdio bridge, Vite preview 127.0.0.1',
        limitations:'headless Linux Chromium is not Pi, physical audio, GPU compositor, or end-to-end sound; no percentile targets assigned by builder'},
      cpu_rank_file:'cpu-ranking.json',cpu_rank_winner:cpuRanking.winner,
      cpu_rank_measured_count:cpuRanking.measured_count,
      cpu_rank_unavailable_count:cpuRanking.unavailable_count,
      patch:{file:selection.chosen.name,sha256:selection.chosen.sha256,
        module_count:selection.chosen.module_count,connection_count:selection.chosen.connection_count},
      source_records:records.map(r=>r.raw_file),results:consolidate(records),
      native_errors:engineLog.slice(-20)
    };
    writeFileSync(path.join(OUT,'summary.json'),JSON.stringify(summary,null,2)+'\n');
    console.log('OBF1_FACTS_JSON='+JSON.stringify({
      source_commit:summary.provenance.source_commit,patch:summary.patch,results:summary.results
    }));
    if(cpuRanking.unavailable_count>0||summary.results.some(r=>r.status!=='measured'))
      process.exitCode=1; // fail advisory honestly; upload actual raw/unavailable records
    await context.close();
  }finally{
    bridgeReady=false;
    if(browser)await browser.close().catch(()=>{});
    server.kill('SIGTERM');
    engine.stdin.end();
    engine.kill('SIGTERM');
  }
}
main().catch(e=>{
  mkdirSync(OUT,{recursive:true});
  writeFileSync(path.join(OUT,'failure.json'),JSON.stringify({
    schema:'wirescape/ob-f1-ui-facts/1',status:'unavailable',
    reason:String(e.stack||e).slice(0,3500),provenance:metadata()
  },null,2)+'\n');
  console.error('OBF1 unavailable:',e);process.exitCode=1;
});
