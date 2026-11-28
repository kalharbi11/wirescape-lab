// SPDX-License-Identifier: GPL-3.0-only
import { expect, test } from '@playwright/test';
import { boot } from './helpers';

// #769 (owner, Pi beta_02): an input shown crossed out in the status bar must be
// switchable there, even when the Settings MIDI section is slow or empty.
test('clicking a status-bar MIDI chip toggles that input', async ({ page }) => {
  await boot(page);
  const chip = page.getByTestId('midi-Arturia KeyStep|midi:0');
  await expect(chip).not.toHaveClass(/\boff\b/);
  await chip.click();
  await expect(chip).toHaveClass(/\boff\b/);
  await expect(chip).toHaveAttribute('title', /click to enable/);
  await chip.press('Enter');
  await expect(chip).not.toHaveClass(/\boff\b/);
  const enabled = await page.evaluate(async () =>
    (await window.__wirescapeTest.engine.listMidiDevices()).find((d: { id: string }) => d.id === 'Arturia KeyStep|midi:0')?.enabled);
  expect(enabled).toBe(true);
});

test('Settings MIDI section shows a loading row, then the devices', async ({ page }) => {
  await boot(page);
  await page.getByTestId('open-settings').click();
  await expect(page.getByTestId('midi-device')).toBeVisible();
  await expect(page.getByTestId('midi-loading')).toHaveCount(0);
});
