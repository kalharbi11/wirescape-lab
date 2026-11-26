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

import { PatchDoc } from '../src/patch/PatchDoc';
import { commitLearn, forgetLearn } from '../src/app/ccLearn';
import type { PatchV2, Connection } from '../src/patch/types';
import type { Device } from '../src/engine/EngineClient';

const ccDevice: Device = { id: 'Controller|test', name: 'Controller', system_name: 'test', kind: 'midi', enabled: true };
const ccTarget = { module: 3, param: 'gain' };
const ccCapture = { deviceId: ccDevice.id, channel: 2, controller: 71 };
function learnDoc(config: unknown, connections: Connection[] = []): PatchDoc {
  const patch: PatchV2 = { format: 'wirescape.native.patch', version: 2, modules: [
    { id: 1, module: 'midi.in' }, { id: 2, module: 'midi.cc_to_cv', config },
    { id: 3, module: 'essentials.vca' }, { id: 4, module: 'essentials.vca' },
  ], connections: [{ kind: 'event', from: { module: 1, port: 'midi' }, to: { module: 2, port: 'midi' } }, ...connections] };
  return PatchDoc.from(patch);
}
const learnServices = (doc: PatchDoc) => ({ doc, allocateId: () => doc.nextId(), devices: () => [ccDevice] });

test('A95 legacy short mapping saves eight rows; after reload Learn reuses first free row', () => {
  const doc = learnDoc({ rows: [{ controller: 41 }] });
  const first = commitLearn(learnServices(doc), ccTarget, ccCapture, false);
  expect(first).toMatchObject({ module: 2, row: 1, created: false });
  const saved = doc.toJSON();
  expect(saved.modules.find(m => m.id === 2)?.data).toMatchObject({ mapping: { rows: expect.any(Array) } });
  const reloaded = PatchDoc.from(saved);
  expect(reloaded.ccRows(2)).toHaveLength(8);
  const second = commitLearn(learnServices(reloaded), { module: 4, param: 'gain' },
    { ...ccCapture, controller: 72 }, false);
  expect(second).toMatchObject({ module: 2, row: 2, created: false });
  expect(reloaded.modules.size).toBe(4);
});

test('A95 Forget resets an unwired row and Learn reuses it without trimming', () => {
  const doc = learnDoc({ rows: [{ controller: 41 }] });
  const svc = learnServices(doc);
  expect(commitLearn(svc, ccTarget, ccCapture, false).row).toBe(1);
  expect(forgetLearn(svc, ccTarget)?.count).toBe(1);
  expect(doc.ccRows(2)).toHaveLength(8);
  expect(doc.ccRows(2)[1]).toMatchObject({ channel: 0, controller: 2, fourteen_bit: false, smoothing_ms: 5, min: 0, max: 1 });
  expect(commitLearn(svc, ccTarget, { ...ccCapture, controller: 72 }, false)).toMatchObject({ module: 2, row: 1, created: false });
});

test('A95 never takes a wired default or a non-default unwired row', () => {
  const doc = learnDoc({ rows: [{ controller: 1 }, { controller: 42 }] }, [
    { kind: 'modulation', from: { module: 2, port: 'cc1' }, to: { module: 4, port: 'gain' }, amount: 1 },
  ]);
  // Save/reload a complete slot to prove length is not occupancy.
  const patch = doc.toJSON();
  const node = patch.modules.find(m => m.id === 2)!;
  Object.assign(node, splitCcMappingSave(node, ccMappingSource(node)).authored);
  const reloaded = PatchDoc.from(patch);
  const learned = commitLearn(learnServices(reloaded), ccTarget, ccCapture, false);
  expect(learned).toMatchObject({ module: 2, row: 2, created: false });
  expect(reloaded.ccRows(2)[0]).toMatchObject({ controller: 1 });
  expect(reloaded.ccRows(2)[1]).toMatchObject({ controller: 42 });
  expect(reloaded.cablesFrom(2, 'cc1')).toHaveLength(1);
});
