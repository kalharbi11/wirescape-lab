// SPDX-License-Identifier: GPL-3.0-only
// Offline Node.js reference harness for the attached, unmodified GUTTUR DSP.
// No npm packages, no worklet/browser needed. Uses original guttur-worklet.js.
const fs=require('fs'),path=require('path'),vm=require('vm');
let source=fs.readFileSync(path.join(__dirname,'../reference/guttur-worklet.js'),'utf8');
source=source.slice(0,source.indexOf('class GutturProcessor extends AudioWorkletProcessor'));
const ctx={console,globalThis:{}};ctx.globalThis=ctx;vm.createContext(ctx);vm.runInContext(source,ctx);
const Core=ctx.GutturCore;
const scenarios=[
 ['plain','clean',1,1,true],['clean','clean',3,1,false],['weathered','weathered',3,1,false],
 ['raspy','raspy',3,1,false],['chant_voice','chant',3,1,false],['growl','growl',3,1,false],
 ['fry','fry',3,1,false],['ayn','ayn',3,1,false],['ring','ring',3,1,false],
 ['whisper','whisper',3,1,false],['small','small',3,1,false],['kargyraa','kargyraa',3,1,false],
 ['ensemble16','clean',8,2,false]
];
const args=process.argv.slice(2);let out='renders_js',selected='',rate=48000;
for(let i=0;i<args.length;i++){
 if(args[i]==='--output-dir')out=args[++i];else if(args[i]==='--case')selected=args[++i];
 else if(args[i]==='--rate')rate=Number(args[++i]);else throw new Error('unknown argument '+args[i]);
}
fs.mkdirSync(out,{recursive:true});
function wav(name,L,R){
 const b=Buffer.alloc(44+L.length*4);b.write('RIFF',0);b.writeUInt32LE(b.length-8,4);b.write('WAVEfmt ',8);b.writeUInt32LE(16,16);
 b.writeUInt16LE(1,20);b.writeUInt16LE(2,22);b.writeUInt32LE(rate,24);b.writeUInt32LE(rate*4,28);b.writeUInt16LE(4,32);b.writeUInt16LE(16,34);
 b.write('data',36);b.writeUInt32LE(L.length*4,40);
 for(let i=0;i<L.length;i++)for(const [j,x] of [L[i],R[i]].entries()){
  let v=Math.max(-1,Math.min(1,x));let pcm=Math.round(Math.abs(v)*32767)*(v<0?-1:1);
  b.writeInt16LE(pcm,44+i*4+j*2);
 }
 fs.writeFileSync(path.join(out,name+'.wav'),b);
}
for(const [id,preset,throats,nnotes,plain]of scenarios){
 if(selected&&selected!=='all'&&selected!==id)continue;
 const e=new Core.Engine({sampleRate:rate,maxSingers:16,seed:17});
 const presetObj=Core.PRESETS.find(p=>p.id===preset);
 e.presetId=preset;
 const p=Object.assign(Core.defaultParams(),presetObj.p,{throats});
 if(plain){for(const k of ['breath','whisper','jitter','shimmer','tremor','wander','growl','creak','tailFry','flutter','rasp','breaks','vibrato','drive','spread'])p[k]=0;
  p.wet=0;p.sizeSpread=0;p.looseness=0;
 }
 e.setParams(p);
 e.noteOn(48,1);if(nnotes===2)e.noteOn(55,.8);
 const N=Math.round(rate*2),noteEnd=Math.round(rate*.8),L=new Float32Array(N),R=new Float32Array(N);
 let pos=0;while(pos<N){if(pos===noteEnd){e.noteOff(48);if(nnotes===2)e.noteOff(55);}
  const n=Math.min(128,N-pos,pos<noteEnd?noteEnd-pos:N-pos);
  const l=new Float32Array(n),r=new Float32Array(n);e.process(l,r,n);L.set(l,pos);R.set(r,pos);pos+=n;
 }
 wav(id,L,R);
 let ss=0,pk=0;for(let i=0;i<N;i++){ss+=L[i]*L[i]+R[i]*R[i];pk=Math.max(pk,Math.abs(L[i]),Math.abs(R[i]));}
 console.log(`${id}: RMS=${Math.sqrt(ss/(N*2)).toFixed(6)} peak=${pk.toFixed(6)}`);
}
