// SPDX-License-Identifier: GPL-3.0-only
import { contextBridge, ipcRenderer } from 'electron';

const LIMIT = 2 * 1024 * 1024;
type Wire = Record<string, unknown>;
const listeners = new Set<(message: Wire) => void>();
let requestedInitialHello = false;
let lastHello: Wire | null = null;
let lastRestartPolicy: Wire | null = null;
const restartListeners = new Set<(message: Wire) => void>();

function checkedCommand(value: Wire): string {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new TypeError('Invalid command');
  const seen = new WeakSet<object>();
  function validate(v: unknown, depth = 0): void {
    if (depth > 64) throw new RangeError('Command nesting too deep');
    if (typeof v === 'number' && !Number.isFinite(v)) throw new TypeError('Non-finite number');
    if (typeof v === 'undefined' || typeof v === 'function' || typeof v === 'symbol' ||
        typeof v === 'bigint') throw new TypeError('Unserializable command');
    if (v && typeof v === 'object') {
      if (seen.has(v)) throw new TypeError('Cyclic command');
      seen.add(v);
      if (!Array.isArray(v) && Object.getPrototypeOf(v) !== Object.prototype &&
          Object.getPrototypeOf(v) !== null) throw new TypeError('Invalid command object');
      for (const child of Object.values(v)) validate(child, depth + 1);
      seen.delete(v);
    }
  }
  validate(value);
  let raw: string;
  try { raw = JSON.stringify(value); } catch { throw new TypeError('Unserializable command'); }
  if (!raw || new TextEncoder().encode(raw).length > LIMIT) throw new RangeError('Command too large');
  const obj: Wire = JSON.parse(raw);
  if (obj.v !== 0 || typeof obj.type !== 'string' || obj.type.length > 64 ||
      typeof obj.id !== 'string' || !/^[\x21-\x7e]{1,64}$/.test(obj.id)) {
    throw new TypeError('Invalid protocol envelope');
  }
  return raw;
}

ipcRenderer.on('wirescape:message', (_event, raw: string) => {
  if (typeof raw !== 'string' || new TextEncoder().encode(raw).length > LIMIT) return;
  let value: Wire;
  try {
    value = JSON.parse(raw);
    if (!value || Array.isArray(value) || typeof value !== 'object' || value.v !== 0) return;
  } catch { return; }
  if (value.type === 'hello') {
    // One hello per engine session: main may push it at start and again on 'ready'.
    if (lastHello && lastHello.session === value.session) return;
    lastHello = value;
  }
  if (value.type === 'app.engineExited') lastHello = null;
  for (const listener of [...listeners]) {
    try { listener(value); } catch (e) { console.error('Wirescape message listener failed', e); }
  }
});

// Keyboard delivery in synthetic tests and some WMs does not always trigger
// webContents' before-input-event; main still checks the trusted sender.
window.addEventListener('keydown', event => {
  if (event.key === 'Escape') ipcRenderer.send('wirescape:escape');
}, true);

contextBridge.exposeInMainWorld('wirescape', Object.freeze({
  send(value: Wire): void {
    ipcRenderer.send('wirescape:send', checkedCommand(value));
  },
  onMessage(listener: (message: Wire) => void): () => void {
    if (typeof listener !== 'function') throw new TypeError('Expected callback');
    listeners.add(listener);
    // Replay only to this late subscriber, not to every existing listener.
    if (lastHello) queueMicrotask(() => {
      if (listeners.has(listener) && lastHello) listener(lastHello);
    });
    if (!requestedInitialHello) {
      requestedInitialHello = true;
      ipcRenderer.send('wirescape:ready');
    }
    return () => { listeners.delete(listener); };
  },
  openPatch(request?: { library: 'list' | 'read' | 'reset'; name?: string }): Promise<{ text: string; name: string } | null> {
    if (request === undefined) return ipcRenderer.invoke('wirescape:open');
    if (!request || !['list', 'read', 'reset'].includes(request.library) ||
        (request.name !== undefined && (typeof request.name !== 'string' || request.name.length > 240 ||
          /[\\/\x00]/.test(request.name))) ||
        (request.library === 'read' && (!request.name || !/\.json$/i.test(request.name)))) {
      return Promise.reject(new TypeError('Invalid patch token'));
    }
    return ipcRenderer.invoke('wirescape:open', request.library === 'read'
      ? { library: request.library, name: request.name } : { library: request.library });
  },
  savePatch(text: string, options?: { saveAs?: boolean }): Promise<{ name: string } | null> {
    if (typeof text !== 'string' || new TextEncoder().encode(text).length > LIMIT) {
      return Promise.reject(new TypeError('Patch too large or not text'));
    }
    if (options !== undefined && (!options || typeof options !== 'object' ||
        typeof options.saveAs !== 'undefined' && typeof options.saveAs !== 'boolean')) {
      return Promise.reject(new TypeError('Invalid save options'));
    }
    return ipcRenderer.invoke('wirescape:save', { text, saveAs: options?.saveAs === true });
  },
  platform: process.platform
}));

// A92: independent file-only bridge; existing five-member engine/patch bridge
// remains unchanged. Main repeats input validation and checks the sender.
contextBridge.exposeInMainWorld('wirescapeOscPresets', Object.freeze({
  list(module: string): Promise<{ file: string; name: string }[]> {
    if (module !== 'osc.in' && module !== 'osc.out') return Promise.reject(new TypeError('Invalid OSC preset module'));
    return ipcRenderer.invoke('wirescape:osc-presets', { op: 'list', module });
  },
  read(file: string): Promise<string> {
    if (typeof file !== 'string' || file.length > 240 || !/^[^\\/:*?"<>|\x00-\x1f]+\.json$/i.test(file))
      return Promise.reject(new TypeError('Invalid OSC preset filename'));
    return ipcRenderer.invoke('wirescape:osc-presets', { op: 'read', file });
  },
  choose(): Promise<string | null> {
    return ipcRenderer.invoke('wirescape:osc-presets', { op: 'choose' });
  },
  async save(text: string, name: string): Promise<void> {
    if (typeof text !== 'string' || new TextEncoder().encode(text).length > 256 * 1024 ||
        typeof name !== 'string' || !name.trim() || name.length > 120)
      throw new TypeError('Invalid OSC preset');
    await ipcRenderer.invoke('wirescape:osc-presets', { op: 'save', text, name });
  },
  async openFolder(): Promise<void> {
    await ipcRenderer.invoke('wirescape:osc-presets', { op: 'folder' });
  },
}));

// RS: separate local banner IPC, not an engine-protocol push. No new engine
// commands, schema changes, or Node access.
ipcRenderer.on('wirescape:restart-policy', (_event, value: Wire) => {
  if (!value || typeof value !== 'object' || value.type !== 'app.engineRestartPolicy' ||
      typeof value.banner !== 'boolean' || !['starting', 'waiting', 'recovering', 'stable'].includes(String(value.phase)) ||
      typeof value.delayMs !== 'number' || value.delayMs < 0 || value.delayMs > 30000) return;
  lastRestartPolicy = value;
  for (const listener of [...restartListeners]) {
    try { listener(value); } catch (e) { console.error('Restart banner listener failed', e); }
  }
});
let requestedRestartPolicy = false;
contextBridge.exposeInMainWorld('wirescapeRestartPolicy', Object.freeze({
  subscribe(listener: (message: Wire) => void): () => void {
    if (typeof listener !== 'function') throw new TypeError('Expected callback');
    restartListeners.add(listener);
    if (!requestedRestartPolicy) { requestedRestartPolicy = true; ipcRenderer.send('wirescape:restart-policy-ready'); }
    if (lastRestartPolicy) queueMicrotask(() => {
      if (restartListeners.has(listener) && lastRestartPolicy) listener(lastRestartPolicy);
    });
    return () => { restartListeners.delete(listener); };
  },
}));
