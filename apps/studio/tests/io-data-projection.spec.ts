// SPDX-License-Identifier: GPL-3.0-only
import { test, expect } from '@playwright/test';
import { oscEditorSource, splitOscEditorSave } from '../src/app/ioData';
import type { OscOutConfig } from '../src/app/OscOutEditor';

test('E3c editor data projection wins over stale config without changing authored patch', () => {
  const m = { id: 4, module: 'osc.out', config: { port: 9001, rows: [{ address: '/old' }],
    notes: { address: '/old/note', enabled: true } }, data: { routes: { rows: [{ address: '/new' }] } } };
  const before = structuredClone(m);
  expect(oscEditorSource(m)).toEqual({ port: 9001, rows: [{ address: '/new' }], notes: {} });
  expect(m).toEqual(before);
});

test('E3c editor split retains opaque storage and sends only declared route fields', () => {
  const m = { id: 4, module: 'osc.out', ownerNote: 'keep', config: { port: 9001,
    future: 4, rows: [{ address: '/old', opaque: 2 }], notes: { enabled: true, opaque: 3 } },
    data: { futureSlot: { keep: true }, routes: { futureField: 'keep' } } };
  const draft: OscOutConfig = { port: 9001, rate_hz: 100, future: 4,
    rows: Array.from({ length: 8 }, (_, i) => ({ address: '/new/' + i, kind: 'cv', deadband: .001 })),
    notes: { address: '/new/note' } };
  const before = structuredClone(m);
  const edit = splitOscEditorSave(m, draft);
  expect(edit.config).toEqual({ port: 9001, rate_hz: 100, future: 4 });
  expect(edit.value.rows).toHaveLength(8);
  expect(edit.value).toMatchObject({ notes_address: '/new/note', notes_enabled: false });
  expect((edit.value.rows as unknown[])[0]).toEqual({ address: '/new/0', kind: 'cv', deadband: .001, enabled: true });
  expect(edit.authored).toMatchObject({ ownerNote: 'keep', config: { rows: [{ opaque: 2 }],
    notes: { opaque: 3 }, future: 4 }, data: { futureSlot: { keep: true }, routes: { futureField: 'keep' } } });
  expect(m).toEqual(before);
});
