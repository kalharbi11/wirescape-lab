// SPDX-License-Identifier: GPL-3.0-only
import { validateProtocolV0, type ProtocolPush } from './generated/protocol_v0';
import type { PatchV2, Connection } from '../patch/types';
import { connKey } from '../patch/types';
import { ioObject, mergeSlotValue } from '../patch/ioProjection';
import type { ModuleDescriptor } from '../modules/types';
import type { ModuleRegistry } from '../modules/registry';
import { EngineRefusal, type EngineClient, type DataAuthoring, type EngineError, type Device, type SystemStatus, type Telemetry, type UnappliedParameter } from './EngineClient';

/** The complete five-member Electron preload surface; never expose Node to the renderer. */
export interface WirescapeBridge {
  send(obj: Record<string, unknown>): void;
  onMessage(cb: (message: Record<string, unknown>) => void): () => void;
  openPatch(request?: { library: 'list' | 'read' | 'reset'; name?: string }): Promise<{ text: string; name: string } | null>;
  savePatch(text: string, options?: { saveAs?: boolean }): Promise<{ name: string } | null>;
  readonly platform: 'linux' | 'win32' | 'darwin';
  /** Set only by the web demo bridge (D14). */
  readonly web?: boolean;
}
declare global { interface Window { wirescape?: WirescapeBridge } }

type Wire = Record<string, unknown>;
type Mutation = { type: string; payload: Wire; authored?: DataAuthoring };
type Edit = {
  id: string; session: string; mutation: Mutation; inverse: PatchV2 | null;
  rollback?: () => void;
  resolve?: () => void;
  reject?: (reason: EngineRefusal) => void;
};
type Pending = {
  session: string; type: string; kind: 'load' | 'edit' | 'query' | 'control' | 'restart';
  resolve?: (value: Wire) => void; reject?: (reason: EngineRefusal) => void;
  revision?: number; edit?: Edit; timeout?: number;
};
type Load = {
  id: string; patch: PatchV2; revision: number; type: 'loadGraph' | 'applyGraph';
  resolve: () => void; reject: (reason: EngineRefusal) => void; sent: boolean;
};

const copy = <T>(value: T): T => JSON.parse(JSON.stringify(value)) as T;
const isRecord = (v: unknown): v is Wire => v !== null && typeof v === 'object' && !Array.isArray(v);
const code = (v: unknown): EngineError['code'] =>
  (typeof v === 'string' && ['unknown-module', 'kind-mismatch', 'duplicate', 'not-found',
    'refused', 'invalid', 'busy', 'limit', 'unavailable'].includes(v)) ? v as EngineError['code'] : 'refused';
const refusal = (c: unknown, msg: unknown): EngineRefusal =>
  new EngineRefusal({ code: code(c), message: typeof msg === 'string' && msg ? msg : 'Engine command refused.' });
const generation = (s: unknown): bigint | null =>
  typeof s === 'string' && /^\d+$/.test(s) ? BigInt(s) : null;

// JSON object key order is not a configuration edit; absent config is {} on wire.
export const sameConfig = (a: unknown, b: unknown): boolean => {
  const ordered = (v: unknown): unknown => Array.isArray(v) ? v.map(ordered) :
    isRecord(v) ? Object.fromEntries(Object.keys(v).sort().map(k => [k, ordered(v[k])])) : v;
  return JSON.stringify(ordered(a ?? {})) === JSON.stringify(ordered(b ?? {}));
};
const cloneConfig = (v: unknown): unknown => v === undefined ? undefined : copy(v);
type DeferredEntry = { deferId: string; module: string; config: unknown; overlay: boolean };
type ConfigPush = Extract<ProtocolPush, { type: 'configDeferred' }>;
export type DeferredCompletion = { moduleId: number; module: string; desired: unknown;
  actual: unknown; outcome: ConfigPush['outcome']; overlay: boolean };

/**
 * Serializes optimistic edits over v0. Only one edit is in flight so a failed
 * mutation can be removed and dependent unsent edits revalidated in order.
 * The editable PatchDoc is never replaced by the executable projection.
 */
export class RealEngine implements EngineClient {
  private session = '';
  private gen = '0';
  private playheadEnabled = false;
  private monitorEnabled = false;
  private applyGraphEnabled = false;
  private configDeferredEnabled = false;
  private negotiatingConfig = false;
  private configNegotiationFailed = false;
  private deferredConfigs = new Map<number, DeferredEntry>();
  private deferredCbs = new Set<(event: DeferredCompletion) => void>();
  private unappliedCbs = new Set<(items: UnappliedParameter[]) => void>();
  private playhead: Telemetry['playhead'] = {};
  private statusGen = '';
  private serial = 0;
  private revision = 0;
  private loadedOnce = false;
  private ready = false;
  private started = false;
  private unsubscribe?: () => void;
  private pending = new Map<string, Pending>();
  private load?: Load;
  /** Live whole-document edits are sent in order, one correlated ACK at a time. */
  private graphQueue: Load[] = [];
  private queue: Edit[] = [];
  private active?: Edit;
  private lastEdit?: Edit;
  private settledWaiters = new Set<() => void>();
  private incrementalWaiters = new Set<() => void>();
  private confirmed: PatchV2 | null = null;
  private usedIds = new Set<number>();
  private audioDevices: Device[] = [];
  private midiDevices: Device[] = [];
  private status?: SystemStatus;
  private state: 'real' | 'restarting' = 'restarting';
  private telemetryCbs = new Set<(t: Telemetry) => void>();
  private statusCbs = new Set<(s: SystemStatus) => void>();
  private refusalCbs = new Set<(r: { requestId: string; type: string; detail: EngineError; gen: string }) => void>();
  private stateCbs = new Set<(state: 'real' | 'restarting') => void>();
  private graphErrorCbs = new Set<(error: EngineRefusal) => void>();
  private catalogueCbs = new Set<() => void>();
  private generationCbs = new Set<(gen: string) => void>();
  setSampleRate?: (hz: number) => void;
  setBufferFrames?: (frames: number) => void;
  midiLearn?: (armed: boolean) => void;

  constructor(
    private readonly bridge: WirescapeBridge,
    private readonly currentDocument: () => PatchV2,
    private readonly registry: ModuleRegistry,
  ) {}

  start(): void {
    if (this.started) return;
    this.started = true;
    this.unsubscribe = this.bridge.onMessage(m => this.receive(m));
    this.setState('restarting');
  }

  stop(): void { this.unsubscribe?.(); this.unsubscribe = undefined; this.started = false; }

  canApplyGroove(moduleId: number): boolean {
    if (!this.ready || this.state !== 'real' || this.load || this.active || this.queue.length) return false;
    if (this.statusGen === this.gen && this.status && this.status.audio.state !== 'running') return true;
    const position = this.playheadEnabled ? this.playhead?.[moduleId] : undefined;
    return position?.[0] === -1 && position[1] === -1;
  }

  onTelemetry(cb: (t: Telemetry) => void): () => void { this.telemetryCbs.add(cb); return () => this.telemetryCbs.delete(cb); }
  onStatus(cb: (s: SystemStatus) => void): () => void {
    this.statusCbs.add(cb);
    if (this.status) cb(this.status);
    return () => this.statusCbs.delete(cb);
  }
  onUnapplied(cb: (items: UnappliedParameter[]) => void): () => void {
    this.unappliedCbs.add(cb); return () => this.unappliedCbs.delete(cb);
  }
  hasApplyGraph(): boolean { return this.applyGraphEnabled; }
  onRefusal(cb: (r: { requestId: string; type: string; detail: EngineError; gen: string }) => void): () => void {
    this.refusalCbs.add(cb); return () => this.refusalCbs.delete(cb);
  }
  onConnection(cb: (state: 'real' | 'restarting') => void): () => void {
    this.stateCbs.add(cb); cb(this.state); return () => this.stateCbs.delete(cb);
  }
  onGraphError(cb: (error: EngineRefusal) => void): () => void {
    this.graphErrorCbs.add(cb); return () => this.graphErrorCbs.delete(cb);
  }
  onCatalogue(cb: () => void): () => void {
    this.catalogueCbs.add(cb); return () => this.catalogueCbs.delete(cb);
  }
  generation(): string { return this.gen; }
  onGeneration(cb: (gen: string) => void): () => void {
    this.generationCbs.add(cb); return () => this.generationCbs.delete(cb);
  }
  /** Legacy loadGraph can settle from a generation push. applyGraph cannot:
   * a successful swap may still report unapplied parameter events in its ACK. */
  settleUnansweredLoad(applied: boolean): boolean {
    const load = this.load;
    if (!load || !load.sent || load.type !== 'loadGraph') return false;
    this.pending.delete(load.id);
    this.load = undefined;
    if (applied) {
      this.confirmed = copy(load.patch);
      this.usedIds = new Set(this.confirmed.modules.map(m => m.id));
      this.ready = true; this.loadedOnce = true;
      load.resolve(); this.setState('real'); this.pumpEdits();
    } else {
      this.ready = this.confirmed !== null;
      load.reject(refusal('unavailable', 'Load was not applied.'));
    }
    this.notifySettled();
    return true;
  }
  private waitForSessionReady(session: string, timeout: number): Promise<void> {
    if (this.session !== session && this.ready && this.state === 'real') return Promise.resolve();
    return new Promise<void>((resolve, reject) => {
      let off = () => {};
      const timer = window.setTimeout(() => {
        off(); reject(refusal('unavailable', 'Engine restart timed out before the patch loaded.'));
      }, timeout);
      off = this.onConnection(state => {
        if (this.session !== session && this.ready && state === 'real') {
          window.clearTimeout(timer); off(); resolve();
        }
      });
    });
  }
  restartEngine(timeoutMs = 10_000): Promise<void> {
    const id = this.id(), session = this.session, deadline = Date.now() + timeoutMs;
    return new Promise<void>((resolve, reject) => {
      const timer = window.setTimeout(() => {
        this.pending.delete(id); reject(refusal('unavailable', 'Engine restart timed out.'));
      }, timeoutMs);
      this.pending.set(id, { session, type: 'app.restartEngine', kind: 'restart', timeout: timer,
        resolve: () => {
          window.clearTimeout(timer);
          void this.waitForSessionReady(session, Math.max(0, deadline - Date.now())).then(resolve, reject);
        },
        reject: err => { window.clearTimeout(timer); reject(err); } });
      try { this.bridge.send({ v: 0, id, type: 'app.restartEngine' }); }
      catch { window.clearTimeout(timer); this.pending.delete(id); reject(refusal('unavailable', 'Could not restart engine.')); }
    });
  }
  /** A graph transaction cannot overtake an unacknowledged incremental edit.
   * While another graph runs, edits queued behind it are deliberately unsent
   * and belong to that transaction's eventual outcome. */
  hasUnconfirmedEdits(): boolean {
    return !this.load && (!!this.active || this.queue.length > 0);
  }
  async whenIncrementalEditsSettled(): Promise<void> {
    while (this.hasUnconfirmedEdits())
      await new Promise<void>(resolve => this.incrementalWaiters.add(resolve));
  }
  /** A snapshot rollback uses the execution graph only after its native ACK. */
  confirmedDocument(): PatchV2 | null { return this.confirmed ? copy(this.confirmed) : null; }
  /** Acknowledged authoring intent, distinct from the running execution graph. */
  confirmedAuthoredDocument(): PatchV2 | null {
    const patch = this.confirmedDocument();
    if (!patch) return null;
    for (const node of patch.modules) {
      const pending = this.deferredConfigs.get(node.id);
      if (pending?.overlay && pending.module === node.module) {
        if (pending.config === undefined) delete node.config;
        else node.config = cloneConfig(pending.config);
      }
    }
    return patch;
  }
  hasPendingConfig(moduleId: number): boolean { return this.deferredConfigs.get(moduleId)?.overlay === true; }
  onDeferredConfig(cb: (event: DeferredCompletion) => void): () => void {
    this.deferredCbs.add(cb); return () => this.deferredCbs.delete(cb);
  }
  private clearDeferred(): void {
    this.deferredConfigs.clear();
    this.configDeferredEnabled = false;
    this.negotiatingConfig = false;
    this.configNegotiationFailed = false;
  }
  private optInConfig(): void {
    const session = this.session, id = this.id();
    this.negotiatingConfig = true;
    const finish = (accepted: boolean) => {
      if (this.session !== session || this.configNegotiationFailed) return;
      this.configDeferredEnabled = accepted;
      this.negotiatingConfig = false;
      this.dispatchLoad();
    };
    // A lost ACK is ambiguous: the server may already have enabled
    // deferral. Do not fall back to legacy busy or resend in this session.
    const fail = () => {
      if (this.session !== session || !this.pending.has(id)) return;
      const p = this.pending.get(id)!;
      if (p.timeout !== undefined) window.clearTimeout(p.timeout);
      this.pending.delete(id);
      this.negotiatingConfig = false;
      this.configNegotiationFailed = true;
      const error = refusal('unavailable', 'Configuration capability acknowledgement lost. Restart the engine to recover.');
      this.ready = false;
      this.setState('restarting');
      this.rejectPending(error);
      for (const cb of this.graphErrorCbs) cb(error);
    };
    const timer = window.setTimeout(fail, 5000);
    this.pending.set(id, { session, type: 'hello', kind: 'query', timeout: timer,
      resolve: reply => finish(reply.ok === true) });
    try { this.send(id, 'hello', { capabilities: ['configDeferred'] }); }
    catch { fail(); }
  }
  private recordDeferred(load: Load, message: Wire): boolean {
    if (!this.configDeferredEnabled || load.type !== 'applyGraph' ||
        message.code !== 'busy' || message.deferred !== true ||
        typeof message.deferId !== 'string' || !message.deferId || message.deferId.length > 128 ||
        !this.confirmed) return false;
    const changed = load.patch.modules.filter(node => {
      const old = this.confirmed?.modules.find(m => m.id === node.id && m.module === node.module);
      const pending = this.deferredConfigs.get(node.id);
      return old && !sameConfig(node.config, old.config) &&
        !(pending?.overlay && pending.module === node.module && sameConfig(node.config, pending.config));
    });
    if (!changed.length) return false;
    for (const node of changed) this.deferredConfigs.set(node.id, {
      deferId: message.deferId, module: node.module, config: cloneConfig(node.config), overlay: true,
    });
    return true;
  }
  private receiveDeferred(message: Wire): void {
    if (!this.configDeferredEnabled || message.session !== this.session ||
        !validateProtocolV0(message) || message.type !== 'configDeferred') return;
    // The generated union has open index signatures; its validator
    // establishes the shape but TS cannot discriminate all other members.
    const event = message as ConfigPush;
    const g = generation(event.generation);
    if (g === null) return;
    const pending = this.deferredConfigs.get(event.moduleId);
    if (!pending || pending.deferId !== event.deferId) return;
    this.deferredConfigs.delete(event.moduleId);
    const node = this.confirmed?.modules.find(m => m.id === event.moduleId && m.module === pending.module);
    if (event.outcome === 'applied' && node && pending.overlay) {
      if (pending.config === undefined) delete node.config;
      else node.config = cloneConfig(pending.config);
    }
    // Status may have advanced generation first. Correlation still settles
    // this exact pending entry; never infer completion from status alone.
    if (g > BigInt(this.gen)) {
      this.gen = event.generation;
      this.playhead = {}; this.statusGen = '';
    }
    for (const cb of this.deferredCbs) cb({ moduleId: event.moduleId, module: pending.module,
      desired: cloneConfig(pending.config), actual: cloneConfig(node?.config),
      outcome: event.outcome, overlay: pending.overlay });
  }
  private finishGraph(load: Load): void {
    this.ready = true;
    this.loadedOnce = true;
    this.load = undefined;
    load.resolve();
    if (this.graphQueue.length) {
      this.load = this.graphQueue.shift()!;
      this.ready = false;
      this.dispatchLoad();
    } else {
      this.setState('real');
      this.pumpEdits();
      this.notifySettled();
    }
  }

  /** A document switch must keep its owner visible until all inverses have settled. */
  async whenEditsSettled(): Promise<void> {
    while (this.active || this.queue.length || this.load || this.graphQueue.length)
      await new Promise<void>(resolve => this.settledWaiters.add(resolve));
  }
  private notifySettled(): void {
    if (!this.hasUnconfirmedEdits()) {
      for (const resolve of this.incrementalWaiters) resolve();
      this.incrementalWaiters.clear();
    }
    if (this.active || this.queue.length || this.load || this.graphQueue.length) return;
    for (const resolve of this.settledWaiters) resolve();
    this.settledWaiters.clear();
  }

  /** Attach an App-owned inverse to the most recently queued optimistic edit. */
  registerRollback(fn: () => void): void { if (this.lastEdit) this.lastEdit.rollback = fn; }

  private setState(next: 'real' | 'restarting'): void {
    this.state = next;
    for (const cb of this.stateCbs) cb(next);
  }
  private id(): string { return 'ui' + (++this.serial); }
  private send(id: string, type: string, payload: Wire = {}): void {
    this.bridge.send({ v: 0, id, type, ...payload });
  }
  private emitStatus(s: SystemStatus): void {
    this.status = s;
    for (const cb of this.statusCbs) cb(s);
  }
  private rejectPending(error: EngineRefusal): void {
    for (const edit of this.queue) edit.reject?.(error);
    for (const [id, p] of this.pending) {
      if (p.kind === 'restart') continue;
      if (p.timeout !== undefined) window.clearTimeout(p.timeout);
      p.reject?.(error); this.pending.delete(id);
    }
    this.active = undefined;
    this.queue = [];
    this.lastEdit = undefined;
    this.load?.reject(error);
    this.load = undefined;
    for (const queued of this.graphQueue) queued.reject(error);
    this.graphQueue = [];
    this.notifySettled();
  }

  private receive(message: Wire): void {
    if (!isRecord(message) || message.v !== 0) return;
    if (message.type === 'app.engineExited') {
      this.session = '';
      this.playhead = {}; this.statusGen = '';
      this.playheadEnabled = false;
      this.monitorEnabled = false;
      this.applyGraphEnabled = false;
      this.clearDeferred();
      this.ready = false;
      this.confirmed = null;
      this.setState('restarting');
      this.rejectPending(refusal('unavailable', 'Engine disconnected.'));
      // Main supervises crash restarts (bounded crash-loop budget); the renderer only waits for the next hello.
      return;
    }
    if (message.type === 'hello') {
      if (message.protocol !== 0 || typeof message.session !== 'string' || !message.session) return;
      if (this.session === message.session) return;
      const resumeLoad = this.load && !this.load.sent ? this.load : undefined;
      const wasRunning = this.loadedOnce && !resumeLoad;
      if (!resumeLoad) this.rejectPending(refusal('unavailable', 'Engine session replaced.'));
      else { this.pending.clear(); this.active = undefined; this.queue = []; }
      this.session = message.session;
      this.clearDeferred();
      this.gen = '0';
      this.playhead = {}; this.statusGen = '';
      this.ready = false;
      this.usedIds.clear();
      this.confirmed = null;
      const capabilities = Array.isArray(message.capabilities) ? message.capabilities : [];
      this.playheadEnabled = capabilities.includes('telemetry.playhead');
      this.monitorEnabled = capabilities.includes('telemetry.monitor');
      this.applyGraphEnabled = capabilities.includes('applyGraph');
      this.setSampleRate = capabilities.includes('setSampleRate')
        ? hz => this.control('setSampleRate', { hz }) : undefined;
      this.setBufferFrames = capabilities.includes('setBufferFrames')
        ? frames => this.control('setBufferFrames', { frames }) : undefined;
      this.midiLearn = capabilities.includes('midiLearn')
        ? armed => this.control('midiLearn', { armed }) : undefined;
      if (isRecord(message.catalogue) && Array.isArray(message.catalogue.modules)) {
        this.registry.replace(message.catalogue.modules as ModuleDescriptor[]);
        for (const cb of this.catalogueCbs) cb();
      }
      if (isRecord(message.audio) && isRecord(message.midi)) {
        this.midiDevices = Array.isArray(message.midi.devices) ? message.midi.devices as Device[] : [];
        this.statusGen = this.gen;
        this.emitStatus({ audio: message.audio as unknown as SystemStatus['audio'],
          midi: { devices: this.midiDevices, activity: isRecord(message.midi.activity)
            ? message.midi.activity as Record<string, number> : {},
          ...(isRecord(message.midi.learn) ? { learn: message.midi.learn as unknown as
            NonNullable<SystemStatus['midi']['learn']> } : {}) } });
      }
      if (capabilities.includes('configDeferred')) this.optInConfig();
      if (resumeLoad) this.dispatchLoad();
      else if (wasRunning) {
        void this.loadGraph(this.currentDocument()).catch(e => {
          for (const cb of this.graphErrorCbs) cb(e as EngineRefusal);
        });
      }
      return;
    }
    if (message.type === 'configDeferred') { this.receiveDeferred(message); return; }
    if (message.type?.toString().startsWith('app.menu')) return; // App consumes menu intents.
    if (message.type === 'status' || message.type === 'telemetry' || message.type === 'devices') {
      const pushedGen = generation(message.gen);
      if (message.session !== this.session || pushedGen === null || pushedGen < BigInt(this.gen)) return;
      if (pushedGen > BigInt(this.gen)) {
        this.gen = message.gen as string;
        this.playhead = {}; this.statusGen = '';
      }
      for (const cb of this.generationCbs) cb(this.gen);
      if (message.type === 'status' && isRecord(message.status)) {
        const next = message.status as unknown as SystemStatus;
        this.midiDevices = next.midi?.devices ?? this.midiDevices;
        this.statusGen = this.gen;
        this.emitStatus(next);
      } else if (message.type === 'devices') {
        if (Array.isArray(message.audioDevices)) this.audioDevices = message.audioDevices as Device[];
        if (Array.isArray(message.midiDevices)) this.midiDevices = message.midiDevices as Device[];
        if (this.status) this.emitStatus({ ...this.status, midi: { ...this.status.midi, devices: this.midiDevices } });
      } else if (message.type === 'telemetry' && isRecord(message.telemetry)) {
        const t = { ...message.telemetry, gen: message.gen } as unknown as Telemetry;
        t.monitorAvailable = this.monitorEnabled; // Renderer-only support bit from hello.
        if (!this.monitorEnabled) delete t.monitor;
        // Older/absent generations are unknown: never let them authorize Apply.
        this.playhead = this.playheadEnabled && message.gen === this.gen && isRecord(t.playhead) ? t.playhead : {};
        if (!this.playheadEnabled) { delete t.playhead; delete t.groove; }
        // v0 transmits JSON arrays, never invent absent scope/effective/outputs.
        t.scope = Object.fromEntries(Object.entries(t.scope ?? {}).map(([k, v]) =>
          [k, Array.isArray(v) ? Float32Array.from(v) : v])) as Telemetry['scope'];
        for (const cb of this.telemetryCbs) cb(t);
      }
      return;
    }
    if (typeof message.re !== 'string') return;
    const p = this.pending.get(message.re);
    if (!p || (p.kind !== 'restart' && (message.session !== p.session || message.session !== this.session))) return;
    // A superseded load's late ACK must not change gen or confirm a newer graph.
    if (p.kind === 'load' && (!this.load || this.load.id !== message.re ||
        p.revision !== this.load.revision)) {
      this.pending.delete(message.re);
      return;
    }
    if (p.type === 'hello' && !validateProtocolV0(message)) return;
    const g = generation(message.gen);
    if (p.kind !== 'restart' && (g === null || (g < BigInt(this.gen) && p.type !== 'setData'))) return;
    this.pending.delete(message.re);
    if (p.timeout !== undefined) window.clearTimeout(p.timeout);
    if (g !== null && g > BigInt(this.gen) && p.kind !== 'restart') {
      this.gen = message.gen as string;
      this.playhead = {}; this.statusGen = '';
    }
    if (p.type === 'hello') { p.resolve?.(message); return; }
    if (message.ok !== true) {
      const err = refusal(message.code, message.message);
      if (p.kind === 'load') {
        // A refused loadGraph leaves the engine on its previous graph (sidecar rollback).
        (err.detail as { engine?: true }).engine = true;
        if (this.load && p.revision === this.load.revision) {
          if (this.recordDeferred(this.load, message)) {
            this.finishGraph(this.load);
            return;
          }
          this.ready = this.confirmed !== null; // the atomic refusal leaves the confirmed graph untouched
          this.queue = []; this.active = undefined;
          this.load?.reject(err); this.load = undefined;
          for (const queued of this.graphQueue) queued.reject(err);
          this.graphQueue = [];
          this.notifySettled();
        }
      } else if (p.kind === 'edit' && p.edit) this.failEdit(p.edit, err);
      else p.reject?.(err);
      return;
    }
    if (p.kind === 'load') {
      if (this.load && p.revision === this.load.revision) {
        const load = this.load;
        const committed = copy(load.patch);
        const unapplied: UnappliedParameter[] = [];
        if (load.type === 'applyGraph') {
          const result = message.result;
          if (!isRecord(result) || !['live', 'restart'].includes(String(result.path)) ||
              !Array.isArray(result.replaced) || !Array.isArray(result.unapplied) ||
              !result.replaced.every(x => Number.isSafeInteger(x) && (x as number) > 0) ||
              new Set(result.replaced).size !== result.replaced.length) {
            this.failGraphAck(load, 'Malformed applyGraph acknowledgement.');
            return;
          }
          const seen = new Set<string>();
          for (const item of result.unapplied) {
            if (!isRecord(item) || !Number.isSafeInteger(item.moduleId) ||
                typeof item.paramId !== 'string' || !item.paramId ||
                seen.has(String(item.moduleId) + ':' + item.paramId)) {
              this.failGraphAck(load, 'Malformed unapplied parameter list.');
              return;
            }
            seen.add(String(item.moduleId) + ':' + item.paramId);
            const old = this.confirmed?.modules.find(m => m.id === item.moduleId);
            const next = committed.modules.find(m => m.id === item.moduleId);
            // Native E1a compares canonical runtime config bytes, which can
            // ignore authored key order and non-execution/defaulted fields.
            // Its 'replaced' IDs authoritatively identify non-continuing instances.
            if (!old || !next || old.module !== next.module ||
                result.replaced.includes(item.moduleId)) {
              this.failGraphAck(load, 'Unapplied parameter is not a continuing instance.');
              return;
            }
            const previous = old.parameters?.[item.paramId as string];
            if (previous === undefined) delete next.parameters?.[item.paramId as string];
            else (next.parameters ??= {})[item.paramId as string] = previous;
            unapplied.push({ moduleId: item.moduleId as number, paramId: item.paramId as string, previous });
          }
        }
        // A successful snapshot carrying the same pending config executes
        // at the committed value; a different config is accepted normally.
        // Only the subsequent terminal event removes its correlation.
        if (load.type === 'loadGraph') this.deferredConfigs.clear();
        else for (const [id, pending] of this.deferredConfigs) {
          const node = committed.modules.find(m => m.id === id && m.module === pending.module);
          const old = this.confirmed?.modules.find(m => m.id === id && m.module === pending.module);
          if (pending.overlay && node && old && sameConfig(node.config, pending.config)) {
            if (old.config === undefined) delete node.config;
            else node.config = cloneConfig(old.config);
          } else pending.overlay = false;
        }
        this.confirmed = committed;
        // applyGraph retains the namespace; an ID removed by a graph replan
        // remains barred from incremental addModule but can return in applyGraph.
        this.usedIds = load.type === 'loadGraph'
          ? new Set(committed.modules.map(m => m.id))
          : new Set([...this.usedIds, ...committed.modules.map(m => m.id)]);
        // A newer authored applyGraph already supersedes intermediate UI values.
        // Reconcile only the final acknowledged document, not an earlier
        // request whose unapplied values the next request can change again.
        if (!this.graphQueue.length && unapplied.length)
          for (const cb of this.unappliedCbs) cb(unapplied);
        this.finishGraph(load);
      }
    } else if (p.kind === 'edit' && p.edit) {
      if (this.confirmed) applyMutation(this.confirmed, p.edit.mutation, this.usedIds);
      p.edit.resolve?.();
      this.queue.shift();
      this.active = undefined;
      this.pumpEdits();
      this.notifySettled();
    } else p.resolve?.(message);
  }

  loadGraph(patch: PatchV2): Promise<void> {
    return this.submitGraph(patch, 'loadGraph');
  }
  applyGraph(patch: PatchV2): Promise<void> {
    // Defensive drain: even a caller that misses App's edit-authoring gate
    // cannot erase a pending incremental ACK or open a graph chain over it.
    if (this.hasUnconfirmedEdits())
      return this.whenIncrementalEditsSettled().then(() => this.applyGraph(patch));
    // A pending live replan is not grounds to silently restart untouched
    // instances. Queue a second live replan behind its correlated ACK.
    return this.applyGraphEnabled && (this.ready || this.load?.type === 'applyGraph')
      ? this.submitGraph(patch, 'applyGraph') : this.loadGraph(patch);
  }
  /** Used only on a success reply whose metadata cannot be trusted. */
  private failGraphAck(load: Load, message: string): void {
    const error = refusal('invalid', message);
    this.ready = false;
    this.load = undefined;
    load.reject(error);
    for (const queued of this.graphQueue) queued.reject(error);
    this.graphQueue = [];
    this.notifySettled();
  }
  private submitGraph(patch: PatchV2, type: 'loadGraph' | 'applyGraph'): Promise<void> {
    if (this.configNegotiationFailed)
      return Promise.reject(refusal('unavailable', 'Restart the engine to recover configuration capability negotiation.'));
    const revision = ++this.revision;
    if (type === 'applyGraph' && this.load?.type === 'applyGraph') {
      return new Promise<void>((resolve, reject) => {
        this.graphQueue.push({ id: this.id(), patch: copy(patch),
          revision, type, resolve, reject, sent: false });
      });
    }
    // A deliberate open/new/recovery load replaces any pending graph edits;
    // only that explicit load may reset the native ID namespace.
    this.playhead = {};
    this.loadedOnce = true;
    this.ready = false;
    for (const edit of this.queue) if (edit.reject) {
      this.pending.delete(edit.id);
      edit.reject(refusal('unavailable', 'Patch load superseded data edit.'));
    }
    this.active = undefined;
    this.queue = [];
    this.lastEdit = undefined;
    if (this.load) {
      this.pending.delete(this.load.id);
      this.load.reject(refusal('unavailable', 'Patch load superseded.'));
    }
    for (const queued of this.graphQueue)
      queued.reject(refusal('unavailable', 'Patch load superseded.'));
    this.graphQueue = [];
    return new Promise<void>((resolve, reject) => {
      this.load = { id: this.id(), patch: copy(patch), revision, type, resolve, reject, sent: false };
      this.dispatchLoad();
    });
  }
  private dispatchLoad(): void {
    const l = this.load;
    if (!l || !this.session || l.sent || this.negotiatingConfig || this.configNegotiationFailed) return;
    l.sent = true;
    this.pending.set(l.id, { session: this.session, type: l.type, kind: 'load',
      revision: l.revision });
    try { this.send(l.id, l.type, { patch: l.patch }); }
    catch {
      this.pending.delete(l.id);
      this.load = undefined;
      const err = refusal('unavailable', 'Bridge unavailable.');
      l.reject(err);
      for (const queued of this.graphQueue) queued.reject(err);
      this.graphQueue = [];
      this.ready = false;
      this.notifySettled();
    }
  }

  private enqueue(type: string, payload: Wire): void {
    // A blank/unavailable patch may have failed its initial load. Once an
    // editable change makes it runnable, resubmit the full document instead
    // of sending an edit against an unknown native generation.
    if (!this.ready && !this.load && this.session) {
      void this.loadGraph(this.currentDocument()).catch(e => {
        for (const cb of this.graphErrorCbs) cb(e as EngineRefusal);
      });
      return;
    }
    const mutation = { type, payload };
    const projected = this.projection();
    const inverse = projected ? copy(projected) : null;
    const entry: Edit = { id: this.id(), session: this.session, mutation, inverse };
    this.queue.push(entry);
    this.lastEdit = entry;
    this.pumpEdits();
  }
  private projection(): PatchV2 | null {
    if (!this.confirmed) return null;
    const patch = copy(this.confirmed);
    const ids = new Set(this.usedIds);
    for (const edit of this.queue) applyMutation(patch, edit.mutation, ids);
    return patch;
  }
  private pumpEdits(): void {
    if (!this.ready || !this.session || this.active || !this.confirmed) return;
    while (this.queue.length) {
      const entry = this.queue[0]!;
      const projection = copy(this.confirmed);
      if (!applyMutation(projection, entry.mutation, new Set(this.usedIds))) {
        this.failEdit(entry, refusal('not-found', 'Edit no longer applies to the running graph.'));
        continue;
      }
      entry.session = this.session;
      this.active = entry;
      this.playhead = {};
      this.pending.set(entry.id, { session: this.session, type: entry.mutation.type, kind: 'edit', edit: entry });
      try { this.send(entry.id, entry.mutation.type, entry.mutation.payload); }
      catch { this.pending.delete(entry.id); this.failEdit(entry, refusal('unavailable', 'Bridge unavailable.')); }
      return;
    }
  }
  private failEdit(entry: Edit, err: EngineRefusal): void {
    this.active = undefined;
    this.queue = this.queue.filter(x => x !== entry);
    entry.rollback?.();
    entry.reject?.(err);
    for (const cb of this.refusalCbs) cb({
      requestId: entry.id, type: entry.mutation.type, detail: err.detail, gen: this.gen,
    });
    // Revalidation of later queued edits is performed against the last ack.
    this.pumpEdits();
    this.notifySettled();
  }
  private request(type: string, payload: Wire = {}): Promise<Wire> {
    if (!this.session) return Promise.reject(refusal('unavailable', 'Engine disconnected.'));
    const id = this.id();
    return new Promise<Wire>((resolve, reject) => {
      this.pending.set(id, { session: this.session, type, kind: 'query', resolve, reject });
      try { this.send(id, type, payload); }
      catch { this.pending.delete(id); reject(refusal('unavailable', 'Bridge unavailable.')); }
    });
  }
  private control(type: string, payload: Wire = {}): void {
    void this.request(type, payload).catch(err => {
      for (const cb of this.refusalCbs) cb({ requestId: '', type, detail: (err as EngineRefusal).detail, gen: this.gen });
    });
  }

  addModule(moduleId: number, moduleType: string, params: Record<string, number> = {}): void {
    this.enqueue('addModule', { moduleId, moduleType, params });
  }
  removeModule(moduleId: number): void { this.enqueue('removeModule', { moduleId }); }
  connect(connection: Connection): void { this.enqueue('connect', { connection: copy(connection) }); }
  disconnect(connection: Connection): void { this.enqueue('disconnect', { connection: copy(connection) }); }
  setParam(moduleId: number, paramId: string, value: number): void { this.enqueue('setParam', { moduleId, paramId, value }); }
  setModAmount(connection: Connection, amount: number): void {
    this.enqueue('setModAmount', { connection: copy(connection), amount });
  }
  /** MM1 acknowledged live edits: unlike optimistic knob drags, never
   * fall back to a whole-graph load when the current session is unavailable. */
  private confirmedLiveEdit(type: 'setParam' | 'setModAmount', payload: Wire): Promise<void> {
    if (!this.ready || !this.session || this.load || !this.confirmed)
      return Promise.reject(refusal('unavailable', 'Engine graph is not ready for a live mapping edit.'));
    return new Promise<void>((resolve, reject) => {
      this.queue.push({ id: this.id(), session: this.session, mutation: { type, payload },
        inverse: this.projection(), resolve, reject });
      this.pumpEdits();
    });
  }
  setParamConfirmed(moduleId: number, paramId: string, value: number): Promise<void> {
    return this.confirmedLiveEdit('setParam', { moduleId, paramId, value });
  }
  setModAmountConfirmed(connection: Connection, amount: number): Promise<void> {
    return this.confirmedLiveEdit('setModAmount', { connection: copy(connection), amount });
  }
  setData(moduleId: number, slot: string, value: Wire, authored?: DataAuthoring): Promise<void> {
    if (!this.ready || !this.session || this.load || !this.confirmed)
      return Promise.reject(refusal('unavailable', 'Engine graph is not ready for a live data edit.'));
    const mutation: Mutation = { type: 'setData', payload: { moduleId, slot, value: copy(value) },
      ...(authored ? { authored: copy(authored) } : {}) };
    return new Promise<void>((resolve, reject) => {
      this.queue.push({ id: this.id(), session: this.session, mutation, inverse: this.projection(), resolve, reject });
      this.pumpEdits();
    });
  }
  noteOn(note: number, velocity: number): void { this.control('noteOn', { note, velocity }); }
  noteOff(note: number): void { this.control('noteOff', { note }); }
  panic(): void { this.control('panic'); }
  async listAudioDevices(): Promise<Device[]> {
    const result = await this.request('listAudioDevices');
    const body = isRecord(result.result) ? result.result : {};
    if (Array.isArray(body.devices)) this.audioDevices = body.devices as Device[];
    // Registry failures are informational, never extra selectable output IDs.
    const reported = isRecord(body.audio) ? body.audio.unavailableDrivers : undefined;
    const unavailable = Array.isArray(reported) ? reported.filter(v =>
      isRecord(v) && typeof v.hostApi === 'string' && typeof v.name === 'string'
    ).map(v => ({
      hostApi: v.hostApi as string, name: v.name as string,
      ...(typeof v.reason === 'string' ? { reason: v.reason } : {}),
      ...(typeof v.detail === 'string' ? { detail: v.detail } : {}),
    })) : [];
    if (this.status) {
      const audio = { ...this.status.audio };
      delete audio.unavailableDrivers;
      if (unavailable.length) audio.unavailableDrivers = unavailable;
      this.emitStatus({ ...this.status, audio });
    }
    return this.audioDevices.slice();
  }
  selectAudioDevice(deviceId: string): void { this.control('selectAudioDevice', { deviceId }); }
  async listMidiDevices(): Promise<Device[]> {
    const result = await this.request('listMidiDevices');
    const devices = (result.result as { devices?: Device[] } | undefined)?.devices;
    if (Array.isArray(devices)) this.midiDevices = devices;
    return this.midiDevices.slice();
  }
  setMidiEnabled(deviceId: string, on: boolean): void { this.control('setMidiEnabled', { deviceId, on }); }
}

/** Pure execution projection: intentionally does not touch ui or other saved metadata. */
function applyMutation(patch: PatchV2, m: Mutation, used: Set<number>): boolean {
  const p = m.payload;
  const id = p.moduleId as number;
  const connection = p.connection as Connection;
  switch (m.type) {
    case 'addModule':
      if (used.has(id) || typeof p.moduleType !== 'string') return false;
      patch.modules.push({ id, module: p.moduleType, parameters: copy(p.params ?? {}) as Record<string, number> });
      used.add(id); return true;
    case 'removeModule':
      if (!patch.modules.some(x => x.id === id)) return false;
      patch.modules = patch.modules.filter(x => x.id !== id);
      patch.connections = patch.connections.filter(x => x.from.module !== id && x.to.module !== id);
      return true;
    case 'connect':
      if (!patch.modules.some(x => x.id === connection.from.module) ||
          !patch.modules.some(x => x.id === connection.to.module) ||
          patch.connections.some(x => connKey(x) === connKey(connection))) return false;
      patch.connections.push(copy(connection)); return true;
    case 'disconnect': {
      const i = patch.connections.findIndex(x => connKey(x) === connKey(connection));
      if (i < 0) return false;
      patch.connections.splice(i, 1); return true;
    }
    case 'setParam': {
      const node = patch.modules.find(x => x.id === id);
      if (!node) return false;
      (node.parameters ??= {})[p.paramId as string] = p.value as number;
      return true;
    }
    case 'setData': {
      const node = patch.modules.find(x => x.id === id);
      if (!node || typeof p.slot !== 'string' || !isRecord(p.value)) return false;
      const data = ioObject(node.data);
      node.data = { ...data, [p.slot]: m.authored ? copy(m.authored.value) : mergeSlotValue(data[p.slot], p.value) };
      if (m.authored?.replaceConfig) {
        if (m.authored.config === undefined) delete node.config;
        else node.config = cloneConfig(m.authored.config);
      }
      return true;
    }
    case 'setModAmount': {
      const found = patch.connections.find(x => connKey(x) === connKey(connection));
      if (!found) return false;
      found.amount = p.amount as number; return true;
    }
  }
  return true;
}
