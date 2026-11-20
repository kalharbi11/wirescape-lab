// SPDX-License-Identifier: GPL-3.0-only
// OB-f1 known-answer tests: no Chromium/native process/device/localhost.
'use strict';
const assert=require('node:assert/strict');
const {mkdtempSync,mkdirSync,writeFileSync,rmSync}=require('node:fs');
const path=require('node:path');
const os=require('node:os');
const {chooseHeaviest,percentile,measuredFrames,correlatedAcks,consolidate}=
  require('./ob_f1_metrics.cjs');

const folder=mkdtempSync(path.join(os.tmpdir(),'ob-f1-'));
const fixture=(name,modules,links)=>writeFileSync(path.join(folder,name),
  JSON.stringify({format:'wirescape.native.patch',version:2,
    modules:Array.from({length:modules},(_,i)=>({id:i+1,module:'essentials.vco'})),
    connections:Array.from({length:links},()=>({kind:'signal',from:{module:1,port:'audio'},
      to:{module:2,port:'audio'}}))}));
try{
  fixture('a.json',3,2);fixture('z.json',3,2);fixture('b.json',3,1);
  const chosen=chooseHeaviest(folder);
  assert.equal(chosen.chosen.name,'a.json');
  assert.equal(chosen.inventory.length,3);
  assert.equal(chosen.chosen.module_count,3);
  assert.equal(chosen.chosen.connection_count,2);
  assert.equal(chosen.chosen.sha256.length,64);
}finally{rmSync(folder,{recursive:true,force:true});}

assert.equal(percentile([1,2,3,4,5],95),5);
assert.deepEqual([10,20,30], [10,20,30]);
assert.deepEqual(measuredFrames([10,20,30]),{
  status:'measured',sample_count:3,p50_ms:20,p95_ms:30,max_ms:30});
assert.equal(measuredFrames([]).status,'unavailable');
assert.equal(measuredFrames([0]).p50_ms,null);
assert.equal(measuredFrames([NaN]).status,'unavailable');
const sent=[{id:'u1',type:'setParam',moduleId:2,paramId:'gain',sent_at_ms:12},
            {id:'u2',type:'setParam',moduleId:2,paramId:'gain',sent_at_ms:22}];
const acks=[{id:'u2',type:'setParam',ok:true,received_at_ms:27,gen:'2'},
            {id:'u1',type:'setParam',ok:true,received_at_ms:15,gen:'2'}];
const ok=correlatedAcks(sent,acks);
assert.equal(ok.status,'measured');
assert.equal(ok.command_count,2);
assert.equal(ok.measured_count,2);
assert.equal(ok.p50_ms,3);
assert.equal(ok.p95_ms,5);
assert.equal(ok.max_ms,5);
assert.deepEqual(ok.observations.map(x=>x.latency_ms),[3,5]);
assert.equal(correlatedAcks(sent,acks.slice(0,1)).status,'unavailable');
assert.equal(correlatedAcks([],[]).p50_ms,null);
assert.equal(correlatedAcks(sent,[{id:'u1',type:'setParam',ok:false,
  code:'refused',received_at_ms:14}]).status,'unavailable');
const fake=[{action:'knob',gesture_completed:true,frames:[15,16],
  sent,acks,telemetry_count:0,raw_file:'raw/knob.json'},
  {action:'telemetry',gesture_completed:true,frames:[16,20],
    sent:[],acks:[],telemetry_count:0,raw_file:'raw/telemetry.json'}];
const rows=consolidate(fake);
assert.equal(rows[0].status,'measured');
assert.equal(rows[1].status,'unavailable');
assert.equal(rows[1].telemetry.count,0);
assert.notEqual(rows[1].telemetry.reason,null);
console.log('OB-f1 patch complexity, frame percentiles and correlated real ACK validation tests passed');
