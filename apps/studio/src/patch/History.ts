// SPDX-License-Identifier: GPL-3.0-only
import type { PatchDoc } from './PatchDoc';
import type { PatchV2 } from './types';

/**
 * Undo/redo for the patch document (phase 4).
 *
 * Snapshot-based: after each user gesture the whole patch (minus the view)
 * is serialised; undo restores the previous snapshot. A patch of 20 modules
 * serialises in well under a millisecond, and snapshots make every edit
 * undoable without each feature writing its own inverse.
 *
 * One gesture is one step (brief: "one knob drag is one step; one
 * multi-cable stereo connection is one step"):
 *  - changes made while a pointer is down are committed on pointerup, so a
 *    knob drag, a module drag, a cable drop or a mapping click is one step;
 *  - other changes (keys, typed values, paste, delete) are committed after
 *    350 ms of quiet, so holding an arrow key is one step too.
 */
/** A saved history cursor can be reconciled to the engine-confirmed graph. */
export type HistoryCheckpoint = (() => void) & {
  reconcile: (authored: PatchV2, confirmed: PatchV2) => void;
};

export class History {
  private past: string[] = [];
  private future: string[] = [];
  private current: string;
  private pending = false;
  private pendingHolds = 0;
  private suppress = false;
  private pointerDown = false;
  private finishingPointer = false;
  private timer: ReturnType<typeof setTimeout> | null = null;
  private listeners = new Set<() => void>();
  readonly limit = 200;

  constructor(private readonly doc: PatchDoc, private readonly restore: (p: PatchV2) => void) {
    this.current = this.snap();
    doc.on(e => {
      if (this.suppress || e.t === 'view' || e.t === 'reset') return;
      this.schedule();
    });
    window.addEventListener('pointerdown', () => {
      // A new gesture must not absorb a keyboard/typed edit still debouncing.
      if (!this.pointerDown) this.flush();
      this.pointerDown = true;
    }, true);
    const up = () => {
      this.pointerDown = false;
      // The click event runs after pointerup and may itself change the doc.
      // Keep its edits in this gesture's end-of-task commit.
      this.finishingPointer = true;
      this.later(0);
    };
    window.addEventListener('pointerup', up, true);
    window.addEventListener('pointercancel', up, true);
    window.addEventListener('blur', up);
  }

  /** Start over from the document as it is (after a load or a new patch). */
  reset(): void {
    this.clearTimer();
    this.pending = false;
    this.finishingPointer = false;
    this.past = [];
    this.future = [];
    this.current = this.snap();
    this.changed();
  }

  /** Save the current document's history before a provisional patch load. */
  checkpoint(): HistoryCheckpoint {
    this.flush();
    let past = [...this.past], future = [...this.future], current = this.current;
    const restore = (() => {
      this.clearTimer();
      this.pending = false;
      this.finishingPointer = false;
      this.past = [...past];
      this.future = [...future];
      this.current = current;
      this.changed();
    }) as HistoryCheckpoint;
    restore.reconcile = (authored, confirmed) => {
      // A snapshot can omit UI metadata that is present in its authored
      // history entry. Match the graph, preserving each entry's own UI: a
      // rejected parameter must not survive merely because positions differ.
      const graph = (patch: PatchV2) => {
        const { ui: _ui, ...rest } = patch;
        return JSON.stringify(rest);
      };
      const from = graph(authored), to = graph(confirmed);
      if (from === to) return;
      const normalize = (item: string): string => {
        const patch = JSON.parse(item) as PatchV2;
        return graph(patch) === from ? this.snapOf({ ...confirmed, ui: patch.ui }) : item;
      };
      // Normalize the saved rollback cursor and live entries before the
      // next graph or undo can restore an unapplied authored value.
      past = past.map(normalize);
      future = future.map(normalize);
      current = normalize(current);
      this.past = this.past.map(normalize);
      this.future = this.future.map(normalize);
      this.current = normalize(this.current);
      this.changed();
    };
    return restore;
  }

  get canUndo(): boolean { return this.past.length > 0 || (this.pending && this.snap() !== this.current); }
  get canRedo(): boolean { return this.future.length > 0; }
  get depth(): { past: number; future: number } { return { past: this.past.length, future: this.future.length }; }

  /** Freeze a debounced optimistic gesture during Q16's incremental ACK hold.
   * The inverse on refusal returns the source to 'current', so releasing
   * commits no unconfirmed 330 and no compensating 220 history entry. */
  holdPending(): () => void {
    ++this.pendingHolds;
    this.clearTimer();
    let released = false;
    return () => {
      if (released) return;
      released = true;
      if (--this.pendingHolds === 0) this.flush();
    };
  }

  /** Commit any pending change now (call before saving or undoing). */
  flush(): void {
    if (this.pendingHolds) return;
    this.clearTimer();
    this.finishingPointer = false;
    if (!this.pending) return;
    this.pending = false;
    const s = this.snap();
    if (s === this.current) return;
    this.past.push(this.current);
    if (this.past.length > this.limit) this.past.shift();
    this.current = s;
    this.future = [];
    this.changed();
  }

  undo(): boolean {
    this.flush();
    const prev = this.past.pop();
    if (prev === undefined) return false;
    this.future.push(this.current);
    this.current = prev;
    this.apply(prev);
    return true;
  }

  redo(): boolean {
    this.flush();
    const next = this.future.pop();
    if (next === undefined) return false;
    this.past.push(this.current);
    this.current = next;
    this.apply(next);
    return true;
  }

  onChange(cb: () => void): () => void { this.listeners.add(cb); return () => this.listeners.delete(cb); }

  // ---- internals ---------------------------------------------------------

  private apply(s: string): void {
    this.suppress = true;
    try { this.restore(JSON.parse(s) as PatchV2); }
    finally { this.suppress = false; }
    this.changed();
  }

  private schedule(): void {
    this.pending = true;
    if (this.pointerDown) { this.clearTimer(); return; }
    this.later(this.finishingPointer ? 0 : 350);
  }

  private later(ms: number): void {
    this.clearTimer();
    if (this.pendingHolds) return;
    this.timer = setTimeout(() => { this.timer = null; this.flush(); }, ms);
  }

  private clearTimer(): void {
    if (this.timer !== null) { clearTimeout(this.timer); this.timer = null; }
  }

  private snap(): string { return this.snapOf(this.doc.toJSON()); }

  private snapOf(j: PatchV2): string {
    const { view: _view, ...ui } = j.ui ?? {};
    return JSON.stringify({ ...j, ui });
  }

  private changed(): void { for (const l of [...this.listeners]) l(); }
}
