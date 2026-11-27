// SPDX-License-Identifier: GPL-3.0-only
import { test, expect } from '@playwright/test';
import { mkdir, readFile, writeFile, readdir } from 'node:fs/promises';
import { join } from 'node:path';
import { buildPlayerBundle } from '../src/app/bundleExport';
import type { PatchV2 } from '../src/patch/types';

test('SC4 builds an ordered setlist, macro pages and linked scripts without rewriting patches', () => {
  const patch: PatchV2 = {
    format: 'wirescape.native.patch', version: 2, connections: [],
    modules: [
      { id: 8, module: 'essentials.macro' },
      { id: 2, module: 'essentials.macro' },
      { id: 4, module: 'osc.in', config: { port: 9000 } },
      { id: 5, module: 'osc.in', config: { port: 9000 } },
    ],
    ui: { scriptLinks: { '4': { script: 'voice.py', part: 0 }, '5': { script: 'voice.py', part: 1 } } },
  };
  const second: PatchV2 = { format: 'wirescape.native.patch', version: 2, modules: [], connections: [] };
  const bundle = buildPlayerBundle('Set', [{ title: 'First', patch }, { title: 'Second', patch: second }]);
  expect(bundle.player.format).toBe('wirescape.player');
  expect(bundle.player.version).toBe(1);
  expect(bundle.player.setlist.map(entry => entry.title)).toEqual(['First', 'Second']);
  const entry = bundle.player.setlist[0];
  expect(entry.controls).toHaveLength(16);
  expect(entry.controls[0].target).toEqual({ macro: { page: 1, knob: 1 } });
  expect(entry.controls[8].target).toEqual({ macro: { page: 2, knob: 1 } });
  expect(entry.pages.map(page => page.controls.length)).toEqual([8, 8]);
  expect(entry.scripts).toEqual([{ file: 'scripts/voice.py', port: 9000 }]);
  expect(bundle.scripts).toEqual(['voice.py']);
  expect(JSON.parse(bundle.patches[0].text)).toEqual(patch);
  expect(JSON.parse(bundle.patches[1].text)).toEqual(second);
});

test('SC4 rejects unsafe script references and incompatible destinations', () => {
  const patch: PatchV2 = { format: 'wirescape.native.patch', version: 2, connections: [],
    modules: [{ id: 1, module: 'osc.in', config: { port: 9000 } }],
    ui: { scriptLinks: { '1': { script: '../outside.py', part: 0 } } } };
  expect(() => buildPlayerBundle('Set', [{ title: 'Patch', patch }])).toThrow();
});

test('SC4 exports a set with scripts into a temporary folder from Studio', async ({ page }, info) => {
  const root = info.outputPath('bundle');
  await mkdir(root, { recursive: true });
  // The browser picker needs an interactive OS chooser. Substitute only the
  // permission-granted directory handle; all UI and manifest code remains real.
  await page.exposeFunction('bundleTestMkdir', (name: string) => mkdir(join(root, name)));
  await page.exposeFunction('bundleTestWrite', (name: string, bytes: number[]) =>
    writeFile(join(root, name), Uint8Array.from(bytes), { flag: 'wx' }));
  await page.addInitScript(() => {
    const api = window as unknown as {
      bundleTestMkdir(name: string): Promise<void>;
      bundleTestWrite(name: string, bytes: number[]): Promise<void>;
    };
    function handle(prefix = '') {
      return {
        async *keys() { /* new empty folder */ },
        async getDirectoryHandle(name: string) {
          await api.bundleTestMkdir(prefix + name);
          return handle(prefix + name + '/');
        },
        async getFileHandle(name: string) {
          return { async createWritable() {
            return {
              async write(value: Blob | string) {
                const bytes = typeof value === 'string' ? new TextEncoder().encode(value)
                  : new Uint8Array(await value.arrayBuffer());
                await api.bundleTestWrite(prefix + name, [...bytes]);
              },
              async close() {},
              async abort() {},
            };
          } };
        },
      };
    }
    Object.defineProperty(window, 'showDirectoryPicker', { value: async () => handle(), configurable: true });
  });
  const extra: PatchV2 = { format: 'wirescape.native.patch', version: 2, connections: [],
    modules: [{ id: 1, module: 'essentials.macro' }, { id: 2, module: 'osc.in', config: { port: 9000 } }],
    ui: { scriptLinks: { '2': { script: 'voice.py', part: 0 } } } };
  await page.goto('/');
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true');
  await page.getByTestId('open-patch-browser').click();
  await page.getByTestId('open-bundle-export').click();
  await page.getByTestId('bundle-title').fill('Example set');
  await page.getByTestId('bundle-patches').setInputFiles({ name: 'second.json',
    mimeType: 'application/json', buffer: Buffer.from(JSON.stringify(extra)) });
  await page.getByTestId('bundle-scripts').setInputFiles({ name: 'voice.py',
    mimeType: 'text/x-python', buffer: Buffer.from('# no execution\n') });
  await expect(page.getByTestId('bundle-write')).toBeEnabled();
  await page.getByTestId('bundle-write').click();
  await expect(page.getByTestId('bundle-status')).toContainText('Exported 2 patches');
  const manifest = JSON.parse(await readFile(join(root, 'player.json'), 'utf8'));
  expect(manifest.title).toBe('Example set');
  expect(manifest.setlist).toHaveLength(2);
  expect(manifest.setlist[1].scripts).toEqual([{ file: 'scripts/voice.py', port: 9000 }]);
  expect(manifest.setlist[1].pages[0].controls).toHaveLength(8);
  expect(JSON.parse(await readFile(join(root, manifest.setlist[1].patch), 'utf8'))).toEqual(extra);
  expect(await readdir(join(root, 'scripts'))).toEqual(['voice.py']);
  expect(await readFile(join(root, 'scripts/voice.py'), 'utf8')).toBe('# no execution\n');
});
