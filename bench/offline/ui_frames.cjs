// SPDX-License-Identifier: GPL-3.0-only
// FakeEngine UI trace and rAF interval measurements, no real devices.
'use strict';
const { chromium } = require('../../apps/studio/node_modules/playwright');
const { spawn } = require('node:child_process');
const { mkdirSync, writeFileSync } = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const { execFileSync } = require('node:child_process');
const ROOT = path.resolve(__dirname, '../..');
const out = path.join(ROOT, 'build_reports/l4/ui');
const BROWSER = process.env.WIRESCAPE_CHROMIUM || '/opt/pw-browsers/chromium';
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
const quant = (values, p) => values.length ? values[Math.ceil(values.length*p/100)-1] : null;
function summary(values) {
  const v = values.slice().sort((a,b) => a-b);
  return { frames: v.length, p50_ms: quant(v,50), p95_ms: quant(v,95), max_ms: v.at(-1) ?? null };
}
function patch(n) {
  const modules = [];
  const positions = {};
  for (let id=1; id<=n; id++) {
    modules.push({id, module: id===1 ? 'essentials.vco' : 'essentials.vcf'});
    positions[id] = id===1 ? [80,80] : id===2 ? [430,80] :
      [80 + ((id-3)%12)*300, 700+Math.floor((id-3)/12)*310];
  }
  return {format: 'wirescape.native.patch', version: 2, modules,
    connections: [], ui: {positions, labels:{}, view:{x:0,y:0,zoom:1}}};
}
async function record(page, n, action) {
  await page.context().tracing.start({screenshots: true, snapshots: true});
  await page.evaluate(() => {
    const times=[]; let prev=0; let active=true;
    const tick=t => { if (!active) return; if (prev) times.push(t-prev); prev=t; requestAnimationFrame(tick); };
    window.__l4Frames={stop: () => {active=false; return times;}};
    requestAnimationFrame(tick);
  });
  const point = async testid => {
    const b = await page.getByTestId(testid).boundingBox();
    if (!b) throw new Error('Not visible: '+testid);
    return {x:b.x+b.width/2,y:b.y+b.height/2};
  };
  if (action==='knob') {
    const b=await page.getByTestId('knob-2-cutoff').locator('.dial-wrap').boundingBox();
    if (!b) throw new Error('Knob absent');
    const x=b.x+b.width/2,y=b.y+b.height/2;
    await page.mouse.move(x,y); await page.mouse.down();
    await page.mouse.move(x,y-80,{steps:30}); await page.mouse.up();
  } else {
    const a=await point('port-1-output-audio');
    const b=await point('port-2-input-audio');
    await page.mouse.move(a.x,a.y); await page.mouse.down();
    await page.mouse.move(b.x,b.y,{steps:30}); await page.mouse.up();
  }
  await pause(250);
  const intervals=await page.evaluate(() => window.__l4Frames.stop());
  await page.context().tracing.stop({path:path.join(out,`trace-${n}-${action}.zip`)});
  return summary(intervals);
}
async function main() {
  mkdirSync(out,{recursive:true});
  const vite=path.join(ROOT,'apps/studio/node_modules/vite/bin/vite.js');
  const server=spawn(process.execPath,[vite,'preview','--host','127.0.0.1'],
                     {cwd:path.join(ROOT,'apps/studio'),stdio:'ignore'});
  server.on('error', error => { console.error('Vite preview spawn failed:', error.message); });
  let browser;
  try {
    let ready=false;
    for (let i=0;i<80;i++) {
      try { const response=await fetch('http://127.0.0.1:4173'); if(response.ok) {ready=true;break;} } catch (_) {}
      await pause(250);
    }
    if (!ready) throw new Error('Vite preview not available on localhost:4173');
    browser=await chromium.launch({executablePath:BROWSER,headless:true,args:['--no-sandbox']});
    const context=await browser.newContext({viewport:{width:1920,height:1080}});
    const records=[];
    for (const n of [50,100,200]) for (const action of ['knob','cable']) {
      const page=await context.newPage();
      await page.goto('http://127.0.0.1:4173');
      await page.waitForFunction(() => document.body.dataset.ready === 'true');
      await page.evaluate(p => {window.__wirescapeTest.clearAutosave();window.__wirescapeTest.load(p,'L4');},patch(n));
      await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
      const result=await record(page,n,action);
      records.push({modules:n,action,...result});
      await page.close();
    }
    await context.close();
    const metadata={commit:execFileSync('git',['rev-parse','HEAD'],{cwd:ROOT,encoding:'utf8'}).trim(),
      date_et:new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York'}).format(new Date()),
      machine:{os:os.platform(),arch:os.arch(),cpu:os.cpus()[0]?.model, audio_devices:'not accessed'},
      method:'Chromium rAF intervals during Playwright mouse drags; trace zip per workload',
      results:records};
    writeFileSync(path.join(out,'summary.json'),JSON.stringify(metadata,null,2)+'\n');
    console.log(path.join(out,'summary.json'));
  } finally { if(browser) await browser.close(); server.kill('SIGTERM'); }
}
main().catch(e=>{console.error(e);process.exitCode=1;});
