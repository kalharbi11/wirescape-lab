// SPDX-License-Identifier: GPL-3.0-only
import { el } from './dom';
import type { OscRow } from './OscEditor';
import type { OscOutRow, OscOutConfig } from './OscOutEditor';

type Module = 'osc.in' | 'osc.out';
type Configs = {
  'osc.in': { port: number; rows: OscRow[] };
  'osc.out': Pick<OscOutConfig, 'port' | 'rows' | 'notes' | 'rate_hz'>;
};
type Preset<M extends Module> = {
  format: 'wirescape.osc.preset'; version: 1; module: M; name: string; config: Configs[M];
};
type DesktopPresets = {
  list(module: Module): Promise<{ file: string; name: string }[]>;
  read(file: string): Promise<string>;
  choose(): Promise<string | null>;
  save(text: string, name: string): Promise<void>;
  openFolder(): Promise<void>;
};
const LIMIT = 256 * 1024;
const obj = (v: unknown): Record<string, unknown> => {
  if (!v || typeof v !== 'object' || Array.isArray(v)) throw new Error('Invalid OSC preset object.');
  return v as Record<string, unknown>;
};
const num = (v: unknown, min = -Infinity, max = Infinity, integer = false): number => {
  if (typeof v !== 'number' || !Number.isFinite(v) || !Number.isFinite(Math.fround(v)) ||
      v < min || v > max || (integer && !Number.isInteger(v))) throw new Error('Invalid OSC preset number.');
  return v;
};
const one = <T extends string>(v: unknown, values: readonly T[]): T => {
  if (typeof v !== 'string' || !values.includes(v as T)) throw new Error('Invalid OSC preset choice.');
  return v as T;
};
const enabled = (v: unknown, defaultOn: boolean): { enabled?: boolean } => {
  if (v !== undefined && typeof v !== 'boolean') throw new Error('Invalid OSC preset row toggle.');
  return v === undefined || v === defaultOn ? {} : { enabled: v };
};
const address = (v: unknown, out: boolean): string => {
  if (typeof v !== 'string' || !v.startsWith('/') || (out
    ? v.length < 2 || v.length > 63 || !/^\/[\x21-\x7e]+$/.test(v) || /[#*,?\[\]{}]/.test(v)
    : v.includes('\0') || new TextEncoder().encode(v).length > 255)) {
    throw new Error('Invalid OSC preset address.');
  }
  return v;
};
function inputRow(raw: unknown): OscRow {
  const r = obj(raw);
  const input_min = num(r.input_min), input_max = num(r.input_max);
  if (r.label !== undefined && (typeof r.label !== 'string' || new TextEncoder().encode(r.label).length > 32))
    throw new Error('OSC preset row label must fit in 32 UTF-8 bytes.');
  if (Math.fround(input_max) <= Math.fround(input_min)) throw new Error('OSC preset input max must exceed min.');
  return {
    pattern: address(r.pattern, false), argument: num(r.argument, 0, 31, true),
    kind: one(r.kind, ['cv', 'gate', 'trigger'] as const), input_min, input_max,
    output_min: num(r.output_min), output_max: num(r.output_max),
    smoothing_ms: num(r.smoothing_ms, 0, 2000), timeout_ms: num(r.timeout_ms, 0, 3600000),
    stale: one(r.stale, ['hold', 'zero'] as const), ...enabled(r.enabled, true),
    ...(typeof r.label === 'string' && r.label ? { label: r.label } : {}),
  };
}
function outputRow(raw: unknown): OscOutRow {
  const r = obj(raw);
  return { address: address(r.address, true), kind: one(r.kind, ['cv', 'gate'] as const),
    deadband: num(r.deadband, 0, 1), ...enabled(r.enabled, true) };
}
/** Explicit allowlist: no preset can write LAN, host, unknown config or row fields. */
export function presetConfig<M extends Module>(module: M, raw: unknown): Configs[M] {
  const c = obj(raw);
  const port = num(c.port, module === 'osc.in' ? 1024 : 1, 65535, true);
  if (!Array.isArray(c.rows) || c.rows.length !== 8) throw new Error('OSC preset needs exactly eight rows.');
  if (module === 'osc.in') return { port, rows: c.rows.map(inputRow) } as Configs[M];
  const n = obj(c.notes);
  return { port, rows: c.rows.map(outputRow), rate_hz: num(c.rate_hz, 1, 500, true),
    notes: { address: address(n.address, true), ...enabled(n.enabled, false) } } as Configs[M];
}
function nameOf(v: unknown): string {
  if (typeof v !== 'string' || !v.trim() || v.length > 120 || /[\x00-\x1f\x7f]/.test(v)) {
    throw new Error('Enter a preset name (1–120 characters).');
  }
  return v.trim();
}
export function encodePreset<M extends Module>(module: M, name: string, raw: unknown): string {
  const p: Preset<M> = { format: 'wirescape.osc.preset', version: 1, module,
    name: nameOf(name), config: presetConfig(module, raw) };
  return JSON.stringify(p, null, 2) + '\n';
}
export function decodePreset<M extends Module>(module: M, text: string): Preset<M> {
  if (new TextEncoder().encode(text).length > LIMIT) throw new Error('OSC preset exceeds 256 KiB.');
  const p = obj(JSON.parse(text));
  if (p.format !== 'wirescape.osc.preset' || p.version !== 1) throw new Error('Unsupported OSC preset format or version.');
  if (p.module !== module) throw new Error('Wrong module: this OSC preset is not for ' + module + '.');
  return { format: 'wirescape.osc.preset', version: 1, module, name: nameOf(p.name),
    config: presetConfig(module, p.config) };
}
export const draftNumber = (input: HTMLInputElement | HTMLSelectElement): number =>
  input.value.trim() ? Number(input.value) : NaN;

/** File operations edit only the modal draft; ordinary Save and apply still owns the patch write. */
export function addOscPresetControls<M extends Module>(
  parent: HTMLElement, module: M, snapshot: () => unknown,
  apply: (value: Configs[M]) => void, errors: HTMLElement, isBusy: () => boolean,
): void {
  const bridge = (window as Window & { wirescapeOscPresets?: DesktopPresets }).wirescapeOscPresets;
  const group = el('div', 'osc-presets');
  group.dataset.testid = 'osc-preset-files';
  const name = el('input', 'input-text') as HTMLInputElement;
  name.type = 'text'; name.maxLength = 120; name.value = module === 'osc.in' ? 'OSC In' : 'OSC Out';
  name.dataset.testid = 'osc-preset-name'; name.setAttribute('aria-label', 'Preset name');
  const button = (label: string, id: string, action: () => void): HTMLButtonElement => {
    const b = el('button', 'btn', label) as HTMLButtonElement;
    b.type = 'button'; b.dataset.testid = id; b.addEventListener('click', action); return b;
  };
  let active = false;
  const run = async (fn: () => Promise<void>) => {
    if (active || isBusy()) return;
    active = true;
    try { errors.textContent = ''; await fn(); }
    catch (e) { if (group.isConnected) errors.textContent = e instanceof Error ? e.message : 'Could not access OSC preset.'; }
    finally { active = false; }
  };
  const load = (text: string) => {
    const p = decodePreset(module, text);
    if (!group.isConnected || !group.getClientRects().length || isBusy()) return;
    apply(p.config); name.value = p.name;
  };
  const list = el('div', 'osc-presets');
  const refresh = async () => {
    if (!bridge) return;
    const files = await bridge.list(module);
    if (!group.isConnected) return;
    list.replaceChildren();
    for (const file of files) list.append(button(file.name, 'osc-preset-library-' + file.file, () => {
      void run(async () => load(await bridge.read(file.file)));
    }));
  };
  const file = el('input') as HTMLInputElement;
  file.type = 'file'; file.accept = '.json,application/json'; file.hidden = true;
  file.dataset.testid = 'osc-preset-file';
  file.addEventListener('change', () => {
    const selected = file.files?.[0]; file.value = '';
    if (selected) void run(async () => {
      if (selected.size > LIMIT) throw new Error('OSC preset exceeds 256 KiB.');
      load(await selected.text());
    });
  });
  group.append(name, button('Save preset…', 'osc-preset-save-file', () => {
    void run(async () => {
      const text = encodePreset(module, name.value, snapshot());
      if (bridge) { await bridge.save(text, name.value.trim()); await refresh(); }
      else {
        const url = URL.createObjectURL(new Blob([text], { type: 'application/json' }));
        const a = document.createElement('a');
        a.href = url; a.download = name.value.trim().replace(/[^a-zA-Z0-9_-]+/g, '_') + '.json';
        document.body.append(a); a.click(); a.remove();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
      }
    });
  }), button('Load preset…', 'osc-preset-load-file', () => {
    if (bridge) void run(async () => { const text = await bridge.choose(); if (text !== null) load(text); });
    else if (!active && !isBusy()) file.click();
  }), file);
  if (bridge) {
    group.append(button('Open presets folder', 'osc-preset-open-folder', () => { void run(async () => { await bridge.openFolder(); }); }), list);
  }
  parent.append(group);
  if (bridge) void run(refresh);
}
