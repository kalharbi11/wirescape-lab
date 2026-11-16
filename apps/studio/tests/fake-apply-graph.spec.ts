// SPDX-License-Identifier: GPL-3.0-only
import { test, expect } from '@playwright/test';
import { boot, state } from './helpers';

const patch = (modules: any[], connections: any[] = []) => ({
  format: 'wirescape.native.patch' as const, version: 2 as const,
  modules, connections, ui: { positions: {}, view: { x: 0, y: 0, zoom: 1 } },
});

test('FakeEngine E1b rules 1-5: preserved phase, ignored state, params, replaced config and restored ID', async ({ page }) => {
  await boot(page);
  const evidence = await page.evaluate(async () => {
    const e = window.__wirescapeTest.engine as any;
    e.stop(); // eliminate timer-driven phase changes from these known-answer assertions
    const initial: any = { format: 'wirescape.native.patch', version: 2,
      modules: [
        { id: 1, module: 'essentials.vco', config: { voicing: 1 }, parameters: { frequency: 220 } },
        { id: 2, module: 'essentials.vcf', config: { channel: 1 } },
      ], connections: [] };
    await e.loadGraph(initial);
    e.phases.set(1, 0.37);
    e.seqStep.set(1, 5);
    const gen0 = e.graphGeneration;
    const same = structuredClone(initial);
    same.modules[0].parameters.frequency = 440;
    same.modules[0].state = { resetMe: true };
    await e.applyGraph(same);
    const kept = { gen: e.graphGeneration, phase: e.phases.get(1), step: e.seqStep.get(1),
      frequency: e.nodes.get(1).params.frequency };
    const changed = structuredClone(same);
    changed.modules[0].config.voicing = 2;
    await e.applyGraph(changed);
    const replaced = { phase: e.phases.get(1), frequency: e.nodes.get(1).params.frequency };
    const removed = structuredClone(changed);
    removed.modules = removed.modules.filter((m: any) => m.id !== 1);
    await e.applyGraph(removed);
    const absent = !e.nodes.has(1);
    await e.applyGraph(changed);
    const restored = e.nodes.has(1);
    return { gen0, kept, replaced, absent, restored, genEnd: e.graphGeneration,
      capability: e.capabilities.includes('applyGraph') };
  });
  expect(evidence.capability).toBe(true);
  expect(evidence.kept).toMatchObject({ gen: evidence.gen0 + 1, phase: 0.37, step: 5, frequency: 440 });
  expect(evidence.replaced.phase).toBeUndefined();
  expect(evidence.replaced.frequency).toBe(440);
  expect(evidence.absent).toBe(true);
  expect(evidence.restored).toBe(true);
  expect(evidence.genEnd).toBe(evidence.gen0 + 4);
});

test('FakeEngine a refused applyGraph leaves graph, document and gen unchanged', async ({ page }) => {
  await boot(page);
  const result = await page.evaluate(async () => {
    const e = window.__wirescapeTest.engine as any;
    e.stop(); // eliminate timer-driven phase changes from these known-answer assertions
    await e.loadGraph({ format: 'wirescape.native.patch', version: 2,
      modules: [{ id: 4, module: 'essentials.vco', parameters: { frequency: 222 } }],
      connections: [] });
    const before = JSON.stringify(e.document), generation = e.graphGeneration;
    e.debug.refuseEdits = true;
    let error = '';
    try {
      await e.applyGraph({ format: 'wirescape.native.patch', version: 2,
        modules: [{ id: 4, module: 'essentials.vco', parameters: { frequency: 555 } }],
        connections: [] });
    } catch (exc) { error = (exc as Error).message; }
    e.debug.refuseEdits = false;
    return { before, after: JSON.stringify(e.document), generation,
      afterGen: e.graphGeneration, actual: e.nodes.get(4).params.frequency, error };
  });
  expect(result.error).toContain('Engine refused');
  expect(result.after).toBe(result.before);
  expect(result.afterGen).toBe(result.generation);
  expect(result.actual).toBe(222);
});

test('FakeEngine event queue exhaustion keeps old parameter and mirrors it in Studio', async ({ page }) => {
  await boot(page);
  await page.evaluate(p => window.__wirescapeTest.load(p), patch([
    { id: 1, module: 'essentials.vco', parameters: { frequency: 220 } },
  ]));
  const values = await page.evaluate(async () => {
    const api = window.__wirescapeTest, e = api.engine as any;
    e.stop();
    e.setNextUnapplied([{ moduleId: 1, paramId: 'frequency' }]);
    api.doc.setParam(1, 'frequency', 880);
    await e.applyGraph(api.state());
    return { actual: e.nodes.get(1).params.frequency,
      committed: e.document.modules[0].parameters.frequency, displayed: api.state().modules[0].parameters.frequency };
  });
  expect(values).toEqual({ actual: 220, committed: 220, displayed: 220 });
});

test('FakeEngine web-preview fallback preserves legacy full reset when capability is absent', async ({ page }) => {
  await boot(page);
  const result = await page.evaluate(async () => {
    const e = window.__wirescapeTest.engine as any;
    e.stop(); // eliminate timer-driven phase changes from these known-answer assertions
    const doc = { format: 'wirescape.native.patch', version: 2,
      modules: [{ id: 1, module: 'essentials.vco' }], connections: [] };
    await e.loadGraph(doc);
    e.phases.set(1, 0.91);
    e.capabilities.splice(e.capabilities.indexOf('applyGraph'), 1);
    await e.applyGraph(doc);
    return { phase: e.phases.get(1), cap: e.capabilities.includes('applyGraph') };
  });
  expect(result).toEqual({ cap: false });
});

test('opening a patch always resets FakeEngine while live replans retain continuing state', async ({ page }) => {
  await boot(page);
  const r = await page.evaluate(async () => {
    const api = window.__wirescapeTest, e = api.engine as any;
    const doc = { format: 'wirescape.native.patch', version: 2,
      modules: [{ id: 3, module: 'essentials.vco', parameters: { frequency: 330 } }], connections: [] };
    await e.loadGraph(doc);
    e.phases.set(3, 0.18);
    await e.applyGraph({ ...doc, modules: [{ ...doc.modules[0], parameters: { frequency: 440 } }] });
    const live = e.phases.get(3);
    await api.load(doc, 'Opened');
    return { live, opened: e.phases.get(3) };
  });
  expect(r.live).toBe(0.18);
  expect(r.opened).toBeUndefined();
  expect((await state(page)).modules[0].parameters.frequency).toBe(330);
});
