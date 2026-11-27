// SPDX-License-Identifier: GPL-3.0-only
import type { ModuleRegistry } from '../modules/registry';
import { findParam, normToValue, valueToNorm } from '../modules/registry';
import type { ModuleParam } from '../modules/types';
import type { Connection, Endpoint, PatchModule, PatchV2 } from '../patch/types';
import { connKey } from '../patch/types';
import { ioObject, ioRows } from '../patch/ioProjection';
import { ccEffectiveRows } from './ioData';

export type MappingSourceKind = 'macro' | 'cc' | 'osc';
export interface MappingSource { kind: MappingSourceKind; label: string; row: number }
export interface Mapping {
  connection: Connection;
  source: MappingSource;
  parameter: ModuleParam;
  /** Display endpoints in normalized target space (legacy ranges may clamp). */
  min: number;
  max: number;
  inverted: boolean;
  base: number;
  amount: number;
}
const clamp = (n: number) => Math.max(0, Math.min(1, n));
const text = (value: unknown, fallback: string) => typeof value === 'string' && value.length ? value : fallback;
const node = (patch: PatchV2, id: number) => patch.modules.find(m => m.id === id);
const rowIndex = (port: string, prefix: string) =>
  new RegExp('^' + prefix + '([1-8])$').exec(port)?.[1];

/** Recognize only the eight signal outputs on the three defined mapping modules.
 * Unknown/legacy document bytes remain untouched; ordinary modulation is not ownership. */
export function mappingSource(patch: PatchV2, endpoint: Endpoint): MappingSource | undefined {
  const m = node(patch, endpoint.module);
  if (!m) return;
  if (m.module === 'essentials.macro') {
    const row = rowIndex(endpoint.port, 'out');
    if (!row) return;
    const labels = ioObject(ioObject(m.data).labels);
    const names = Array.isArray(labels.rows) ? labels.rows : [];
    const page = patch.modules.filter(x => x.module === m.module).findIndex(x => x.id === m.id) + 1;
    return { kind: 'macro', row: Number(row), label: text(labels.page, 'Macros ' + page) +
      ' · ' + text(ioObject(names[Number(row) - 1]).name, 'Knob ' + row) };
  }
  if (m.module === 'midi.cc_to_cv') {
    const row = rowIndex(endpoint.port, 'cc');
    if (!row) return;
    const config = ccEffectiveRows(m)[Number(row) - 1];
    const source = patch.connections.find(c => c.kind === 'event' && c.to.module === m.id && c.to.port === 'midi');
    const deviceEndpoint = source && ioObject(node(patch, source.from.module)?.config).endpoint;
    return { kind: 'cc', row: Number(row), label: 'CC ' + config.controller +
      ' · ' + (config.channel === 0 ? 'any channel' : 'ch ' + config.channel) +
      (typeof deviceEndpoint === 'string' ? ' · ' + deviceEndpoint : '') };
  }
  if (m.module === 'osc.in') {
    const row = rowIndex(endpoint.port, 'row');
    if (!row) return;
    const config = ioObject(ioRows(m, 'routes')[Number(row) - 1]);
    return { kind: 'osc', row: Number(row), label: 'OSC ' + text(config.pattern, 'row ' + row) };
  }
}

function targetParameter(patch: PatchV2, registry: ModuleRegistry, endpoint: Endpoint): ModuleParam | undefined {
  const m = node(patch, endpoint.module);
  const d = m && registry.get(m.module);
  const p = d && findParam(d, endpoint.port);
  return p?.modulatable ? p : undefined;
}

export function deriveMappings(patch: PatchV2, registry: ModuleRegistry): Mapping[] {
  const out: Mapping[] = [];
  for (const c of patch.connections) {
    if (c.kind !== 'modulation') continue;
    const source = mappingSource(patch, c.from);
    const parameter = targetParameter(patch, registry, c.to);
    if (!source || !parameter) continue;
    const base = node(patch, c.to.module)?.parameters?.[c.to.port] ?? parameter.default;
    const amount = c.amount ?? 0;
    const min = valueToNorm(parameter, base);
    out.push({ connection: structuredClone(c), source, parameter, base, amount,
      min, max: clamp(min + amount), inverted: amount < 0 });
  }
  return out;
}

export function mappingOwner(patch: PatchV2, registry: ModuleRegistry, target: Endpoint): Mapping | undefined {
  return deriveMappings(patch, registry).find(m =>
    m.connection.to.module === target.module && m.connection.to.port === target.port);
}

export function ownerRefusal(owner: Mapping): Error {
  return new Error('Mapped to ' + owner.source.label + '. Remove that mapping, or map the source to a macro.');
}

function currentMapping(patch: PatchV2, registry: ModuleRegistry, c: Connection): Mapping {
  const found = deriveMappings(patch, registry).find(m => connKey(m.connection) === connKey(c));
  if (!found) throw new Error('The mapping no longer exists.');
  return found;
}

export interface MappingRangeEdit { connection: Connection; base?: number; amount: number }
/** Inputs are normalized target positions. Snap through the descriptor before
 * computing the new amount, so stepped targets use their actual authored base. */
export function planMappingRange(patch: PatchV2, registry: ModuleRegistry, c: Connection,
  end: 'min' | 'max', normalized: number): MappingRangeEdit {
  if (!Number.isFinite(normalized)) throw new Error('Mapping range must be finite.');
  const m = currentMapping(patch, registry, c);
  const value = normToValue(m.parameter, normalized);
  const n = valueToNorm(m.parameter, value);
  return end === 'min' ? { connection: m.connection, base: value, amount: m.max - n }
    : { connection: m.connection, amount: n - m.min };
}

interface ParamWrite { module: number; param: string; value: number }
export interface MappingGraphEdit { patch: PatchV2; connection: Connection; writes: ParamWrite[] }
function write(patch: PatchV2, writes: ParamWrite[], module: number, param: string, value: number): void {
  const m = node(patch, module)!;
  (m.parameters ??= {})[param] = value;
  writes.push({ module, param, value });
}

/** New mappings require a unipolar source; historical bipolar CC/OSC
 * mappings remain visible with their actual authored base/amount. */
function requireUnipolar(m: PatchModule, source: MappingSource): void {
  if (source.kind === 'macro') return;
  const row = source.kind === 'cc' ? ccEffectiveRows(m)[source.row - 1] :
    ioObject(ioRows(m, 'routes')[source.row - 1]);
  const lo = source.kind === 'cc' ? row.min : row.output_min ?? 0;
  const hi = source.kind === 'cc' ? row.max : row.output_max ?? 1;
  if (lo !== 0 || hi !== 1) throw new Error('Mapping source must output 0..1.');
  if (source.kind === 'osc' && row.enabled === false) throw new Error('Mapping source is disabled.');
}

/** Pure graph plans: one applyGraph transaction, no mutation before acceptance. */
export function planAddMapping(patch: PatchV2, registry: ModuleRegistry, from: Endpoint, to: Endpoint,
  currentTarget?: number): MappingGraphEdit {
  const owner = mappingOwner(patch, registry, to);
  if (owner) throw ownerRefusal(owner);
  const source = mappingSource(patch, from);
  const p = targetParameter(patch, registry, to);
  if (!source) throw new Error('Not a mapping source.');
  if (!p) throw new Error('sets voices or structure; map it in the Player');
  requireUnipolar(node(patch, from.module)!, source);
  const next = structuredClone(patch), writes: ParamWrite[] = [];
  const connection: Connection = { kind: 'modulation', from: structuredClone(from), to: structuredClone(to), amount: 1 };
  if (source.kind === 'macro' && !deriveMappings(patch, registry).some(m =>
    m.connection.from.module === from.module && m.connection.from.port === from.port)) {
    const base = node(patch, to.module)?.parameters?.[to.port] ?? p.default;
    write(next, writes, from.module, 'knob' + source.row,
      valueToNorm(p, currentTarget !== undefined && Number.isFinite(currentTarget) ? currentTarget : base));
  }
  write(next, writes, to.module, to.port, p.minimum);
  next.connections.push(connection);
  return { patch: next, connection, writes };
}

/** When the current source value is unavailable, preserve the authored base.
 * The source contribution is removed without baking unrelated additive cables
 * into the base. A legacy bipolar source is not silently normalized. */
export function planRemoveMapping(patch: PatchV2, registry: ModuleRegistry, c: Connection,
  sourceValue?: number): MappingGraphEdit {
  const m = currentMapping(patch, registry, c);
  const next = structuredClone(patch), writes: ParamWrite[] = [];
  const value = sourceValue !== undefined && Number.isFinite(sourceValue)
    ? normToValue(m.parameter, m.min + m.amount * sourceValue) : m.base;
  write(next, writes, m.connection.to.module, m.connection.to.port, value);
  next.connections = next.connections.filter(x => connKey(x) !== connKey(c));
  return { patch: next, connection: m.connection, writes };
}
