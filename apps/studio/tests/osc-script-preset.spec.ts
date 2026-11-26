// SPDX-License-Identifier: GPL-3.0-only
import { test, expect } from '@playwright/test';
import { boot, settle, state } from './helpers';

test('OB-h5 Script preset maps MIDI pitch and preserves LAN and patch shape', async ({ page }) => {
  await boot(page);
  await page.evaluate(() => window.__wirescapeTest.load({
    format: 'wirescape.native.patch', version: 2,
    modules: [{ id: 1, module: 'osc.in', config: { port: 9123, lan: true } }],
    connections: [],
    ui: { positions: { '1': [48, 30] }, view: { x: 0, y: 0, zoom: 1 } },
  }));
  await settle(page);
  await page.getByTestId('osc-edit-1').click();
  await expect(page.getByTestId('osc-row1-pattern')).toHaveValue('/pico1/knob/1');
  await page.getByRole('button', { name: 'Script (/ws/…)', exact: true }).click();
  await expect(page.getByTestId('osc-editor-lan')).toBeChecked();
  await expect(page.getByTestId('osc-editor-save')).toBeEnabled();
  await page.getByTestId('osc-editor-save').click();
  await expect(page.getByTestId('osc-editor')).toBeHidden();
  const saved = await state(page);
  expect(saved.modules[0].config.lan).toBe(true);
  const rows = saved.modules[0].config.rows;
  expect(rows).toHaveLength(8);
  expect(rows[0]).toMatchObject({ pattern: '/ws/pitch/*', kind: 'cv', input_min: 0, input_max: 127, smoothing_ms: 0 });
  // MIDI to CV uses 1 V/oct with MIDI note 60 = 0 (engine/voice/allocator.h).
  // Exercise the authored endpoints with OSC In's clamped linear map.
  for (const note of [0, 60, 127]) {
    const p = rows[0];
    const t = Math.max(0, Math.min(1, (note - p.input_min) / (p.input_max - p.input_min)));
    expect(p.output_min + t * (p.output_max - p.output_min)).toBeCloseTo((note - 60) / 12, 6);
  }
  expect(rows[1]).toMatchObject({ pattern: '/ws/trig/*', kind: 'trigger' });
  expect(rows[2]).toMatchObject({ pattern: '/ws/gate/*', kind: 'gate', timeout_ms: 2000, stale: 'zero' });
  expect(rows[3]).toMatchObject({ pattern: '/ws/vel/*', kind: 'cv', input_min: 0, input_max: 1, output_min: 0, output_max: 1 });
  for (let i = 4; i < 8; i++) {
    expect(rows[i]).toMatchObject({ pattern: `/ws/cv/${i - 3}`, kind: 'cv', input_min: 0, input_max: 1, output_min: 0, output_max: 1, smoothing_ms: 5 });
  }
  expect(rows.every((row: { enabled?: boolean }) => row.enabled !== false)).toBe(true);
  expect(saved.format).toBe('wirescape.native.patch');
  expect(saved.version).toBe(2);
  await page.evaluate(() => window.__wirescapeTest.autosaveNow());
  await page.reload();
  await page.waitForFunction(() => document.body.dataset.ready === 'true');
  await settle(page);
  expect((await state(page)).modules[0].config).toEqual(saved.modules[0].config);
});
