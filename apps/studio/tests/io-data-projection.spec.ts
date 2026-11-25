// SPDX-License-Identifier: GPL-3.0-only
import { test, expect } from '@playwright/test';
import { oscEditorSource, splitOscEditorSave, oscConstructionChanged, ccMappingSource, splitCcMappingSave } from '../src/app/ioData';
import type { OscOutConfig } from '../src/app/OscOutEditor';

test('E3c editor data projection wins over stale config without changing authored patch', () => {
  const m = { id: 4, module: 'osc.out', config: { port: 9001, rows: [{ address: '/old' }],
    notes: { address: '/old/note', enabled: true } }, data: { routes: { rows: [{ address: '/new' }] } } };
  const before = structuredClone(m);
  expect(oscEditorSource(m)).toEqual({ port: 9001, rows: [{ address: '/new' }], notes: {} });
  expect(m).toEqual(before);
});

test('E3c editor split retains opaque storage and sends only declared route fields', () => {
  const m = { id: 4, module: 'osc.out', ownerNote: 'keep', config: { port: 9001,
    future: 4, rows: [{ address: '/old', opaque: 2 }], notes: { enabled: true, opaque: 3 } },
    data: { futureSlot: { keep: true }, routes: { futureField: 'keep' } } };
  const draft: OscOutConfig = { port: 9001, rate_hz: 100, future: 4,
    rows: Array.from({ length: 8 }, (_, i) => ({ address: '/new/' + i, kind: 'cv', deadband: .001 })),
    notes: { address: '/new/note' } };
  const before = structuredClone(m);
  const edit = splitOscEditorSave(m, draft);
  expect(edit.config).toEqual({ port: 9001, rate_hz: 100, future: 4 });
  expect(edit.value.rows).toHaveLength(8);
  expect(edit.value).toMatchObject({ notes_address: '/new/note', notes_enabled: false });
  expect((edit.value.rows as unknown[])[0]).toEqual({ address: '/new/0', kind: 'cv', deadband: .001, enabled: true });
  expect(edit.authored).toMatchObject({ ownerNote: 'keep', config: { rows: [{ opaque: 2 }],
    notes: { opaque: 3 }, future: 4 }, data: { futureSlot: { keep: true }, routes: { futureField: 'keep' } } });
  expect(m).toEqual(before);
});

test('E3c FakeEngine accepts live route and CC slots without replacement and refuses atomically', async ({ page }) => {
  const { boot } = await import('./helpers');
  await boot(page);
  const result = await page.evaluate(async () => {
    const e = window.__wirescapeTest.engine as any;
    e.stop();
    const rows = Array.from({ length: 8 }, (_, i) => ({ address: '/old/' + i, kind: 'cv', deadband: .001, enabled: false }));
    await e.loadGraph({ format: 'wirescape.native.patch', version: 2, connections: [], modules: [
      { id: 4, module: 'osc.out', config: { port: 9001, rows } },
      { id: 5, module: 'midi.cc_to_cv', config: { rows: [{ controller: 21 }] } },
    ] });
    e.phases.set(4, .5);
    const generation = e.graphGeneration;
    const next = { rows: rows.map((row, i) => ({ ...row, address: '/new/' + i, enabled: i === 0 })),
      notes_address: '/new/note', notes_enabled: false };
    e.debug.refuseEdits = true;
    let refused = false;
    try { await e.setData(4, 'routes', next); } catch { refused = true; }
    const refusedState = { generation: e.graphGeneration, state: e.osc.out[0].state,
      data: e.document.modules[0].data ?? null };
    e.debug.refuseEdits = false;
    await e.setData(4, 'routes', next);
    await e.setData(5, 'mapping', { rows: Array.from({ length: 8 }, (_, i) =>
      ({ controller: i + 31, channel: 0, fourteen_bit: false, min: 0, max: 1, smoothing_ms: 5 })) });
    return { refused, refusedState, generation, after: e.graphGeneration, state: e.osc.out[0].state,
      address: e.document.modules[0].data.routes.rows[0].address, cc: e.ccRowsOf(5)[0].controller,
      retained: e.phases.get(4) };
  });
  expect(result.refused).toBe(true);
  expect(result.refusedState).toEqual({ generation: result.generation, state: 'disabled', data: null });
  expect(result.after).toBe(result.generation);
  expect(result).toMatchObject({ state: 'sending', address: '/new/0', cc: 31, retained: .5 });
});

test('A86 row-only save is not a construction edit even when defaults were omitted', () => {
  const m = { id: 2, module: 'osc.out' };
  const draft: OscOutConfig = { port: 9001, rate_hz: 100,
    rows: Array.from({ length: 8 }, (_, i) => ({ address: '/live/' + i, kind: 'cv', deadband: .001 })),
    notes: { address: '/new/note' } };
  expect(oscConstructionChanged(m, draft)).toBe(false);
  expect(oscConstructionChanged(m, { ...draft, port: 9011 })).toBe(true);
  expect(oscConstructionChanged(m, { ...draft, rate_hz: 200 })).toBe(true);
  const explicit = { ...m, config: { version: 1, port: 9001, rate_hz: 100 } };
  expect(oscConstructionChanged(explicit, draft)).toBe(false);
});

test('E3c CC migration completes indexed defaults and legacy bipolar without changing opaque data', () => {
  const m = { id: 9, module: 'midi.cc_to_cv', config: { rows: [
    { channel: 2, controller: 11, bipolar: true, max: -.25 },
    { controller: 12, min: 1, max: -1 },
  ] }, data: { futureSlot: { keep: true } } };
  const before = structuredClone(m);
  const edit = splitCcMappingSave(m, ccMappingSource(m));
  expect(edit.value.rows).toHaveLength(8);
  expect((edit.value.rows as unknown[])[0]).toEqual({ channel: 2, controller: 11,
    fourteen_bit: false, smoothing_ms: 5, min: -1, max: -.25 });
  expect((edit.value.rows as unknown[])[1]).toMatchObject({ min: 1, max: -1 });
  expect((edit.value.rows as unknown[])[7]).toMatchObject({ controller: 8, min: 0, max: 1 });
  expect(edit.authored.config).toBeUndefined();
  expect(edit.authored.data).toMatchObject({ futureSlot: { keep: true } });
  expect(m).toEqual(before);
});

test('E3c explicit mapping wins, edits preserve opaque row/slot fields only in authored data', () => {
  const m = { id: 9, module: 'midi.cc_to_cv', config: { rows: [{ controller: 99 }] },
    data: { mapping: { opaqueSlot: 7, rows: [{ controller: 21, opaqueRow: 8 }] } } };
  const rows = ccMappingSource(m);
  expect(rows[0]).toMatchObject({ controller: 21 });
  const edit = splitCcMappingSave(m, [{ ...rows[0], controller: 31 }]);
  expect(edit.value).not.toHaveProperty('opaqueSlot');
  expect((edit.value.rows as unknown[])[0]).not.toHaveProperty('opaqueRow');
  expect(edit.authored.data).toMatchObject({ mapping: { opaqueSlot: 7, rows: [
    expect.objectContaining({ controller: 31, opaqueRow: 8 }), ...Array.from({ length: 7 }, () => expect.anything()),
  ] } });
  expect(ccMappingSource({ ...m, data: { mapping: {} } })).toEqual([]);
});
