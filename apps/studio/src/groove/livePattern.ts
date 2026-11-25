// SPDX-License-Identifier: GPL-3.0-only
// Pure Groove editor -> E3b wire projection. Shared client transport is owned
// separately; this module performs no I/O and does not mutate saved drafts.
import { engineConfig, trackLength, readConfig, LENGTHS, type GrooveConfig, type Step, type Track } from './pattern';
import type { PatchModule } from '../patch/types';

export interface LivePatternRow {
  kind: 'rest' | 'note' | 'tie';
  key: number; velocity: number; mod1: number; mod2: number;
  gate_q: number; cond_type: number; cond_a: number; cond_b: number;
  key_count: number; keys: number[];
}
export interface GrooveLivePattern {
  length_1: number; length_2: number; tempo_source: 'internal' | 'host';
  steps_1: Partial<LivePatternRow>[]; steps_2: Partial<LivePatternRow>[];
}
export interface GrooveExecution {
  config: { version: number; bpm: number; tracks: { armed?: boolean; mute?: boolean; div?: unknown }[] };
  pattern: GrooveLivePattern;
}

const isObject = (v: unknown): v is Record<string, unknown> =>
  !!v && typeof v === 'object' && !Array.isArray(v);

/** Map exactly the descriptor's numeric condition encoding, not a new musical schema. */
function row(s: Step): Partial<LivePatternRow> | null {
  const key = s.kind === 'note' ? s.key ?? 60 : 60;
  const authored = s.kind === 'note' ? s.keys ?? [key] : [key];
  // Do not pad malformed input into a valid chord; let the existing native
  // refusal path handle legacy invalid config rather than silently repairing it.
  if (!Array.isArray(authored) || authored.length < 1 || authored.length > 5 ||
      authored[0] !== key || authored.some(k => !Number.isInteger(k) || k < 0 || k > 127) ||
      new Set(authored).size !== authored.length ||
      authored.slice(2).some((k, i) => k <= authored[i + 1]!)) return null;
  const keys = [...authored];
  while (keys.length < 5) keys.push(0);
  const condition = s.cond;
  const cond_type = condition?.type === 'chance' ? 1 : condition?.type === 'ab' ? 2 :
    condition?.type === 'first' ? 3 : condition?.type === 'not_first' ? 4 : 0;
  const cond_a = condition?.type === 'chance' ? condition.p : condition?.type === 'ab' ? condition.a : 0;
  const cond_b = condition?.type === 'ab' ? condition.b : 0;
  const velocity = Math.fround(s.kind === 'note' ? s.velocity ?? 0.8 : 0);
  const mod1 = Math.fround(s.mod1 ?? 0), mod2 = Math.fround(s.mod2 ?? 0);
  const gate_q = (s.gate ?? 1) * 4;
  if (s.kind === 'rest' && mod1 === 0 && mod2 === 0 && gate_q === 4) return {};
  return { kind: s.kind, key, velocity, mod1, mod2, gate_q, cond_type, cond_a, cond_b,
    key_count: authored.length, keys };
}

/**
 * Known editor fields -> construction-only config + live data. This mirrors
 * the legacy host decoder's padded 64-row representation so unchanged data
 * is stable across legacy reload and the first live Apply. Unknown authored
 * fields are not changed here; the execution copy never sends them as edits.
 * Undefined/malformed legacy config takes its existing refusal/default path.
 */
export function grooveExecution(raw: unknown): GrooveExecution | null {
  const config = engineConfig(raw);
  if (!isObject(config) || (config.version !== 1 && config.version !== 2) ||
      !Array.isArray(config.tracks) || !config.tracks.length) return null;
  const cfg = config as unknown as GrooveConfig;
  const patterns: Partial<LivePatternRow>[][] = [[], []];
  for (let t = 0; t < 2; ++t) {
    const steps = cfg.tracks[t]?.steps ?? [];
    for (const step of steps) {
      const converted = row(step);
      if (converted === null) return null;
      patterns[t]!.push(converted);
    }
    while (patterns[t]!.length < 64) patterns[t]!.push({});
  }
  const source = isObject(raw) ? raw.tempo_source : undefined;
  if (source !== undefined && (cfg.version !== 2 || (source !== 'internal' && source !== 'host'))) return null;
  return {
    config: {
      version: cfg.version, bpm: Math.fround(cfg.bpm),
      tracks: cfg.tracks.map(track => {
        const out: GrooveExecution['config']['tracks'][number] = {};
        if (track.armed !== undefined) out.armed = track.armed;
        if (track.mute !== undefined) out.mute = track.mute;
        if ('div' in track) out.div = track.div;
        return out;
      }),
    },
    pattern: { length_1: trackLength(cfg, 0), length_2: cfg.tracks[1] ? trackLength(cfg, 1) : 32,
      tempo_source: source === 'host' ? 'host' : 'internal',
      steps_1: patterns[0]!, steps_2: patterns[1]! },
  };
}

// A canonical saved module has construction config + data.pattern; legacy
// documents keep their editable config. Do not let an old config pattern
// override explicitly authored data. The v2 *editor view* is not itself a
// construction-version change, which is decided separately at Apply time.
const integer = (v: unknown, min: number, max: number): v is number =>
  typeof v === 'number' && Number.isInteger(v) && v >= min && v <= max;
const number = (v: unknown, min: number, max: number): v is number =>
  typeof v === 'number' && Number.isFinite(v) && v >= min && v <= max;

function editorRow(value: unknown): Step | null {
  if (!isObject(value)) return null;
  const kind = value.kind ?? 'rest', key = value.key ?? 60, velocity = value.velocity ?? 0;
  const mod1 = value.mod1 ?? 0, mod2 = value.mod2 ?? 0, gate = value.gate_q ?? 4;
  const count = value.key_count ?? 1, keys = value.keys ?? [60, 60, 60, 60, 60];
  const type = value.cond_type ?? 0, a = value.cond_a ?? 0, b = value.cond_b ?? 0;
  if ((kind !== 'rest' && kind !== 'note' && kind !== 'tie') || !integer(key, 0, 127) ||
      !number(velocity, 0, 1) || !number(mod1, 0, 1) || !number(mod2, 0, 1) ||
      !integer(gate, 1, 4) || !integer(count, 1, 5) || !integer(type, 0, 4) ||
      !integer(a, 0, 99) || !integer(b, 0, 8) ||
      !Array.isArray(keys) || keys.length !== 5 || keys.some(k => !integer(k, 0, 127)) ||
      keys[0] !== key || new Set(keys.slice(0, count)).size !== count ||
      keys.slice(2, count).some((k, i) => k <= keys[i + 1]) ||
      (kind !== 'note' && (type !== 0 || count !== 1))) return null;
  if ((type === 0 || type === 3 || type === 4) && (a !== 0 || b !== 0) ||
      type === 1 && (!integer(a, 1, 99) || b !== 0) ||
      type === 2 && (!integer(b, 2, 8) || !integer(a, 1, b))) return null;
  const step: Step = { kind };
  if (kind === 'note') {
    step.key = key;
    step.velocity = velocity;
    if (count > 1) step.keys = keys.slice(0, count);
    if (type === 1) step.cond = { type: 'chance', p: a };
    else if (type === 2) step.cond = { type: 'ab', a, b };
    else if (type === 3 || type === 4) step.cond = { type: type === 3 ? 'first' : 'not_first' };
  }
  if (mod1 !== 0) step.mod1 = mod1;
  if (mod2 !== 0) step.mod2 = mod2;
  if (gate !== 4) step.gate = gate / 4;
  return step;
}

/** Read a canonical or legacy source without mutating it or silently repairing a bad slot. */
export function grooveEditorConfig(module: Pick<PatchModule, 'config' | 'data'>): GrooveConfig | null {
  if (module.data === undefined) return readConfig(module.config);
  if (!isObject(module.data)) return null;
  if (!Object.prototype.hasOwnProperty.call(module.data, 'pattern')) return readConfig(module.config);
  const data = module.data.pattern;
  if (!isObject(data)) return null;
  const config = module.config ?? {};
  if (!isObject(config)) return null;
  const empty = Object.keys(config).length === 0;
  if (!empty && ((config.version !== 1 && config.version !== 2) || !number(config.bpm, 20, 300) ||
      !Array.isArray(config.tracks) || config.tracks.length < 1 || config.tracks.length > 2)) return null;
  const construction = empty ? [{}] : config.tracks as unknown[];
  const tempo = data.tempo_source ?? 'internal';
  if (tempo !== 'internal' && tempo !== 'host') return null;
  const lengths = [data.length_1 ?? 32, data.length_2 ?? 32];
  const rows = [data.steps_1 ?? [], data.steps_2 ?? []];
  const tracks: Track[] = [];
  for (let t = 0; t < 2; ++t) {
    const len = lengths[t], rawRows = rows[t];
    if (typeof len !== 'number' || !(LENGTHS as readonly number[]).includes(len) ||
        !Array.isArray(rawRows) || rawRows.length > 64) return null;
    const steps: Step[] = [];
    for (const raw of rawRows) {
      const decoded = editorRow(raw);
      if (!decoded) return null;
      steps.push(decoded);
    }
    if (t >= construction.length) continue;
    const track = construction[t];
    if (!isObject(track)) return null;
    // Retain authored construction extras in the editor view; row extras stay
    // in the original data envelope and are preserved by mergeGroovePattern.
    const out: Track = { ...structuredClone(track), length: len, steps };
    tracks.push(out);
  }
  return { ...structuredClone(config), version: 2, bpm: empty ? 120 : config.bpm as number,
    tempo_source: tempo, tracks };
}

/**
 * Merge only known editable slot fields into the authored envelope for saving.
 * Opaque sibling slots, slot keys and row keys survive. The wire edit must
 * use the known-fields-only projected pattern, never this stored envelope.
 */
export function mergeGroovePattern(rawData: unknown, pattern: GrooveLivePattern): Record<string, unknown> {
  const data = isObject(rawData) ? structuredClone(rawData) : {};
  const old = isObject(data.pattern) ? data.pattern : {};
  const known = new Set(['kind', 'key', 'velocity', 'mod1', 'mod2', 'gate_q', 'cond_type',
    'cond_a', 'cond_b', 'key_count', 'keys']);
  const mergeRows = (before: unknown, after: Partial<LivePatternRow>[]) => after.map((r, i) => {
    const prev = Array.isArray(before) && isObject(before[i]) ? before[i] : {};
    const extras = Object.fromEntries(Object.entries(prev).filter(([k]) => !known.has(k)));
    return { ...extras, ...structuredClone(r) };
  });
  data.pattern = { ...old, ...pattern, steps_1: mergeRows(old.steps_1, pattern.steps_1),
    steps_2: mergeRows(old.steps_2, pattern.steps_2) };
  return data;
}
