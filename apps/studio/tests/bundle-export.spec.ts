// SPDX-License-Identifier: GPL-3.0-only
import { test, expect } from '@playwright/test';
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
  patch.modules.push({ id: 2, module: 'osc.in', config: { port: 9001 } });
  patch.ui = { scriptLinks: { '1': { script: 'voice.py', part: 0 }, '2': { script: 'voice.py', part: 1 } } };
  expect(() => buildPlayerBundle('Set', [{ title: 'Patch', patch }])).toThrow(/different OSC ports/);
});

