// SPDX-License-Identifier: GPL-3.0-only
import type { PatchModule } from '../patch/types';
import { oscProjection } from '../patch/ioProjection';
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
  return oscProjection(m);
}

/** Only effective construction fields select the whole-graph path. Adding
 * display defaults to an omitted legacy config is not a port/rate/LAN edit. */
export function oscConstructionChanged(m: PatchModule, draft: OscConfig | OscOutConfig): boolean {
  const prior = object(m.config);
  const out = m.module === 'osc.out';
  const version = prior.version ?? 1;
  if (version !== (draft.version ?? 1) || (prior.port ?? (out ? 9001 : 9000)) !== draft.port) return true;
  return out ? (prior.rate_hz ?? 100) !== (draft as OscOutConfig).rate_hz
    : (prior.lan ?? false) !== (draft as OscConfig).lan;
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

/** CC editor projection: explicit mapping always wins over stale legacy rows. */
export function ccMappingSource(m: PatchModule): RecordValue[] {
  const data = object(m.data);
  const source = own(data, 'mapping') ? object(data.mapping) : object(m.config);
  return Array.isArray(source.rows) ? copy(source.rows.map(object)) : [];
}

/** Indexed defaults are part of the native eight-row mapping contract (A95). */
export function ccDefaultRow(index: number): RecordValue {
  return { channel: 0, controller: index + 1, fourteen_bit: false, smoothing_ms: 5, min: 0, max: 1 };
}
export function ccEffectiveRows(m: PatchModule): RecordValue[] {
  const rows = ccMappingSource(m);
  const legacy = !own(object(m.data), 'mapping');
  return Array.from({ length: 8 }, (_, index) => {
    const row = object(rows[index]);
    const defaults = ccDefaultRow(index);
    return { ...defaults, ...(legacy && row.bipolar === true ? { min: -1 } : {}), ...row };
  });
}
export function ccRowIsDefault(row: RecordValue, index: number): boolean {
  return Object.entries(ccDefaultRow(index)).every(([key, value]) => row[key] === value);
}

export interface CcSlotEdit {
  value: RecordValue;
  authored: PatchModule;
}

/** Build the complete eight-row wire slot. Legacy bipolar is a migration
 * shorthand only: the live slot has explicit F32 min/max, including inverted
 * ranges. Keep opaque authored keys out of the Edit-mode request. */
export function splitCcMappingSave(m: PatchModule, rows: RecordValue[]): CcSlotEdit {
  if (rows.length > 8) throw new Error('CC row capacity exceeded');
  const authored = copy(m);
  const data = copy(object(m.data));
  const legacy = !own(data, 'mapping');
  const old = object(data.mapping);
  const config = copy(object(m.config));
  const keys = ['channel', 'controller', 'fourteen_bit', 'smoothing_ms', 'min', 'max'];
  const prior = Array.isArray(old.rows) ? old.rows : [];
  const wireRows = Array.from({ length: 8 }, (_, index) => {
    const row = object(rows[index]);
    const defaults = ccDefaultRow(index);
    if (legacy && row.bipolar === true) defaults.min = -1;
    for (const key of keys) if (own(row, key)) defaults[key] = row[key];
    return defaults;
  });
  const authoredRows = wireRows.map((row, index) => {
    const opaque = { ...object(prior[index]), ...object(rows[index]) };
    for (const key of keys) delete opaque[key];
    if (legacy) delete opaque.bipolar;
    return { ...opaque, ...row };
  });
  delete config.rows;
  if (Object.keys(config).length) authored.config = config;
  else delete authored.config;
  authored.data = { ...data, mapping: { ...old, rows: authoredRows } };
  return { value: { rows: wireRows }, authored };
}
