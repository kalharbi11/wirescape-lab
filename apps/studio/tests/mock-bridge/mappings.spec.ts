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
