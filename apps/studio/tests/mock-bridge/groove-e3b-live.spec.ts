// SPDX-License-Identifier: GPL-3.0-only
import { expect, test } from '@playwright/test';
import { boot, settle, state } from '../helpers';
import { mockBridge } from './bridge';

test('Groove E3b A90 real bridge retains v1 construction on running pattern Apply', async ({ page }) => {
  await mockBridge(page, { applyGraph: true, configDeferred: true, dataSlots: { 'sequencing.groove': ['pattern'] } });
  await boot(page);
  const config = { version: 1, bpm: 120, future: 'untouched',
    tracks: [{ armed: true, steps: [{ kind: 'note', key: 60, velocity: .5 }] }] };
  const patch = { format: 'wirescape.native.patch', version: 2, connections: [],
    modules: [{ id: 1, module: 'sequencing.groove', version: 2, config }] };
  await page.evaluate(p => window.__wirescapeTest.load(p, 'E3b v1'), patch);
  await expect.poll(() => page.evaluate(() => (window as any).__mockBridge.getGraph().modules.length)).toBe(1);
  await settle(page);
  await page.evaluate(() => {
    const v = window.__wirescapeTest.canvas.viewport;
    const c = document.querySelector('[data-testid="groove-1"]')!.getBoundingClientRect();
    const r = v.rect();
    v.setView(v.view.x - (c.left - r.left) + 40, v.view.y - (c.top - r.top) + 60, 1);
    (window as any).__mockBridge.telemetry({ playhead: { 1: [3, -1] } });
    (window as any).__mockBridge.sent.length = 0;
  });
  await expect(page.getByTestId('groove-status-1')).toContainText('PLAYING');
  await page.getByTestId('groove-pad-1-1').click();
  await page.getByTestId('groove-pad-1-1').click();
  await expect(page.getByTestId('groove-draft-1')).toBeVisible();
  const apply = page.getByTestId('groove-apply-1');
  await expect(apply).toBeEnabled(); // red until E3b removes the pattern-only stopped gate
  const gen = await page.evaluate(() => (window as any).__mockBridge.generation());
  await page.evaluate(() => (window as any).__mockBridge.refuseNext('setData', 'busy'));
  await apply.click();
  await expect(page.getByTestId('toast')).toContainText('Scripted busy');
  await expect(page.getByTestId('groove-draft-1')).toBeVisible();
  expect((await state(page)).modules[0].data).toBeUndefined();
  await page.evaluate(() => (window as any).__mockBridge.holdNext('setData'));
  await apply.click();
  await expect.poll(() => page.evaluate(() => (window as any).__mockBridge.sent
    .filter((m: any) => m.type === 'setData').length)).toBe(2);
  expect((await state(page)).modules[0].data).toBeUndefined(); // not yet ACKed
  await page.evaluate(() => (window as any).__mockBridge.acceptHeld());
  await expect(page.getByTestId('groove-draft-1')).toBeHidden();
  const saved = (await state(page)).modules[0];
  expect(saved.config).toEqual(config);
  expect(saved.data.pattern.steps_1[0]).toEqual({});
  const wire = await page.evaluate(() => {
    const b = (window as any).__mockBridge;
    return { sent: b.sent, gen: b.generation(), native: b.getGraph().modules[0] };
  });
  expect(wire.gen).toBe(gen);
  expect(wire.sent.filter((m: any) => m.type === 'loadGraph' || m.type === 'applyGraph')).toHaveLength(0);
  expect(wire.native.data.pattern.steps_1[0]).toEqual({});
});


test('Groove E3b canonical reopen hydrates slot without authoring and Revert keeps source bytes', async ({ page }) => {
  await mockBridge(page, { applyGraph: true, configDeferred: true, dataSlots: { 'sequencing.groove': ['pattern'] } });
  await boot(page);
  const source = { id: 1, module: 'sequencing.groove', version: 2,
    config: { version: 1, bpm: 120, tracks: [{ armed: true }] },
    data: { future_slot: { keep: true }, pattern: { length_1: 32, tempo_source: 'internal',
      steps_1: [{ kind: 'note', key: 67, keys: [67, 0, 0, 0, 0], velocity: .5, future: 7 }] } } };
  const patch = { format: 'wirescape.native.patch', version: 2, connections: [], modules: [source] };
  await page.evaluate(p => window.__wirescapeTest.load(p, 'Canonical Groove'), patch);
  await expect.poll(() => page.evaluate(() => (window as any).__mockBridge.getGraph().modules.length)).toBe(1);
  await settle(page);
  await page.evaluate(() => {
    const v = window.__wirescapeTest.canvas.viewport;
    const c = document.querySelector('[data-testid="groove-1"]')!.getBoundingClientRect();
    const r = v.rect();
    v.setView(v.view.x - (c.left - r.left) + 40, v.view.y - (c.top - r.top) + 60, 1);
    (window as any).__mockBridge.sent.length = 0;
  });
  const pad = page.getByTestId('groove-pad-1-1');
  await expect(pad.locator('.g-nn')).toHaveText('G4');
  expect((await state(page)).modules[0]).toEqual(source);
  await expect(page.getByTestId('groove-draft-1')).toBeHidden();
  await pad.click();
  await pad.click();
  await expect(page.getByTestId('groove-draft-1')).toBeVisible();
  await page.getByTestId('groove-revert-1').click();
  await expect(page.getByTestId('groove-draft-1')).toBeHidden();
  await expect(pad.locator('.g-nn')).toHaveText('G4');
  expect((await state(page)).modules[0]).toEqual(source);
  const sent = await page.evaluate(() => (window as any).__mockBridge.sent);
  expect(sent.filter((m: any) => ['setData','loadGraph','applyGraph'].includes(m.type))).toHaveLength(0);
});


test('Groove E3b A90 construction divisor discloses deferred and accepted replacement', async ({ page }) => {
  await mockBridge(page, { applyGraph: true, configDeferred: true, dataSlots: { 'sequencing.groove': ['pattern'] } });
  await boot(page);
  const source = { id: 1, module: 'sequencing.groove', version: 2,
    config: { version: 1, bpm: 120, tracks: [{ armed: true }] },
    data: { pattern: { length_1: 32, steps_1: [{ kind: 'note', key: 60,
      keys: [60, 0, 0, 0, 0], velocity: .5 }] } } };
  const patch = { format: 'wirescape.native.patch', version: 2, connections: [], modules: [source] };
  await page.evaluate(p => window.__wirescapeTest.load(p, 'A90 construction'), patch);
  await expect.poll(() => page.evaluate(() => (window as any).__mockBridge.getGraph().modules.length)).toBe(1);
  await settle(page);
  await page.evaluate(() => {
    const v = window.__wirescapeTest.canvas.viewport;
    const c = document.querySelector('[data-testid="groove-1"]')!.getBoundingClientRect();
    const r = v.rect();
    v.setView(v.view.x - (c.left - r.left) + 40, v.view.y - (c.top - r.top) + 60, 1);
    const b = (window as any).__mockBridge;
    b.telemetry({ playhead: { 1: [3, -1] } });
    b.sent.length = 0;
    b.deferNextGraph('a90-divisor');
  });
  await page.getByTestId('groove-div-4-1').click();
  const apply = page.getByTestId('groove-apply-1');
  await expect(apply).toBeEnabled();
  await apply.click();
  await expect(page.getByTestId('toast')).toContainText('construction (divisor) queued');
  const submitted = await page.evaluate(() => (window as any).__mockBridge.sent.find((m: any) => m.type === 'applyGraph'));
  expect(submitted.patch.modules[0].data).toEqual(source.data); // pure config: A75 eligible
  expect((await state(page)).modules[0].config.tracks[0].div).toBe(4);
  expect(await page.evaluate(() => (window as any).__mockBridge.getGraph().modules[0].config)).toEqual(source.config);
  await page.evaluate(() => (window as any).__mockBridge.completeConfig(1, 'failed'));
  await expect.poll(async () => (await state(page)).modules[0].config).toEqual(source.config);
  expect((await state(page)).modules[0].data).toEqual(source.data);
  await page.getByTestId('groove-div-4-1').click();
  await expect(apply).toBeEnabled();
  await apply.click();
  await expect(page.getByTestId('toast')).toContainText('construction (divisor) applied through graph replacement');
  const result = await page.evaluate(() => {
    const b = (window as any).__mockBridge;
    return { node: b.getGraph().modules[0], sent: b.sent };
  });
  expect(result.node.config.tracks[0].div).toBe(4);
  expect(result.node.data).toEqual(source.data);
  expect(result.sent.filter((m: any) => m.type === 'applyGraph')).toHaveLength(2);
  expect(result.sent.filter((m: any) => m.type === 'setData')).toHaveLength(0);
});
