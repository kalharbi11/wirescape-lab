// SPDX-License-Identifier: GPL-3.0-only
import { test, expect } from '@playwright/test';
import { boot, settle, state } from './helpers';
import { mockBridge } from './mock-bridge/bridge';
import type { PatchV2 } from '../src/patch/types';

const legacy: PatchV2 = {
  format: 'wirescape.native.patch', version: 2,
  modules: [{ id: 1, module: 'osc.in' }, { id: 2, module: 'osc.out' }],
  connections: [], ui: { positions: { '1': [40, 40], '2': [430, 40] } },
};

test('SC1 new OSC modules explicitly author generic defaults; old modules remain unchanged', async ({ page }) => {
  await boot(page);
  await page.evaluate(p => window.__wirescapeTest.load(p), legacy);
  await settle(page);
  const before = await state(page);
  expect(before.modules).toEqual(legacy.modules);
  const inId = await page.evaluate(async () => await window.__wirescapeTest.addModule('osc.in'));
  expect(typeof inId).toBe('number');
  await settle(page);
  const outId = await page.evaluate(async () => await window.__wirescapeTest.addModule('osc.out'));
  expect(typeof outId).toBe('number');
  await settle(page);
  const saved = await state(page);
  expect(saved.modules.slice(0, 2)).toEqual(legacy.modules);
  const input = saved.modules.find((m: any) => m.id > 2 && m.module === 'osc.in');
  const output = saved.modules.find((m: any) => m.id > 2 && m.module === 'osc.out');
  expect(input?.id).toBe(inId);
  expect(output?.id).toBe(outId);
  const rows = input?.data?.routes?.rows ?? input?.config?.rows;
  expect(rows).toHaveLength(8);
  for (let i = 0; i < 8; i++) {
    expect(rows[i]).toMatchObject({ pattern: '/ws/knob/' + (i + 1), kind: 'cv',
      input_min: 0, input_max: 1, output_min: 0, output_max: 1,
      smoothing_ms: 5, timeout_ms: 0, stale: 'hold' });
    expect(rows[i]).not.toHaveProperty('label');
  }
  const outRows = output?.data?.routes?.rows ?? output?.config?.rows;
  expect(outRows?.length).toBeGreaterThan(0);
  expect(outRows[0]).toMatchObject({ address: '/ws/out/1' });
});

test('SC1 OSC In optional labels are recognized and survive editor save and reopen', async ({ page }) => {
  await boot(page);
  const patch: PatchV2 = { ...legacy, modules: [{ id: 1, module: 'osc.in',
    config: { rows: [{ pattern: '/ws/knob/1', label: 'Filter' }] } }] };
  await page.evaluate(p => window.__wirescapeTest.load(p), patch);
  await settle(page);
  const before = await state(page);
  expect(before.modules).toEqual(patch.modules);
  await page.getByTestId('osc-edit-1').click();
  await expect(page.getByTestId('osc-unknown-warning')).toBeHidden();
  await expect(page.getByTestId('osc-row1-label')).toHaveValue('Filter');
  await page.getByTestId('osc-row1-label').fill('é'.repeat(17));
  await page.getByTestId('osc-editor-save').click();
  await expect(page.getByTestId('osc-editor-errors')).toContainText('32');
  expect((await state(page)).modules).toEqual(before.modules);
  await page.getByTestId('osc-row1-label').fill('Cutoff');
  await page.getByTestId('osc-editor-save').click();
  await expect(page.getByTestId('osc-editor')).toBeHidden();
  const saved = await state(page);
  const rows = saved.modules[0].data?.routes?.rows ?? saved.modules[0].config?.rows;
  expect(rows[0].label).toBe('Cutoff');
  expect(rows[1]).not.toHaveProperty('label');
  await page.getByTestId('osc-edit-1').click();
  await expect(page.getByTestId('osc-row1-label')).toHaveValue('Cutoff');
});


test('SC1 canvas shows authored output label and quick kind change is one undo step', async ({ page }) => {
  await boot(page);
  const patch: PatchV2 = { ...legacy, modules: [{ id: 1, module: 'osc.in',
    config: { rows: [{ pattern: '/ws/knob/1', label: 'Filter' }] } }] };
  await page.evaluate(p => window.__wirescapeTest.load(p), patch);
  await settle(page);
  await expect(page.getByTestId('port-1-output-row1').locator('.port-label')).toHaveText('Filter');
  const before = await page.evaluate(() => window.__wirescapeTest.historyDepth());
  const kind = page.getByTestId('osc-quick-kind-1-row1');
  await expect(kind).toHaveValue('cv');
  await kind.selectOption('gate');
  await settle(page);
  const saved = await state(page);
  const rows = saved.modules[0].data?.routes?.rows ?? saved.modules[0].config?.rows;
  expect(rows[0]).toMatchObject({ label: 'Filter', kind: 'gate', pattern: '/ws/knob/1' });
  expect((await page.evaluate(() => window.__wirescapeTest.historyDepth())).past).toBe(before.past + 1);
  await expect(kind).toHaveValue('gate');
});

test('SC1 real bridge quick kind sends one graph; label editor keeps metadata off setData', async ({ page }) => {
  await mockBridge(page, { applyGraph: true });
  await boot(page);
  const patch: PatchV2 = { ...legacy, modules: [{ id: 1, module: 'osc.in',
    config: { rows: [{ pattern: '/ws/knob/1', label: 'Filter' }] } }] };
  await page.evaluate(p => window.__wirescapeTest.load(p), patch);
  await expect.poll(() => page.evaluate(() => (window as any).__mockBridge.getGraph().modules.length)).toBe(1);
  await settle(page);
  await page.evaluate(() => { (window as any).__mockBridge.sent.length = 0; });
  const commands = () => page.evaluate(() => (window as any).__mockBridge.sent
    .filter((m: any) => ['applyGraph', 'loadGraph', 'setData'].includes(m.type)));
  await page.getByTestId('osc-quick-kind-1-row1').selectOption('trigger');
  await expect.poll(async () => (await commands()).map((m: any) => m.type)).toEqual(['applyGraph']);
  await expect(page.getByTestId('osc-quick-kind-1-row1')).toBeEnabled();
  const after = await state(page);
  expect(after.modules[0].data.routes.rows[0]).toMatchObject({ label: 'Filter', kind: 'trigger' });
  await page.getByTestId('osc-edit-1').click();
  await page.getByTestId('osc-row1-label').fill('Cutoff');
  await page.getByTestId('osc-editor-save').click();
  await expect(page.getByTestId('osc-editor')).toBeHidden();
  const sent = await commands();
  expect(sent.map((m: any) => m.type)).toEqual(['applyGraph', 'setData']);
  expect(sent[1].value.rows[0]).not.toHaveProperty('label');
  expect((await state(page)).modules[0].data.routes.rows[0].label).toBe('Cutoff');
  await expect(page.getByTestId('port-1-output-row1').locator('.port-label')).toHaveText('Cutoff');
});

test('SC2 row indicators follow native per-row status, timeout, disabled and route errors', async ({ page }) => {
  await mockBridge(page, { applyGraph: true });
  await boot(page);
  const patch: PatchV2 = { ...legacy, modules: [{ id: 1, module: 'osc.in', config: { rows: [
    { pattern: '/a', label: 'Active', timeout_ms: 100 }, { pattern: '/b', timeout_ms: 100 },
    { pattern: '/c', enabled: false }, { pattern: '/d', timeout_ms: 0 }
  ] } }] };
  await page.evaluate(p => window.__wirescapeTest.load(p), patch);
  await settle(page);
  const dot = (n: number) => page.getByTestId(`osc-row-indicator-1-row${n}`);
  const push = async (routeState: string, rows?: { received: number; ageMs: number | null }[]) => {
    await page.evaluate(({ routeState, rows }) => (window as any).__mockBridge.oscStatus({
      enabled: true, port: 9000, bind: '127.0.0.1', lan: false, routes: [{
        module: '1', port: 9000, bind: '127.0.0.1', state: routeState, received: 4, dropped: 0,
        ...(rows ? { rows } : {})
      }] }), { routeState, rows });
  };
  const activity = [{ received: 1, ageMs: 100 }, { received: 1, ageMs: 101 },
    { received: 1, ageMs: 0 }, { received: 1, ageMs: 100000 }];
  await push('listening'); // older engines omit rows
  await expect(dot(1)).toHaveAttribute('data-state', 'grey');
  await push('listening', activity);
  await expect(dot(1)).toHaveAttribute('data-state', 'green');
  await expect(dot(2)).toHaveAttribute('data-state', 'amber');
  await expect(dot(3)).toHaveAttribute('data-state', 'grey');
  await expect(dot(4)).toHaveAttribute('data-state', 'green');
  await expect(dot(5)).toHaveAttribute('data-state', 'grey');
  await expect(dot(1)).toHaveAttribute('aria-label', 'Active: Receiving');
  // Observe the animation synchronously with the status push (no timing sleeps).
  const pulse = await page.evaluate(() => {
    (window as any).__mockBridge.oscStatus({ enabled: true, port: 9000, routes: [{
      module: '1', port: 9000, bind: '127.0.0.1', state: 'listening', received: 5, dropped: 0,
      rows: [{ received: 2, ageMs: 0 }]
    }] });
    const dot = document.querySelector('[data-testid="osc-row-indicator-1-row1"]')!;
    return dot.getAnimations().map(a => a.effect?.getTiming().duration);
  });
  expect(pulse).toContain(250);
  await push('port-busy', activity);
  await expect(dot(1)).toHaveAttribute('data-state', 'red');
  await push('lan-not-confirmed', activity);
  await expect(dot(3)).toHaveAttribute('data-state', 'red');
  await push('listening', Array.from({ length: 8 }, () => ({ received: 0, ageMs: null })));
  await expect(dot(1)).toHaveAttribute('data-state', 'grey');
  expect((await state(page)).modules).toEqual(patch.modules);
});
