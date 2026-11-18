// SPDX-License-Identifier: GPL-3.0-only
import type { Page } from '@playwright/test';

/** Electron's five-member bridge, injected before any Studio module runs. */
export async function mockBridge(page: Page, options: { applyGraph?: boolean } = {}): Promise<void> {
  await page.addInitScript((options) => {
    type Message = Record<string, any>;
    const listeners = new Set<(m: Message) => void>();
    const audio = [{ id: 'USB Stereo', name: 'USB Stereo', kind: 'audio', sampleRates: [48000], index: 3 }];
    const midi = [{ id: 'M8 MIDI 1|M8:M8 MIDI 1', name: 'M8 MIDI 1',
      system_name: 'M8:M8 MIDI 1', enabled: true, kind: 'midi' }];
    const audioStatus = { state: 'running', deviceId: 'USB Stereo', deviceName: 'USB Stereo',
      sampleRate: 48000, bufferFrames: 256, latencyMs: 10.6667, cpuPercent: 2.1, dropouts: 0 };
    let sessionNo = 1, gen = 0, graph: Message = { modules: [], connections: [] };
    let catalogue: Message = { modules: [] };
    let delay = 0, saved = '', openText: { text: string; name: string } | null = null;
    const refused: { type: string; code: string }[] = [];
    const held: { cmd: Message; session: string; gen: string; result?: Message; applied?: boolean }[] = [];
    let nextUnapplied: { moduleId: number; paramId: string }[] = [];
    let nextReplaced: number[] | undefined;
    const sent: Message[] = [];
    let learnArmed = false, learnSeq = 0, learnPacket: Message | null = null;
    const session = () => 's' + sessionNo;
    const emit = (m: Message) => { for (const cb of listeners) cb(m); };
    const copy = (v: any) => JSON.parse(JSON.stringify(v));
    const midiStatus = () => ({ devices: copy(midi), activity: {},
      ...(learnArmed ? { learn: { armed: true, ...(learnPacket ?? {}) } } : {}) });
    const emitStatus = (overrides: Message = {}) => emit({ v: 0, type: 'status', session: session(), gen: String(gen),
      status: { audio: { ...copy(audioStatus), ...overrides }, midi: midiStatus() } });
    const reply = (cmd: Message, ok: boolean, response: Message = {}, s = session(), g = String(gen)) => {
      emit({ v: 0, session: s, re: cmd.id, ok, gen: g, ...response });
    };
    const hello = async () => {
      if (!catalogue.modules.length) {
        catalogue = await (await fetch('/wirescape_modules.json')).json();
      }
      emit({ v: 0, type: 'hello', session: session(), protocol: 0,
        engine: { version: 'test', sha: 'abc1234' }, capabilities: ['midiLearn', 'telemetry.playhead', ...(options.applyGraph ? ['applyGraph'] : [])],
        catalogue, audio: audioStatus,
        midi: midiStatus() });
    };
    const canonical = (value: any): string => JSON.stringify((function ordered(v: any): any {
      if (Array.isArray(v)) return v.map(ordered);
      if (v !== null && typeof v === 'object')
        return Object.fromEntries(Object.entries(v).sort(([a], [b]) => a.localeCompare(b))
          .map(([key, child]) => [key, ordered(child)]));
      return v;
    })(value ?? {}));
    const commitGraph = (cmd: Message): Message => {
      const oldById = new Map(graph.modules.map((m: Message) => [m.id, m]));
      const next = copy(cmd.patch);
      const computed = next.modules.filter((m: Message) => {
        const previous = oldById.get(m.id) as Message | undefined;
        return previous && (previous.module !== m.module ||
          m.module === 'osc.out' || canonical(previous.config) !== canonical(m.config));
      }).map((m: Message) => m.id);
      // Explicit simulated native canonical-config result; authoring JSON
      // may differ while runtime bytes are equal (e.g. ignored/default keys).
      const replaced = nextReplaced ?? computed;
      nextReplaced = undefined;
      const unapplied = cmd.type === 'applyGraph' ? nextUnapplied.splice(0) : [];
      for (const item of unapplied) {
        const before = oldById.get(item.moduleId) as Message | undefined;
        const module = next.modules.find((m: Message) => m.id === item.moduleId);
        if (!module || !before) continue;
        const oldValue = before.parameters?.[item.paramId];
        if (oldValue === undefined) delete module.parameters?.[item.paramId];
        else (module.parameters ??= {})[item.paramId] = oldValue;
      }
      graph = next; gen++;
      return cmd.type === 'applyGraph' ? { result: { path: 'live', replaced, unapplied } } : {};
    };
    const accept = (cmd: Message, s: string) => {
      if (s !== session()) return;
      const rejectAt = refused.findIndex(x => x.type === cmd.type);
      if (rejectAt >= 0) {
        const [r] = refused.splice(rejectAt, 1);
        reply(cmd, false, { code: r!.code, message: 'Scripted ' + r!.code }, s);
        return;
      }
      switch (cmd.type) {
        case 'loadGraph':
        case 'applyGraph': {
          if (cmd.type === 'applyGraph' && !options.applyGraph) {
            reply(cmd, false, { code: 'unavailable', message: 'No applyGraph capability' }, s); break;
          }
          if (cmd.patch.modules.some((m: Message) =>
            !catalogue.modules.some((d: Message) => d.id === m.module))) {
            reply(cmd, false, { code: 'unknown-module', message: 'Module not installed' }, s);
            return;
          }
          reply(cmd, true, commitGraph(cmd), s);
          break;
        }
        case 'addModule':
          if (!catalogue.modules.some((d: Message) => d.id === cmd.moduleType)) {
            reply(cmd, false, { code: 'unknown-module', message: 'Module not installed' }, s);
            break;
          }
          graph.modules.push({ id: cmd.moduleId, module: cmd.moduleType, parameters: cmd.params });
          gen++; reply(cmd, true, {}, s); break;
        case 'removeModule':
          graph.modules = graph.modules.filter((m: Message) => m.id !== cmd.moduleId);
          graph.connections = graph.connections.filter((c: Message) =>
            c.from.module !== cmd.moduleId && c.to.module !== cmd.moduleId);
          gen++; reply(cmd, true, {}, s); break;
        case 'connect':
          graph.connections.push(copy(cmd.connection)); gen++; reply(cmd, true, {}, s); break;
        case 'disconnect':
          graph.connections = graph.connections.filter((c: Message) =>
            JSON.stringify([c.kind, c.from, c.to]) !==
            JSON.stringify([cmd.connection.kind, cmd.connection.from, cmd.connection.to]));
          gen++; reply(cmd, true, {}, s); break;
        case 'setParam': {
          const node = graph.modules.find((m: Message) => m.id === cmd.moduleId);
          if (!node) { reply(cmd, false, { code: 'not-found', message: 'No module' }, s); break; }
          (node.parameters ??= {})[cmd.paramId] = cmd.value;
          reply(cmd, true, {}, s); break;
        }
        case 'setModAmount': {
          const conn = graph.connections.find((c: Message) =>
            c.kind === cmd.connection.kind && c.from.module === cmd.connection.from.module &&
            c.from.port === cmd.connection.from.port && c.to.module === cmd.connection.to.module &&
            c.to.port === cmd.connection.to.port);
          if (!conn) { reply(cmd, false, { code: 'not-found', message: 'No cable' }, s); break; }
          conn.amount = cmd.amount; gen++; reply(cmd, true, {}, s); break;
        }
        case 'listAudioDevices': reply(cmd, true, { result: { devices: copy(audio) } }, s); break;
        case 'listMidiDevices': reply(cmd, true, { result: { devices: copy(midi) } }, s); break;
        case 'midiLearn':
          if (typeof cmd.armed !== 'boolean') {
            reply(cmd, false, { code: 'invalid', message: 'Invalid armed flag' }, s); break;
          }
          learnArmed = cmd.armed; learnPacket = null;
          reply(cmd, true, { result: { armed: learnArmed } }, s);
          emitStatus();
          break;
        case 'setMidiEnabled':
          for (const d of midi) if (d.id === cmd.deviceId) d.enabled = cmd.on;
          reply(cmd, true, {}, s); break;
        default: reply(cmd, true, {}, s);
      }
    };
    const send = (cmd: Message) => {
      sent.push(copy(cmd));
      if (cmd.type === 'app.restartEngine') {
        restarts++;
        exit(true);
        if (!dropRestartReply) setTimeout(() => reply(cmd, true, {}, session(), '0'), 0);
        dropRestartReply = false;
        return;
      }
      const s = session();
      if (holdType === cmd.type) { holdType = ''; held.push({ cmd: copy(cmd), session: s, gen: String(gen) }); return; }
      setTimeout(() => accept(cmd, s), delay);
    };
    let holdType = '';
    let holdOpen = false;
    let pendingOpen: (() => void) | undefined;
    const saves: Message[] = [];
    let opens = 0, restarts = 0, dropRestartReply = false;
    const exit = (expected = false) => {
      emit({ v: 0, type: 'app.engineExited', exitCode: expected ? 0 : null,
        signal: null, expected });
      sessionNo++; gen = 0;
      learnArmed = false; learnPacket = null;
      graph = { modules: [], connections: [] };
      setTimeout(() => void hello(), 250);
    };
    (window as any).wirescape = {
      send,
      onMessage(cb: (m: Message) => void) {
        listeners.add(cb);
        setTimeout(() => void hello(), 0);
        return () => listeners.delete(cb);
      },
      openPatch: async (request?: { library: string }) => {
        opens++;
        if (request) return request.library === 'list' ? { name: 'User patches', text: '[]' } : null;
        const selected = openText;
        if (holdOpen) { holdOpen = false; await new Promise<void>(resolve => { pendingOpen = resolve; }); }
        return selected;
      },
      savePatch: async (text: string, options: Message = {}) => {
        saves.push({ text, ...options }); saved = text; return { name: 'Saved.wirescape.json' };
      },
      platform: 'linux',
    };
    (window as any).__mockBridge = {
      sent, getGraph: () => copy(graph), getSession: session, generation: () => String(gen),
      getSaved: () => saved, getSaves: () => copy(saves), openCount: () => opens, restartCount: () => restarts,
      dropNextRestartReply: () => { dropRestartReply = true; },
      loseHeldWithPush: (applied: boolean) => {
        if (applied) for (const h of held) if (!h.applied && h.session === session() &&
          (h.cmd.type === 'loadGraph' || h.cmd.type === 'applyGraph')) {
          h.result = commitGraph(h.cmd);
          h.applied = true;
        }
        emitStatus();
      },
      replyHeldLate: () => { for (const h of held.splice(0))
        reply(h.cmd, true, h.result ?? {}, h.session, String(gen)); },
      lateReply: (id: string, g = String(gen)) =>
        emit({ v: 0, session: session(), re: id, ok: true, gen: g,
          result: { path: 'live', replaced: [], unapplied: [] } }),
      holdOpen: () => { holdOpen = true; },
      releaseOpen: () => { pendingOpen?.(); pendingOpen = undefined; },
      menu: (type: string) => emit({ v: 0, type }),
      acceptHeld: () => { for (const h of held.splice(0)) {
        if (h.applied) reply(h.cmd, true, h.result ?? {}, h.session, String(gen));
        else accept(h.cmd, h.session);
      } },
      refuseHeld: (code = 'refused') => { for (const h of held.splice(0))
        reply(h.cmd, false, { code, message: 'Scripted ' + code }, h.session, h.gen); },
      setOpen: (value: { text: string; name: string } | null) => { openText = value; },
      setDelay: (ms: number) => { delay = ms; },
      setUnapplied: (items: { moduleId: number; paramId: string }[]) => { nextUnapplied = copy(items); },
      setNativeReplaced: (items: number[]) => { nextReplaced = copy(items); },
      refuseNext: (type: string, code = 'refused') => { refused.push({ type, code }); },
      holdNext: (type: string) => { holdType = type; },
      releaseHeld: () => { for (const h of held.splice(0)) reply(h.cmd, true, {}, h.session, h.gen); },
      exit,
      devices: () => emit({ v: 0, type: 'devices', session: session(), gen: String(gen),
        audioDevices: copy(audio), midiDevices: copy(midi) }),
      status: emitStatus,
      captureCc: (deviceId: string, channel: number, controller: number, value: number) => {
        if (!learnArmed || !midi.some(d => d.id === deviceId && d.enabled) ||
            !Number.isInteger(channel) || channel < 1 || channel > 16 ||
            !Number.isInteger(controller) || controller < 0 || controller > 127 ||
            !Number.isInteger(value) || value < 0 || value > 127) return;
        learnSeq = (learnSeq + 1) >>> 0;
        learnPacket = { seq: String(learnSeq), deviceId, channel, controller, value };
        emitStatus();
      },
      telemetry: (data: Message, atGen = String(gen)) => emit({ v: 0, type: 'telemetry', session: session(),
        gen: atGen, telemetry: { tick: 12, time: 0.4, effective: {}, phase: {},
          envelope: {}, meters: {}, scope: {}, eventActivity: {}, heldNotes: [], ...data } }),
    };
  }, options);
}
