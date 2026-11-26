// SPDX-License-Identifier: GPL-3.0-only
import type { PatchV2 } from '../patch/types';
import type { PatchDoc } from '../patch/PatchDoc';
import { GROOVE, engineConfig, readConfig, upgrade, type GrooveConfig } from './pattern';
import { classifyGrooveApply, grooveEditorConfig, grooveExecution, mergeGroovePattern, type GrooveApply } from './livePattern';

export interface GrooveSource { config?: unknown; data?: unknown }
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
  private pending = new Map<number, Applied>();
  private listeners = new Set<() => void>();
  private absentTrackEdits = new Set<number>();

  private readonly doc: PatchDoc;
  constructor(doc: PatchDoc) {
    this.doc = doc;
    doc.on(e => {
      if (e.t === 'module-added' && doc.modules.get(e.id)?.module === GROOVE) this.record(e.id);
      else if (e.t === 'module-removed') {
        this.applied.delete(e.id);
        this.pending.delete(e.id);
        this.absentTrackEdits.delete(e.id);
      }
      if (e.t === 'config' || e.t === 'reset' || e.t === 'module-added') this.changed();
    });
  }

  /** A whole new document is about to load: its drafts become what plays. */
  forget(): void { this.applied.clear(); this.pending.clear(); this.absentTrackEdits.clear(); this.changed(); }

  /** Preserve the actually running patterns around a trial document load that may refuse. */
  checkpoint(): () => void {
    const before = new Map(this.applied), pending = new Map(this.pending), intents = new Set(this.absentTrackEdits);
    return () => { this.applied = before; this.pending = pending; this.absentTrackEdits = intents; this.changed(); };
  }

  /** Execution copy of a full patch: each Groove carries its applied, known-fields-only config. */
  project(patch: PatchV2): PatchV2 {
    const out = clone(patch);
    for (const m of out.modules) {
      if (m.module !== GROOVE) continue;
      if (!this.applied.has(m.id)) this.applied.set(m.id, {
        engine: json(engineConfig(m.config)), raw: clone(m.config), data: clone(m.data),
      });
      const a = this.pending.get(m.id) ?? this.applied.get(m.id)!;
      if (a.engine === 'null') delete m.config; else m.config = JSON.parse(a.engine) as unknown;
      if (a.data === undefined) delete m.data; else m.data = clone(a.data);
    }
    return out;
  }

  /** The draft differs from what plays (unknown keys never count). */
  isDraft(id: number): boolean {
    const a = this.pending.get(id) ?? this.applied.get(id);
    const m = this.doc.modules.get(id);
    return !!a && !!m && (a.engine !== json(engineConfig(m.config)) ||
      json(a.data) !== json(m.data) || this.absentTrackEdits.has(id));
  }
  /** The applied pattern as the document held it (unknown keys kept), for Revert and change cues. */
  appliedRaw(id: number): unknown { return clone(this.applied.get(id)?.raw); }

  /** GrooveSource construction and slot bytes remain separate from the editor's v2 draft. */
  appliedFields(id: number): GrooveSource | undefined {
    const a = this.applied.get(id);
    return a && { config: clone(a.raw), data: clone(a.data) };
  }

  private intendedFields(id: number): GrooveSource | undefined {
    const p = this.pending.get(id);
    return p ? { config: clone(p.raw), data: clone(p.data) } : this.appliedFields(id);
  }

  appliedEditorConfig(id: number): GrooveConfig | null {
    const source = this.appliedFields(id);
    return source ? grooveEditorConfig(source) : null;
  }

  /** Canonical slot data wins on load; an edited config view wins only while it
   * differs from the applied source and still carries that source's data. */
  editorConfig(id: number): GrooveConfig | null {
    const m = this.doc.modules.get(id), a = this.pending.get(id) ?? this.applied.get(id);
    if (!m) return null;
    if (a && json(m.data) === json(a.data) && json(m.config) !== json(a.raw))
      return readConfig(m.config);
    return grooveEditorConfig({ config: m.config, data: m.data });
  }

  /** Explicit second-track intent matters even when the edit equals its UI default. */
  noteTrackEdit(id: number, track: number): void {
    const source = this.intendedFields(id);
    if (source && track >= (grooveEditorConfig(source)?.tracks.length ?? 2))
      this.absentTrackEdits.add(id);
  }

  classify(id: number): GrooveApply<GrooveSource> | null {
    const source = this.intendedFields(id), edited = this.editorConfig(id);
    return source && edited ? classifyGrooveApply(source, edited, this.absentTrackEdits.has(id)) : null;
  }

  /** Invoke only after the correlated accepted slot reply, before the document
   * emits its change event. No pending draft may enter an unrelated graph load. */
  acceptPattern(id: number, saved: GrooveSource): void {
    const pending = this.pending.get(id), actual = this.applied.get(id);
    if (pending && actual) {
      this.applied.set(id, { ...actual, data: clone(saved.data) });
      this.pending.set(id, { ...pending, data: clone(saved.data) });
    } else this.applied.set(id, { engine: json(engineConfig(saved.config)), raw: clone(saved.config), data: clone(saved.data) });
    this.absentTrackEdits.delete(id);
  }

  /** Restore the complete accepted source, including the data envelope. */
  revertFields(id: number): GrooveSource | undefined {
    this.absentTrackEdits.delete(id);
    return this.intendedFields(id);
  }

  /** Construction changes may upgrade the version/track count. Rebuild the
   * explicit pattern together with the edited config so a stale canonical
   * slot cannot override a new construction edit on reload. */
  constructionFields(id: number): GrooveSource | null {
    const source = this.intendedFields(id), draft = this.editorConfig(id);
    const original = source && grooveEditorConfig(source);
    if (!source || !draft || !original) return null;
    const edited = clone(draft), baseline = clone(original);
    upgrade(baseline);
    // A synthetic second editor track is not an explicit activation, even
    // when some other construction setting changes.
    if (original.tracks.length === 1 && edited.tracks.length === 2 &&
        !this.absentTrackEdits.has(id) && json(baseline.tracks[1]) === json(edited.tracks[1]))
      edited.tracks.length = 1;
    baseline.tracks.length = original.tracks.length;
    const data = source.data;
    const canonical = data && typeof data === 'object' && !Array.isArray(data)
      ? (data as Record<string, unknown>).pattern : undefined;
    const before = grooveExecution(baseline, true, canonical);
    const after = grooveExecution(edited, true, canonical);
    if (!before || !after) return null;
    // Preserve data byte-for-byte on config-only edits so native A75
    // deferral remains eligible. A mixed pattern+construction edit is one
    // atomic graph transaction; it is never split or silently deferred.
    return { config: edited, data: json(before.pattern) === json(after.pattern)
      ? clone(data) : mergeGroovePattern(data, after.pattern) };
  }

  /** Stage an explicit source for applyGraph; restore the accepted source on
   * a refusal. Caller owns document rollback and correlated deferral. */
  stageFields(id: number, source: GrooveSource): () => void {
    const before = this.applied.get(id), pending = this.pending.get(id), intent = this.absentTrackEdits.has(id);
    this.pending.delete(id);
    this.acceptPattern(id, source);
    this.changed();
    return () => {
      if (before) this.applied.set(id, before); else this.applied.delete(id);
      if (pending) this.pending.set(id, pending); else this.pending.delete(id);
      if (intent) this.absentTrackEdits.add(id);
      this.changed();
    };
  }

  /** A deferred ACK authors an intent but does not change the playing source. */
  queueConstruction(id: number, source: GrooveSource): void {
    this.pending.set(id, { engine: json(engineConfig(source.config)), raw: clone(source.config), data: clone(source.data) });
    this.absentTrackEdits.delete(id);
    this.changed();
  }

  /** Only a correlated terminal event changes the accepted construction.
   * Preserve an independently accepted pattern slot under pending config. */
  finishConstruction(id: number, desired: unknown, outcome: string):
    { desired: GrooveSource; actual: GrooveSource } | undefined {
    const p = this.pending.get(id), actual = this.appliedFields(id);
    if (!p || !actual || p.engine !== json(engineConfig(desired))) return undefined;
    this.pending.delete(id);
    const source = { config: clone(p.raw), data: clone(p.data) };
    if (outcome === 'applied') this.applied.set(id, p);
    this.changed();
    return { desired: source, actual: outcome === 'applied' ? source : actual };
  }

  /** Legacy stopped Apply keeps the old behavior. */
  stage(id: number): () => void {
    const m = this.doc.modules.get(id);
    return this.stageFields(id, { config: m?.config, data: m?.data });
  }

  onChange(cb: () => void): () => void { this.listeners.add(cb); return () => this.listeners.delete(cb); }
  changed(): void { for (const cb of [...this.listeners]) cb(); }

  private record(id: number, raw: unknown = this.doc.modules.get(id)?.config,
    data: unknown = this.doc.modules.get(id)?.data): void {
    this.applied.set(id, { engine: json(engineConfig(raw)), raw: clone(raw), data: clone(data) });
  }
}
