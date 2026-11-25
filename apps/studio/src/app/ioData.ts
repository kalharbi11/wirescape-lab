// SPDX-License-Identifier: GPL-3.0-only
import type { PatchModule } from '../patch/types';
import type { OscConfig } from './OscEditor';
import type { OscOutConfig } from './OscOutEditor';

type RecordValue = Record<string, unknown>;
const object = (v: unknown): RecordValue =>
  v !== null && typeof v === 'object' && !Array.isArray(v) ? v as RecordValue : {};
const own = (v: RecordValue, key: string): boolean => Object.prototype.hasOwnProperty.call(v, key);
const copy = <T>(v: T): T => structuredClone(v);

/** Editor projection only. Opening a legacy patch must not rewrite it.
 * An explicit routes slot wins even when it omits a field: never fill it
 * from stale config rows. The editor's own per-row defaults fill gaps. */
export function oscEditorSource(m: PatchModule): RecordValue {
  const config = copy(object(m.config));
  const data = object(m.data);
  if (!own(data, 'routes')) return config;
  const routes = object(data.routes);
  delete config.rows;
  if (m.module === 'osc.out') delete config.notes;
  if (own(routes, 'rows')) config.rows = copy(routes.rows);
  if (m.module === 'osc.out') {
    const notes: RecordValue = {};
    if (own(routes, 'notes_address')) notes.address = routes.notes_address;
    if (own(routes, 'notes_enabled')) notes.enabled = routes.notes_enabled;
    config.notes = notes;
  }
  return config;
}

export interface OscSlotEdit {
  /** Construction fields only; a change to these needs the graph path. */
  config: RecordValue;
  /** Complete, known-field wire value for the setData transaction. */
  value: RecordValue;
  /** Editable document copy preserves unknown slot and module metadata. */
  authored: PatchModule;
}

/** Split a completed editor draft into authored data and the validated wire
 * shape. Keep unknown legacy OSC Out keys in their original storage when
 * possible, but remove migrated known construction-row keys; otherwise a
 * later slot reset could resurrect stale values. Native code remains the
 * authority for range, pattern and cross-field validation. */
export function splitOscEditorSave(m: PatchModule, draft: OscConfig | OscOutConfig): OscSlotEdit {
  const out = m.module === 'osc.out';
  const authored = copy(m);
  const priorData = copy(object(m.data));
  const priorSlot = object(priorData.routes);
  const cfg = copy(draft as unknown as RecordValue);
  const rowKeys = out ? ['address', 'kind', 'deadband', 'enabled']
    : ['pattern', 'argument', 'kind', 'input_min', 'input_max', 'output_min', 'output_max',
      'smoothing_ms', 'timeout_ms', 'stale', 'enabled'];
  const rowValue = (raw: unknown): RecordValue => {
    const row = object(raw);
    const value: RecordValue = {};
    for (const key of rowKeys) if (own(row, key)) value[key] = row[key];
    value.enabled = row.enabled !== false;
    return value;
  };
  const rows = draft.rows.map(rowValue);
  const value: RecordValue = { rows };
  const nextSlot: RecordValue = { ...priorSlot, rows: rows.map((row, i) =>
    ({ ...(Array.isArray(priorSlot.rows) ? object(priorSlot.rows[i]) : {}), ...row })) };
  if (out) {
    const notes = (draft as OscOutConfig).notes;
    value.notes_address = notes.address;
    value.notes_enabled = notes.enabled === true;
    nextSlot.notes_address = value.notes_address;
    nextSlot.notes_enabled = value.notes_enabled;
  }
  delete cfg.rows;
  if (out) delete cfg.notes;
  const config = copy(cfg);
  if (out) {
    // Preserve opaque legacy row/notes keys in the source document, never
    // send them as an Edit-mode slot field. Known route content lives in data.
    const legacy = object(m.config);
    const unknownRows = (Array.isArray(legacy.rows) ? legacy.rows : []).map(raw =>
      Object.fromEntries(Object.entries(object(raw)).filter(([key]) => !rowKeys.includes(key))));
    if (unknownRows.some(row => Object.keys(row).length)) cfg.rows = unknownRows;
    const unknownNotes = Object.fromEntries(Object.entries(object(legacy.notes))
      .filter(([key]) => key !== 'address' && key !== 'enabled'));
    if (Object.keys(unknownNotes).length) cfg.notes = unknownNotes;
  }
  authored.config = cfg;
  authored.data = { ...priorData, routes: nextSlot };
  return { config, value, authored };
}
