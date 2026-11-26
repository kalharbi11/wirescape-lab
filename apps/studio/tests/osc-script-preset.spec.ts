// SPDX-License-Identifier: GPL-3.0-only
import { test, expect, type Download, type Page } from '@playwright/test';
import { boot, settle, state } from './helpers';

// Use the actual Playwright download bytes and DOM File API without adding
// Node ambient types or dependencies to the Studio browser project.
async function readPreset(download: Download) {
  const stream = await download.createReadStream();
  const decoder = new TextDecoder();
  let text = '';
  for await (const chunk of stream) text += decoder.decode(chunk, { stream: true });
  return JSON.parse(text + decoder.decode());
}
async function uploadPreset(page: Page, value: unknown) {
  await page.getByTestId('osc-preset-file').evaluate((input, json) => {
    const data = new DataTransfer();
    data.items.add(new File([json], 'preset.json', { type: 'application/json' }));
    (input as HTMLInputElement).files = data.files;
    input.dispatchEvent(new Event('change', { bubbles: true }));
  }, JSON.stringify(value));
}

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
  expect(saved.modules[0].config.rows).toBeUndefined();
  const rows = saved.modules[0].data.routes.rows;
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
  const reloaded = (await state(page)).modules[0];
  expect(reloaded.config).toEqual(saved.modules[0].config);
  expect(reloaded.data).toEqual(saved.modules[0].data);
});

test('OB-h5 OSC In portable file round trip, wrong module and network isolation', async ({ page }) => {
  await boot(page);
  await page.evaluate(() => window.__wirescapeTest.load({
    format: 'wirescape.native.patch', version: 2, connections: [],
    modules: [{ id: 1, module: 'osc.in', config: { port: 9123, lan: true } }],
    ui: { positions: { '1': [48, 30] }, view: { x: 0, y: 0, zoom: 1 } },
  }));
  await settle(page);
  await page.getByTestId('osc-edit-1').click();
  await page.getByRole('button', { name: 'Script (/ws/…)', exact: true }).click();
  await page.getByTestId('osc-preset-name').fill('Script copy');
  const downloading = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Save preset…', exact: true }).click();
  const download = await downloading;
  const file = await readPreset(download);
  expect(file).toMatchObject({ format: 'wirescape.osc.preset', version: 1, module: 'osc.in', name: 'Script copy' });
  expect(Object.keys(file.config).sort()).toEqual(['port', 'rows']);
  expect(file.config.port).toBe(9123);
  expect(file.config.rows[0].pattern).toBe('/ws/pitch/*');
  const beforeSave = (await state(page)).modules[0];
  expect(beforeSave.config.rows).toBeUndefined();
  expect(beforeSave.data).toBeUndefined();
  await page.getByTestId('osc-preset-pico').click();
  const upload = (value: unknown) => uploadPreset(page, value);
  await upload({ ...file, module: 'osc.out' });
  await expect(page.getByTestId('osc-editor-errors')).toContainText('Wrong module');
  await expect(page.getByTestId('osc-row1-pattern')).toHaveValue('/pico1/knob/1');
  await upload({ ...file, config: { ...file.config, lan: false, host: '192.0.2.1' } });
  await expect(page.getByTestId('osc-row1-pattern')).toHaveValue('/ws/pitch/*');
  await expect(page.getByTestId('osc-editor-lan')).toBeChecked();
  await page.getByTestId('osc-editor-save').click();
  await expect(page.getByTestId('osc-editor')).toBeHidden();
  const saved = (await state(page)).modules[0];
  expect(saved.config).toMatchObject({ port: 9123, lan: true });
  expect(saved.config.rows).toBeUndefined();
  expect(saved.config.host).toBeUndefined();
  expect(saved.data.routes.rows).toEqual(file.config.rows.map((row: Record<string, unknown>) => ({ ...row, enabled: row.enabled !== false })));
});

test('OB-h5 OSC Out portable file round trip excludes destination and preserves unknown authored fields', async ({ page }) => {
  await boot(page);
  await page.evaluate(() => window.__wirescapeTest.load({
    format: 'wirescape.native.patch', version: 2, connections: [],
    modules: [{ id: 1, module: 'osc.out', config: { port: 9011, rate_hz: 50, futureOption: true } }],
    ui: { positions: { '1': [48, 30] }, view: { x: 0, y: 0, zoom: 1 } },
  }));
  await settle(page);
  await page.getByTestId('osc-out-edit-1').click();
  await page.getByTestId('osc-out-row1-address').fill('/custom/send');
  await page.getByTestId('osc-out-row2-enabled').uncheck();
  await page.getByTestId('osc-out-notes-enabled').check();
  await page.getByTestId('osc-out-notes-address').fill('/custom/notes');
  const downloading = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Save preset…', exact: true }).click();
  const download = await downloading;
  const file = await readPreset(download);
  expect(file.module).toBe('osc.out');
  expect(Object.keys(file.config).sort()).toEqual(['notes', 'port', 'rate_hz', 'rows']);
  await page.getByTestId('osc-out-row1-address').fill('/changed');
  await page.getByTestId('osc-out-row2-enabled').check();
  await page.getByTestId('osc-out-notes-enabled').uncheck();
  await uploadPreset(page, { ...file, config: { ...file.config, host: '192.0.2.1', lan: true } });
  await expect(page.getByTestId('osc-out-row1-address')).toHaveValue('/custom/send');
  await expect(page.getByTestId('osc-out-row2-enabled')).not.toBeChecked();
  await expect(page.getByTestId('osc-out-notes-enabled')).toBeChecked();
  await page.getByTestId('osc-out-save').click();
  await expect(page.getByTestId('osc-editor')).toBeHidden();
  const saved = (await state(page)).modules[0];
  const config = saved.config;
  expect(config).toMatchObject({ port: file.config.port, rate_hz: file.config.rate_hz, futureOption: true });
  expect(config.rows).toBeUndefined();
  expect(config.notes).toBeUndefined();
  expect(saved.data.routes).toMatchObject({
    rows: file.config.rows.map((row: Record<string, unknown>) => ({ ...row, enabled: row.enabled !== false })),
    notes_address: file.config.notes.address, notes_enabled: file.config.notes.enabled === true,
  });
  expect(config.host).toBeUndefined();
  expect(config.lan).toBeUndefined();
});
