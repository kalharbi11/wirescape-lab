// SPDX-License-Identifier: GPL-3.0-only
import { test, expect } from '@playwright/test';
import { grooveExecution } from '../src/groove/livePattern';

test('Groove E3b projection separates live fields and preserves typed rows', () => {
  const cfg = { version: 2, bpm: 120, tempo_source: 'host', extra: 'preserved',
    tracks: [{ length: 8, div: 2, armed: false, steps: [
      { kind: 'note', key: 64, keys: [64, 60, 67], velocity: .75, gate: .5,
        cond: { type: 'ab', a: 1, b: 2 }, mod1: .25, custom: true },
      { kind: 'tie', gate: .25 }, { kind: 'rest' },
    ] }] };
  const before = structuredClone(cfg);
  const first = grooveExecution(cfg)!;
  expect(first.config).toEqual({ version: 2, bpm: 120, tracks: [{ armed: false, div: 2 }] });
  expect(first.pattern.length_1).toBe(8);
  expect(first.pattern.length_2).toBe(32);
  expect(first.pattern.tempo_source).toBe('host');
  expect(first.pattern.steps_1).toHaveLength(64);
  expect(first.pattern.steps_1[0]).toEqual({ kind: 'note', key: 64, keys: [64, 60, 67, 0, 0],
    key_count: 3, velocity: .75, gate_q: 2, cond_type: 2, cond_a: 1, cond_b: 2, mod1: .25, mod2: 0 });
  expect(first.pattern.steps_1[1]).toMatchObject({ kind: 'tie', gate_q: 1 });
  expect(first.pattern.steps_1[2]).toEqual({});
  expect(cfg).toEqual(before);
  const edited = structuredClone(cfg);
  edited.tracks[0]!.length = 16;
  edited.tracks[0]!.steps[0]!.velocity = .5;
  const second = grooveExecution(edited)!;
  expect(second.config).toEqual(first.config);
  expect(second.pattern).not.toEqual(first.pattern);
  edited.bpm = 130;
  expect(grooveExecution(edited)!.config).not.toEqual(first.config);
});

test('Groove E3b legacy v1 keeps 32-step meaning and invalid chords are not repaired', () => {
  const legacy = { version: 1, bpm: 120, tracks: [{ steps: [{ kind: 'note', key: 72, velocity: .8 }] }] };
  const projected = grooveExecution(legacy)!;
  expect(projected.config).toEqual({ version: 1, bpm: 120, tracks: [{}] });
  expect(projected.pattern.length_1).toBe(32);
  expect(projected.pattern.steps_1[0]).toMatchObject({ key: 72, keys: [72, 0, 0, 0, 0],
    velocity: Math.fround(.8), key_count: 1 });
  expect(grooveExecution({ version: 2, bpm: 120, tracks: [{ steps: [
    { kind: 'note', key: 60, keys: [60, 60], velocity: 1 }] }] })).toBeNull();
});
