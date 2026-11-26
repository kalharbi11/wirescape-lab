// SPDX-License-Identifier: GPL-3.0-only
// Pure Groove editor -> E3b wire projection. Shared client transport is owned
// separately; this module performs no I/O and does not mutate saved drafts.
import { engineConfig, trackLength, readConfig, upgrade, LENGTHS, type GrooveConfig, type Step, type Track } from './pattern';

export interface LivePatternRow {
  kind: 'rest' | 'note' | 'tie';
  key: number; velocity: number; mod1: number; mod2: number;
  gate_q: number; cond_type: number; cond_a: number; cond_b: number;
  key_count: number; keys: number[];
}
export interface GrooveLivePattern extends Record<string, unknown> {
  length_1: number; length_2: number; tempo_source: 'internal' | 'host';
  steps_1: Partial<LivePatternRow>[]; steps_2: Partial<LivePatternRow>[];
}
export interface GrooveExecution {
  config: { version: number; bpm: number; tracks: { armed?: boolean; mute?: boolean; div?: unknown }[] };
  pattern: GrooveLivePattern;
}

const isObject = (v: unknown): v is Record<string, unknown> =>
  !!v && typeof v === 'object' && !Array.isArray(v);
const ROW_FIELDS = new Set(['kind', 'key', 'velocity', 'mod1', 'mod2', 'gate_q', 'cond_type',
  'cond_a', 'cond_b', 'key_count', 'keys']);

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
export function grooveExecution(raw: unknown, preserveHiddenRows = false,
  untouchedCanonicalPattern?: unknown): GrooveExecution | null {
  const config = engineConfig(raw, preserveHiddenRows);
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
  // A one-track editor cannot express the inactive second track's slot rows.
  // Preserve them in a pattern-only save, rather than treating invisibility
  // as an authored reset. An actual second-track edit has two editor tracks
  // and is classified separately as a construction change when necessary.
  let length2 = cfg.tracks[1] ? trackLength(cfg, 1) : 32;
  if (cfg.tracks.length === 1 && untouchedCanonicalPattern !== undefined) {
    if (!isObject(untouchedCanonicalPattern)) return null;
    const len = field(untouchedCanonicalPattern, 'length_2', 32);
    const rows = field(untouchedCanonicalPattern, 'steps_2', []);
    if (typeof len !== 'number' || !(LENGTHS as readonly number[]).includes(len) ||
        !Array.isArray(rows) || rows.length > 64) return null;
    const preserved: Partial<LivePatternRow>[] = [];
    for (const row of rows) {
      if (!isObject(row) || !editorRow(row)) return null;
      // Known fields only on the wire, retaining even the unused chord
      // entries and the original row count for unchanged inactive data.
      preserved.push(structuredClone(Object.fromEntries(Object.entries(row)
        .filter(([key]) => ROW_FIELDS.has(key)))) as Partial<LivePatternRow>);
    }
    length2 = len;
    patterns[1] = preserved;
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
    pattern: { length_1: trackLength(cfg, 0), length_2: length2,
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

// Descriptor defaults apply only to an absent field, never explicit null.
const field = (object: Record<string, unknown>, key: string, fallback: unknown): unknown =>
  Object.prototype.hasOwnProperty.call(object, key) ? object[key] : fallback;

function editorRow(value: unknown): Step | null {
  if (!isObject(value)) return null;
  const kind = field(value, 'kind', 'rest'), key = field(value, 'key', 60), velocity = field(value, 'velocity', 0);
  const mod1 = field(value, 'mod1', 0), mod2 = field(value, 'mod2', 0), gate = field(value, 'gate_q', 4);
  const count = field(value, 'key_count', 1), keys = field(value, 'keys', [60, 60, 60, 60, 60]);
  const type = field(value, 'cond_type', 0), a = field(value, 'cond_a', 0), b = field(value, 'cond_b', 0);
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
export function grooveEditorConfig(module: { config?: unknown; data?: unknown }): GrooveConfig | null {
  const config = module.config === undefined ? {} : module.config;
  if (!isObject(config)) return null;
  if (module.data !== undefined && !isObject(module.data)) return null;
  const envelope = module.data as Record<string, unknown> | undefined;
  const explicit = envelope !== undefined && Object.prototype.hasOwnProperty.call(envelope, 'pattern');
  // A construction-only document with a removed slot means descriptor
  // defaults. Only an actual legacy config pattern falls back to readConfig.
  // Match the native adapter's canonical shape, not an inferred edit version.
  const constructionOnly = Array.isArray(config.tracks) && config.tracks.length > 0 &&
    !Object.prototype.hasOwnProperty.call(config, 'tempo_source') &&
    config.tracks.every(t => isObject(t) && !Object.prototype.hasOwnProperty.call(t, 'steps') &&
      !Object.prototype.hasOwnProperty.call(t, 'length'));
  if (!explicit && !constructionOnly) return readConfig(module.config);
  const data = explicit ? envelope!.pattern : {};
  if (!isObject(data)) return null;
  const empty = Object.keys(config).length === 0;
  if (!empty && ((config.version !== 1 && config.version !== 2) || !number(config.bpm, 20, 300) ||
      !Array.isArray(config.tracks) || config.tracks.length < 1 || config.tracks.length > 2)) return null;
  const construction = empty ? [{}] : config.tracks as unknown[];
  const tempo = field(data, 'tempo_source', 'internal');
  if (tempo !== 'internal' && tempo !== 'host') return null;
  const lengths = [field(data, 'length_1', 32), field(data, 'length_2', 32)];
  const rows = [field(data, 'steps_1', []), field(data, 'steps_2', [])];
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
  const mergeRows = (before: unknown, after: Partial<LivePatternRow>[]) => after.map((r, i) => {
    const prev = Array.isArray(before) && isObject(before[i]) ? before[i] : {};
    const extras = Object.fromEntries(Object.entries(prev).filter(([k]) => !ROW_FIELDS.has(k)));
    return { ...extras, ...structuredClone(r) };
  });
  data.pattern = { ...old, ...pattern, steps_1: mergeRows(old.steps_1, pattern.steps_1),
    steps_2: mergeRows(old.steps_2, pattern.steps_2) };
  return data;
}

export type GrooveApply<T> =
  | { kind: 'pattern'; pattern: GrooveLivePattern; saved: T & { data: Record<string, unknown> } }
  | { kind: 'construction'; reason: 'bpm' | 'divisor' | 'armed' | 'mute' | 'track-count' | 'version' };

/**
 * A90: the editor's automatic v2/two-track upgrade is not a construction edit.
 * An explicit edit of the otherwise absent track must pass its intent even if
 * the final value equals the synthetic track's default (e.g. an activation).
 * This is pure preparation; the caller still owns the correlated ACK,
 * document commit/history and construction replacement disclosure.
 */
export function classifyGrooveApply<T extends { config?: unknown; data?: unknown }>(
  module: T, edited: GrooveConfig, explicitAbsentTrackEdit = false): GrooveApply<T> | null {
  const original = grooveEditorConfig(module);
  const source = module.config;
  if (!original || !isObject(source) || (source.version !== 1 && source.version !== 2) ||
      !Array.isArray(source.tracks) || source.tracks.length < 1 || source.tracks.length > 2 ||
      edited.tracks.length < source.tracks.length || edited.tracks.length > 2) return null;
  const count = source.tracks.length;
  const baseline = structuredClone(original);
  const next = structuredClone(edited);
  // Compare in the same editor schema so v1's implicit 32-step length and
  // the synthetic second track are not mistaken for authored construction.
  if (baseline.version === 1 || next.tracks.length > count) upgrade(baseline);
  if (next.version !== 1 && next.version !== 2) return { kind: 'construction', reason: 'version' };
  if (baseline.bpm !== next.bpm) return { kind: 'construction', reason: 'bpm' };
  const same = (a: unknown, b: unknown) => JSON.stringify(a) === JSON.stringify(b);
  for (let t = 0; t < count; ++t) {
    const a = original.tracks[t]!, b = next.tracks[t]!;
    if ((a.div ?? 1) !== (b.div ?? 1)) return { kind: 'construction', reason: 'divisor' };
    if ((a.armed ?? true) !== (b.armed ?? true)) return { kind: 'construction', reason: 'armed' };
    if ((a.mute ?? false) !== (b.mute ?? false)) return { kind: 'construction', reason: 'mute' };
  }
  if (count === 1 && (explicitAbsentTrackEdit ||
      (next.tracks.length === 2 && !same(baseline.tracks[1], next.tracks[1]))))
    return { kind: 'construction', reason: 'track-count' };
  // Do not pass the synthetic track to the native projection. A canonical
  // inactive track's authored slot is independent from the editor placeholder.
  baseline.tracks.length = count;
  next.tracks.length = count;
  const canonical = isObject(module.data) && isObject(module.data.pattern) ? module.data.pattern : undefined;
  const before = grooveExecution(baseline, true, canonical);
  const after = grooveExecution(next, true, canonical);
  if (!before || !after) return null;
  // The native slot validates independently of construction version: all
  // lengths, conditions, gate quarters, chords and tempo source are expressible.
  // Preserve the source construction verbatim, including a legacy source
  // (explicit pattern wins at reload, the host migrates only the execution copy).
  let data: Record<string, unknown>;
  if (!canonical) {
    data = mergeGroovePattern(module.data, after.pattern);
  } else {
    data = structuredClone(module.data as Record<string, unknown>);
    const saved = data.pattern as Record<string, unknown>;
    for (const key of ['length_1', 'length_2', 'tempo_source'] as const)
      if (!same(before.pattern[key], after.pattern[key])) saved[key] = after.pattern[key];
    for (const key of ['steps_1', 'steps_2'] as const) {
      const a = before.pattern[key], b = after.pattern[key];
      const rows = Array.isArray(saved[key]) ? saved[key] as unknown[] : [];
      for (let i = 0; i < Math.max(a.length, b.length); ++i) {
        const old = a[i] ?? {}, fresh = b[i] ?? {};
        if (same(old, fresh)) continue;
        while (rows.length <= i) rows.push({});
        const r = isObject(rows[i]) ? rows[i] : {};
        const oldFields = old as Record<string, unknown>, newFields = fresh as Record<string, unknown>;
        for (const name of ROW_FIELDS) {
          if (same(oldFields[name], newFields[name])) continue;
          if (Object.prototype.hasOwnProperty.call(newFields, name)) r[name] = structuredClone(newFields[name]);
          else delete r[name];
        }
        rows[i] = r;
        saved[key] = rows;
      }
    }
  }
  return { kind: 'pattern', pattern: after.pattern, saved: { ...structuredClone(module), data } };
}
