// SPDX-License-Identifier: GPL-3.0-only
import { expect, test, type Page } from '@playwright/test';
import { boot } from './helpers';
import { mockBridge } from './mock-bridge/bridge';

/**
 * OB-g3 #317 — Studio-only, device-off preliminary baseline.
 *
 * Use the real Studio settings toggle and RealEngine request/reply projection.
 * mockBridge is deliberately NOT an injected native MIDI service: its CC
 * capture is a protocol simulation, not proof of event delivery to engine DSP.
 * End-to-end subscribed-endpoint Note On/Off + monitor evidence must wait for
 * B2 #308's separately released native test seam. Do not infer Host::select
 * as a root cause or make a source fix from these browser tests alone.
 */
const ID = 'M8 MIDI 1|M8:M8 MIDI 1';

async function midiSettings(page: Page) {
  await page.getByTestId('open-settings').click();
  await expect(page.getByTestId('midi-device')).toHaveValue(ID);
  return page.getByTestId('midi-enabled');
}

async function lastToggleCommand(page: Page) {
  return page.evaluate(() => {
    const cmds = (window as any).__mockBridge.sent as
      Array<{ id?: string; type: string; deviceId?: string; on?: boolean }>;
    const toggles = cmds.filter(cmd => cmd.type === 'setMidiEnabled');
    return toggles[toggles.length - 1] ?? null;
  });
}

async function appliedDeviceState(page: Page) {
  return page.evaluate(() => {
    const devices = (window.__wirescapeTest.engine as any).status?.midi?.devices as
      Array<{ id: string; enabled: boolean }> | undefined;
    return devices?.find(device => device.id === 'M8 MIDI 1|M8:M8 MIDI 1')?.enabled;
  });
}

test.describe('OB-g3 #317 MIDI endpoint toggle — preliminary mock-bridge baseline', () => {
  test.beforeEach(async ({ page }) => {
    await mockBridge(page);
    await boot(page);
    await expect(page.getByTestId('status-engine')).toHaveText('engine: real');
    await expect(page.getByTestId('status-audio')).toHaveText('RUNNING');
  });

  test('strict XFAIL: a refused enable while running must not leave a misleading ON switch', async ({ page }) => {
    // Failing baseline at the Studio UI/request boundary only, not the
    // owner-reported accepted-but-dead native endpoint. A passing assertion
    // below becomes an unexpected pass and requires review/removal of XFAIL.
    test.fail(true, '#317 preliminary UI baseline: App optimistically latches a refused MIDI enable');

    let toggle = await midiSettings(page);
    await expect(toggle).toHaveAttribute('aria-pressed', 'true');
    await toggle.click(); // establish an actually disabled endpoint first
    await expect.poll(() => lastToggleCommand(page)).toMatchObject({
      type: 'setMidiEnabled', deviceId: ID, on: false,
    });
    // Same authoritative devices push as the native sidecar sends on OK.
    await page.evaluate(() => (window as any).__mockBridge.devices());
    await expect.poll(() => appliedDeviceState(page)).toBe(false);
    await expect(page.getByTestId('midi-' + ID)).toHaveAttribute('title', /disabled/);

    // Reopen so the toggle is rebuilt from the authoritative disabled state.
    await page.getByTestId('settings-modal-close').click();
    toggle = await midiSettings(page);
    await expect(toggle).toHaveAttribute('aria-pressed', 'false');

    await page.evaluate(() => (window as any).__mockBridge.refuseNext('setMidiEnabled', 'busy'));
    await toggle.click(); // native control refused, still disabled in service
    await expect.poll(() => lastToggleCommand(page)).toMatchObject({
      type: 'setMidiEnabled', deviceId: ID, on: true,
    });
    await expect(page.getByTestId('toast').last()).toContainText('Scripted busy');
    await page.evaluate(() => (window as any).__mockBridge.devices());
    await expect.poll(() => appliedDeviceState(page)).toBe(false);
    await expect(page.getByTestId('midi-' + ID)).toHaveAttribute('title', /disabled/);

    // This is the actual failing assertion at the settings toggle boundary:
    // UI still reads ON after the request was refused and native status is OFF.
    await expect(toggle).toHaveAttribute('aria-pressed', 'false');
  });

  test('accepted enable: Studio command, authoritative status, and mock CC gate agree', async ({ page }) => {
    const toggle = await midiSettings(page);
    await expect(toggle).toHaveAttribute('aria-pressed', 'true');
    await toggle.click(); // disable
    await expect.poll(() => lastToggleCommand(page)).toMatchObject({
      type: 'setMidiEnabled', deviceId: ID, on: false,
    });
    await page.evaluate(() => (window as any).__mockBridge.devices());
    await expect.poll(() => appliedDeviceState(page)).toBe(false);

    // Scripted CC capture is intentionally *mock only*. It proves the browser
    // projection can distinguish enabled vs disabled, not native delivery.
    await page.evaluate(() => (window.__wirescapeTest.engine as any).midiLearn(true));
    await expect.poll(() => page.evaluate(() =>
      (window.__wirescapeTest.engine as any).status?.midi?.learn?.armed)).toBe(true);
    await page.evaluate(id => (window as any).__mockBridge.captureCc(id, 1, 74, 99), ID);
    expect(await page.evaluate(() =>
      (window.__wirescapeTest.engine as any).status?.midi?.learn?.seq)).toBeUndefined();

    await toggle.click(); // enable during an active engine session
    await expect.poll(() => lastToggleCommand(page)).toMatchObject({
      type: 'setMidiEnabled', deviceId: ID, on: true,
    });
    await page.evaluate(() => (window as any).__mockBridge.devices());
    await expect.poll(() => appliedDeviceState(page)).toBe(true);
    await expect(page.getByTestId('midi-' + ID)).toHaveAttribute('title', /enabled/);

    await page.evaluate(id => (window as any).__mockBridge.captureCc(id, 1, 74, 99), ID);
    await expect.poll(() => page.evaluate(() => {
      const learn = (window.__wirescapeTest.engine as any).status?.midi?.learn;
      return learn?.deviceId === 'M8 MIDI 1|M8:M8 MIDI 1' &&
        learn?.controller === 74 && learn?.seq === '1';
    })).toBe(true);
    // The native subscription and actual scripted Note On reaching DSP remain
    // unproven until #308 provides an approved injection/monitor test surface.
  });
});
