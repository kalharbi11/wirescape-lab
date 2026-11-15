// SPDX-License-Identifier: GPL-3.0-only
// Deterministic known-answer CPU and main-thread timing tests. No browser/device/sockets.
'use strict';
const assert=require('node:assert/strict');
const {frameSummary,sanitizedSource,cpuSummary,traceSummary,aggregateTrials}
  =require('./ui_profile_parse.cjs');

function cpuFixture() {
  return {nodes:[
      {id:1,callFrame:{functionName:'(root)',url:''}},
      {id:2,callFrame:{functionName:'renderKnob',url:'http://127.0.0.1:4173/assets/index.js',lineNumber:14}},
      {id:3,callFrame:{functionName:'(idle)',url:''}}],
    samples:[2,2,3],timeDeltas:[1000,2000,1000]};
}
function traceFixture() {
  const main={pid:9,tid:7}, e=(name,ts,dur)=>({...main,ph:'X',name,ts,dur});
  return {traceEvents:[
    {...main,ph:'M',name:'thread_name',args:{name:'CrRendererMain'}},
    {...main,ph:'I',name:'TimeStamp',ts:1000,args:{data:{message:'WS_UI_PROFILE_START'}}},
    e('RunTask',1000,8000),
    e('FunctionCall',2000,3000),
    e('Layout',3000,1000),
    e('RecalculateStyles',5000,1000),
    e('Paint',7000,1000),
    {...main,ph:'I',name:'TimeStamp',ts:11000,args:{data:{message:'WS_UI_PROFILE_END'}}},
    {pid:11,tid:1,ph:'X',name:'Layout',ts:1000,dur:5000},
  ]};
}
const cpu=cpuSummary(cpuFixture());
assert.equal(cpu.status,'measured');
assert.equal(cpu.sample_count,3);
assert.equal(cpu.sampled_ms,4);
assert.equal(cpu.idle_ms,1);
assert.equal(cpu.top_self[0].function,'renderKnob');
assert.equal(cpu.top_self[0].source,'/assets/index.js');
assert.equal(cpu.top_self[0].line,15);
assert.equal(cpu.top_self[0].self_sampled_ms,3);
assert.equal(sanitizedSource('/home/runner/private.js'),'[local-file redacted]');
const trace=traceSummary(traceFixture());
assert.equal(trace.status,'measured');
assert.equal(trace.window_ms,10);
assert.equal(trace.observed_busy_ms,8);
assert.equal(trace.unobserved_window_ms,2);
assert.deepEqual(trace.categories_ms,{script:2,style:1,layout:1,paint:1,unattributed_busy:3});
assert.equal(trace.boundary,'explicit Chromium trace markers');
const aggregate=aggregateTrials([
  {frame_intervals_ms:[10,20],interactions:3,observed_duration_ms:30,cpu,trace},
  {frame_intervals_ms:[30,40],interactions:3,observed_duration_ms:70,cpu,trace},
]);
assert.deepEqual(aggregate.frame,{sample_count:4,p50_ms:20,p95_ms:40,max_ms:40});
assert.equal(aggregate.completed_interactions,6);
assert.equal(aggregate.observed_duration_ms,100);
assert.equal(aggregate.cpu_attribution.top_self[0].self_sampled_ms,6);
assert.equal(aggregate.trace_attribution.categories_ms.layout,2);
assert.equal(aggregate.trace_attribution.observed_busy_ms,16);
assert.equal(aggregate.trace_attribution.unobserved_window_ms,4);
assert.equal(cpuSummary({}).status,'unavailable');
assert.equal(traceSummary({traceEvents:[]}).status,'unavailable');
const missing=aggregateTrials([{frame_intervals_ms:[16],interactions:1,
  cpu:cpuSummary(null),trace:traceSummary(null)}]);
assert.equal(missing.cpu_attribution.status,'unavailable');
assert.equal(missing.trace_attribution.status,'unavailable');
assert.ok(missing.unavailable_reasons.length===2);
console.log('ui_profile_parse known-answer CPU and timeline tests passed');
