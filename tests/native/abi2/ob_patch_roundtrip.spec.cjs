// SPDX-License-Identifier: GPL-3.0-only
// Product Studio PatchDoc load/save/load test; native loader and renderer
// are checked independently for every saved document by patch_roundtrip.py.
const { test, expect } = require('@playwright/test');
const { readFileSync, writeFileSync } = require('node:fs');
const { PatchDoc } = require('../../../apps/studio/src/patch/PatchDoc');

function normalized(v) {
  if (Array.isArray(v)) return v.map(normalized);
  if (v && typeof v === 'object')
    return Object.fromEntries(Object.entries(v).sort(([a], [b]) => a.localeCompare(b))
      .map(([key, value]) => [key, normalized(value)]));
  return v;
}

test('OB-a1 actual PatchDoc load/save/load preserves all bundled and config-shape data', () => {
  const file = process.env.OB_PATCH_MANIFEST;
  expect(file, 'missing OB_PATCH_MANIFEST').toBeTruthy();
  const cases = JSON.parse(readFileSync(file, 'utf8'));
  expect(cases.length).toBeGreaterThan(0);
  const failures = [];
  for (const item of cases) {
    try {
      const source = JSON.parse(readFileSync(item.source, 'utf8'));
      const saved = JSON.stringify(PatchDoc.from(source).toJSON(), null, 2);
      writeFileSync(item.saved, saved, 'utf8');
      const reopened = PatchDoc.from(JSON.parse(readFileSync(item.saved, 'utf8'))).toJSON();
      writeFileSync(item.reopened, JSON.stringify(reopened, null, 2), 'utf8');
      // Do not strip unknown, UI, device or module-state fields.
      expect(normalized(JSON.parse(saved)), item.name + ': first save').toEqual(normalized(source));
      expect(normalized(reopened), item.name + ': second load').toEqual(normalized(source));
    } catch (error) {
      failures.push(item.name + ': ' + String(error));
    }
  }
  expect(failures, failures.join('\n')).toEqual([]);
});
