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
assert.equal(cpu.self_samples_all.length,1);
assert.equal(cpu.self_samples_all[0].sampled_us,3000);
// An empty/malformed/zero-duration CPU capture must never be reported measured.
const empty=cpuSummary({nodes:[],samples:[],timeDeltas:[]});
assert.equal(empty.status,'unavailable');
assert.match(empty.reason,/no .*CPU sample/i);
assert.equal(cpuSummary({nodes:[{id:1,callFrame:{functionName:'work'}}],
  samples:[],timeDeltas:[]}).status,'unavailable');
assert.equal(cpuSummary({nodes:[{id:1,callFrame:{functionName:'work'}}],
  samples:[1],timeDeltas:[0]}).status,'unavailable');
assert.equal(cpuSummary({nodes:[{id:1,callFrame:{functionName:'work'}}],
  samples:[99],timeDeltas:[1000]}).status,'unavailable');
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
// A function ranked #13 in one trial contributes in full when it ranks
// highly in another. Aggregating per-trial top12 lists loses this 1ms.
const manyNodes=Array.from({length:13},(_,i)=>({
  id:i+1,callFrame:{functionName:i===12?'tail':'large'+i,
                   url:'http://127.0.0.1:4173/assets/profiler.js',lineNumber:i}
}));
const c1=cpuSummary({nodes:manyNodes,
  samples:manyNodes.map(x=>x.id),timeDeltas:manyNodes.map((x,i)=>i===12?1000:2000)});
const c2=cpuSummary({nodes:[
  {id:99,callFrame:{functionName:'tail',
    url:'http://127.0.0.1:4173/assets/profiler.js',lineNumber:12}},
  {id:100,callFrame:{functionName:'weak',url:'',lineNumber:0}}],
  samples:[99,100],timeDeltas:[3000,500]});
assert.equal(c1.status,'measured');
assert.equal(c1.self_samples_all.length,13);
assert.equal(c1.top_self.length,12);
assert.ok(!c1.top_self.some(x=>x.function==='tail'));
const summed=aggregateTrials([
  {frame_intervals_ms:[16],interactions:1,cpu:c1,trace},
  {frame_intervals_ms:[17],interactions:1,cpu:c2,trace}
]);
const totalTail=summed.cpu_attribution.top_self.find(x=>x.function==='tail');
assert.ok(totalTail,'tail should rank after combining complete maps');
assert.equal(totalTail.self_sampled_ms,4); // 1 ms omitted from c1 top12 + 3 ms in c2
assert.equal(totalTail.samples,2);
assert.equal(summed.cpu_attribution.status,'measured');
assert.match(summed.cpu_attribution.self_time_aggregation,/before top-10 truncation/);
assert.equal(cpuSummary({}).status,'unavailable');
// A stale 'measured' object without its full self-time map is ineligible
// for complete aggregation. Never silently sum a truncated leaderboard.
const legacy=aggregateTrials([{frame_intervals_ms:[16],interactions:1,
  cpu:{status:'measured',top_self:[{function:'old',source:'/',line:1,self_sampled_ms:1,samples:1}]},trace}]);
assert.equal(legacy.cpu_attribution.status,'unavailable');
assert.match(legacy.unavailable_reasons.join(' '),/complete CPU self-sample map/);
assert.equal(traceSummary({traceEvents:[]}).status,'unavailable');
const missing=aggregateTrials([{frame_intervals_ms:[16],interactions:1,
  cpu:cpuSummary(null),trace:traceSummary(null)}]);
assert.equal(missing.cpu_attribution.status,'unavailable');
assert.equal(missing.trace_attribution.status,'unavailable');
assert.ok(missing.unavailable_reasons.length===2);
console.log('ui_profile_parse known-answer CPU and timeline tests passed');
