// SPDX-License-Identifier: GPL-3.0-only
import { test, expect } from '@playwright/test';
import { boot } from './helpers';
import type { PatchV2, Connection } from '../src/patch/types';
import type { ModuleRegistry } from '../src/modules/registry';
import type { ModuleDescriptor } from '../src/modules/types';

const cable = (source: number, port: string, target = 3, param = 'depth', amount = .4): Connection =>
  ({ kind: 'modulation', from: { module: source, port }, to: { module: target, port: param }, amount });
const fixture = (): PatchV2 => ({
  format: 'wirescape.native.patch', version: 2,
  modules: [
    { id: 1, module: 'essentials.macro', parameters: { knob1: .2 } },
    { id: 2, module: 'midi.cc_to_cv' },
    { id: 3, module: 'essentials.lfo', parameters: { depth: .25, offset: .2 } },
    { id: 4, module: 'essentials.lfo' },
    { id: 5, module: 'osc.in' },
  ],
  connections: [cable(1, 'out1'), cable(4, 'control', 3, 'depth', .1), cable(2, 'cc1', 3, 'offset', -.4)],
});
const target: ModuleDescriptor = {
  id: 'essentials.lfo', name: 'LFO', category: 'Test', ports: [],
  parameters: [
    { id: 'depth', name: 'Depth', unit: '', minimum: 0, maximum: 1, default: 1, taper: 'linear', step: 0, decimals: 3, modulatable: true },
    { id: 'offset', name: 'Offset', unit: '', minimum: -1, maximum: 1, default: 0, taper: 'linear', step: 0, decimals: 3, modulatable: true },
  ],
};

test('MM1 Node: derives macro, CC and OSC ownership, not ordinary modulation, without mutating authored bytes', async () => {
  const { deriveMappings } = await import('../src/app/mappings');
  const p = fixture();
  p.connections.push(cable(5, 'row1', 4, 'depth', .5));
  const before = JSON.stringify(p);
  const rows = deriveMappings(p, { get: (id: string) => id === target.id ? target : undefined } as ModuleRegistry);
  expect(rows.map((m: any) => m.connection.from.module)).toEqual([1, 2, 5]);
  expect(rows[0]).toMatchObject({ min: .25, max: .65, inverted: false });
  expect(rows[1].min).toBeCloseTo(.6);
  expect(rows[1].max).toBeCloseTo(.2);
  expect(rows[1].inverted).toBe(true);
  expect(JSON.stringify(p)).toBe(before);
});

test('MM1 Studio: descriptor, min then amount, max amount only, one history step', async ({ page }) => {
  await boot(page);
  const result = await page.evaluate(async p => {
    const a = window.__wirescapeTest;
    const d = a.registry.get('essentials.macro');
    if (!d) return { missingMacro: true };
    await a.load(p);
    a.flushHistory();
    const e = a.engine;
    const calls: any[] = [];
    for (const method of ['setParam', 'setModAmount', 'loadGraph', 'applyGraph']) {
      const original = e[method].bind(e);
      e[method] = (...args: any[]) => { calls.push([method, ...args]); return original(...args); };
    }
    const before = a.historyDepth().past;
    const c = p.connections[0];
    await a.editMappingRange(c, 'min', .1);
    const first = calls.splice(0), afterMin = a.state(), depthMin = a.historyDepth().past;
    await a.editMappingRange(c, 'max', .9);
    return { descriptor: d, first, second: calls, afterMin, final: a.state(), before, depthMin, depthMax: a.historyDepth().past };
  }, fixture());
  expect(result).not.toHaveProperty('missingMacro');
  const r = result as any;
  expect(r.descriptor.parameters.map((p: any) => [p.id,p.minimum,p.maximum,p.default,p.modulatable]))
    .toEqual(Array.from({ length: 8 }, (_, i) => ['knob' + (i+1), 0, 1, 0, true]));
  expect(r.descriptor.ports.map((p: any) => [p.id,p.direction,p.hint]))
    .toEqual(Array.from({ length: 8 }, (_, i) => ['out' + (i+1), 'output', 'cv_uni']));
  expect(r.first.map((c: any[]) => c[0])).toEqual(['setParam', 'setModAmount']);
  expect(r.first[0]).toEqual(['setParam', 3, 'depth', .1]);
  expect(r.first[1][2]).toBeCloseTo(.55);
  expect(r.second.map((c: any[]) => c[0])).toEqual(['setModAmount']);
  expect(r.second[0][2]).toBeCloseTo(.8);
  expect(r.final.modules.find((m: any) => m.id === 3).parameters.depth).toBe(.1);
  expect(r.final.connections[0].amount).toBeCloseTo(.8);
  expect(r.depthMin).toBe(r.before + 1);
  expect(r.depthMax).toBe(r.before + 2);
});

test('MM1 Studio: second owner refused; new macro mapping full range; removal and refused graph atomic', async ({ page }) => {
  await boot(page);
  const result = await page.evaluate(async p => {
    const a = window.__wirescapeTest;
    await a.load(p);
    a.flushHistory();
    const before = a.state();
    let duplicate = '';
    try { await a.addMapping({module: 5, port: 'row1'}, {module: 3, port: 'depth'}); }
    catch (e) { duplicate = String((e as Error).message); }
    const afterDuplicate = a.state();
    const e = a.engine, original = e.applyGraph.bind(e);
    let applies = 0;
    e.applyGraph = (...args: any[]) => { applies++; return original(...args); };
    const depth0 = a.historyDepth().past;
    await a.addMapping({module: 1, port: 'out2'}, {module: 4, port: 'depth'});
    const added = a.state(), depth1 = a.historyDepth().past;
    const mapping = added.connections.find((c: any) => c.from.module === 1 && c.from.port === 'out2');
    await a.removeMapping(mapping, .6);
    const removed = a.state(), depth2 = a.historyDepth().past;
    e.debug.refuseEdits = true;
    let refused = false;
    try { await a.addMapping({module: 1, port: 'out3'}, {module: 4, port: 'depth'}); }
    catch { refused = true; }
    return {before, afterDuplicate, duplicate, added, removed, refused, final: a.state(), depth0, depth1, depth2, finalDepth: a.historyDepth().past, applies};
  }, fixture());
  expect(result.duplicate).toMatch(/^Mapped to .+\. Remove that mapping, or map the source to a macro\.$/);
  expect(result.afterDuplicate).toEqual(result.before);
  expect(result.added.modules.find((m: any) => m.id === 1).parameters.knob2).toBe(1);
  expect(result.added.modules.find((m: any) => m.id === 4).parameters.depth).toBe(0);
  expect(result.added.connections.find((c: any) => c.from.port === 'out2').amount).toBe(1);
  expect(result.removed.modules.find((m: any) => m.id === 4).parameters.depth).toBeCloseTo(.6);
  expect(result.removed.connections).toEqual(result.before.connections);
  expect(result.depth1).toBe(result.depth0 + 1);
  expect(result.depth2).toBe(result.depth1 + 1);
  expect(result.refused).toBe(true);
  expect(result.final).toEqual(result.removed);
  expect(result.finalDepth).toBe(result.depth2);
  expect(result.applies).toBe(3);
});


test('MM1 canvas: one owner enforced before mutation, ordinary modulation still adds', async ({ page }) => {
  await boot(page);
  await page.evaluate(async p => {
    const a = window.__wirescapeTest;
    await a.load(p);
    a.flushHistory();
  }, fixture());
  const snapshot = () => page.evaluate(() => {
    const a = window.__wirescapeTest;
    a.flushHistory();
    return { patch: a.state(), history: a.historyDepth() };
  });
  const before = await snapshot();
  await page.evaluate(async c => {
    await (window.__wirescapeTest.canvas as any).commitConnection(c, false);
  }, cable(1, 'out2'));
  expect(await snapshot()).toEqual(before);
  await expect(page.getByText('Mapped to Macros 1 · Knob 1. Remove that mapping, or map the source to a macro.', { exact: true })).toBeVisible();
  await page.evaluate(async c => {
    await (window.__wirescapeTest.canvas as any).commitConnection(c, false);
  }, cable(4, 'control', 3, 'offset', .15));
  await expect.poll(async () => (await snapshot()).patch.connections).toContainEqual(cable(4, 'control', 3, 'offset', .15));
  expect((await snapshot()).patch.connections).toContainEqual(cable(2, 'cc1', 3, 'offset', -.4));
});

test('MM1 canvas: new mapping uses full range and first Macro knob initialization', async ({ page }) => {
  await boot(page);
  await page.evaluate(async p => {
    const a = window.__wirescapeTest;
    await a.load(p);
    a.flushHistory();
  }, fixture());
  const depth = await page.evaluate(() => window.__wirescapeTest.historyDepth().past);
  await page.evaluate(async c => {
    await (window.__wirescapeTest.canvas as any).commitConnection(c, false);
  }, cable(1, 'out2', 4, 'depth', .25));
  await expect.poll(() => page.evaluate(() => {
    const a = window.__wirescapeTest;
    a.flushHistory();
    const p = a.state();
    return { knob: p.modules.find((m: any) => m.id === 1).parameters.knob2,
      base: p.modules.find((m: any) => m.id === 4).parameters?.depth,
      amount: p.connections.find((c: any) => c.from.module === 1 && c.from.port === 'out2')?.amount,
      depth: a.historyDepth().past };
  })).toEqual({ knob: 1, base: 0, amount: 1, depth: depth + 1 });
});


test('MM1 canvas: selected mapping removal holds source contribution and is one undo step', async ({ page }) => {
  await boot(page);
  const p = fixture();
  p.connections = [p.connections[0]];
  await page.evaluate(async patch => {
    const a = window.__wirescapeTest;
    await a.load(patch);
    a.flushHistory();
    a.select({ kind: 'cable', c: patch.connections[0] });
  }, p);
  const before = await page.evaluate(() => window.__wirescapeTest.historyDepth().past);
  await page.evaluate(() => window.__wirescapeTest.deleteSelection());
  await expect.poll(() => page.evaluate(() => {
    const a = window.__wirescapeTest;
    a.flushHistory();
    const p = a.state();
    return { cables: p.connections.length, depth: p.modules.find((m: any) => m.id === 3).parameters.depth,
      past: a.historyDepth().past };
  })).toEqual({ cables: 0, depth: .33, past: before + 1 });
});

test('MM1 A101 fake: partial ACK is refused and compensated exactly once', async ({ page }) => {
  await boot(page);
  const result = await page.evaluate(async p => {
    const a = window.__wirescapeTest;
    await a.load(p);
    a.flushHistory();
    const before = a.state(), history = a.historyDepth();
    const engine = a.engine;
    const calls: string[] = [];
    for (const method of ['applyGraph', 'loadGraph', 'setParam', 'setModAmount']) {
      const original = engine[method].bind(engine);
      engine[method] = (...args: any[]) => { calls.push(method); return original(...args); };
    }
    engine.setNextUnapplied([{ moduleId: 1, paramId: 'knob2' }]);
    let error = '';
    try { await a.addMapping({ module: 1, port: 'out2' }, { module: 4, port: 'depth' }); }
    catch (e) { error = (e as Error).message; }
    return { before, history, after: a.state(), finalHistory: a.historyDepth(), calls, error };
  }, fixture());
  expect(result.error).not.toBe('');
  expect(result.calls).toEqual(['applyGraph', 'applyGraph']);
  expect(result.after).toEqual(result.before);
  expect(JSON.stringify(result.after)).toBe(JSON.stringify(result.before));
  expect(result.finalHistory).toEqual(result.history);
});
