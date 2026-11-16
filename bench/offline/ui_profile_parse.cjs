// SPDX-License-Identifier: GPL-3.0-only
// Pure devices-off aggregation of Chromium CDP CPU and performance traces.
'use strict';

const quantile = (values, percent) => {
  if (!values.length) return null;
  const sorted = [...values].sort((a,b) => a-b);
  return sorted[Math.max(0, Math.ceil(sorted.length*percent/100)-1)];
};
const round = value => Math.round(value*1000)/1000;
function frameSummary(intervals) {
  const a = intervals.filter(x => Number.isFinite(x) && x > 0);
  return {sample_count:a.length, p50_ms:quantile(a,50),
    p95_ms:quantile(a,95), max_ms:a.length?Math.max(...a):null};
}
function sanitizedSource(url) {
  if (!url) return '[native/anonymous]';
  try {
    const parsed = new URL(url);
    if (parsed.protocol==='http:' || parsed.protocol==='https:')
      return parsed.pathname || '/';
    if (parsed.protocol==='file:') return '[local-file redacted]';
  } catch (_) {}
  if (/^(?:[A-Za-z]:[\\/]|\/|~\/)/.test(url)) return '[local-file redacted]';
  return url.split(/[?#]/)[0].slice(0,180);
}
function cpuSummary(profile) {
  if (!profile || !Array.isArray(profile.nodes) || !Array.isArray(profile.samples)
      || !Array.isArray(profile.timeDeltas) ||
      profile.samples.length !== profile.timeDeltas.length)
    return {status:'unavailable',reason:'missing CDP Profiler nodes/samples/timeDeltas'};
  if (!profile.nodes.length || !profile.samples.length)
    return {status:'unavailable',reason:'no CDP CPU sample observations'};
  const nodes = new Map(profile.nodes.filter(n => n && n.id != null).map(n => [n.id,n]));
  const totals = new Map();
  let totalUs=0, unattributedUs=0, idleUs=0, validSamples=0;
  for (let i=0;i<profile.samples.length;i++) {
    const sample=nodes.get(profile.samples[i]);
    const delta=profile.timeDeltas[i];
    // Zero/negative/nonfinite durations cannot establish a CPU observation.
    if (!Number.isFinite(delta) || delta<=0) continue;
    totalUs += delta;
    if (!sample || !sample.callFrame) {unattributedUs+=delta;continue;}
    validSamples++;
    const frame=sample.callFrame;
    const fn=frame.functionName || '[anonymous]';
    const url=sanitizedSource(frame.url);
    const line=Number.isFinite(frame.lineNumber)?frame.lineNumber+1:null;
    const key=JSON.stringify([fn,url,line]);
    if (/^\((idle|program|garbage collector)\)$/i.test(fn)) {
      if (fn.toLowerCase()==='(idle)') idleUs+=delta;
      else unattributedUs+=delta;
      continue;
    }
    const prior=totals.get(key) || {function:fn,source:url,line,sampled_us:0,samples:0};
    prior.sampled_us+=delta; prior.samples++; totals.set(key,prior);
  }
  if (!validSamples)
    return {status:'unavailable',reason:'no valid positive-duration CDP CPU samples with call frames'};
  // Preserve ALL self samples at microsecond precision until the cross-trial
  // merge is finished. Per-trial and aggregate leaderboards are views, not
  // input to aggregation; top-12 truncation would silently lose small stacks.
  const self_samples_all=[...totals.values()].sort((a,b)=>b.sampled_us-a.sampled_us);
  const top=self_samples_all.slice(0,12).map(x=>({function:x.function,source:x.source,line:x.line,
    self_sampled_ms:round(x.sampled_us/1000),samples:x.samples}));
  return {status:'measured',sample_count:validSamples,
    invalid_or_unattributed_samples:profile.samples.length-validSamples,
    sampled_ms:round(totalUs/1000),idle_ms:round(idleUs/1000),
    unattributed_ms:round(unattributedUs/1000),
    self_samples_all,top_self:top,
    sampling_limit:'CDP statistical CPU self-samples; excludes or blurs sub-sample work; not inclusive call-stack totals'};
}
function markerLabel(event) {
  const values=[event.name,event.args?.name,event.args?.data?.name,
    event.args?.data?.message,event.args?.message];
  return values.filter(x=>typeof x==='string').join(' ');
}
function eventKind(name) {
  if (/^(?:RecalculateStyles|UpdateLayoutTree|ScheduleStyleRecalculation|ParseAuthorStyleSheet)$/.test(name)) return 'style';
  if (/^(?:Layout|Document::UpdateStyleAndLayout|UpdateLayerTree|LayoutInvalidationTracking)$/.test(name)) return 'layout';
  if (/^(?:PrePaint|Paint|PaintImage|CompositeLayers|RasterTask|Rasterize)$/.test(name)) return 'paint';
  if (/^(?:EvaluateScript|FunctionCall|EventDispatch|FireAnimationFrame|RunMicrotasks|TimerFire|V8\.Execute|v8\.execute|CompileScript)$/.test(name)) return 'script';
  return 'unattributed_busy';
}
const priority={unattributed_busy:0,script:1,paint:2,style:3,layout:4};
function traceSummary(trace) {
  const events=Array.isArray(trace)?trace:trace?.traceEvents;
  if (!Array.isArray(events)) return {status:'unavailable',reason:'no Chromium Tracing.traceEvents'};
  const candidates=events.filter(e=>e.ph==='M' && e.name==='thread_name' &&
    /CrRendererMain|RendererMain/.test(String(e.args?.name||'')));
  if (!candidates.length) return {status:'unavailable',reason:'renderer main-thread metadata not present'};
  // Several renderer processes may exist; prefer the page with explicit
  // interaction markers instead of blindly using the first renderer thread.
  let main=null,thread=[];
  let bestScore=-1;
  for(const candidate of candidates) {
    const entries=events.filter(e=>e.pid===candidate.pid && e.tid===candidate.tid);
    const marked=entries.some(e=>markerLabel(e).includes('WS_UI_PROFILE_START')) &&
                 entries.some(e=>markerLabel(e).includes('WS_UI_PROFILE_END'));
    const durations=entries.filter(e=>e.ph==='X' && Number.isFinite(e.dur) && e.dur>0).length;
    const score=(marked?1000000:0)+durations;
    if(score>bestScore){bestScore=score;main=candidate;thread=entries;}
  }
  const starts=thread.filter(e=>markerLabel(e).includes('WS_UI_PROFILE_START') && Number.isFinite(e.ts));
  const ends=thread.filter(e=>markerLabel(e).includes('WS_UI_PROFILE_END') && Number.isFinite(e.ts));
  const windows=thread.filter(e=>e.ph==='X' && Number.isFinite(e.ts)
    && Number.isFinite(e.dur) && e.dur>0);
  if (!windows.length) return {status:'unavailable',reason:'no duration events on renderer main thread'};
  const marked=starts.length>0 && ends.length>0 && ends.at(-1).ts>starts[0].ts;
  const start=marked?starts[0].ts:windows.reduce((v,e)=>Math.min(v,e.ts),Infinity);
  const end=marked?ends.at(-1).ts:windows.reduce((v,e)=>Math.max(v,e.ts+e.dur),-Infinity);
  const transitions=[];
  for (const e of windows) {
    const a=Math.max(start,e.ts), b=Math.min(end,e.ts+e.dur);
    if (b<=a)continue;
    const kind=eventKind(e.name||'');
    transitions.push({t:a,begin:true,kind},{t:b,begin:false,kind});
  }
  transitions.sort((a,b)=>a.t-b.t || Number(a.begin)-Number(b.begin));
  const counts={script:0,style:0,layout:0,paint:0,unattributed_busy:0};
  const durations={script:0,style:0,layout:0,paint:0,unattributed_busy:0};
  let prev=start;
  for(const e of transitions){
    const elapsed=e.t-prev;
    if(elapsed>0) {
      const active=Object.keys(counts).filter(k=>counts[k]>0);
      if(active.length) {
        active.sort((a,b)=>priority[b]-priority[a]);
        durations[active[0]]+=elapsed;
      }
    }
    counts[e.kind]+=(e.begin?1:-1);
    prev=e.t;
  }
  const busy=Object.values(durations).reduce((a,b)=>a+b,0);
  const window=end-start;
  const categories_ms=Object.fromEntries(Object.entries(durations).map(([k,v])=>[k,round(v/1000)]));
  return {status:'measured',window_ms:round(window/1000),
    observed_busy_ms:round(busy/1000),categories_ms,
    unobserved_window_ms:round(Math.max(0,window-busy)/1000),
    renderer_thread:{pid:main.pid,tid:main.tid},
    boundary:marked?'explicit Chromium trace markers':'renderer event-span fallback (interaction window not precisely identified)',
    duration_limit:'Renderer main-thread nested X events, disjoint priority-based duration; compositor/GPU threads excluded; unobserved is not necessarily idle',
    event_count:windows.length};
}
function aggregateTrials(trials) {
  const intervals=trials.flatMap(t=>t.frame_intervals_ms||[]);
  const frame=frameSummary(intervals);
  const cpu=trials.map(t=>t.cpu).filter(r=>r?.status==='measured'
    && Array.isArray(r.self_samples_all));
  const trace=trials.map(t=>t.trace).filter(t=>t?.status==='measured');
  const top=new Map();
  for (const report of cpu) for(const row of report.self_samples_all) {
    const key=JSON.stringify([row.function,row.source,row.line]);
    const p=top.get(key)||{function:row.function,source:row.source,line:row.line,sampled_us:0,samples:0};
    p.sampled_us+=row.sampled_us;p.samples+=row.samples;top.set(key,p);
  }
  const categories={script:0,style:0,layout:0,paint:0,unattributed_busy:0};
  for (const report of trace)for(const key of Object.keys(categories))
    categories[key]+=report.categories_ms[key]||0;
  return {frame,...{repetitions:trials.length,completed_interactions:trials.reduce((a,t)=>a+(t.interactions||0),0),
      observed_duration_ms:round(trials.reduce((a,t)=>a+(t.observed_duration_ms||0),0))},
    cpu_attribution:{status:cpu.length===trials.length?'measured':cpu.length?'partial':'unavailable',
      measured_trials:cpu.length,total_trials:trials.length,
      sampled_ms:round(cpu.reduce((a,r)=>a+r.sampled_ms,0)),
      unattributed_ms:round(cpu.reduce((a,r)=>a+r.unattributed_ms,0)),
      self_time_aggregation:'all per-trial positive-duration function samples, merged before top-10 truncation',
      top_self:[...top.values()].sort((a,b)=>b.sampled_us-a.sampled_us).slice(0,10)
        .map(row=>({function:row.function,source:row.source,line:row.line,
          self_sampled_ms:round(row.sampled_us/1000),samples:row.samples}))},
    trace_attribution:{status:trace.length===trials.length?'measured':trace.length?'partial':'unavailable',
      measured_trials:trace.length,total_trials:trials.length,
      categories_ms:Object.fromEntries(Object.entries(categories).map(([k,v])=>[k,round(v)])),
      observed_busy_ms:round(trace.reduce((a,r)=>a+r.observed_busy_ms,0)),
      unobserved_window_ms:round(trace.reduce((a,r)=>a+r.unobserved_window_ms,0)),
      boundary_modes:[...new Set(trace.map(t=>t.boundary))] },
    unavailable_reasons:trials.flatMap(t=>[t.cpu,t.trace].filter(x=>x?.status!=='measured')
      .map(x=>x?.reason||'missing profile')).concat(
        trials.filter(t=>t.cpu?.status==='measured' && !Array.isArray(t.cpu.self_samples_all))
          .map(()=>'missing complete CPU self-sample map; excluded from aggregate attribution'))};
}
module.exports={frameSummary,sanitizedSource,cpuSummary,traceSummary,aggregateTrials};
