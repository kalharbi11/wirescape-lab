// SPDX-License-Identifier: GPL-3.0-only
// OB-f1: pure deterministic selection and measurement parsing; no device or browser.
'use strict';
const crypto=require('node:crypto');
const {readFileSync,readdirSync}=require('node:fs');
const path=require('node:path');

const hash=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
function chooseHeaviest(folder) {
  const rows=readdirSync(folder).filter(n=>n.endsWith('.json')).sort().map(name=>{
    const file=path.join(folder,name),bytes=readFileSync(file);
    const doc=JSON.parse(bytes);
    if(doc.format!=='wirescape.native.patch'||doc.version!==2||
       !Array.isArray(doc.modules)||!Array.isArray(doc.connections))
      throw new Error('invalid bundled native patch: '+name);
    return {name,document:doc,sha256:hash(bytes),bytes:bytes.length,
      module_count:doc.modules.length,connection_count:doc.connections.length};
  });
  if(!rows.length)throw new Error('bundled patch set empty');
  // Heaviest proxy: largest module count, then cable count; lexical tie.
  // This is a GRAPH-COMPLEXITY proxy, never claimed highest actual CPU cost.
  rows.sort((a,b)=>b.module_count-a.module_count||
    b.connection_count-a.connection_count||a.name.localeCompare(b.name,'en'));
  return {selection_rule:'max native module_count, then connection_count, then lexical filename; complexity proxy, not measured CPU-heaviest',
          chosen:rows[0],inventory:rows.map(({document,...rest})=>rest)};
}
function percentile(values,p) {
  if(!values.length)return null;
  const ordered=values.slice().sort((a,b)=>a-b);
  return ordered[Math.ceil(p*ordered.length/100)-1];
}
function measuredFrames(frames) {
  if(!Array.isArray(frames)||frames.some(x=>!Number.isFinite(x)||x<=0))
    return {status:'unavailable',reason:'missing/invalid positive rAF frame intervals',
            sample_count:Array.isArray(frames)?frames.length:0,p50_ms:null,p95_ms:null,max_ms:null};
  if(!frames.length)return {status:'unavailable',reason:'zero captured rAF intervals',
      sample_count:0,p50_ms:null,p95_ms:null,max_ms:null};
  return {status:'measured',sample_count:frames.length,
    p50_ms:percentile(frames,50),p95_ms:percentile(frames,95),
    max_ms:Math.max(...frames)};
}
function correlatedAcks(sent,acks,downAt=null) {
  const candidates=sent.filter(x=>x.type==='setParam');
  const byId=new Map(acks.filter(x=>x.type==='setParam').map(x=>[x.id,x]));
  const matched=candidates.map(x=>{
    const a=byId.get(x.id);
    if(!a)return {id:x.id,status:'unavailable',reason:'matching native ACK not observed'};
    if(!a.ok)return {id:x.id,status:'refused',reason:a.code||'native refusal'};
    if(!Number.isFinite(x.sent_at_ms)||!Number.isFinite(a.received_at_ms)||
       a.received_at_ms<x.sent_at_ms)
      return {id:x.id,status:'unavailable',reason:'missing/invalid browser monotonic timestamps'};
    return {id:x.id,status:'measured',latency_ms:a.received_at_ms-x.sent_at_ms,
            module_id:x.moduleId,param_id:x.paramId,reply_gen:a.gen};
  });
  const values=matched.filter(x=>x.status==='measured').map(x=>x.latency_ms);
  const successful=acks.filter(x=>x.type==='setParam'&&x.ok===true&&
    sent.some(s=>s.id===x.id&&s.type==='setParam')&&
    Number.isFinite(x.received_at_ms)).map(x=>x.received_at_ms);
  const anchored=Number.isFinite(downAt)&&downAt!==null&&successful.length>0&&
    successful.every(t=>t>=downAt);
  const dragToFirst=anchored?Math.min(...successful)-downAt:null;
  const dragToLast=anchored?Math.max(...successful)-downAt:null;
  return {status:candidates.length>0&&values.length===candidates.length?'measured':'unavailable',
          command_count:candidates.length,measured_count:values.length,
          p50_ms:percentile(values,50),p95_ms:percentile(values,95),
          max_ms:values.length?Math.max(...values):null,
          drag_to_first_native_ack_ms:dragToFirst,
          drag_to_last_native_ack_ms:dragToLast,
          observations:matched,
          reason:!candidates.length?'no native setParam issued by actual knob drag':
                 values.length!==candidates.length?'native setParam ACK incomplete/refused':null,
          definition:'browser performance.now() bridge.send(setParam) to correlated sidecar reply delivered via stdin/stdout bridge, includes transport and scheduling, not audio application latency'};
}
function consolidate(records) {
  return records.map(r=>{
    const frame=measuredFrames(r.frames);
    const ack=r.action==='knob'?correlatedAcks(r.sent||[],r.acks||[],r.down_at_ms):
      {status:'not_applicable',reason:'only knob drag issues setParam'};
    const tele=r.action==='telemetry'?
      (r.telemetry_count>0?{status:'measured',count:r.telemetry_count}:
        {status:'unavailable',count:0,reason:'no observed native telemetry; count not interpreted as zero throughput'}):
      {status:'not_applicable'};
    return {action:r.action,status:frame.status==='measured'&&
      (r.action!=='knob'||ack.status==='measured')&&
      (r.action!=='telemetry'||tele.status==='measured')&&
      r.gesture_completed===true?'measured':'unavailable',
      frame,parameter_ack:ack,telemetry:tele,
      gesture_completed:r.gesture_completed===true,
      reason:r.error||null,source_observation:r.raw_file||null};
  });
}
module.exports={hash,chooseHeaviest,percentile,measuredFrames,correlatedAcks,consolidate};
