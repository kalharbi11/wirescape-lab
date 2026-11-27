// SPDX-License-Identifier: GPL-3.0-only
const { test, expect } = require('../../studio/node_modules/@playwright/test');
const { _electron: electron } = require('../../studio/node_modules/playwright');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

test('SC4 desktop write-only bridge cancels, refuses escapes and non-empty folders, exports bytes', async () => {
  const dir = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), 'wirescape-sc4-')));
  const target = path.join(dir, 'bundle'), occupied = path.join(dir, 'occupied');
  fs.mkdirSync(target); fs.mkdirSync(occupied);
  fs.writeFileSync(path.join(occupied, 'keep'), 'untouched');
  const stub = path.join(dir, 'engine.cjs');
  fs.writeFileSync(stub, `const readline = require('node:readline');
const send = x => process.stdout.write(JSON.stringify({v:0,session:'sc4',...x})+'\\n');
send({type:'hello',protocol:0,engine:{version:'test',sha:'fixture'},capabilities:[],
 catalogue:{modules:[]},audio:{state:'no-device',deviceId:null,deviceName:null,
 sampleRate:48000,bufferFrames:256,latencyMs:0,cpuPercent:0,dropouts:0},midi:{devices:[],activity:{}}});
const input=readline.createInterface({input:process.stdin});
input.on('line',line=>{const c=JSON.parse(line);send({re:c.id,ok:true,gen:'0'});});
input.on('close',()=>process.exit(0));`);
  const env = { ...process.env, WIRESCAPE_TEST_STUB: '1' }; delete env.ELECTRON_RUN_AS_NODE;
  let app;
  try {
    app = await electron.launch({ executablePath: require('electron'),
      args: ['--no-sandbox', path.resolve(__dirname, '../build/main.js'), '--engine', stub,
        '--null-audio', '--profile-dir', path.join(dir, 'profile')], env });
    const page = await app.firstWindow();
    await expect(page.locator('body')).toHaveAttribute('data-ready', 'true');
    const choose = file => app.evaluate(({dialog}, filename) => {
      dialog.showOpenDialog = async () => {
        globalThis.__sc4Dialogs = (globalThis.__sc4Dialogs ?? 0) + 1;
        return { canceled: filename === null, filePaths: filename === null ? [] : [filename] };
      };
    }, file);
    const write = (bad = false) => page.evaluate(async bad => {
      const name = bad ? '../escape.json' : 'patch-0001.json';
      const patch = JSON.stringify({format:'wirescape.native.patch',version:2,modules:[],connections:[]}) + '\n';
      const manifest = JSON.stringify({format:'wirescape.player',version:1,title:'Set',
        setlist:[{patch:'patches/'+name,title:'Patch',controls:[],pages:[],scripts:[{file:'scripts/voice.py',port:9000}]}]}) + '\n';
      return window.wirescapeBundleExport.write({playerJson:manifest, patches:[{name,text:patch}],
        scripts:[{name:'voice.py',bytes:new Uint8Array([35,10])}]});
    }, bad);
    await choose(null);
    expect(await write()).toBeNull();
    expect(await app.evaluate(() => globalThis.__sc4Dialogs)).toBe(1);
    await choose(target);
    await expect(write(true)).rejects.toThrow(/Invalid native bundle patch/);
    expect(await app.evaluate(() => globalThis.__sc4Dialogs)).toBe(1);
    expect(fs.readdirSync(target)).toEqual([]);
    await choose(occupied);
    await expect(write()).rejects.toThrow(/empty folder/);
    expect(fs.readFileSync(path.join(occupied,'keep'),'utf8')).toBe('untouched');
    await choose(target);
    expect(await write()).toEqual({name:'bundle'});
    expect(fs.readFileSync(path.join(target,'patches/patch-0001.json'),'utf8')).toBe(
      JSON.stringify({format:'wirescape.native.patch',version:2,modules:[],connections:[]})+'\n');
    expect(fs.readFileSync(path.join(target,'scripts/voice.py'))).toEqual(Buffer.from([35,10]));
    expect(JSON.parse(fs.readFileSync(path.join(target,'player.json'),'utf8')).setlist[0].patch).toBe('patches/patch-0001.json');
    await expect(write()).rejects.toThrow(/empty folder/);
    expect(fs.existsSync(path.join(dir,'escape.json'))).toBe(false);
  } finally { if (app) await app.close(); fs.rmSync(dir,{recursive:true,force:true}); }
});
