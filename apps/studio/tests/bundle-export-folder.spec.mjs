// SPDX-License-Identifier: GPL-3.0-only
import { test, expect } from '@playwright/test';
import { mkdir, readFile, writeFile, readdir } from 'node:fs/promises';
import { join } from 'node:path';

test('SC4 exports a set with scripts into a temporary folder from Studio', async ({ page }, info) => {
  const root = info.outputPath('bundle');
  await mkdir(root, { recursive: true });
  // The browser picker needs an interactive OS chooser. Substitute only the
  // permission-granted directory handle; all UI and manifest code remains real.
  await page.exposeFunction('bundleTestMkdir', (name) => mkdir(join(root, name)));
  await page.exposeFunction('bundleTestWrite', (name, bytes) =>
    writeFile(join(root, name), Uint8Array.from(bytes), { flag: 'wx' }));
  await page.addInitScript(() => {
    const api = window;
    function handle(prefix = '') {
      return {
        async *keys() { /* new empty folder */ },
        async getDirectoryHandle(name) {
          await api.bundleTestMkdir(prefix + name);
          return handle(prefix + name + '/');
        },
        async getFileHandle(name) {
          return { async createWritable() {
            return {
              async write(value) {
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
  const extra = { format: 'wirescape.native.patch', version: 2, connections: [],
    modules: [{ id: 1, module: 'essentials.macro' }, { id: 2, module: 'osc.in', config: { port: 9000 } }],
    ui: { scriptLinks: { '2': { script: 'voice.py', part: 0 } } } };
  await page.goto('/');
  await expect(page.locator('body')).toHaveAttribute('data-ready', 'true');
  await page.getByTestId('open-patch-browser').click();
  await page.getByTestId('open-bundle-export').click();
  await page.getByTestId('bundle-title').fill('Example set');
  const sourceText = JSON.stringify(extra, null, 4) + '\n\n';
  await page.getByTestId('bundle-patches').setInputFiles({ name: 'second.json',
    mimeType: 'application/json', buffer: Buffer.from(sourceText) });
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
  expect(await readFile(join(root, manifest.setlist[1].patch), 'utf8')).toBe(sourceText);
  expect(await readdir(join(root, 'scripts'))).toEqual(['voice.py']);
  expect(await readFile(join(root, 'scripts/voice.py'), 'utf8')).toBe('# no execution\n');
});
