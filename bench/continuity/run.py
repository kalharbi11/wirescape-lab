# SPDX-License-Identifier: GPL-3.0-only
"""End-to-end edit-continuity run (T0.13b, #100; proposals/0005 section 4; M0 r3 ruling R7).

    python bench/continuity/run.py --engine <wirescape-engine> [--repeats 3] [--only NAME ...]

For every edit and repeat: one sidecar run on the null sink with the capture flag,
load probe patch -> ~2 s -> noteOn (held-note witness) -> ~2 s -> edit -> ~2 s -> stop, and one
shared no-edit reference run per repeat. The edit's position comes only from its mark (b0, b1).
A reference is aligned on the marks of a shared earlier command (`load` or `note`, per witness);
inside the offsets those two brackets allow, the offset whose pre-edit samples match exactly (or
best) is chosen and its residual reported. Writes facts/dsp/edit_continuity.{json,md}. Numbers
only: no thresholds, no pass/fail.
"""
from __future__ import annotations

import argparse
import datetime
import json
import math
import platform
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import engine as eng  # noqa: E402
import marks as mk  # noqa: E402
import metrics as m  # noqa: E402
import probe  # noqa: E402

RATE, BLOCK = 48000, 256
PAUSE = 20  # status messages (~100 ms each) between steps
ROOT = Path(__file__).resolve().parents[2]


def script(edit: dict | None, setup: dict | None) -> list[eng.Step]:
    steps = [eng.Step('loadGraph', dict(patch=setup or probe.base()), PAUSE, 'load'),
             eng.Step('noteOn', dict(note=69, velocity=0.8), PAUSE, 'note')]
    if edit:
        method, payload = edit['cmd']
        steps.append(eng.Step(method, payload, PAUSE, 'edit'))
    else:
        steps.append(eng.Step(None, {}, PAUSE))
    return steps


def channels(run: eng.Run) -> list[list[float]]:
    """Each bus channel concatenated across capture segments (total-sample index)."""
    out = [[] for _ in range(run.segments[0].channels)]
    for seg in run.segments:
        for c, row in enumerate(seg.data):
            out[c].extend(row)
    return out


def refine(x, ref, alignment: mk.Alignment, edit: int, block: int = BLOCK) -> dict:
    """Pick, among the block offsets the shared marks allow, the one whose steady pre-edit samples
    match best. Returns the shifted reference and how well it matched (residual 0.0 = exact)."""
    s_lo, s_hi = m.steady(x, RATE, edit)
    best, exact = None, []
    for off in range(alignment.lo, alignment.hi + 1):
        shifted = mk.shift(ref, off * block)
        seg = shifted[s_lo:s_hi]
        if any(v != v for v in seg):
            continue
        residual = max(abs(a - b) for a, b in zip(x[s_lo:s_hi], seg))
        if residual == 0.0:
            exact.append(off)
        if best is None or residual < best['residual']:
            best = dict(offset=off, residual=residual, shifted=shifted)
    if best is None:
        raise ValueError('no allowed offset leaves the reference overlapping the steady region')
    best['exact_offsets'] = exact
    best['allowed'] = [alignment.lo, alignment.hi]
    return best


def safe(fn, *a, **k):
    try:
        v = fn(*a, **k)
        return v, None
    except ValueError as e:
        return None, str(e)


def finite(v):
    if isinstance(v, float) and math.isinf(v):
        return '-inf' if v < 0 else 'inf'
    return v


def analyse(run: eng.Run, ref: eng.Run, subject: int | None) -> dict:
    mark = mk.locate(run.marks, 'edit')
    geo = mk.Geometry.of(run.segments)
    win = mk.edit_window(geo, mark)
    x_all, r_all = channels(run), channels(ref)
    edit, late = win.edit, win.late
    reply = run.replies['edit']
    out = dict(ok=reply['ok'], code=reply.get('code'), message=reply.get('message'),
               gen_before=mk.locate(run.marks, 'note').gen, gen_after=mark.gen,
               b0=mark.b0, b1=mark.b1, bracket_blocks=win.width_blocks,
               segments=[[s.block, s.blocks] for s in run.segments], witnesses={})
    for ch, name in [*probe.WITNESS.items(), *([(subject, 'subject')] if subject is not None else [])]:
        x = x_all[ch]
        row, errors = {}, {}
        al = mk.align_offset(run.marks, ref.marks, probe.ALIGN_ON[ch])
        aligned, err = safe(refine, x, r_all[ch], al, edit)
        if err:
            errors['alignment'] = err
            cont = None
        else:
            cont = aligned['shifted']
            row['alignment'] = dict(on=probe.ALIGN_ON[ch], offset_blocks=aligned['offset'],
                                    allowed_blocks=aligned['allowed'], residual=aligned['residual'],
                                    exact_offsets=aligned['exact_offsets'])
        def put(key, fn, *a, **k):
            v, e = safe(fn, *a, **k)
            if e:
                errors[key] = e
            row[key] = finite(v) if not isinstance(v, dict) else v
        if name == 'slip_tone':
            put('time_slip_ms', m.time_slip_tone_ms, x, RATE, edit, probe.SLIP_HZ, late)
        elif name == 'subject':
            load = mk.locate(run.marks, 'load')
            start_at = mk.block_sample(geo, load.b0)
            if cont is not None:
                r, e = safe(m.restarted, x, x[start_at:start_at + RATE], cont, RATE, edit, late=late)
                if e:
                    errors['restarted'] = e
                else:
                    row['restarted'] = r.state
                    row['restarted_note'] = r.note
                level = m.rms(x[edit - RATE // 2:edit])
                limit = level * 1e-3 if level > 0 else 10 ** (m.SILENCE_DBFS / 20)
                lo, hi = win.lo, win.hi
                d, e = safe(mk.first_divergence, x, cont, lo, hi, limit)
                if e:
                    errors['divergence'] = e
                else:
                    p = mk.place_divergence(geo, mark, d)
                    row['divergence'] = dict(block=None if d is None else mk.sample_block(geo, d),
                                             inside_bracket=p.inside, finding=p.finding)
        else:
            if name != 'clock':  # percussive: silent between hits by design, so no silence/dip
                put('silence_ms', m.silence_ms, x, RATE, edit, late)
                put('dip_db', m.dip_db, x, RATE, edit, late)
            put('jump_ratio', m.jump_ratio, x, RATE, edit, late)
            if name == 'tone':
                put('disturbed_ms', m.disturbed_ms, x, m.sine_continuation(x, RATE, edit, probe.TONE_HZ),
                    RATE, edit, late)
            elif cont is not None:
                put('disturbed_ms', m.disturbed_ms, x, cont, RATE, edit, late)
            if name == 'clock':
                v, e = safe(m.clock_slip, x, RATE, edit, 0.1, late)
                if e:
                    errors['time_slip_ms'] = e
                else:
                    row['time_slip_ms'] = v['slip_ms']
                    row['clock_missing'] = len(v['missing'])
                    row['clock_extra'] = len(v['extra'])
        if errors:
            row['not_measured'] = errors
        out['witnesses'][name] = row
    return out


WORST = {'silence_ms': max, 'dip_db': min, 'jump_ratio': max, 'disturbed_ms': max,
         'bracket_blocks': max, 'clock_missing': max, 'clock_extra': max}


def _num(v):
    if v == '-inf':
        return -math.inf
    if v == 'inf':
        return math.inf
    return v


def worst(values: list, key: str):
    vals = [v for v in values if v is not None]
    if not vals:
        return None
    if key == 'time_slip_ms':
        return max(vals, key=abs)
    if key == 'restarted':
        return True if True in vals else (False if False in vals else None)
    return finite(WORST[key]([_num(v) for v in vals]))


def provenance() -> dict:
    sh = lambda *a: subprocess.run(a, capture_output=True, text=True, cwd=ROOT).stdout.strip()
    cpu = ''
    try:
        cpu = next((l.split(':', 1)[1].strip() for l in open('/proc/cpuinfo') if l.startswith('model name')), '')
    except OSError:
        pass
    now = datetime.datetime.now(datetime.timezone.utc)
    return dict(lab_commit=sh('git', 'rev-parse', 'HEAD'), dirty=bool(sh('git', 'status', '--porcelain', '--',
                                                                         'native', 'bench')),
                machine=dict(system=platform.system(), arch=platform.machine(), cpu=cpu,
                             python=platform.python_version(), kind='cloud container, null sink, devices off'),
                date_utc=now.strftime('%Y-%m-%dT%H:%MZ'), rate=RATE, block=BLOCK)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--engine', required=True)
    ap.add_argument('--repeats', type=int, default=3)
    ap.add_argument('--only', nargs='*')
    ap.add_argument('--out', default=str(ROOT / 'facts' / 'dsp' / 'edit_continuity'))
    a = ap.parse_args(argv)
    edits = [e for e in probe.edits() if not a.only or e['name'] in a.only]
    per_edit = {e['name']: [] for e in edits}
    for rep in range(a.repeats):
        ref = eng.run(a.engine, script(None, None))
        for e in edits:
            print(f'repeat {rep + 1}/{a.repeats}: {e["name"]}', flush=True)
            run = eng.run(a.engine, script(e, e.get('setup')))
            per_edit[e['name']].append(analyse(run, ref, e['subject']))
    rows = []
    for e in edits:
        reps = per_edit[e['name']]
        names = list(reps[0]['witnesses'])
        for w in names:
            keys = sorted({k for r in reps for k in r['witnesses'][w]
                           if k not in ('alignment', 'not_measured', 'restarted_note', 'divergence')})
            row = dict(edit=e['name'], command=e['cmd'][0], witness=w,
                       channel=e['subject'] if w == 'subject' else next(c for c, n in probe.WITNESS.items() if n == w),
                       replies=[dict(ok=r['ok'], code=r['code']) for r in reps],
                       bracket_blocks=worst([r['bracket_blocks'] for r in reps], 'bracket_blocks'),
                       worst={k: worst([r['witnesses'][w].get(k) for r in reps], k) for k in keys},
                       repeats=[r['witnesses'][w] for r in reps],
                       marks=[dict(b0=r['b0'], b1=r['b1'], gen_before=r['gen_before'], gen_after=r['gen_after'],
                                   segments=r['segments']) for r in reps])
            rows.append(row)
    doc = dict(provenance=provenance(), repeats=a.repeats,
               method='proposals/0005 section 4 as amended by M0 r3 ruling R7; bench/continuity/DESIGN.md',
               rows=rows, unsupported=probe.UNSUPPORTED)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.with_suffix('.json').write_text(json.dumps(doc, indent=1) + '\n')
    out.with_suffix('.md').write_text(markdown(doc))
    print(f'wrote {out}.json and .md')


def markdown(doc: dict) -> str:
    p = doc['provenance']
    fmt = lambda v: '—' if v is None else (f'{v:.3g}' if isinstance(v, float) else str(v))
    cols = ['silence_ms', 'dip_db', 'time_slip_ms', 'jump_ratio', 'disturbed_ms', 'restarted']
    lines = ['<!-- SPDX-License-Identifier: GPL-3.0-only -->', '# Edit continuity (T0.13b)', '',
             f'Lab commit `{p["lab_commit"]}`{" (dirty)" if p["dirty"] else ""}; {p["machine"]["kind"]}; '
             f'{p["machine"]["system"]} {p["machine"]["arch"]}, {p["machine"]["cpu"] or "cpu unknown"}; '
             f'{p["date_utc"]} UTC; {p["rate"]} Hz, {p["block"]} frames; {doc["repeats"]} repeats, worst shown.',
             'Method: ' + doc['method'] + '. Edit position from the marks file only; "bracket" is '
             '`b1 + 1 − b0` blocks. `—` means not measured; the JSON gives the reason and every repeat. '
             'No thresholds.', '',
             '| edit | witness | ch | reply | bracket | ' + ' | '.join(cols) + ' |',
             '|' + '---|' * (5 + len(cols))]
    for r in doc['rows']:
        reply = 'ok' if all(x['ok'] for x in r['replies']) else ', '.join(sorted({str(x['code']) for x in r['replies']}))
        lines.append(f'| {r["edit"]} | {r["witness"]} | {r["channel"]} | {reply} | {r["bracket_blocks"]} | ' +
                     ' | '.join(fmt(r['worst'].get(c)) for c in cols) + ' |')
    lines += ['', '## Not measured (not supported today)', '']
    lines += [f'- {u["name"]}: {u["reason"]}' for u in doc['unsupported']]
    return '\n'.join(lines) + '\n'


if __name__ == '__main__':
    main()
