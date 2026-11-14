// SPDX-License-Identifier: GPL-3.0-only
// Requires Release sidecar, built Electron/Studio, Xvfb on headless Linux.
'use strict';
const { _electron } = require('../../apps/studio/node_modules/playwright');
const electronExecutable = require('../../apps/desktop/node_modules/electron');
const { mkdirSync, writeFileSync, readFileSync, readdirSync, statSync } = require('node:fs');
const { execFileSync } = require('node:child_process');
const path = require('node:path');
const os = require('node:os');
const ROOT = path.resolve(__dirname, '../..');
const out = path.join(ROOT, 'build_reports/l4/startup');
const main = path.join(ROOT, 'apps/desktop/build/main.js');
const engine = path.join(ROOT, 'build/native/wirescape-engine');
function procTree(rootPid) {
  if (os.platform() !== 'linux') return null;
  const processes=[];
  for (const entry of readdirSync('/proc').filter(n=>/^\d+$/.test(n))) {
    try {
      const stat=readFileSync('/proc/'+entry+'/stat','utf8');
      const rest=stat.slice(stat.lastIndexOf(')')+2).split(' ');
      const ppid=Number(rest[1]);
      const status=readFileSync('/proc/'+entry+'/status','utf8');
      const rss=/^VmRSS:\s+(\d+) kB/m.exec(status);
      processes.push({pid:Number(entry),ppid,rss_kib:rss?Number(rss[1]):0,
        process:readFileSync('/proc/'+entry+'/comm','utf8').trim()});
    } catch (_) { /* process exited during enumeration */ }
  }
  const selected=new Set([rootPid]);
  let changed=true;
  while(changed) { changed=false; for(const p of processes) if(selected.has(p.ppid) && !selected.has(p.pid)) {
    selected.add(p.pid); changed=true;
  }}
  const group=processes.filter(p=>selected.has(p.pid));
  return {rss_kib:group.reduce((sum,p)=>sum+p.rss_kib,0), processes:group};
}
const quant = (v,p) => v.length ? v.slice().sort((a,b)=>a-b)[Math.ceil(v.length*p/100)-1] : null;
async function sample() {
  const wall = Date.now();
  const app = await _electron.launch({
    executablePath: electronExecutable,
    args: ['--no-sandbox',main,'--engine',engine,'--null-audio'],
    env: {...process.env, CI:'1', GITHUB_ACTIONS:'1'},
  });
  const stderr=[];
  try {
    app.process().stderr?.on('data', chunk=>stderr.push(chunk.toString('utf8')));
    const page = await app.firstWindow();
    await page.waitForFunction(() => document.body.dataset.ready === 'true');
    const paint = await page.evaluate(() => {
      const nav = performance.getEntriesByType('navigation')[0];
      const paints = performance.getEntriesByType('paint');
      const fcp = paints.find(p=>p.name==='first-contentful-paint') || paints[0];
      return {paint_since_navigation_ms: fcp?.startTime ?? null,
              paint_epoch_ms: fcp ? performance.timeOrigin+fcp.startTime : null,
              nav_start_epoch_ms:performance.timeOrigin,
              navigation_duration_ms:nav?.duration ?? null};
    });
    const boot=stderr.join('').match(/boot-to-first-hello-ms=(\d+(?:\.\d+)?)/);
    const idle=procTree(app.process().pid);
    let loaded=null;
    try {
      const dir=path.join(ROOT,'native/examples');
      const candidates=readdirSync(dir).filter(f=>f.endsWith('.json')).map(f=>{
        const file=path.join(dir,f), document=JSON.parse(readFileSync(file,'utf8'));
        return {file,document,size:statSync(file).size};
      }).filter(x=>x.document.format==='wirescape.native.patch').sort((a,b)=>b.size-a.size);
      if(candidates.length) {
        await page.evaluate(p => window.__wirescapeTest.load(p,'L4'),candidates[0].document);
        await page.waitForTimeout(500);
        loaded={patch:path.relative(ROOT,candidates[0].file), ...procTree(app.process().pid)};
      }
    } catch(e) {loaded={error:String(e)};}
    return {electron_idle:idle,electron_loaded:loaded,
            hello_from_main_boot_ms:boot ? Number(boot[1]) : null,
            studio_first_paint_from_launch_ms:paint.paint_epoch_ms===null ? null : paint.paint_epoch_ms-wall,
            ...paint};
  } finally { await app.close(); }
}
async function mainRun() {
  mkdirSync(out,{recursive:true});
  const records=[];
  for(let i=0;i<10;i++) records.push({run:i+1,...await sample()});
  const hello=records.map(r=>r.hello_from_main_boot_ms).filter(Number.isFinite);
  const fcp=records.map(r=>r.studio_first_paint_from_launch_ms).filter(Number.isFinite);
  const record={commit:execFileSync('git',['rev-parse','HEAD'],{cwd:ROOT,encoding:'utf8'}).trim(),
    date_et:new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York'}).format(new Date()),
    machine:{os:os.platform(),arch:os.arch(),cpu:os.cpus()[0]?.model,audio_devices:'not accessed'},
    mode:'--null-audio',runs:records,
    summary:{hello:{n:hello.length,median_ms:quant(hello,50),max_ms:hello.length?Math.max(...hello):null},
             first_paint:{n:fcp.length,median_ms:quant(fcp,50),max_ms:fcp.length?Math.max(...fcp):null}},
    clocks:'hello value from Electron main boot stderr; paint epoch from renderer performance; launch wall clock Date.now()'};
  writeFileSync(path.join(out,'summary.json'),JSON.stringify(record,null,2)+'\n');
  console.log(path.join(out,'summary.json'));
}
mainRun().catch(e=>{console.error(e);process.exitCode=1;});
