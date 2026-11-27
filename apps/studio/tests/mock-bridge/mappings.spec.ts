// SPDX-License-Identifier: GPL-3.0-only
import { test, expect, type Page } from '@playwright/test';
import { boot, settle } from '../helpers';
import { mockBridge } from './bridge';
import type { Connection, PatchV2 } from '../../src/patch/types';

const connection: Connection = { kind: 'modulation', from: { module: 1, port: 'cc1' },
  to: { module: 2, port: 'depth' }, amount: .4 };
const fixture: PatchV2 = {
  format: 'wirescape.native.patch', version: 2, modules: [
    { id: 1, module: 'midi.cc_to_cv' },
    { id: 2, module: 'essentials.lfo', parameters: { depth: .25 } },
    { id: 3, module: 'essentials.lfo', parameters: { depth: .5 } },
  ], connections: [connection],
  ui: { positions: { '1': [20, 20], '2': [300, 20], '3': [600, 20] },
    view: { x: 0, y: 0, zoom: 1 }, labels: {} },
};
async function setup(page: Page, capability = true) {
  await mockBridge(page, { applyGraph: capability });
  await boot(page);
  await page.evaluate(p => window.__wirescapeTest.load(p, 'MM1'), fixture);
  await expect.poll(() => page.evaluate(() => (window as any).__mockBridge.getGraph().modules.length)).toBe(3);
  await settle(page);
  await page.evaluate(() => { window.__wirescapeTest.flushHistory(); (window as any).__mockBridge.sent.length = 0; });
}
const commands = (page: Page) => page.evaluate(() => (window as any).__mockBridge.sent
  .filter((m: any) => ['setParam', 'setModAmount', 'loadGraph', 'applyGraph'].includes(m.type))
  .map((m: any) => m.type));
const snapshot = (page: Page) => page.evaluate(() => {
  const a = window.__wirescapeTest, b = (window as any).__mockBridge;
  return { patch: a.state(), history: a.historyDepth(), graph: b.getGraph(), gen: b.generation() };
});

test('MM1 real bridge: live min waits for base ACK, then amount, no graph rebuild', async ({ page }) => {
  await setup(page);
  const before = await snapshot(page);
  await page.evaluate(c => {
    const a = window.__wirescapeTest, b = (window as any).__mockBridge;
    b.holdNext('setParam');
    (window as any).__mmPending = a.editMappingRange(c, 'min', .1);
  }, connection);
  await expect.poll(() => commands(page)).toEqual(['setParam']);
  expect(await snapshot(page)).toEqual(before);
  await page.evaluate(() => (window as any).__mockBridge.acceptHeld());
  await page.evaluate(() => (window as any).__mmPending);
  expect(await commands(page)).toEqual(['setParam', 'setModAmount']);
  const after = await snapshot(page);
  expect(after.patch.modules[1].parameters.depth).toBe(.1);
  expect(after.patch.connections[0].amount).toBeCloseTo(.55);
  expect(after.graph.modules[1].parameters.depth).toBe(.1);
  expect(after.graph.connections[0].amount).toBeCloseTo(.55);
  expect(after.gen).toBe(before.gen);
  expect(after.history.past).toBe(before.history.past + 1);
  await page.evaluate(c => window.__wirescapeTest.editMappingRange(c, 'max', .9), connection);
  expect(await commands(page)).toEqual(['setParam', 'setModAmount', 'setModAmount']);
});

test('MM1 real bridge: refused base sends no amount and keeps authored state/history', async ({ page }) => {
  await setup(page);
  const before = await snapshot(page);
  await page.evaluate(() => (window as any).__mockBridge.refuseNext('setParam', 'refused'));
  const error = await page.evaluate(async c => {
    try { await window.__wirescapeTest.editMappingRange(c, 'min', .1); return ''; }
    catch (e) { return (e as Error).message; }
  }, connection);
  expect(error).toContain('Scripted refused');
  expect(await commands(page)).toEqual(['setParam']);
  expect(await snapshot(page)).toEqual(before);
});

test('MM1 real bridge: refused mapping graph preserves graph, document and undo cursor', async ({ page }) => {
  await setup(page);
  const before = await snapshot(page);
  await page.evaluate(() => (window as any).__mockBridge.refuseNext('applyGraph', 'refused'));
  const error = await page.evaluate(async () => {
    try { await window.__wirescapeTest.addMapping({ module: 1, port: 'cc2' }, { module: 3, port: 'depth' }); return ''; }
    catch (e) { return (e as Error).message; }
  });
  expect(error).toContain('Scripted refused');
  expect(await commands(page)).toEqual(['applyGraph']);
  expect(await snapshot(page)).toEqual(before);
});

test('MM1 real bridge: no applyGraph capability refuses new mapping without loadGraph fallback', async ({ page }) => {
  await setup(page, false);
  const before = await snapshot(page);
  const error = await page.evaluate(async () => {
    try { await window.__wirescapeTest.addMapping({ module: 1, port: 'cc2' }, { module: 3, port: 'depth' }); return ''; }
    catch (e) { return (e as Error).message; }
  });
  expect(error).toContain('applyGraph');
  expect(await commands(page)).toEqual([]);
  expect(await snapshot(page)).toEqual(before);
});

test('MM1 A101 real bridge: partial ACK compensates the whole prior document', async ({ page }) => {
  await setup(page);
  const before = await snapshot(page);
  const error = await page.evaluate(async () => {
    const a = window.__wirescapeTest, b = (window as any).__mockBridge;
    b.setUnapplied([{ moduleId: 3, paramId: 'depth' }]);
    try { await a.addMapping({ module: 1, port: 'cc2' }, { module: 3, port: 'depth' }); return ''; }
    catch (e) { return (e as Error).message; }
  });
  expect(error).not.toBe('');
  expect(await commands(page)).toEqual(['applyGraph', 'applyGraph']);
  const after = await snapshot(page);
  expect(after.patch).toEqual(before.patch);
  expect(JSON.stringify(after.patch)).toBe(JSON.stringify(before.patch));
  expect(after.history).toEqual(before.history);
  expect(after.graph).toEqual(before.graph);
});

test('MM1 A101 real bridge: refused compensation restores last acknowledged graph', async ({ page }) => {
  await setup(page);
  await page.evaluate(() => {
    const a = window.__wirescapeTest, b = (window as any).__mockBridge;
    b.setUnapplied([{ moduleId: 3, paramId: 'depth' }]);
    b.holdNext('applyGraph');
    (window as any).__mmPending = a.addMapping({ module: 1, port: 'cc2' }, { module: 3, port: 'depth' })
      .then(() => '', (e: Error) => e.message);
  });
  await expect.poll(() => commands(page)).toEqual(['applyGraph']);
  await page.evaluate(() => {
    const b = (window as any).__mockBridge;
    b.acceptHeld();
    b.refuseNext('applyGraph', 'refused');
  });
  expect(await page.evaluate(() => (window as any).__mmPending)).not.toBe('');
  expect(await commands(page)).toEqual(['applyGraph', 'applyGraph']);
  const after = await snapshot(page);
  expect(after.patch.connections).toEqual(after.graph.connections);
  expect(after.patch.modules).toEqual(after.graph.modules);
  expect(after.patch.connections).toContainEqual({
    kind: 'modulation', from: { module: 1, port: 'cc2' },
    to: { module: 3, port: 'depth' }, amount: 1,
  });
  expect(after.patch.modules[2].parameters.depth).toBe(.5);
});

test('MM1 Forget: known CC source holds the base in one applyGraph and undo step', async ({ page }) => {
  await setup(page);
  const before = await snapshot(page);
  await page.evaluate(() => (window as any).__mockBridge.telemetry({ outputs: { '1:cc1': .5 } }));
  await expect.poll(() => page.evaluate(() => window.__wirescapeTest.ticker.last?.outputs?.['1:cc1'])).toBe(.5);
  await page.evaluate(() => (window.__wirescapeTest.canvas as any).s.midiLearn.forget(2, 'depth'));
  await expect.poll(() => page.evaluate(() => window.__wirescapeTest.canEdit())).toBe(true);
  expect(await commands(page)).toEqual(['applyGraph']);
  const after = await snapshot(page);
  expect(after.patch.connections).toHaveLength(0);
  expect(after.patch.modules[1].parameters.depth).toBeCloseTo(.45);
  expect(after.history.past).toBe(before.history.past + 1);
  expect(after.graph.modules[1].parameters.depth).toBeCloseTo(.45);
});

test('MM1 Forget: partial ACK uses A101 whole-graph compensation', async ({ page }) => {
  await setup(page);
  const before = await snapshot(page);
  await page.evaluate(() => (window as any).__mockBridge.telemetry({ outputs: { '1:cc1': .5 } }));
  await expect.poll(() => page.evaluate(() => window.__wirescapeTest.ticker.last?.outputs?.['1:cc1'])).toBe(.5);
  await page.evaluate(() => {
    (window as any).__mockBridge.setUnapplied([{ moduleId: 2, paramId: 'depth' }]);
    (window.__wirescapeTest.canvas as any).s.midiLearn.forget(2, 'depth');
  });
  await expect.poll(() => page.evaluate(() => window.__wirescapeTest.canEdit())).toBe(true);
  expect(await commands(page)).toEqual(['applyGraph', 'applyGraph']);
  const after = await snapshot(page);
  expect(after.patch).toEqual(before.patch);
  expect(after.history).toEqual(before.history);
  expect(after.graph).toEqual(before.graph);
});

test('MM1 real bridge: refused amount compensates accepted base without rebuilding or authoring history', async ({ page }) => {
  await setup(page);
  const before = await snapshot(page);
  await page.evaluate(() => (window as any).__mockBridge.refuseNext('setModAmount', 'refused'));
  const error = await page.evaluate(async c => {
    try { await window.__wirescapeTest.editMappingRange(c, 'min', .1); return ''; }
    catch (e) { return (e as Error).message; }
  }, connection);
  expect(error).toContain('Scripted refused');
  expect(await commands(page)).toEqual(['setParam', 'setModAmount', 'setParam']);
  expect(await snapshot(page)).toEqual(before);
});

test('MM1 Groove: mapping applyGraph leaves an unrelated uncommitted pattern off the wire', async ({ page }) => {
  await setup(page);
  const config = { version: 1, bpm: 120, tracks: [{ steps: [{ kind: 'note', key: 60, velocity: .5 }] }] };
  const patch: PatchV2 = { ...fixture, modules: [...fixture.modules, { id: 4, module: 'sequencing.groove', config }] };
  await page.evaluate(p => window.__wirescapeTest.load(p, 'MM1 Groove'), patch);
  await expect.poll(() => page.evaluate(() => (window as any).__mockBridge.getGraph().modules.length)).toBe(4);
  await settle(page);
  const running = await page.evaluate(() => (window as any).__mockBridge.getGraph().modules.find((m: any) => m.id === 4).config);
  const draft = { ...config, bpm: 135 };
  await page.evaluate(d => {
    const a = window.__wirescapeTest;
    a.doc.setModuleConfig(4, d);
    a.flushHistory();
    (window as any).__mockBridge.sent.length = 0;
  }, draft);
  await page.evaluate(() => window.__wirescapeTest.addMapping({ module: 1, port: 'cc2' }, { module: 3, port: 'depth' }));
  expect(await commands(page)).toEqual(['applyGraph']);
  const after = await snapshot(page);
  expect(after.patch.modules.find(m => m.id === 4)?.config).toEqual(draft);
  expect(after.graph.modules.find((m: any) => m.id === 4).config).toEqual(running);
});
