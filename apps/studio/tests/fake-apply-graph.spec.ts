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
      replaced: e.lastApplyResult?.replaced,
      frequency: e.nodes.get(1).params.frequency };
    const changed = structuredClone(same);
    changed.modules[0].config.voicing = 2;
    await e.applyGraph(changed);
    const replaced = { phase: e.phases.get(1), frequency: e.nodes.get(1).params.frequency,
      ids: e.lastApplyResult?.replaced };
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
  expect(evidence.kept).toMatchObject({ gen: evidence.gen0 + 1, phase: 0.37, step: 5, frequency: 440, replaced: [] });
  expect(evidence.replaced.phase).toBeUndefined();
  expect(evidence.replaced.ids).toEqual([1]);
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
    return { phaseWasReset: e.phases.get(1) === undefined, cap: e.capabilities.includes('applyGraph') };
  });
  expect(result).toEqual({ cap: false, phaseWasReset: true });
});


test('FakeEngine reconciles prior document after incremental addModule and ignores config key order', async ({ page }) => {
  await boot(page);
  const result = await page.evaluate(async () => {
    const e = window.__wirescapeTest.engine as any;
    e.stop();
    await e.loadGraph({ format: 'wirescape.native.patch', version: 2,
      modules: [], connections: [] });
    e.addModule(9, 'essentials.vco', { frequency: 330 });
    e.phases.set(9, 0.625);
    const afterAdd = { format: 'wirescape.native.patch', version: 2,
      modules: [{ id: 9, module: 'essentials.vco', parameters: { frequency: 440 } }],
      connections: [] };
    await e.applyGraph(afterAdd);
    const firstReplaced = [...e.lastApplyResult.replaced];
    const continuedPhase = e.phases.get(9);
    const configured = { ...afterAdd, modules: [{ ...afterAdd.modules[0],
      config: { first: 1, second: 2 } }] };
    await e.applyGraph(configured); // real config replacement must reset this instance
    const changedConfigReplaced = [...e.lastApplyResult.replaced];
    e.phases.set(9, 0.25);
    const reordered = { ...configured, modules: [{ ...configured.modules[0],
      config: { second: 2, first: 1 }, parameters: { frequency: 550 } }] };
    await e.applyGraph(reordered);
    return { firstReplaced, continuedPhase, changedConfigReplaced,
      secondReplaced: e.lastApplyResult.replaced,
      phase: e.phases.get(9), value: e.nodes.get(9).params.frequency };
  });
  expect(result).toEqual({ firstReplaced: [], continuedPhase: 0.625,
    changedConfigReplaced: [9], secondReplaced: [], phase: 0.25, value: 550 });
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


test('FakeEngine replaces an existing note source and releases its notes, but retains unchanged source', async ({ page }) => {
  await boot(page);
  const observed = await page.evaluate(async () => {
    const e = window.__wirescapeTest.engine as any;
    e.stop();
    const initial: any = { format: 'wirescape.native.patch', version: 2,
      modules: [
        { id: 4, module: 'host.keyboard', config: { mode: 'a' } },
        { id: 5, module: 'essentials.vco', parameters: { frequency: 220 } },
      ], connections: [] };
    await e.loadGraph(initial);
    e.noteOn(60, 0.9);
    e.phases.set(5, 0.42);
    await e.applyGraph({ ...initial, modules: [
      { ...initial.modules[0], state: { mustBeIgnored: true } },
      { ...initial.modules[1], parameters: { frequency: 440 } },
    ] });
    const continuing = { notes: e.voices.length, held: e.lastNote,
      replaced: [...e.lastApplyResult.replaced], phase: e.phases.get(5) };
    const changed = structuredClone(initial);
    changed.modules[0].config.mode = 'b';
    await e.applyGraph(changed);
    const replacement = { notes: e.voices.length, held: e.lastNote,
      replaced: [...e.lastApplyResult.replaced], phase: e.phases.get(5) };
    e.noteOn(62, 0.7);
    const removed = structuredClone(changed);
    removed.modules = removed.modules.filter((m: any) => m.id !== 4);
    await e.applyGraph(removed);
    const removal = { notes: e.voices.length, held: e.lastNote };
    return { continuing, replacement, removal };
  });
  expect(observed.continuing).toEqual({ notes: 1, held: 60, replaced: [], phase: 0.42 });
  expect(observed.replacement).toEqual({ notes: 0, held: null, replaced: [4], phase: 0.42 });
  expect(observed.removal).toEqual({ notes: 0, held: null });
});

test('FakeEngine OSC Out is always replaced, even for identical config and unrelated edits', async ({ page }) => {
  await boot(page);
  const result = await page.evaluate(async () => {
    const e = window.__wirescapeTest.engine as any;
    e.stop();
    const original: any = { format: 'wirescape.native.patch', version: 2,
      modules: [
        { id: 5, module: 'osc.out', config: { port: 9001, rows: [] } },
        { id: 6, module: 'essentials.vco', parameters: { frequency: 220 } },
      ], connections: [] };
    await e.loadGraph(original);
    e.setOscOutStatus(5, 12, 3);
    e.phases.set(6, 0.61);
    await e.applyGraph(structuredClone(original));
    const repeated = { replaced: [...e.lastApplyResult.replaced],
      counters: { ...e.osc.out[0] }, witnessPhase: e.phases.get(6) };
    e.setOscOutStatus(5, 7, 1);
    const added = { ...original, modules: [...original.modules, { id: 7, module: 'essentials.noise' }] };
    await e.applyGraph(added);
    const structural = { replaced: [...e.lastApplyResult.replaced],
      counters: e.osc.out[0], witnessPhase: e.phases.get(6) };
    return { repeated, structural };
  });
  expect(result.repeated.replaced).toEqual([5]);
  expect(result.structural.replaced).toEqual([5]);
  expect(result.repeated.counters).toMatchObject({ module: '5', sent: 0, dropped: 0 });
  expect(result.structural.counters).toMatchObject({ module: '5', sent: 0, dropped: 0 });
  expect(result.repeated.witnessPhase).toBe(0.61);
  expect(result.structural.witnessPhase).toBe(0.61);
});

test('FakeEngine MIDI In replacement releases notes but unchanged config preserves them', async ({ page }) => {
  await boot(page);
  const result = await page.evaluate(async () => {
    const e = window.__wirescapeTest.engine as any;
    e.stop();
    const original: any = { format: 'wirescape.native.patch', version: 2,
      modules: [{ id: 8, module: 'midi.in', config: { endpoint: 'all_enabled' } }],
      connections: [] };
    await e.loadGraph(original);
    e.noteOn(63, 0.8);
    await e.applyGraph(structuredClone(original));
    const retained = e.voices.length;
    const newConfig = structuredClone(original);
    newConfig.modules[0].config.endpoint = 'Another input';
    await e.applyGraph(newConfig);
    return { retained, released: e.voices.length, replaced: e.lastApplyResult.replaced };
  });
  expect(result).toEqual({ retained: 1, released: 0, replaced: [8] });
});
