// SPDX-License-Identifier: GPL-3.0-only
import type { PatchModule } from './types';
type Value = Record<string, unknown>;
export const ioObject = (v: unknown): Value =>
  v !== null && typeof v === 'object' && !Array.isArray(v) ? v as Value : {};
const owns = (v: Value, key: string): boolean => Object.prototype.hasOwnProperty.call(v, key);

/** Read only: explicit data wins even when its fields are absent. */
export function ioRows(module: PatchModule, slot: 'mapping' | 'routes'): Record<string, unknown>[] {
  const data = ioObject(module.data);
  const value = owns(data, slot) ? ioObject(data[slot]) : ioObject(module.config);
  return Array.isArray(value.rows) ? structuredClone(value.rows) : [];
}
export function oscProjection(module: PatchModule): Value {
  const config = structuredClone(ioObject(module.config));
  const data = ioObject(module.data);
  if (!owns(data, 'routes')) return config;
  const routes = ioObject(data.routes);
  delete config.rows;
  if (owns(routes, 'rows')) config.rows = structuredClone(routes.rows);
  if (module.module === 'osc.out') {
    const notes: Value = {};
    if (owns(routes, 'notes_address')) notes.address = routes.notes_address;
    if (owns(routes, 'notes_enabled')) notes.enabled = routes.notes_enabled;
    config.notes = notes;
  }
  return config;
}
/** Mirrors the native one-way row migration for the fake graph's instance test. */
export function ioConstruction(module: PatchModule): unknown {
  if (!['midi.cc_to_cv', 'osc.in', 'osc.out'].includes(module.module)) return module.config;
  const config = { ...ioObject(module.config) };
  delete config.rows;
  if (module.module === 'osc.out') delete config.notes;
  return config;
}

/** Replace declared data fields while preserving opaque authored slot and row metadata. */
export function mergeSlotValue(previous: unknown, value: Value): Value {
  const old = ioObject(previous);
  const next = { ...old, ...structuredClone(value) };
  if (Array.isArray(value.rows)) {
    const rows = Array.isArray(old.rows) ? old.rows : [];
    next.rows = value.rows.map((row, i) => ({ ...ioObject(rows[i]), ...ioObject(row) }));
  }
  return next;
}
