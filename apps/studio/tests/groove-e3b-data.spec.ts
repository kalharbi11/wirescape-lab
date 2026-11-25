// SPDX-License-Identifier: GPL-3.0-only
import { test, expect } from '@playwright/test';
import { grooveExecution, grooveEditorConfig, mergeGroovePattern } from '../src/groove/livePattern';

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

test('Groove E3b canonical data hydrates the editor, explicit slot wins and unknown fields survive save', () => {
  const module = { config: { version: 2, bpm: 120, tracks: [{ div: 2,
    steps: [{ kind: 'note', key: 60, velocity: 1 }] }] }, data: { future_slot: { keep: true },
    pattern: { length_1: 8, length_2: 32, tempo_source: 'host', future: { opaque: true },
      steps_1: [{ kind: 'note', key: 72, velocity: .5, key_count: 2, keys: [72, 67, 0, 0, 0],
        gate_q: 2, cond_type: 1, cond_a: 50, future_row: 9 }], steps_2: [] } } };
  const before = structuredClone(module);
  const editor = grooveEditorConfig(module)!;
  expect(editor.tracks[0]!.steps[0]).toEqual({ kind: 'note', key: 72, velocity: .5,
    keys: [72, 67], gate: .5, cond: { type: 'chance', p: 50 } });
  expect(editor.tracks[0]!.length).toBe(8);
  expect(editor.tempo_source).toBe('host');
  editor.tracks[0]!.steps[0]!.velocity = .75;
  const wire = grooveExecution(editor)!.pattern;
  expect(wire.steps_1[0]).not.toHaveProperty('future_row');
  const saved = mergeGroovePattern(module.data, wire);
  expect(saved.future_slot).toEqual({ keep: true });
  expect(saved.pattern).toMatchObject({ future: { opaque: true } });
  expect((saved.pattern as { steps_1: unknown[] }).steps_1[0]).toMatchObject({ future_row: 9, velocity: .75 });
  expect(module).toEqual(before);
  expect(grooveEditorConfig({ config: module.config, data: { pattern: { length_1: 12 } } })).toBeNull();
  expect(grooveEditorConfig({ config: module.config, data: { pattern: {} } })!.tracks[0]!.steps).toEqual([]);
});

test('Groove E3b canonical hidden rows stay intact until an explicit truncation', () => {
  const rows = Array.from({ length: 10 }, (_, i) => i === 9
    ? { kind: 'note', key: 65, keys: [65, 0, 0, 0, 0], velocity: .5 } : {});
  const module = { config: { version: 2, bpm: 120, tracks: [{}] },
    data: { pattern: { length_1: 8, steps_1: rows } } };
  const editor = grooveEditorConfig(module)!;
  expect(editor.tracks[0]!.steps[9]).toMatchObject({ kind: 'note', key: 65 });
  const wire = grooveExecution(editor, true)!.pattern;
  expect(wire.steps_1[9]).toMatchObject({ kind: 'note', key: 65 });
  editor.tracks[0]!.steps.length = 8; // explicit editor length truncation
  expect(grooveExecution(editor, true)!.pattern.steps_1[9]).toEqual({});
  for (const invalid of [{ length_1: null }, { tempo_source: null }, { steps_1: null },
    { steps_1: [{ velocity: null }] }, { steps_1: [{ kind: null }] }]) {
    expect(grooveEditorConfig({ config: module.config, data: { pattern: invalid } })).toBeNull();
  }
});

test('Groove E3b one-track edit does not clear authored inactive-track rows', () => {
  const pattern = { length_1: 8, length_2: 64, steps_1: [],
    steps_2: [{ kind: 'note', key: 67, keys: [67, 0, 0, 0, 0], velocity: .5, future_row: 9 }] };
  const module = { config: { version: 2, bpm: 120, tracks: [{}] }, data: { pattern } };
  const editor = grooveEditorConfig(module)!;
  expect(editor.tracks).toHaveLength(1);
  editor.tracks[0]!.steps.push({ kind: 'note', key: 60, velocity: .5 });
  const wire = grooveExecution(editor, true, pattern)!.pattern;
  expect(wire.length_2).toBe(64);
  expect(wire.steps_2).toEqual([{ kind: 'note', key: 67, keys: [67, 0, 0, 0, 0], velocity: .5 }]);
  const saved = mergeGroovePattern(module.data, wire);
  expect((saved.pattern as { steps_2: unknown[] }).steps_2).toEqual(pattern.steps_2);
});

test('Groove E3b canonical slot removal reads silent descriptor defaults in the editor', () => {
  const config = { version: 2, bpm: 120, tracks: [{ div: 2, armed: false }] };
  for (const data of [undefined, {}, { future_slot: { keep: true } }]) {
    const editor = grooveEditorConfig({ config, data })!;
    expect(editor.tempo_source).toBe('internal');
    expect(editor.tracks).toEqual([{ div: 2, armed: false, length: 32, steps: [] }]);
  }
  const legacy = { version: 1, bpm: 120, tracks: [{ steps: [{ kind: 'note', key: 72, velocity: .8 }] }] };
  expect(grooveEditorConfig({ config: legacy, data: {} })).toEqual(legacy);
  expect(grooveEditorConfig({ config, data: { pattern: null } })).toBeNull();
});
