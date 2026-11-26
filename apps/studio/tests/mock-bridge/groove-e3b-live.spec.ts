// SPDX-License-Identifier: GPL-3.0-only
import { expect, test } from '@playwright/test';
import { boot, settle, state } from '../helpers';
import { mockBridge } from './bridge';

test('Groove E3b A90 real bridge retains v1 construction on running pattern Apply', async ({ page }) => {
  await mockBridge(page, { applyGraph: true, configDeferred: true });
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
  await page.evaluate(() => (window as any).__mockBridge.releaseHeld());
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
