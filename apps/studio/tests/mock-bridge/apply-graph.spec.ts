// SPDX-License-Identifier: GPL-3.0-only
import { test, expect, type Page } from '@playwright/test';
import { boot, settle, state } from '../helpers';
import { mockBridge } from './bridge';

type Wire = { type: string; patch?: any };
const patch = (modules: any[]) => ({
  format: 'wirescape.native.patch' as const, version: 2 as const, modules,
  connections: [], ui: { positions: Object.fromEntries(modules.map((m, i) => [m.id, [70 + i * 600, 50]])),
    view: { x: 0, y: 0, zoom: 1 }, labels: {} },
});
const wires = (page: Page) => page.evaluate(() =>
  ((window as any).__mockBridge.sent as Wire[]).filter(m => m.type === 'loadGraph' || m.type === 'applyGraph'));
async function setup(page: Page, capability: boolean, modules: any[]) {
  await mockBridge(page, { applyGraph: capability });
  await boot(page);
  await page.evaluate(p => window.__wirescapeTest.load(p, 'E1b'), patch(modules));
  await expect.poll(async () => (await page.evaluate(() => (window as any).__mockBridge.getGraph())).modules.length)
    .toBe(modules.length);
  await page.evaluate(() => { (window as any).__mockBridge.sent.length = 0; });
  await settle(page);
}
async function expectGraphCommands(page: Page, expected: string[]) {
  await expect.poll(async () => (await wires(page)).map(m => m.type)).toEqual(expected);
}

for (const capability of [true, false]) {
  const wire = capability ? 'applyGraph' : 'loadGraph';
  test.describe('E1b real bridge ' + (capability ? 'applyGraph capability' : 'legacy fallback'), () => {
    test('config edit, undo, redo and explicit snapshot restore all use the negotiated command', async ({ page }) => {
      await setup(page, capability, [{ id: 1, module: 'osc.in' }]);
      await page.evaluate(async () => {
        await window.__wirescapeTest.commitOscConfig(1,
          { port: 9005, lan: false, rows: [] }, 'osc.in');
      });
      await expectGraphCommands(page, [wire]);
      await page.evaluate(() => window.__wirescapeTest.undo());
      await expectGraphCommands(page, [wire, wire]);
      await page.evaluate(() => window.__wirescapeTest.redo());
      await expectGraphCommands(page, [wire, wire, wire]);
      await page.evaluate(() => window.__wirescapeTest.restoreSnapshot({
        format: 'wirescape.native.patch', version: 2,
        modules: [{ id: 1, module: 'osc.in', config: { port: 9010, rows: [] } }],
        connections: [],
      }));
      await expectGraphCommands(page, [wire, wire, wire, wire]);
      const graph = await page.evaluate(() => (window as any).__mockBridge.getGraph());
      expect(graph.modules[0].config.port).toBe(9010);
    });

    test('OSC In row edit and MIDI endpoint config edit use the negotiated command', async ({ page }) => {
      await setup(page, capability, [{ id: 1, module: 'osc.in' }, { id: 2, module: 'midi.in' }]);
      await page.getByTestId('osc-edit-1').click();
      await page.getByTestId('osc-row1-pattern').fill('/e1b/row');
      await page.getByTestId('osc-editor-save').click();
      await expectGraphCommands(page, [wire]);
      await page.evaluate(() => window.__wirescapeTest.setMidiEndpoint(2, 'M8 MIDI 1', 'M8:M8 MIDI 1'));
      await expectGraphCommands(page, [wire, wire]);
    });

    test('CC Learn commits one complete graph using the negotiated command', async ({ page }) => {
      await setup(page, capability, [{ id: 2, module: 'essentials.vcf' }]);
      await page.getByTestId('knob-2-cutoff').click({ button: 'right' });
      await page.getByTestId('context-midi').click();
      await expect(page.getByTestId('learn-bar')).toBeVisible();
      await expect(async () => {
        await page.evaluate(() => (window as any).__mockBridge.captureCc(
          'M8 MIDI 1|M8:M8 MIDI 1', 3, 74, 64));
        await expect(page.getByTestId('learn-message')).toContainText('CC 74', { timeout: 600 });
      }).toPass({ timeout: 10_000 });
      await page.getByTestId('learn-confirm').click();
      await expectGraphCommands(page, [wire]);
      const graph = await page.evaluate(() => (window as any).__mockBridge.getGraph());
      expect(graph.modules.some((m: any) => m.module === 'midi.cc_to_cv')).toBe(true);
      expect(graph.connections.some((c: any) => c.kind === 'modulation' && c.to.port === 'cutoff')).toBe(true);
    });
  });
}

test('capability-on graph refusal leaves running document, graph and generation untouched', async ({ page }) => {
  await setup(page, true, [{ id: 1, module: 'osc.in' }]);
  const before = await page.evaluate(() => ({
    graph: (window as any).__mockBridge.getGraph(),
    gen: (window as any).__mockBridge.generation(),
  }));
  await page.evaluate(() => (window as any).__mockBridge.refuseNext('applyGraph', 'refused'));
  await page.evaluate(() => window.__wirescapeTest.commitOscConfig(1,
    { port: 9012, lan: false, rows: [] }, 'osc.in'));
  await expectGraphCommands(page, ['applyGraph']);
  await expect.poll(() => page.evaluate(() => (window as any).__mockBridge.getGraph())).toEqual(before.graph);
  await expect.poll(async () => (await state(page)).modules[0].config).toBeUndefined();
  expect(await page.evaluate(() => (window as any).__mockBridge.generation())).toBe(before.gen);
});

test('successful applyGraph with unapplied values reconciles engine and visible authored document', async ({ page }) => {
  await setup(page, true, [{ id: 2, module: 'essentials.vco', parameters: { frequency: 220 } }]);
  await page.evaluate(() => (window as any).__mockBridge.setUnapplied([{ moduleId: 2, paramId: 'frequency' }]));
  await page.evaluate(() => window.__wirescapeTest.restoreSnapshot({
    format: 'wirescape.native.patch', version: 2,
    modules: [{ id: 2, module: 'essentials.vco', parameters: { frequency: 440 } }],
    connections: [],
  }));
  await expectGraphCommands(page, ['applyGraph']);
  await expect.poll(async () => (await state(page)).modules[0].parameters.frequency).toBe(220);
  expect(await page.evaluate(() => (window as any).__mockBridge.getGraph().modules[0].parameters.frequency)).toBe(220);
});


test('refused undo restores history position and authored document without a compensating reload', async ({ page }) => {
  await setup(page, true, [{ id: 1, module: 'osc.in' }]);
  await page.evaluate(() => window.__wirescapeTest.commitOscConfig(1,
    { port: 9021, lan: false, rows: [] }, 'osc.in'));
  await expectGraphCommands(page, ['applyGraph']);
  const depth = await page.evaluate(() => window.__wirescapeTest.historyDepth());
  const before = await state(page);
  const gen = await page.evaluate(() => (window as any).__mockBridge.generation());
  await page.evaluate(() => (window as any).__mockBridge.refuseNext('applyGraph', 'refused'));
  await page.evaluate(() => window.__wirescapeTest.undo());
  await expectGraphCommands(page, ['applyGraph', 'applyGraph']);
  await expect.poll(async () => (await state(page)).modules[0].config.port).toBe(9021);
  expect(await page.evaluate(() => window.__wirescapeTest.historyDepth())).toEqual(depth);
  expect(await page.evaluate(() => (window as any).__mockBridge.generation())).toBe(gen);
  expect(await page.evaluate(() => (window as any).__mockBridge.getGraph().modules[0].config.port)).toBe(9021);
  expect((await state(page)).modules[0]).toEqual(before.modules[0]);
});

test('opening a different patch remains loadGraph even when applyGraph is supported', async ({ page }) => {
  await setup(page, true, [{ id: 1, module: 'osc.in' }]);
  await page.evaluate(p => window.__wirescapeTest.load(p, 'Opened patch'), patch([{ id: 8, module: 'essentials.vco' }]));
  await expectGraphCommands(page, ['loadGraph']);
});
