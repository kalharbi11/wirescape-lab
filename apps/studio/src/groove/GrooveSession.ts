// SPDX-License-Identifier: GPL-3.0-only
import type { PatchV2 } from '../patch/types';
import type { PatchDoc } from '../patch/PatchDoc';
import { GROOVE, engineConfig, readConfig, type GrooveConfig } from './pattern';
import { classifyGrooveApply, grooveEditorConfig, type GrooveApply } from './livePattern';

interface Source { config?: unknown; data?: unknown }
interface Applied { engine: string; raw: unknown; data: unknown }

const json = (v: unknown): string => JSON.stringify(v ?? null);
const clone = <T>(v: T): T => v === undefined ? v : JSON.parse(JSON.stringify(v)) as T;

/**
 * What the engine is playing for each Groove, versus the editable draft in
 * the document. Every whole-graph load goes through `project`, so an undo,
 * an engine restart or another module's reload never sends an unapplied
 * draft: only `apply` moves a draft to the engine (stopped Apply, #498).
 */
export class GrooveSession {
  private applied = new Map<number, Applied>();
  private listeners = new Set<() => void>();
  private absentTrackEdits = new Set<number>();

  constructor(private readonly doc: PatchDoc) {
    doc.on(e => {
      if (e.t === 'module-added' && doc.modules.get(e.id)?.module === GROOVE) this.record(e.id);
      else if (e.t === 'module-removed') {
        this.applied.delete(e.id);
        this.absentTrackEdits.delete(e.id);
      }
      if (e.t === 'config' || e.t === 'reset' || e.t === 'module-added') this.changed();
    });
  }

  /** A whole new document is about to load: its drafts become what plays. */
  forget(): void { this.applied.clear(); this.absentTrackEdits.clear(); this.changed(); }

  /** Preserve the actually running patterns around a trial document load that may refuse. */
  checkpoint(): () => void {
    const before = new Map(this.applied), intents = new Set(this.absentTrackEdits);
    return () => { this.applied = before; this.absentTrackEdits = intents; this.changed(); };
  }

  /** Execution copy of a full patch: each Groove carries its applied, known-fields-only config. */
  project(patch: PatchV2): PatchV2 {
    const out = clone(patch);
    for (const m of out.modules) {
      if (m.module !== GROOVE) continue;
      if (!this.applied.has(m.id)) this.applied.set(m.id, {
        engine: json(engineConfig(m.config)), raw: clone(m.config), data: clone(m.data),
      });
      const a = this.applied.get(m.id)!;
      if (a.engine === 'null') delete m.config; else m.config = JSON.parse(a.engine) as unknown;
      if (a.data === undefined) delete m.data; else m.data = clone(a.data);
    }
    return out;
  }

  /** The draft differs from what plays (unknown keys never count). */
  isDraft(id: number): boolean {
    const a = this.applied.get(id);
    const m = this.doc.modules.get(id);
    return !!a && !!m && (a.engine !== json(engineConfig(m.config)) ||
      json(a.data) !== json(m.data) || this.absentTrackEdits.has(id));
  }
  /** The applied pattern as the document held it (unknown keys kept), for Revert and change cues. */
  appliedRaw(id: number): unknown { return clone(this.applied.get(id)?.raw); }

  /** Source construction and slot bytes remain separate from the editor's v2 draft. */
  appliedFields(id: number): Source | undefined {
    const a = this.applied.get(id);
    return a && { config: clone(a.raw), data: clone(a.data) };
  }

  /** Canonical slot data wins on load; an edited config view wins only while it
   * differs from the applied source and still carries that source's data. */
  editorConfig(id: number): GrooveConfig | null {
    const m = this.doc.modules.get(id), a = this.applied.get(id);
    if (!m) return null;
    if (a && json(m.data) === json(a.data) && json(m.config) !== json(a.raw))
      return readConfig(m.config);
    return grooveEditorConfig({ config: m.config, data: m.data });
  }

  /** Explicit second-track intent matters even when the edit equals its UI default. */
  noteTrackEdit(id: number, track: number): void {
    const source = this.appliedFields(id);
    if (source && track >= (grooveEditorConfig(source)?.tracks.length ?? 2))
      this.absentTrackEdits.add(id);
  }

  classify(id: number): GrooveApply<Source> | null {
    const source = this.appliedFields(id), edited = this.editorConfig(id);
    return source && edited ? classifyGrooveApply(source, edited, this.absentTrackEdits.has(id)) : null;
  }

  /** Invoke only after the correlated accepted slot reply, before the document
   * emits its change event. No pending draft may enter an unrelated graph load. */
  acceptPattern(id: number, saved: Source): void {
    this.applied.set(id, { engine: json(engineConfig(saved.config)), raw: clone(saved.config), data: clone(saved.data) });
    this.absentTrackEdits.delete(id);
  }

  /** Restore the complete accepted source, including the data envelope. */
  revertFields(id: number): Source | undefined {
    this.absentTrackEdits.delete(id);
    return this.appliedFields(id);
  }

  /** Mark the current draft as the one to send; returns an undo for a refused load. */
  stage(id: number): () => void {
    const before = this.applied.get(id);
    this.record(id);
    this.changed();
    return () => { if (before) this.applied.set(id, before); else this.applied.delete(id); this.changed(); };
  }

  onChange(cb: () => void): () => void { this.listeners.add(cb); return () => this.listeners.delete(cb); }
  changed(): void { for (const cb of [...this.listeners]) cb(); }

  private record(id: number, raw: unknown = this.doc.modules.get(id)?.config,
    data: unknown = this.doc.modules.get(id)?.data): void {
    this.applied.set(id, { engine: json(engineConfig(raw)), raw: clone(raw), data: clone(data) });
  }
}
