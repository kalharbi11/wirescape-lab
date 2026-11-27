// SPDX-License-Identifier: GPL-3.0-only
import { app, BrowserWindow, dialog, ipcMain, Menu, net, protocol, screen, shell } from 'electron';
import { spawn, ChildProcessWithoutNullStreams } from 'node:child_process';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { pathToFileURL } from 'node:url';
import { randomUUID } from 'node:crypto';

protocol.registerSchemesAsPrivileged([{
  scheme: 'app', privileges: { standard: true, secure: true, supportFetchAPI: true }
}]);
const LIMIT = 2 * 1024 * 1024;
const MAX_PENDING = 256;
const MAX_STDIN_BUFFER = 4 * LIMIT;
// RS / 0023 R2.5: indefinite backoff; only a stable heartbeat resets it.
const RESTART_INITIAL_MS = 250;
const RESTART_MAX_MS = 30_000;
const RESTART_WINDOW_MS = 30_000;
const RESTART_STATUS_GAP_MS = 2_000;
const ENGINE_FLAGS_WITH_VALUE = new Set(['--device', '--block', '--rate', '--settings']);
const argv = process.argv.slice(1);
let enginePath: string | undefined;
let initialFullscreen = false;
let isolatedProfile: string | null = null;
const engineArgs: string[] = [];
for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  if (a === '--engine') enginePath = argv[++i];
  else if (a === '--fullscreen') initialFullscreen = true;
  else if (a === '--profile-dir') {
    const chosen = argv[++i];
    if (!chosen || !path.isAbsolute(chosen)) throw new Error('--profile-dir requires an absolute directory');
    if (isolatedProfile !== null) throw new Error('--profile-dir must be supplied only once');
    isolatedProfile = path.resolve(chosen);
  }
  else if (a === '--confirm-audio' || a === '--confirm-midi' || a === '--confirm-lan' || a === '--null-audio') engineArgs.push(a);
  else if (ENGINE_FLAGS_WITH_VALUE.has(a)) engineArgs.push(a, argv[++i]);
}
// Opt-in source/test profile: configure both Electron paths before app readiness.
// Fail closed on duplicate settings flags and symlinked paths; the engine uses
// the LAST --settings, so validating only the first would leak outside profile.
if (isolatedProfile !== null) {
  const profile = isolatedProfile;
  // Check existing ancestors BEFORE creating anything through a symlink.
  let ancestor = profile;
  while (!fs.existsSync(ancestor)) {
    const parent = path.dirname(ancestor);
    if (parent === ancestor) throw new Error('Invalid profile directory');
    ancestor = parent;
  }
  if (fs.realpathSync(ancestor) !== ancestor)
    throw new Error('Profile directory must not contain a symlinked ancestor');
  fs.mkdirSync(profile, { recursive: true, mode: 0o700 });
  if (fs.realpathSync(profile) !== profile) throw new Error('Profile directory must not be a symlink');
  const userData = path.join(profile, 'userData');
  const sessionData = path.join(profile, 'sessionData');
  for (const dir of [userData, sessionData]) {
    fs.mkdirSync(dir, { recursive: true, mode: 0o700 });
    if (fs.lstatSync(dir).isSymbolicLink() || !fs.statSync(dir).isDirectory() ||
        fs.realpathSync(dir) !== dir)
      throw new Error('Invalid profile subdirectory');
  }
  const positions: number[] = [];
  for (let i = 0; i < engineArgs.length; i++) {
    if (engineArgs[i] === '--settings') {
      positions.push(i);
      i++; // Skip this flag's value; reject missing/relative values below.
    }
  }
  if (positions.length > 1) throw new Error('Duplicate --settings in isolated profile');
  const settingsIndex = positions.length ? positions[0] : -1;
  const requested = settingsIndex === -1 ?
    path.join(profile, 'native-settings.json') : engineArgs[settingsIndex + 1];
  if (!requested || !path.isAbsolute(requested))
    throw new Error('Isolated native --settings must be an absolute file path');
  const selected = path.resolve(requested);
  if (!selected.startsWith(profile + path.sep))
    throw new Error('Native settings must stay within the isolated profile');

  // The file may not yet exist. Resolve its nearest existing parent, so an
  // inside-looking path through a symlink cannot write to an outside directory.
  let settingsParent = path.dirname(selected);
  while (!fs.existsSync(settingsParent)) {
    const parent = path.dirname(settingsParent);
    if (parent === settingsParent) throw new Error('Invalid native settings parent');
    settingsParent = parent;
  }
  const realParent = path.resolve(fs.realpathSync(settingsParent),
    path.relative(settingsParent, path.dirname(selected)));
  if (realParent !== profile && !realParent.startsWith(profile + path.sep))
    throw new Error('Native settings parent escapes the isolated profile');
  // lstat also catches dangling symlinks, which existsSync would miss.
  try {
    if (fs.lstatSync(selected).isSymbolicLink() ||
        fs.realpathSync(selected) !== path.join(realParent, path.basename(selected)))
      throw new Error('Native settings file must not be a symlink');
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== 'ENOENT') throw error;
  }

  app.setPath('userData', userData);
  app.setPath('sessionData', sessionData);
  if (settingsIndex === -1) engineArgs.push('--settings', selected);
  else engineArgs[settingsIndex + 1] = selected;
}
let window: BrowserWindow | null = null;
const UI_DIR = path.resolve(__dirname, '../../studio/dist');
type EngineProcess = {
  process: ChildProcessWithoutNullStreams; expected: boolean; session: string | null;
  statusSince: number | null; lastStatusAt: number | null; stable: boolean;
};
let active: EngineProcess | null = null;
let shuttingDown = false;
let restartInProgress = false;
let lastHello: string | null = null;
let engineReady = false;
let readyAt: bigint | null = null;
let loggedHelloTime = false;
let loggedAudioTime = false;
let patchPath: string | null = null;
let menuId = 0;
const pending = new Set<string>();
const fastCrashes: number[] = [];
let nextRestartDelay = RESTART_INITIAL_MS;
let restartTimer: ReturnType<typeof setTimeout> | null = null;
let restartBanner = false;
type RestartPhase = 'starting' | 'waiting' | 'recovering' | 'stable';
let lastRestartPolicy = {
  v: 0, type: 'app.engineRestartPolicy', phase: 'starting' as RestartPhase,
  delayMs: 0, banner: false,
};
function publishRestartPolicy(phase: RestartPhase, delayMs = 0): void {
  lastRestartPolicy = { v: 0, type: 'app.engineRestartPolicy', phase, delayMs, banner: restartBanner };
  sendRestartPolicy();
}
function sendRestartPolicy(): void {
  if (window && !window.isDestroyed() && !window.webContents.isDestroyed())
    window.webContents.send('wirescape:restart-policy', lastRestartPolicy);
}
function cancelRestartTimer(): void {
  if (restartTimer !== null) clearTimeout(restartTimer);
  restartTimer = null;
}
function scheduleCrashRestart(): void {
  if (shuttingDown || restartTimer !== null) return;
  const now = performance.now();
  fastCrashes.push(now);
  while (fastCrashes.length && now - fastCrashes[0] > RESTART_WINDOW_MS) fastCrashes.shift();
  if (fastCrashes.length >= 3) restartBanner = true;
  // Only the three newest failures matter to the banner; no unbounded history.
  if (fastCrashes.length > 3) fastCrashes.shift();
  const delay = nextRestartDelay;
  nextRestartDelay = Math.min(RESTART_MAX_MS, delay * 2);
  publishRestartPolicy('waiting', delay);
  console.error('engine-restart-delay-ms=' + delay);
  restartTimer = setTimeout(() => {
    restartTimer = null;
    if (!active && !shuttingDown && !restartInProgress) startEngine();
  }, delay);
}
// Stability is 30 seconds of status from the current hello/session, with no
// gap above 2 seconds. A hello alone or merely an alive process is not proof
// of recovery. This is a reset condition, not a new hang-kill policy.
function observeRestartStatus(state: EngineProcess): void {
  if (state.stable) return;
  const now = performance.now();
  if (state.lastStatusAt === null || now - state.lastStatusAt > RESTART_STATUS_GAP_MS)
    state.statusSince = now;
  state.lastStatusAt = now;
  if (state.statusSince === null || now - state.statusSince < RESTART_WINDOW_MS) return;
  state.stable = true;
  nextRestartDelay = RESTART_INITIAL_MS;
  fastCrashes.length = 0;
  restartBanner = false;
  publishRestartPolicy('stable');
}

function notify(message: object | string): void {
  if (window && !window.isDestroyed() && !window.webContents.isDestroyed()) {
    window.webContents.send('wirescape:message', typeof message === 'string' ? message : JSON.stringify(message));
  }
}
function refusal(id: string | null, code: string, message: string): void {
  notify({ v: 0, re: id, ok: false, gen: '0', code, message });
}
function decodeLine(bytes: Buffer): string | null {
  if (bytes.length > LIMIT) return null;
  try { return new TextDecoder('utf-8', { fatal: true }).decode(bytes); } catch { return null; }
}
function handleEngineLine(raw: string, owner: ChildProcessWithoutNullStreams): void {
  const state = active;
  if (!state || state.process !== owner) return;
  let obj: Record<string, unknown>;
  try {
    obj = JSON.parse(raw);
    if (!obj || typeof obj !== 'object' || Array.isArray(obj) || obj.v !== 0) return;
  } catch { return; }
  if (obj.type === 'hello') {
    if (typeof obj.session !== 'string') return;
    if (state.session !== obj.session) {
      state.session = obj.session;
      state.statusSince = state.lastStatusAt = null;
      state.stable = false;
      publishRestartPolicy('recovering');
    }
    engineReady = true;
    lastHello = raw;
    if (!loggedHelloTime && readyAt !== null) {
      loggedHelloTime = true;
      console.error('boot-to-first-hello-ms=' + Number(process.hrtime.bigint() - readyAt) / 1e6);
    }
  } else if (!engineReady) return;
  const status = obj.status as { audio?: { state?: unknown }; midi?: unknown } | undefined;
  if (obj.type === 'status' && state.session !== null && obj.session === state.session &&
      status && typeof status === 'object' && status.audio && typeof status.audio === 'object' &&
      status.midi && typeof status.midi === 'object') observeRestartStatus(state);
  if (obj.type === 'status' && !loggedAudioTime && readyAt !== null &&
      status?.audio?.state === 'running') {
    loggedAudioTime = true;
    console.error('boot-to-audio-running-ms=' + Number(process.hrtime.bigint() - readyAt) / 1e6);
  }
  if (typeof obj.type === 'string' && obj.type.startsWith('app.')) return;
  if (typeof obj.re === 'string') pending.delete(obj.re);
  notify(raw); // Preserve the child's wire line; only app.* is main-owned.
}
function drainLines(proc: ChildProcessWithoutNullStreams): void {
  let fragments: Buffer[] = [];
  let size = 0;
  let dropping = false;
  proc.stdout.on('data', (chunk: Buffer) => {
    let start = 0;
    while (start < chunk.length) {
      const lf = chunk.indexOf(10, start);
      const end = lf < 0 ? chunk.length : lf;
      let part = chunk.subarray(start, end);
      if (!dropping) {
        if (size + part.length > LIMIT + 1) {
          fragments = [];
          size = 0;
          dropping = true;
        } else {
          fragments.push(part);
          size += part.length;
        }
      }
      if (lf >= 0) {
        if (!dropping) {
          let line = Buffer.concat(fragments, size);
          if (line.length && line[line.length - 1] === 13) line = line.subarray(0, -1);
          const raw = decodeLine(line);
          if (raw !== null) handleEngineLine(raw, proc);
        }
        fragments = [];
        size = 0;
        dropping = false;
      }
      start = end + 1;
    }
  });
}
function command(raw: string): void {
  if (Buffer.byteLength(raw, 'utf8') > LIMIT) return;
  let obj: Record<string, unknown>;
  try {
    obj = JSON.parse(raw);
    if (!obj || typeof obj !== 'object' || Array.isArray(obj) || obj.v !== 0 ||
        typeof obj.type !== 'string' || typeof obj.id !== 'string' ||
        !/^[\x21-\x7e]{1,64}$/.test(obj.id)) return;
  } catch { return; }
  const id = obj.id as string;
  if (obj.type === 'app.restartEngine') {
    void restartEngine().then(() => notify({ v: 0, re: id, ok: true, gen: '0' }))
      .catch(() => refusal(id, 'unavailable', 'Could not restart engine'));
    return;
  }
  if (obj.type.startsWith('app.')) { refusal(id, 'invalid', 'Unknown app command'); return; }
  if (!active || !engineReady || active.process.stdin.destroyed) {
    refusal(id, 'unavailable', 'Engine is disconnected');
    return;
  }
  if (pending.has(id)) { refusal(id, 'duplicate', 'Request id already pending'); return; }
  if (pending.size >= MAX_PENDING || active.process.stdin.writableLength + Buffer.byteLength(raw) + 1 > MAX_STDIN_BUFFER) {
    refusal(id, 'busy', 'Engine queue full');
    return;
  }
  pending.add(id);
  try { active.process.stdin.write(raw + '\n', 'utf8'); }
  catch { pending.delete(id); refusal(id, 'unavailable', 'Engine pipe failed'); }
}
function engineExecutable(): string {
  if (enginePath) return enginePath;
  const filename = process.platform === 'win32' ? 'wirescape-engine.exe' : 'wirescape-engine';
  const installed = path.join(app.getAppPath(), filename);
  if (fs.existsSync(installed)) return installed;
  return path.resolve(app.getAppPath(), '../../build/native', filename);
}
function startEngine(): void {
  if (active || shuttingDown) return;
  publishRestartPolicy('starting');
  engineReady = false;
  lastHello = null;
  pending.clear();
  const executable = engineExecutable();
  // Only the explicit test harness may run a Node protocol stub.
  const stub = process.env.WIRESCAPE_TEST_STUB === '1';
  let child: ChildProcessWithoutNullStreams;
  try {
    child = spawn(stub ? process.execPath : executable, stub ? [executable, ...engineArgs] : engineArgs, {
      // Node's default stdio is three pipes; no socket or shell is involved.
      windowsHide: true,
      env: stub ? { ...process.env, ELECTRON_RUN_AS_NODE: '1' } : process.env
    });
  } catch (error) {
    console.error('wirescape-engine spawn:', error);
    notify({ v: 0, type: 'app.engineExited', exitCode: null, signal: null, expected: false });
    scheduleCrashRestart();
    return;
  }
  const state: EngineProcess = { process: child, expected: false, session: null,
    statusSince: null, lastStatusAt: null, stable: false };
  active = state;
  drainLines(child);
  child.stdin.on('error', () => {
    if (active !== state) return;
    for (const id of pending) refusal(id, 'unavailable', 'Engine pipe failed');
    pending.clear();
  });
  child.stderr.on('data', (data: Buffer) => console.error('wirescape-engine:', data.toString('utf8').slice(0, 2048)));
  child.on('error', err => console.error('wirescape-engine spawn:', err.message));
  child.once('close', (code, signal) => {
    // One line per exit so an owner log separates crashes (e.g. 3221225477) from restarts.
    console.error(`engine-exit code=${code} signal=${signal} expected=${state.expected}`);
    if (active !== state) return;
    active = null;
    engineReady = false;
    lastHello = null;
    for (const id of pending) refusal(id, 'unavailable', 'Engine disconnected');
    pending.clear();
    notify({ v: 0, type: 'app.engineExited', exitCode: code, signal, expected: state.expected });
    if (!state.expected && !shuttingDown && !restartInProgress) scheduleCrashRestart();
  });
}
async function stopEngine(): Promise<void> {
  const state = active;
  if (!state) return;
  state.expected = true;
  const child = state.process;
  if (!child.stdin.destroyed) child.stdin.end(); // EOF is the protocol's graceful shutdown.
  await new Promise<void>(resolve => {
    if (child.exitCode !== null || child.signalCode !== null) { resolve(); return; }
    const timeout = setTimeout(() => { if (!child.killed) child.kill(); }, 2000);
    child.once('close', () => { clearTimeout(timeout); resolve(); });
  });
}
async function restartEngine(): Promise<void> {
  if (shuttingDown || restartInProgress) throw new Error('Restart unavailable');
  restartInProgress = true;
  // Explicit user restart supersedes a scheduled retry, but does not reset its
  // backoff history. Only stable status resets that. Never leave a second timer.
  cancelRestartTimer();
  try {
    await stopEngine();
    active = null;
    startEngine();
  } finally { restartInProgress = false; }
}
function savedBounds(): Electron.Rectangle | undefined {
  try {
    const file = path.join(app.getPath('userData'), 'window-state.json');
    if (fs.statSync(file).size > 2048) return;
    const value: unknown = JSON.parse(fs.readFileSync(file, 'utf8'));
    if (!value || typeof value !== 'object') return;
    const b = value as Record<string, number>;
    if (![b.x, b.y, b.width, b.height].every(Number.isInteger) ||
        b.width < 640 || b.height < 480 || b.width > 10000 || b.height > 10000) return;
    if (!screen.getAllDisplays().some(d => b.x < d.bounds.x + d.bounds.width &&
        b.x + b.width > d.bounds.x && b.y < d.bounds.y + d.bounds.height &&
        b.y + b.height > d.bounds.y)) return;
    return { x: b.x, y: b.y, width: b.width, height: b.height };
  } catch { return; }
}
function saveBounds(): void {
  if (!window || window.isDestroyed() || window.isMinimized() || window.isFullScreen()) return;
  try {
    const file = path.join(app.getPath('userData'), 'window-state.json');
    fs.writeFileSync(file, JSON.stringify(window.getBounds()), { mode: 0o600 });
  } catch { /* An unwritable preference must not block closing. */ }
}
function senderAllowed(event: Electron.IpcMainEvent | Electron.IpcMainInvokeEvent): boolean {
  return !!window && !window.isDestroyed() && event.sender === window.webContents &&
    event.senderFrame === window.webContents.mainFrame;
}

// A92: separate, narrowly scoped preset I/O. No patch file identity changes,
// and renderer-supplied filenames are accepted only as leaf tokens for listing.
const PRESET_LIMIT = 256 * 1024;
type PresetModule = 'osc.in' | 'osc.out';
function presetModule(value: unknown): value is PresetModule {
  return value === 'osc.in' || value === 'osc.out';
}
function presetHeader(text: string): { module: PresetModule; name: string; config: Record<string, unknown> } {
  if (Buffer.byteLength(text, 'utf8') > PRESET_LIMIT) throw new Error('OSC preset exceeds 256 KiB.');
  const p = JSON.parse(text);
  if (!p || p.format !== 'wirescape.osc.preset' || p.version !== 1 || !presetModule(p.module) ||
      typeof p.name !== 'string' || !p.name.trim() || p.name.length > 120 ||
      /[\x00-\x1f\x7f]/.test(p.name) || !p.config || typeof p.config !== 'object' ||
      Array.isArray(p.config)) throw new Error('Invalid OSC preset header.');
  return { module: p.module, name: p.name, config: p.config };
}
// At the write boundary accept only the v1 portable shape; imports may contain
// extra fields because Studio explicitly discards them before applying a preset.
function portablePreset(preset: ReturnType<typeof presetHeader>): boolean {
  const isIn = preset.module === 'osc.in';
  const only = (v: unknown, keys: string[]): v is Record<string, unknown> =>
    !!v && typeof v === 'object' && !Array.isArray(v) &&
    Object.keys(v).every(k => keys.includes(k));
  const config = preset.config;
  const rowKeys = isIn ? ['pattern', 'argument', 'kind', 'input_min', 'input_max',
    'output_min', 'output_max', 'smoothing_ms', 'timeout_ms', 'stale', 'enabled']
    : ['address', 'kind', 'deadband', 'enabled'];
  return only(config, isIn ? ['port', 'rows'] : ['port', 'rows', 'notes', 'rate_hz']) &&
    Array.isArray(config.rows) && config.rows.length === 8 &&
    config.rows.every(row => only(row, rowKeys)) &&
    (isIn || only(config.notes, ['address', 'enabled']));
}
function presetLeaf(value: unknown): value is string {
  return typeof value === 'string' && value.length <= 240 && /^[^\\/:*?"<>|\x00-\x1f]+\.json$/i.test(value) &&
    path.basename(value) === value;
}
async function presetRoot(): Promise<string> {
  const root = await fs.promises.realpath(app.getPath('userData'));
  let current = root;
  for (const part of ['presets', 'osc']) {
    current = path.join(current, part);
    try { await fs.promises.mkdir(current, { mode: 0o700 }); }
    catch (e) { if ((e as NodeJS.ErrnoException).code !== 'EEXIST') throw e; }
    const info = await fs.promises.lstat(current);
    if (!info.isDirectory() || info.isSymbolicLink()) throw new Error('Invalid OSC preset directory.');
  }
  return current;
}
async function readPreset(filename: string): Promise<string> {
  if (!/\.json$/i.test(filename)) throw new Error('Expected an OSC preset JSON file.');
  const info = await fs.promises.lstat(filename);
  if (!info.isFile() || info.isSymbolicLink() || info.size > PRESET_LIMIT)
    throw new Error('Invalid OSC preset file (256 KiB maximum).');
  const handle = await fs.promises.open(filename, fs.constants.O_RDONLY | (fs.constants.O_NOFOLLOW ?? 0));
  try {
    const stat = await handle.stat();
    if (!stat.isFile() || stat.size > PRESET_LIMIT) throw new Error('Invalid OSC preset file.');
    const buffer = Buffer.allocUnsafe(PRESET_LIMIT + 1);
    let size = 0;
    while (size < buffer.length) {
      const { bytesRead } = await handle.read(buffer, size, buffer.length - size, size);
      if (!bytesRead) break;
      size += bytesRead;
    }
    if (size > PRESET_LIMIT) throw new Error('OSC preset exceeds 256 KiB.');
    const text = new TextDecoder('utf-8', { fatal: true }).decode(buffer.subarray(0, size));
    presetHeader(text);
    return text;
  } finally { await handle.close(); }
}
async function presetOperation(request: unknown): Promise<unknown> {
  if (!window || !request || typeof request !== 'object') throw new Error('Invalid OSC preset request.');
  const { op, file, module, text, name } = request as Record<string, unknown>;
  const root = await presetRoot();
  if (op === 'list') {
    if (!presetModule(module)) throw new Error('Invalid OSC preset module.');
    const entries: { file: string; name: string }[] = [];
    let examined = 0;
    const dir = await fs.promises.opendir(root);
    for await (const entry of dir) {
      if (++examined > 1024 || entries.length >= 256) break;
      if (!entry.isFile() || !presetLeaf(entry.name)) continue;
      try {
        const p = presetHeader(await readPreset(path.join(root, entry.name)));
        if (p.module === module) entries.push({ file: entry.name, name: p.name });
      } catch { /* Broken or oversized files never become buttons. */ }
    }
    return entries.sort((a, b) => a.name.localeCompare(b.name) || a.file.localeCompare(b.file));
  }
  if (op === 'read') {
    if (!presetLeaf(file)) throw new Error('Invalid OSC preset filename.');
    const filename = path.join(root, file);
    if (path.dirname(await fs.promises.realpath(filename)) !== root)
      throw new Error('OSC preset is outside the preset directory.');
    return readPreset(filename);
  }
  if (op === 'choose') {
    const result = await dialog.showOpenDialog(window, { title: 'Load OSC preset', defaultPath: root,
      properties: ['openFile'], filters: [{ name: 'OSC preset', extensions: ['json'] }] });
    return result.canceled || !result.filePaths[0] ? null : readPreset(result.filePaths[0]);
  }
  if (op === 'save') {
    if (typeof text !== 'string' || typeof name !== 'string') throw new Error('Invalid OSC preset save.');
    const preset = presetHeader(text);
    if (name !== preset.name || !portablePreset(preset))
      throw new Error('OSC presets may contain only portable mapping fields, not network settings.');
    const leaf = name.replace(/[^a-zA-Z0-9_-]+/g, '_') + '.json';
    const result = await dialog.showSaveDialog(window, { title: 'Save OSC preset',
      defaultPath: path.join(root, leaf), filters: [{ name: 'OSC preset', extensions: ['json'] }] });
    if (result.canceled || !result.filePath) return null;
    const filename = result.filePath;
    if (!/\.json$/i.test(filename)) throw new Error('Expected an OSC preset JSON filename.');
    // Refuse overwriting unrelated documents (including a native patch).
    try { await readPreset(filename); }
    catch (e) { if ((e as NodeJS.ErrnoException).code !== 'ENOENT') throw new Error('Refusing to overwrite a non-preset file.'); }
    const temp = path.join(path.dirname(filename), '.' + path.basename(filename) + '.' + randomUUID() + '.tmp');
    try {
      await fs.promises.writeFile(temp, text, { flag: 'wx', mode: 0o600 });
      await fs.promises.rename(temp, filename);
    } finally { await fs.promises.rm(temp, { force: true }).catch(() => {}); }
    return null;
  }
  if (op === 'folder') {
    const error = await shell.openPath(root);
    if (error) throw new Error('Could not open OSC preset folder.');
    return null;
  }
  throw new Error('Unknown OSC preset request.');
}

async function patchDialogPath(save: boolean): Promise<string> {
  if (patchPath) return patchPath;
  const directory = path.join(app.getPath('userData'), 'patches');
  try {
    await fs.promises.mkdir(directory, { recursive: true, mode: 0o700 });
  } catch { throw new Error('Could not create patch folder'); }
  return save ? path.join(directory, 'Untitled.json') : directory;
}
async function libraryPatch(request: unknown): Promise<{ text: string; name: string } | null> {
  try {
    if (!request || typeof request !== 'object') throw new Error();
    const { library, name } = request as { library: unknown; name?: unknown };
    if (library === 'reset') { patchPath = null; return null; }
    if (library !== 'list' && library !== 'read') throw new Error();
    const directory = path.join(app.getPath('userData'), 'patches');
    await fs.promises.mkdir(directory, { recursive: true, mode: 0o700 });
    if ((await fs.promises.lstat(directory)).isSymbolicLink()) throw new Error();
    const root = await fs.promises.realpath(directory);
    if (library === 'list') {
      const names: string[] = [];
      const dir = await fs.promises.opendir(root);
      let examined = 0;
      for await (const entry of dir) {
        if (++examined > 1024 || names.length >= 256) break;
        if (entry.isFile() && entry.name.length <= 240 && /\.json$/i.test(entry.name)) names.push(entry.name);
      }
      return { name: 'User patches', text: JSON.stringify(names.sort()) };
    }
    if (typeof name !== 'string' || !name || name.length > 240 || /[\\/\x00]/.test(name) ||
        path.basename(name) !== name || !/\.json$/i.test(name)) throw new Error();
    const filename = path.join(root, name);
    if ((await fs.promises.lstat(filename)).isSymbolicLink() ||
        path.dirname(await fs.promises.realpath(filename)) !== root) throw new Error();
    const source = await readNativeFile(filename);
    patchPath = filename;
    return { name, text: source.text };
  } catch { throw new Error('Could not access user patch (JSON files, 2 MiB maximum)'); }
}

// File identity is bound only after a supported native document has been read.
// The renderer remains the editable-document owner; these checks only guard I/O.
function nativeFile(text: string): { version: number; preserved?: unknown } {
  const value = JSON.parse(text);
  if (!value || value.format !== 'wirescape.native.patch' || ![1, 2].includes(value.version) ||
      (value.modules !== undefined && !Array.isArray(value.modules)) ||
      (value.connections !== undefined && !Array.isArray(value.connections))) throw new Error('Unsupported patch');
  const object = (item: unknown): boolean => !!item && typeof item === 'object' && !Array.isArray(item);
  if (value.ui !== undefined && (!object(value.ui) ||
      ['positions', 'view', 'labels', 'cableColors'].some(key => value.ui[key] !== undefined && !object(value.ui[key])))) {
    throw new Error('Invalid patch UI containers');
  }
  const v1 = value.version === 1;
  if (v1 && (!Array.isArray(value.modules) || !Array.isArray(value.connections))) throw new Error('Invalid v1 patch');
  const ids = new Set<number>();
  for (const m of value.modules ?? []) {
    if (!m || !Number.isSafeInteger(m.id) || m.id <= 0 || ids.has(m.id) ||
        typeof (v1 ? m.type : m.module) !== 'string' ||
        (v1 && m.values != null && typeof m.values !== 'object')) throw new Error('Invalid patch module');
    ids.add(m.id);
  }
  const endpoint = (e: any): boolean => !!e && Number.isSafeInteger(e.module) && e.module > 0 && typeof e.port === 'string';
  for (const c of value.connections ?? []) {
    const readable = c && (v1
      ? ['audio', 'control', 'signal', 'modulation', 'event'].includes(c.kind) &&
        Number.isSafeInteger(c.fromNode) && c.fromNode > 0 && typeof c.fromPort === 'string' &&
        Number.isSafeInteger(c.toNode) && c.toNode > 0 && typeof c.toPort === 'string'
      : ['signal', 'modulation', 'event'].includes(c.kind) && endpoint(c.from) && endpoint(c.to));
    if (!readable) throw new Error('Invalid patch connection');
  }
  // JSON.parse accepts duplicate keys. Refuse them before any open/save binding;
  // decoded keys detect escaped aliases, including nested objects inside arrays.
  const stack: (Set<string> | null)[] = [];
  const tokens = /"(?:\\[\s\S]|[^"\\])*"|[{}[\]]/g;
  for (const token of text.matchAll(tokens)) {
    const word = token[0];
    if (word === '{' || word === '[') {
      if (stack.length >= 64) throw new Error('Patch nesting limit');
      stack.push(word === '{' ? new Set() : null);
    } else if (word === '}' || word === ']') stack.pop();
    else {
      let end = token.index! + word.length;
      while (/\s/.test(text[end] ?? '') && end < text.length) end++;
      if (text[end] === ':') {
        const keys = stack[stack.length - 1]!;
        const key = JSON.parse(word) as string;
        if (keys.has(key)) throw new Error('Duplicate patch key');
        keys.add(key);
      }
    }
  }
  return value;
}
async function readNativeFile(filename: string): Promise<{ bytes: Buffer; text: string; value: ReturnType<typeof nativeFile> }> {
  const handle = await fs.promises.open(filename, fs.constants.O_RDONLY | (fs.constants.O_NOFOLLOW ?? 0));
  let bytes: Buffer;
  try {
    if (!(await handle.stat()).isFile()) throw new Error('Invalid patch file');
    bytes = Buffer.allocUnsafe(LIMIT + 1);
    const { bytesRead } = await handle.read(bytes, 0, LIMIT + 1, 0);
    if (bytesRead > LIMIT) throw new Error('Patch exceeds 2 MiB limit');
    bytes = bytes.subarray(0, bytesRead);
  } finally { await handle.close(); }
  const text = new TextDecoder('utf-8', { fatal: true }).decode(bytes);
  return { bytes, text, value: nativeFile(text) };
}
// OB-a3: stage and fsync the original bytes, then atomically link a backup
// without clobbering an existing name. Backups are deliberately not *.json.
async function backupV1(filename: string, bytes: Buffer): Promise<void> {
  const backup = filename + '.bak-v1';
  const staged = backup + '.' + randomUUID() + '.tmp';
  try {
    const handle = await fs.promises.open(staged, 'wx', 0o600);
    try {
      await handle.writeFile(bytes);
      await handle.sync();
    } finally { await handle.close(); }
    for (let index = 1; index <= 10000; ++index) {
      const candidate = index === 1 ? backup : backup + '.' + index;
      try {
        await fs.promises.link(staged, candidate); // atomic no-clobber
        return;
      } catch (error) {
        if ((error as NodeJS.ErrnoException).code !== 'EEXIST') throw error;
      }
      // A directory, symlink or unusual file at a backup name is a refusal,
      // never a reason to follow it or silently skip to another suffix.
      const stat = await fs.promises.lstat(candidate);
      if (!stat.isFile() || stat.isSymbolicLink()) throw new Error('Unsafe backup collision');
      const existing = await fs.promises.open(candidate,
        fs.constants.O_RDONLY | (fs.constants.O_NOFOLLOW ?? 0));
      try {
        if (!(await existing.stat()).isFile()) throw new Error('Unsafe backup collision');
        if ((await existing.readFile()).equals(bytes)) return; // no new write
      } finally { await existing.close(); }
    }
    throw new Error('Too many backup collisions');
  } finally { await fs.promises.rm(staged, { force: true }).catch(() => {}); }
}
async function openPatch(): Promise<{ text: string; name: string } | null> {
  if (!window) throw new Error('Window unavailable');
  const result = await dialog.showOpenDialog(window, {
    title: 'Open patch', defaultPath: await patchDialogPath(false),
    properties: ['openFile'], filters: [{ name: 'Wirescape patch', extensions: ['json'] }]
  });
  if (result.canceled || !result.filePaths.length) return null;
  try {
    const filename = result.filePaths[0];
    const source = await readNativeFile(filename);
    patchPath = filename;
    return { text: source.text, name: path.basename(filename) };
  } catch { throw new Error('Could not read a supported UTF-8 native patch (2 MiB maximum)'); }
}
async function savePatch(input: unknown): Promise<{ name: string } | null> {
  if (!window || !input || typeof input !== 'object') throw new Error('Invalid patch');
  const { text, saveAs } = input as { text: unknown; saveAs: unknown };
  if (typeof text !== 'string' || typeof saveAs !== 'boolean' ||
      Buffer.byteLength(text, 'utf8') > LIMIT) throw new Error('Invalid patch or 2 MiB limit exceeded');
  let filename = !saveAs ? patchPath : null;
  if (!filename) {
    const result = await dialog.showSaveDialog(window, {
      title: 'Save patch', defaultPath: await patchDialogPath(true),
      filters: [{ name: 'Wirescape patch', extensions: ['json'] }]
    });
    if (result.canceled || !result.filePath) return null;
    filename = result.filePath;
  }
  // In Save As the explicitly chosen filename is the destination, even when
  // it matches the opened path (OB r2.2a); any v1 destination gets a backup.
  nativeFile(text);
  let previous: Awaited<ReturnType<typeof readNativeFile>> | undefined;
  try { previous = await readNativeFile(filename); }
  catch (error) { if ((error as NodeJS.ErrnoException).code !== 'ENOENT') throw new Error('Refusing to overwrite an unsupported patch'); }
  // Only the existing destination's native v1 bytes qualify for a backup.
  // Neither a v2 destination nor a new Save As file gets a v1 backup.
  try { if (previous?.value.version === 1) await backupV1(filename, previous.bytes); }
  catch { throw new Error('Could not create original patch backup; target was kept'); }
  const temp = path.join(path.dirname(filename), '.' + path.basename(filename) + '.' + randomUUID() + '.tmp');
  try {
    await fs.promises.writeFile(temp, text, { flag: 'wx', mode: 0o600 });
    await fs.promises.rename(temp, filename);
    patchPath = filename;
    return { name: path.basename(filename) };
  } catch {
    throw new Error('Could not save patch');
  } finally { await fs.promises.rm(temp, { force: true }).catch(() => {}); }
}
// SC4: a separate folder-write operation. No patch save-target changes,
// renderer-chosen destination paths, generic filesystem access or script execution.
const BUNDLE_MAX_FILES = 256;
const BUNDLE_MAX_BYTES = 64 * 1024 * 1024;
type BundlePatchFile = { name: string; text: string };
type BundleScriptFile = { name: string; bytes: Uint8Array };
function checkedBundle(input: unknown): { playerJson: string; patches: BundlePatchFile[]; scripts: BundleScriptFile[] } {
  if (!input || typeof input !== 'object') throw new Error('Invalid bundle');
  const { playerJson, patches, scripts } = input as { playerJson: unknown; patches: unknown; scripts: unknown };
  if (typeof playerJson !== 'string' || Buffer.byteLength(playerJson, 'utf8') > LIMIT ||
      !Array.isArray(patches) || !patches.length || patches.length > BUNDLE_MAX_FILES ||
      !Array.isArray(scripts) || scripts.length > BUNDLE_MAX_FILES) throw new Error('Invalid bundle or file limit');
  let total = Buffer.byteLength(playerJson, 'utf8');
  const patchPaths = new Set<string>(), scriptPaths = new Set<string>(), folded = new Set<string>();
  for (const [i, p] of patches.entries()) {
    if (!p || p.name !== `patch-${String(i + 1).padStart(4, '0')}.json` || typeof p.text !== 'string' ||
        Buffer.byteLength(p.text, 'utf8') > LIMIT || nativeFile(p.text).version !== 2)
      throw new Error('Invalid native bundle patch');
    patchPaths.add('patches/' + p.name);
    total += Buffer.byteLength(p.text, 'utf8');
  }
  for (const s of scripts) {
    if (!s || typeof s.name !== 'string' || !/^[a-zA-Z0-9_-][a-zA-Z0-9_.-]{0,119}\.py$/.test(s.name) ||
        /^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)/i.test(s.name) ||
        folded.has(s.name.toLowerCase()) || !(s.bytes instanceof Uint8Array) || s.bytes.byteLength > LIMIT)
      throw new Error('Invalid or duplicate bundle script');
    folded.add(s.name.toLowerCase());
    scriptPaths.add('scripts/' + s.name);
    total += s.bytes.byteLength;
  }
  if (total > BUNDLE_MAX_BYTES) throw new Error('Bundle exceeds 64 MiB');
  const manifest = JSON.parse(playerJson);
  if (!manifest || manifest.format !== 'wirescape.player' || manifest.version !== 1 ||
      typeof manifest.title !== 'string' || !manifest.title.trim() ||
      !Array.isArray(manifest.setlist) || manifest.setlist.length !== patches.length)
    throw new Error('Invalid Player manifest');
  const ordered = [...patchPaths], usedScripts = new Set<string>();
  for (const [i, entry] of manifest.setlist.entries()) {
    if (!entry || entry.patch !== ordered[i] || typeof entry.title !== 'string' ||
        !Array.isArray(entry.scripts)) throw new Error('Invalid Player setlist');
    const entryScripts = new Set<string>();
    for (const s of entry.scripts) {
      if (!s || !scriptPaths.has(s.file) || entryScripts.has(s.file) ||
          !Number.isInteger(s.port) || s.port < 1024 || s.port > 65535)
        throw new Error('Invalid Player script reference');
      entryScripts.add(s.file); usedScripts.add(s.file);
    }
  }
  if (usedScripts.size !== scriptPaths.size) throw new Error('Unreferenced bundle script');
  return { playerJson, patches, scripts };
}
async function savePlayerBundle(input: unknown): Promise<{ name: string } | null> {
  if (!window) throw new Error('Window unavailable');
  const bundle = checkedBundle(input); // Reject malformed input before asking for a folder.
  const result = await dialog.showOpenDialog(window, {
    title: 'Choose an empty Player bundle folder', properties: ['openDirectory', 'createDirectory'],
  });
  if (result.canceled || !result.filePaths.length) return null;
  const root = await fs.promises.realpath(result.filePaths[0]);
  if (!(await fs.promises.stat(root)).isDirectory() || (await fs.promises.readdir(root)).length)
    throw new Error('Choose an empty folder; existing files are not overwritten.');
  const patchDir = path.join(root, 'patches'), scriptDir = path.join(root, 'scripts');
  // Exclusive creation for every directory and file. A failure leaves an
  // incomplete folder, reported to the user, rather than overwriting data.
  try {
    await fs.promises.mkdir(patchDir, { mode: 0o700 });
    await fs.promises.mkdir(scriptDir, { mode: 0o700 });
    for (const p of bundle.patches)
      await fs.promises.writeFile(path.join(patchDir, p.name), p.text, { flag: 'wx', mode: 0o600 });
    for (const s of bundle.scripts)
      await fs.promises.writeFile(path.join(scriptDir, s.name), s.bytes, { flag: 'wx', mode: 0o600 });
    await fs.promises.writeFile(path.join(root, 'player.json'), bundle.playerJson, { flag: 'wx', mode: 0o600 });
    return { name: path.basename(root) };
  } catch {
    throw new Error('Bundle write incomplete; choose a new empty folder for retry.');
  }
}
function configureMenu(): void {
  const intent = (type: string, options: Record<string, unknown> = {}) => notify({ v: 0, type, ...options });
  const menu = Menu.buildFromTemplate([
    { label: 'File', submenu: [
      { id: 'open-patch', label: 'Open patch…', accelerator: 'CmdOrCtrl+O', click: () => intent('app.menuOpenPatch') },
      { id: 'save-patch', label: 'Save patch', accelerator: 'CmdOrCtrl+S', click: () => intent('app.menuSavePatch', { saveAs: false }) },
      { id: 'save-as', label: 'Save as…', accelerator: 'CmdOrCtrl+Shift+S', click: () => intent('app.menuSavePatch', { saveAs: true }) },
      { type: 'separator' },
      { role: 'quit', accelerator: 'CmdOrCtrl+Q' }
    ] },
    { label: 'View', submenu: [
      { label: 'Toggle fullscreen', accelerator: 'F11', click: () => window?.setFullScreen(!window.isFullScreen()) },
      { label: 'Reload UI', accelerator: 'CmdOrCtrl+R', click: () => window?.reload() }
    ] },
    { label: 'Engine', submenu: [
      { label: 'Restart engine', click: () => { void restartEngine().catch(error => console.error('Engine restart:', error)); } },
      { label: 'Panic', click: () => command(JSON.stringify({ v: 0, id: 'menu-' + (++menuId), type: 'panic' })) }
    ] }
  ]);
  Menu.setApplicationMenu(menu);
}
function createWindow(): void {
  window = new BrowserWindow({
    width: 1280, height: 800, minWidth: 640, minHeight: 480,
    ...savedBounds(), title: 'Wirescape',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true, nodeIntegration: false, sandbox: true
    }
  });
  window.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
  window.webContents.on('will-navigate', event => event.preventDefault());
  window.webContents.on('before-input-event', (event, input) => {
    if (input.key === 'Escape' && window?.isFullScreen()) {
      window.setFullScreen(false);
      event.preventDefault();
    }
  });
  window.on('close', saveBounds);
  window.on('closed', () => { window = null; });
  if (initialFullscreen) window.setFullScreen(true);
  void window.loadURL('app://wirescape/index.html').catch(() => {
    void dialog.showMessageBox({ type: 'error', message: 'Build the Studio UI before launching Wirescape.' });
  });
}
app.whenReady().then(() => {
  readyAt = process.hrtime.bigint();
  // Same-origin, local-only assets: unlike file://, fetch() can load catalogue JSON.
  // Reject path traversal and foreign hosts; never dispatch HTTP/network requests.
  protocol.handle('app', request => {
    try {
      const url = new URL(request.url);
      if (url.hostname !== 'wirescape' || (request.method !== 'GET' && request.method !== 'HEAD'))
        return new Response('Not found', { status: 404 });
      const pathname = decodeURIComponent(url.pathname);
      const filename = path.resolve(UI_DIR, '.' + pathname);
      if (!filename.startsWith(UI_DIR + path.sep) || !fs.existsSync(filename))
        return new Response('Not found', { status: 404 });
      return net.fetch(pathToFileURL(filename).toString());
    } catch { return new Response('Invalid path', { status: 400 }); }
  });
  ipcMain.on('wirescape:ready', event => {
    if (!senderAllowed(event)) return;
    if (lastHello) notify(lastHello);
  });
  ipcMain.on('wirescape:restart-policy-ready', event => { if (senderAllowed(event)) sendRestartPolicy(); });
  ipcMain.on('wirescape:escape', event => {
    if (senderAllowed(event) && window?.isFullScreen()) window.setFullScreen(false);
  });
  ipcMain.on('wirescape:send', (event, raw: unknown) => {
    if (senderAllowed(event) && typeof raw === 'string') command(raw);
  });
  ipcMain.handle('wirescape:osc-presets', (event, request: unknown) => {
    if (!senderAllowed(event)) throw new Error('Unavailable');
    return presetOperation(request);
  });
  ipcMain.handle('wirescape:open', (event, request: unknown) => {
    if (!senderAllowed(event)) throw new Error('Unavailable');
    return request === undefined ? openPatch() : libraryPatch(request);
  });
  ipcMain.handle('wirescape:bundle-export', (event, input: unknown) => {
    if (!senderAllowed(event)) throw new Error('Unavailable');
    return savePlayerBundle(input);
  });
  ipcMain.handle('wirescape:save', (event, input: unknown) => {
    if (!senderAllowed(event)) throw new Error('Unavailable');
    return savePatch(input);
  });
  createWindow();
  configureMenu();
  startEngine();
});
app.on('window-all-closed', () => app.quit());
app.on('before-quit', event => {
  if (shuttingDown) return;
  event.preventDefault();
  shuttingDown = true;
  cancelRestartTimer();
  void stopEngine().finally(() => app.quit());
});
