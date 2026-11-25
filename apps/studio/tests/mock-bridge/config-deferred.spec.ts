// SPDX-License-Identifier: GPL-3.0-only
import { test, expect, type Page } from '@playwright/test';
import { boot, settle } from '../helpers';
import { mockBridge } from './bridge';

const config = (port: number) => ({ port, lan: false, rows: [] });
const snapshot = (a: number, b: number) => ({
  format: 'wirescape.native.patch' as const, version: 2 as const,
  modules: [{ id: 1, module: 'osc.in', config: config(a) },
    { id: 2, module: 'osc.in', config: config(b) }],
  connections: [],
});
async function setup(page: Page, capability: boolean) {
  await mockBridge(page, { applyGraph: true, configDeferred: capability });
  await boot(page);
  await page.evaluate(p => window.__wirescapeTest.load(p, 'A80'), snapshot(9001, 9002));
  await expect.poll(() => ports(page)).toEqual({ authored: [9001, 9002], confirmed: [9001, 9002], native: [9001, 9002] });
  await settle(page);
}
async function ports(page: Page) {
  return page.evaluate(() => {
    const t = window.__wirescapeTest;
    const pick = (p: any) => p?.modules?.map((m: any) => m.config?.port);
    return { authored: pick(t.state()), confirmed: pick((t.engine as any).confirmedDocument()),
      native: pick((window as any).__mockBridge.getGraph()) };
  });
}
async function defer(page: Page, id: string, a: number, b: number) {
  await page.evaluate(({ id, patch }) => {
    (window as any).__mockBridge.deferNextGraph(id);
    return window.__wirescapeTest.restoreSnapshot(patch);
  }, { id, patch: snapshot(a, b) });
}

test('A80 opts in once and independently reconciles correlated terminal events', async ({ page }) => {
  await setup(page, true);
  const hello = await page.evaluate(() => (window as any).__mockBridge.sent.filter((m: any) => m.type === 'hello'));
  expect(hello).toHaveLength(1);
  expect(hello[0].capabilities).toContain('configDeferred');
  await defer(page, 'd1', 9011, 9012);
  await expect.poll(() => ports(page)).toEqual({ authored: [9011, 9012], confirmed: [9001, 9002], native: [9001, 9002] });
  await page.evaluate(() => {
    const bridge = (window as any).__mockBridge;
    bridge.pushConfig({ deferId: 'unknown', moduleId: 1, outcome: 'applied' });
    bridge.pushConfig({ deferId: 'd1', moduleId: 2, outcome: 'failed', session: 'old' });
    bridge.status();
  });
  expect(await ports(page)).toEqual({ authored: [9011, 9012], confirmed: [9001, 9002], native: [9001, 9002] });
  await page.evaluate(() => (window as any).__mockBridge.completeConfig(1, 'applied'));
  await expect.poll(() => ports(page)).toEqual({ authored: [9011, 9012], confirmed: [9011, 9002], native: [9011, 9002] });
  await page.evaluate(() => (window as any).__mockBridge.completeConfig(2, 'failed'));
  await expect.poll(() => ports(page)).toEqual({ authored: [9011, 9002], confirmed: [9011, 9002], native: [9011, 9002] });
  await page.evaluate(() => (window as any).__mockBridge.pushConfig({ deferId: 'd1', moduleId: 1, outcome: 'failed' }));
  expect(await ports(page)).toEqual({ authored: [9011, 9002], confirmed: [9011, 9002], native: [9011, 9002] });
});

test('A80 pending config survives unrelated full snapshot then explicit revert supersedes', async ({ page }) => {
  await setup(page, true);
  await defer(page, 'd2', 9011, 9002);
  await expect.poll(() => ports(page)).toEqual({ authored: [9011, 9002], confirmed: [9001, 9002], native: [9001, 9002] });
  await page.evaluate(p => window.__wirescapeTest.restoreSnapshot(p), snapshot(9011, 9022));
  await expect.poll(() => ports(page)).toEqual({ authored: [9011, 9022], confirmed: [9001, 9022], native: [9001, 9022] });
  await page.evaluate(p => window.__wirescapeTest.restoreSnapshot(p), snapshot(9001, 9022));
  await expect.poll(() => ports(page)).toEqual({ authored: [9001, 9022], confirmed: [9001, 9022], native: [9001, 9022] });
  await page.evaluate(() => (window as any).__mockBridge.pushConfig({ deferId: 'd2', moduleId: 1, outcome: 'applied' }));
  expect(await ports(page)).toEqual({ authored: [9001, 9022], confirmed: [9001, 9022], native: [9001, 9022] });
});

test('A80 legacy client does not opt in and plain busy rolls back', async ({ page }) => {
  await setup(page, false);
  await defer(page, 'legacy', 9011, 9012);
  await expect.poll(() => ports(page)).toEqual({ authored: [9001, 9002], confirmed: [9001, 9002], native: [9001, 9002] });
  expect(await page.evaluate(() => (window as any).__mockBridge.sent.filter((m: any) => m.type === 'hello'))).toHaveLength(0);
});
