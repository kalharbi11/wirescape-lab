// SPDX-License-Identifier: GPL-3.0-only
import { expect, test, type Page } from '@playwright/test';
import { boot } from './helpers';
import { mockBridge } from './mock-bridge/bridge';

/**
 * OB-g3 / #317: exercise the running Studio settings toggle through RealEngine.
 *
 * This bridge is a device-off renderer/IPC simulator, NOT a native MIDI host.
 * Its captureCc hook is simulated; even a green event check here is NOT proof
 * that a real post-toggle MIDI subscription delivers Note On/Off to the graph.
 * That separate end-to-end witness awaits #308's injected native seam.
 */
const DEVICE = 'M8 MIDI 1|M8:M8 MIDI 1';

const toggleCommands = (page: Page) => page.evaluate(() =>
  (window as any).__mockBridge.sent.filter((m: any) => m.type === 'setMidiEnabled'));

const appliedEnabled = (page: Page) => page.evaluate(async id => {
  // Query the bridge again. The switch's aria-pressed state is only optimistic.
  const devices = await window.__wirescapeTest.engine.listMidiDevices();
  return devices.find((d: any) => d.id === id)?.enabled ?? null;
}, DEVICE);

const replyFor = (page: Page, id: string) => page.evaluate(requestId =>
  (window as any).__obG3Replies.find((m: any) => m.re === requestId) ?? null, id);

test.beforeEach(async ({ page }) => {
  await mockBridge(page);
  await boot(page);
  await expect(page.getByTestId('status-engine')).toHaveText('engine: real');
  await expect(page.getByTestId('status-audio')).toHaveText('RUNNING');
  // Listen to genuine protocol replies rather than infer acceptance from the UI.
  // The extra same-session hello emitted by mockBridge.onMessage is ignored by RealEngine.
  await page.evaluate(() => {
    const w = window as any;
    w.__obG3Replies = [];
    w.wirescape.onMessage((message: any) => {
      if (typeof message.re === 'string') w.__obG3Replies.push(message);
    });
  });
});

test('running input off/on: correlated ACK, fresh device state and scripted CC observation without restart (mock-only)', async ({ page }) => {
  const before = await page.evaluate(() => ({
    session: (window as any).__mockBridge.getSession(),
    restarts: (window as any).__mockBridge.restartCount(),
  }));
  await expect.poll(() => appliedEnabled(page)).toBe(true);
  await page.getByTestId('open-settings').click();
  await expect(page.getByTestId('midi-device')).toHaveValue(DEVICE);
  const enabled = page.getByTestId('midi-enabled');
  await expect(enabled).toHaveAttribute('aria-pressed', 'true');

  await enabled.click();
  await expect.poll(async () => (await toggleCommands(page)).length).toBe(1);
  const off = (await toggleCommands(page))[0];
  expect(off).toMatchObject({ type: 'setMidiEnabled', deviceId: DEVICE, on: false });
  await expect.poll(() => replyFor(page, off.id)).toMatchObject({ re: off.id, ok: true });
  await expect.poll(() => appliedEnabled(page)).toBe(false);

  // Drive the existing mock CC source via the actual RealEngine MIDI Learn
  // status subscription. A disabled endpoint must not yield a capture.
  await page.evaluate(() => {
    const w = window as any;
    w.__obG3Learn = null;
    window.__wirescapeTest.engine.onStatus((s: any) => { w.__obG3Learn = s.midi.learn ?? null; });
    window.__wirescapeTest.engine.midiLearn?.(true);
  });
  await expect.poll(() => page.evaluate(() => (window as any).__obG3Learn))
    .toEqual({ armed: true });
  await page.evaluate(id => (window as any).__mockBridge.captureCc(id, 2, 74, 80), DEVICE);
  expect(await page.evaluate(() => (window as any).__obG3Learn)).toEqual({ armed: true });

  await enabled.click();
  await expect.poll(async () => (await toggleCommands(page)).length).toBe(2);
  const on = (await toggleCommands(page))[1];
  expect(on).toMatchObject({ type: 'setMidiEnabled', deviceId: DEVICE, on: true });
  expect(on.id).not.toBe(off.id);
  await expect.poll(() => replyFor(page, on.id)).toMatchObject({ re: on.id, ok: true });
  await expect.poll(() => appliedEnabled(page)).toBe(true);

  await page.evaluate(id => (window as any).__mockBridge.captureCc(id, 2, 74, 80), DEVICE);
  await expect.poll(() => page.evaluate(() => (window as any).__obG3Learn))
    .toEqual({ armed: true, seq: '1', deviceId: DEVICE, channel: 2, controller: 74, value: 80 });
  const after = await page.evaluate(() => ({
    session: (window as any).__mockBridge.getSession(),
    restarts: (window as any).__mockBridge.restartCount(),
  }));
  expect(after).toEqual(before);
});

test('RED baseline: refused running endpoint toggle must not display an unapplied switch state', async ({ page }) => {
  await page.getByTestId('open-settings').click();
  await expect(page.getByTestId('midi-device')).toHaveValue(DEVICE);
  const enabled = page.getByTestId('midi-enabled');
  await expect(enabled).toHaveAttribute('aria-pressed', 'true');

  // This refusal is an actual mock protocol response, not a synthetic assertion
  // against a fabricated native delivery failure. It isolates the optimistic UI.
  await page.evaluate(() => (window as any).__mockBridge.refuseNext('setMidiEnabled', 'busy'));
  await enabled.click();
  await expect.poll(async () => (await toggleCommands(page)).length).toBe(1);
  const cmd = (await toggleCommands(page))[0];
  expect(cmd).toMatchObject({ type: 'setMidiEnabled', deviceId: DEVICE, on: false });
  await expect.poll(() => replyFor(page, cmd.id))
    .toMatchObject({ re: cmd.id, ok: false, code: 'busy' });
  await expect.poll(() => appliedEnabled(page)).toBe(true);

  // Expected RED on current main: App.ts leaves the switch at OFF even though
  // the bridge rejected the operation and still reports this endpoint enabled.
  // No product code is changed in #317; a separately released fix is required.
  // Mark XFAIL only after the correlated refusal and authoritative-state checks:
  // unexpected setup failures must remain normal CI failures, not masked XFAILs.
  test.fail(true, '#317: expected Studio MIDI toggle refusal UI inconsistency');
  await expect(enabled).toHaveAttribute('aria-pressed', 'true');
});
