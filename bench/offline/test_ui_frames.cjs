// SPDX-License-Identifier: GPL-3.0-only
// Synthetic Playwright-compatible objects; no browser, network or audio devices.
'use strict';
const assert = require('node:assert/strict');
const {patch, record, previewCommand} = require('./ui_frames.cjs');

function mockPage(activity) {
  const tracing = {
    async start(options) { activity.push(['start', options.screenshots, options.snapshots]); },
    async stop(options) { activity.push(['stop', options.path]); },
  };
  const mouse = {
    async move(x,y) { activity.push(['move', x,y]); },
    async down() { activity.push(['down']); },
    async up() { activity.push(['up']); },
  };
  const bounds = {x: 20, y: 30, width: 40, height: 20};
  return {
    context() { return {tracing}; },
    async evaluate(fn) { return String(fn).includes('__l4Frames.stop()') ? [12,16,22,30] : undefined; },
    getByTestId(testid) {
      activity.push(['target', testid]);
      return {locator(selector) {
        assert.equal(selector, '.dial-wrap');
        return {async boundingBox() { return bounds; }};
      },async boundingBox() {return bounds;}};
    },
    mouse,
  };
}

async function main() {
  const cmd = previewCommand();
  assert.equal(cmd.executable, process.execPath);
  assert.ok(cmd.args[0].endsWith('vite.js'));
  assert.deepEqual(cmd.args.slice(1), ['preview','--host','127.0.0.1']);
  const graph = patch(50);
  assert.equal(graph.modules.length, 50);
  assert.equal(graph.modules[0].module, 'essentials.vco');
  assert.equal(graph.modules[1].module, 'essentials.vcf');
  for (const action of ['knob','cable']) {
    const activity=[];
    const report=await record(mockPage(activity),50,action);
    assert.deepEqual(report,{frames:4,p50_ms:16,p95_ms:30,max_ms:30});
    assert.equal(activity[0][0], 'start');
    assert.equal(activity.at(-1)[0], 'stop');
    assert.ok(activity.at(-1)[1].endsWith('trace-50-'+action+'.zip'));
    assert.ok(activity.some(event=>event[0]==='down'));
    assert.ok(activity.some(event=>event[0]==='up'));
    if(action==='knob') assert.ok(activity.some(event=>event[1]==='knob-2-cutoff'));
    else assert.ok(activity.some(event=>event[1]==='port-1-output-audio'));
  }
  console.log('ui_frames synthetic regression tests passed');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
