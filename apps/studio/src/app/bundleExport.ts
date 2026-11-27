// SPDX-License-Identifier: GPL-3.0-only
import type { PatchV2 } from '../patch/types';
import { ioObject } from '../patch/ioProjection';

export interface ExportPatch { title: string; patch: PatchV2; sourceText?: string }
interface MacroControl { id: string; target: { macro: { page: number; knob: number } } }
interface MacroPage { title: string; controls: string[] }
interface ScriptEntry { file: string; port: number }
interface PlayerEntry {
  patch: string; title: string; controls: MacroControl[]; pages: MacroPage[]; scripts: ScriptEntry[];
}
export interface PlayerBundle {
  player: { format: 'wirescape.player'; version: 1; title: string; setlist: PlayerEntry[] };
  patches: { name: string; text: string }[];
  scripts: string[];
}

/** Basenames only, portable across the Studio and Player platforms. */
export function safeScriptName(value: unknown): value is string {
  return typeof value === 'string' && /^[a-zA-Z0-9_-][a-zA-Z0-9_.-]{0,119}\.py$/.test(value)
    && !/^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)/i.test(value);
}

export function buildPlayerBundle(title: string, inputs: readonly ExportPatch[]): PlayerBundle {
  if (!title.trim() || !inputs.length) throw new Error('Choose a bundle title and at least one patch.');
  const scripts = new Map<string, string>();
  const patches: PlayerBundle['patches'] = [];
  const setlist = inputs.map(({ title, patch, sourceText }, i): PlayerEntry => {
    if (!title.trim() || patch.format !== 'wirescape.native.patch' || patch.version !== 2 ||
        !Array.isArray(patch.modules) || !Array.isArray(patch.connections))
      throw new Error('Export requires named native v2 patches.');
    // Preserve authored module-array order: Player macro page addresses are ordinal.
    const controls: MacroControl[] = [], pages: MacroPage[] = [];
    for (const mod of patch.modules) {
      if (mod.module !== 'essentials.macro') continue;
      const page = pages.length + 1;
      if (page > 64) throw new Error('Player supports at most 64 macro pages per patch.');
      const ids: string[] = [];
      for (let knob = 1; knob <= 8; knob++) {
        const id = `macro-${page}-${knob}`;
        ids.push(id);
        controls.push({ id, target: { macro: { page, knob } } });
      }
      const label = patch.ui?.labels?.[String(mod.id)];
      pages.push({ title: typeof label === 'string' && label.trim() ? label : `Macro ${page}`, controls: ids });
    }
    const linked = new Map<string, ScriptEntry>();
    for (const [id, raw] of Object.entries(ioObject(patch.ui?.scriptLinks))) {
      const mod = patch.modules.find(m => String(m.id) === id && m.module === 'osc.in');
      const link = ioObject(raw);
      if (!mod || !safeScriptName(link.script) || typeof link.part !== 'number' ||
          !Number.isInteger(link.part) || link.part < 0)
        throw new Error(`Invalid script link on module ${id} in ${title}.`);
      const port = ioObject(mod.config).port ?? 9000;
      if (typeof port !== 'number' || !Number.isInteger(port) || port < 1024 || port > 65535)
        throw new Error(`Invalid OSC port for ${link.script} in ${title}.`);
      const prior = linked.get(link.script);
      if (prior && prior.port !== port)
        throw new Error(`Script ${link.script} links to different OSC ports in ${title}.`);
      const key = link.script.toLowerCase();
      if (scripts.has(key) && scripts.get(key) !== link.script)
        throw new Error('Script names differ only in letter case.');
      scripts.set(key, link.script);
      linked.set(link.script, { file: `scripts/${link.script}`, port });
    }
    // Numbered filenames avoid user-controlled paths, collisions and reordering.
    const name = `patch-${String(i + 1).padStart(4, '0')}.json`;
    // File imports preserve their bytes, including whitespace and unknown fields.
    // A current editor snapshot has no source file and is serialized normally.
    if (sourceText !== undefined && JSON.stringify(JSON.parse(sourceText)) !== JSON.stringify(patch))
      throw new Error('Patch source text does not match its parsed document.');
    patches.push({ name, text: sourceText ?? (JSON.stringify(patch, null, 2) + '\n') });
    return { patch: `patches/${name}`, title, controls, pages, scripts: [...linked.values()] };
  });
  return { player: { format: 'wirescape.player', version: 1, title, setlist },
    patches, scripts: [...scripts.values()] };
}
