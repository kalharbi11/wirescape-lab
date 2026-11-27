// SPDX-License-Identifier: GPL-3.0-only
import { test, expect } from '@playwright/test';
import { boot, settle, state } from './helpers';
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
  await page.evaluate(() => window.__wirescapeTest.addModule('osc.in'));
  await settle(page);
  await page.evaluate(() => window.__wirescapeTest.addModule('osc.out'));
  await settle(page);
  const saved = await state(page);
  expect(saved.modules.slice(0, 2)).toEqual(legacy.modules);
  const input = saved.modules.find((m: any) => m.id > 2 && m.module === 'osc.in');
  const output = saved.modules.find((m: any) => m.id > 2 && m.module === 'osc.out');
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
