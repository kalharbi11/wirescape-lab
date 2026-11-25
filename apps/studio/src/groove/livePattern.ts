// SPDX-License-Identifier: GPL-3.0-only
// Pure Groove editor -> E3b wire projection. Shared client transport is owned
// separately; this module performs no I/O and does not mutate saved drafts.
import { engineConfig, trackLength, type GrooveConfig, type Step } from './pattern';

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
