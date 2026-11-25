# SPDX-License-Identifier: GPL-3.0-only
"""End-to-end edit-continuity run (T0.13b, #100; proposals/0005 section 4; M0 r3 ruling R7).

    python bench/continuity/run.py --engine <wirescape-engine> [--repeats 3] [--only NAME ...]

For every edit and repeat: one sidecar run on the null sink with the capture flag,
load probe patch -> ~2 s -> noteOn (held-note witness) -> ~2 s -> edit -> ~2 s -> stop, and one
shared no-edit reference run per repeat. The edit's position comes only from its mark (b0, b1).
A reference uses the edited capture's setup and is aligned on the marks of a shared earlier
command (`load` or `note`, per witness);
inside the offsets those two brackets allow, the offset whose pre-edit samples match exactly (or
best) is chosen and its residual reported. Writes facts/dsp/edit_continuity.{json,md}. Numbers
only: no thresholds, no pass/fail.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
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


def reset_reference(x, geo: mk.Geometry, marks, subject: int, edit: int) -> list[float]:
    """The subject's own reset output, the reference `restarted` compares against.
    Channels whose reset state is silence (probe.IDLE_SILENT: the held note sounds only after its
    noteOn) use the silent stretch just before the `note` mark. All others start at their first
    sounding sample after the `load` mark: from b0 itself the silent lead would include however
    many blocks passed before the graph swapped in, an arbitrary length no later reset repeats."""
    floor = 10 ** (m.SILENCE_DBFS / 20)
    if subject in probe.IDLE_SILENT:
        note_at = mk.block_sample(geo, mk.locate(marks, 'note').b0)
        idle = x[max(0, note_at - RATE // 4):note_at]
        if len(idle) < RATE // 4 or any(abs(v) >= floor for v in idle):
            raise ValueError('held-note subject is not silent before its noteOn: no idle reference')
        return list(idle)
    load_at = mk.block_sample(geo, mk.locate(marks, 'load').b0)
    start_at = next((i for i in range(load_at, edit) if abs(x[i]) >= floor), load_at)
    return list(x[start_at:start_at + RATE])


def subject_restart(x, cont, geo, marks, subject, edit, late, changes_subject=False) -> tuple:
    """(restarted, note) for the subject. A False where the edit changes the subject's own sound is
    not evidence (a reset could not repeat the old output), so it becomes None with the reason;
    None from the metric (silent reset reference: reset and mute look the same) is kept."""
    r = m.restarted(x, reset_reference(x, geo, marks, subject, edit), cont, RATE, edit, late=late)
    if r.state is False and changes_subject:
        return None, ('not testable: the edit changes the subject\'s own sound, so a reset cannot '
                      'repeat its reset output (' + r.note + ')')
    return r.state, r.note


def applygraph_reply(reply: dict, mark: mk.Mark, gen_before: str) -> dict:
    """Require the marked E1a reply shape; no invented metric/pass threshold."""
    if mark.type != 'applyGraph' or mark.re != 'edit':
        raise ValueError('applyGraph requires its own edit mark')
    if mark.ok is not reply.get('ok') or mark.gen != reply.get('gen'):
        raise ValueError('applyGraph mark and reply disagree')
    if not reply['ok']:
        return dict(ok=False, code=reply.get('code'), path=None,
                    replaced=None, unapplied=None)
    result = reply.get('result')
    if not isinstance(result, dict) or result.get('path') not in ('live', 'restart'):
        raise ValueError('applyGraph success lacks a valid path')
    replaced, unapplied = result.get('replaced'), result.get('unapplied')
    positive_id = lambda n: type(n) is int and 1 <= n <= 0xffffffff
    if not isinstance(replaced, list) or not all(positive_id(n) for n in replaced):
        raise ValueError('applyGraph replaced requires numeric module IDs')
    if not isinstance(unapplied, list) or not all(
            isinstance(item, dict) and positive_id(item.get('moduleId')) and
            isinstance(item.get('paramId'), str) and bool(item['paramId'])
            for item in unapplied):
        raise ValueError('applyGraph unapplied requires moduleId and paramId')
    if not gen_before.isascii() or not gen_before.isdigit() or int(reply['gen']) <= int(gen_before):
        raise ValueError('accepted applyGraph must advance gen')
    return dict(ok=True, code=None, path=result['path'],
                replaced=replaced, unapplied=unapplied)


def buffer_reply(reply, mark, rebuild, patch):
    """A62 wire evidence: distinguish absence from an empty rebuild list."""
    if (mark.type != 'setBufferFrames' or mark.re != 'edit' or
            mark.ok is not reply.get('ok') or mark.gen != reply.get('gen')):
        raise ValueError('buffer reply disagrees with marked command')
    result = reply.get('result')
    present = isinstance(result, dict) and 'freshModules' in result
    fresh = result['freshModules'] if present else None
    if reply['ok']:
        if present != rebuild:
            raise ValueError('freshModules presence disagrees with A62 buffer path')
        if present:
            ids = {m['id']: m['module'] for m in patch['modules']}
            if not isinstance(fresh, list) or len(fresh) > 64:
                raise ValueError('invalid freshModules list')
            seen = set()
            for item in fresh:
                if (not isinstance(item, dict) or type(item.get('moduleId')) is not int or
                        item['moduleId'] not in ids or item.get('module') != ids[item['moduleId']] or
                        item['moduleId'] in seen):
                    raise ValueError('invalid or duplicate fresh module identity')
                seen.add(item['moduleId'])
    return dict(ok=reply['ok'], code=reply.get('code'),
                fresh_modules_present=present, fresh_modules=fresh)


def buffer_activity(x, edit, late):
    """Witness activity, not a new gate: existing -80 dBFS floor and CN time intervals."""
    pre, post = x[edit - RATE // 2:edit], x[late:late + RATE]
    if len(pre) != RATE // 2 or len(post) != RATE or not all(math.isfinite(v) for v in (*pre, *post)):
        raise ValueError('unavailable activity window')
    floor = 10 ** (m.SILENCE_DBFS / 20)
    return dict(pre_peak_fs=max(map(abs, pre)), post_peak_fs=max(map(abs, post)),
                pre_sounding_samples=sum(abs(v) >= floor for v in pre),
                post_sounding_samples=sum(abs(v) >= floor for v in post),
                pre_min_fs=min(pre), pre_max_fs=max(pre),
                post_min_fs=min(post), post_max_fs=max(post))


def compare_control(x, cont, name, edit, late) -> dict:
    actual, expected = m.paired_window(x, cont, RATE, edit, late)
    first = next((i - RATE for i, (a, b) in enumerate(zip(actual, expected)) if a != b), None)
    compared = dict(samples=len(actual), identical=first is None, first_mismatch_from_edit=first,
                    max_abs_difference=max(abs(a - b) for a, b in zip(actual, expected)))
    if name in ('tone', 'tail', 'held_note', 'slew'):
        compared.update({key: finite(value) for key, value in m.paired_levels(actual, expected, RATE).items()})
    if name in ('tone', 'tail', 'held_note', 'clock', 'slew'):
        compared['jump_ratio'] = m.paired_steps(actual, expected)
    if name == 'slip_tone':
        a = m.time_slip_tone_ms(x, RATE, edit, probe.SLIP_HZ, late)
        b = m.time_slip_tone_ms(cont, RATE, edit, probe.SLIP_HZ, late)
        period = 1000 / probe.SLIP_HZ
        compared['time_slip_ms'] = None if a is None or b is None else (a - b + period / 2) % period - period / 2
    if name == 'clock':
        _, hi = m.window(x, RATE, edit, late)
        starts = [[i for i in m.onsets(signal[:hi], RATE, 0.1) if i >= edit] for signal in (x, cont)]
        offsets = [(a - b) * 1000 / RATE for a, b in zip(*starts)]
        compared['time_slip_ms'] = max(offsets, key=abs, default=None)
        compared['edited_onsets'], compared['control_onsets'] = map(len, starts)
    return compared


def analyse(run: eng.Run, ref: eng.Run, subject: int | None, changes_subject: bool = False,
            buffer_case: dict | None = None) -> dict:
    mark = mk.locate(run.marks, 'edit')
    geo = mk.Geometry.of(run.segments)
    win = mk.edit_window(geo, mark)
    x_all, r_all = channels(run), channels(ref)
    edit, late = win.edit, win.late
    reply = run.replies['edit']
    if mark.ok is not reply.get('ok') or mark.gen != reply.get('gen'):
        raise ValueError('edit reply disagrees with capture marks')
    out = dict(ok=reply['ok'], code=reply.get('code'), message=reply.get('message'),
               all_marks=[m_._asdict() for m_ in run.marks], reference_marks=[m_._asdict() for m_ in ref.marks],
               gen_before=mk.locate(run.marks, 'note').gen, gen_after=mark.gen,
               b0=mark.b0, b1=mark.b1, bracket_blocks=win.width_blocks,
               segments=[[s.block, s.blocks] for s in run.segments], witnesses={})
    if mark.type == 'applyGraph':
        out['applygraph'] = applygraph_reply(reply, mark, out['gen_before'])
    witnesses = dict(probe.WITNESS)
    if buffer_case is not None:
        out['buffer'] = buffer_reply(reply, mark, buffer_case['buffer_rebuild'],
                                     buffer_case.get('setup') or probe.base())
        out['reference_segments'] = [[s.block, s.blocks] for s in ref.segments]
        witnesses.update(buffer_case.get('extra_witnesses', {}))
        if reply['ok']:
            expected = buffer_case['cmd'][1]['frames']
            if run.segments[0].block != BLOCK or run.segments[-1].block != expected:
                raise ValueError('buffer capture lacks the requested segment geometry')
            if any(s.block != BLOCK for s in ref.segments):
                raise ValueError('no-edit buffer control changed block geometry')
    for ch, name in [*witnesses.items(), *([(subject, 'subject')] if subject is not None else [])]:
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
        if cont is not None and name != 'subject':
            put('control_comparison', compare_control, x, cont, name, edit, late)
        if buffer_case is not None and name in ('held_note', 'tail', 'slew'):
            activity, err = safe(buffer_activity, x, edit, late)
            if err:
                errors['activity'] = err
            else:
                row['activity'] = activity
            if cont is not None:
                activity, err = safe(buffer_activity, cont, edit, late)
                if err:
                    errors['control_activity'] = err
                else:
                    row['control_activity'] = activity
        if name == 'slip_tone':
            put('time_slip_ms', m.time_slip_tone_ms, x, RATE, edit, probe.SLIP_HZ, late)
        elif name == 'subject':
            if cont is not None:
                r, e = safe(subject_restart, x, cont, geo, run.marks, subject, edit, late, changes_subject)
                if e:
                    errors['restarted'] = e
                else:
                    row['restarted'], row['restarted_note'] = r
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


def binary_hash(binary: str) -> str:
    digest = hashlib.sha256()
    with Path(binary).open('rb') as src:
        for part in iter(lambda: src.read(1024 * 1024), b''):
            digest.update(part)
    return digest.hexdigest()


def provenance(binary: str | None = None, built_head: str | None = None,
               engine_source: Path = ROOT) -> dict:
    def sh(*args, cwd=ROOT):
        return subprocess.run(args, capture_output=True, text=True, cwd=cwd).stdout.strip()
    cpu = ''
    try:
        cpu = next((l.split(':', 1)[1].strip() for l in open('/proc/cpuinfo') if l.startswith('model name')), '')
    except OSError:
        pass
    now = datetime.datetime.now(datetime.timezone.utc)
    head = sh('git', 'rev-parse', 'HEAD', cwd=engine_source)
    if built_head and built_head != head:
        raise ValueError(f'built source pin {built_head} does not match checkout {head}')
    return dict(lab_commit=head, built_head_claim=built_head,
                harness_commit=sh('git', 'rev-parse', 'HEAD'),
                harness_dirty=bool(sh('git', 'status', '--porcelain', '--', 'bench/continuity')),
                engine_sha256=binary_hash(binary) if binary else None,
                toolchain=dict(cmake=sh('cmake', '--version').splitlines()[:1],
                               cxx=sh('c++', '--version').splitlines()[:1]),
                dirty=bool(sh('git', 'status', '--porcelain', cwd=engine_source)),
                machine=dict(system=platform.system(), arch=platform.machine(), cpu=cpu,
                             python=platform.python_version(), kind='cloud container, null sink, devices off'),
                date_utc=now.strftime('%Y-%m-%dT%H:%MZ'), rate=RATE, block=BLOCK)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--engine', required=True)
    ap.add_argument('--repeats', type=int, default=3)
    ap.add_argument('--only', nargs='*')
    ap.add_argument('--out', default=str(ROOT / 'facts' / 'dsp' / 'edit_continuity'))
    ap.add_argument('--keep', help='directory to keep every raw capture and marks file (for an artifact)')
    ap.add_argument('--built-head', help='assert sidecar built at this exact checkout SHA')
    ap.add_argument('--engine-source', type=Path, default=ROOT,
                    help='separate engine source checkout for an exact-head capture')
    a = ap.parse_args(argv)
    cases = [*probe.edits(), probe.latency_probe(probe.base())]
    # Keep the legacy default case inventory unchanged; A62 is explicit.
    if a.only:
        cases += probe.buffer_edits()
    known = {e['name'] for e in cases}
    if a.only and (unknown := set(a.only) - known):
        ap.error('unknown edit(s): ' + ', '.join(sorted(unknown)))
    if a.repeats < 1:
        ap.error('--repeats must be positive')
    source = provenance(a.engine, a.built_head, a.engine_source)
    edits = [e for e in cases if not a.only or e['name'] in a.only]
    per_edit = {e['name']: [] for e in edits}
    artifact_rows = {}

    for rep in range(a.repeats):
        keep = lambda tag: str(Path(a.keep) / f'r{rep + 1}-{tag}') if a.keep else None
        references = {}
        for e in edits:
            print(f'repeat {rep + 1}/{a.repeats}: {e["name"]}', flush=True)
            setup = e.get('setup')
            setup_key = json.dumps(setup, sort_keys=True)
            if setup_key not in references:
                references[setup_key] = eng.run(a.engine, script(None, setup),
                                                keep=keep(f'reference-{len(references)}'),
                                                expected_head=a.built_head)
            ref = references[setup_key]
            run = eng.run(a.engine, script(e, setup), keep=keep(e['name'].replace(' ', '_')),
                          expected_head=a.built_head)
            per_edit[e['name']].append(analyse(
                run, ref, e['subject'], e.get('changes_subject', False),
                e if 'buffer_rebuild' in e else None))
            if a.keep:
                artifact_rows.setdefault(e['name'], []).append(dict(
                    repeat=rep + 1, edited=run.artifacts, reference=ref.artifacts))

    rows = []
    for e in edits:
        reps = per_edit[e['name']]
        names = list(reps[0]['witnesses'])
        for w in names:
            keys = sorted({k for r in reps for k in r['witnesses'][w]
                           if k not in ('alignment', 'not_measured', 'restarted_note', 'divergence',
                                        'control_comparison', 'activity', 'control_activity')})
            row = dict(edit=e['name'], command=e['cmd'][0], witness=w,
                       channel=e['subject'] if w == 'subject' else next(
                           c for c, n in {**probe.WITNESS, **e.get('extra_witnesses', {})}.items() if n == w),
                       replies=[dict(ok=r['ok'], code=r['code']) for r in reps],
                       bracket_blocks=worst([r['bracket_blocks'] for r in reps], 'bracket_blocks'),
                       worst={k: worst([r['witnesses'][w].get(k) for r in reps], k) for k in keys},
                       repeats=[r['witnesses'][w] for r in reps],
                       marks=[dict(b0=r['b0'], b1=r['b1'], gen_before=r['gen_before'], gen_after=r['gen_after'],
                                   segments=r['segments'], run=r['all_marks'], reference=r['reference_marks'])
                              for r in reps])
            if e.get('report_only'):
                row['report_only'] = True
            if e['cmd'][0] == 'applyGraph':
                row['applygraph_results'] = [r['applygraph'] for r in reps]
            if 'buffer_rebuild' in e:
                row['buffer_results'] = [r['buffer'] for r in reps]
                for entry, rep in zip(row['marks'], reps):
                    entry['reference_segments'] = rep['reference_segments']
            rows.append(row)
    doc = dict(provenance=source, repeats=a.repeats,
               method='proposals/0005 sections 4–5, R7 and A50; bench/continuity/DESIGN.md',
               rows=rows, unsupported=probe.UNSUPPORTED, artifacts=artifact_rows)
    out = Path(a.out)
    if out.with_suffix('.json').exists() or out.with_suffix('.md').exists():
        raise ValueError('refusing to overwrite historical facts: supply a new --out path; '
                         'merge fresh rows only after measured capture review')
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
    paired_cols = ['silence_ms', 'dip_db', 'time_slip_ms', 'jump_ratio']
    lines += ['', '## Aligned no-edit comparison by repeat', '',
              '| edit | witness | repeat | report only | identical | first mismatch (samples) | '
              + ' | '.join(paired_cols) + ' |', '|' + '---|' * (6 + len(paired_cols))]
    for row in doc['rows']:
        for i, repeat in enumerate(row['repeats'], 1):
            comparison = repeat.get('control_comparison')
            if comparison is None:
                continue
            fields = [row['edit'], row['witness'], i, 'yes' if row.get('report_only') else '',
                      comparison['identical'], comparison['first_mismatch_from_edit']]
            fields.extend(comparison.get(key) for key in paired_cols)
            lines.append('| ' + ' | '.join(map(fmt, fields)) + ' |')
    buffer_rows = [row for row in doc['rows'] if 'buffer_results' in row]
    if buffer_rows:
        lines += ['', '## A62 buffer reply and witness activity', '',
                  'Fresh modules are the actual host-reported uncarried instances. An absent field '
                  'is not an empty rebuild list. See JSON for all geometry and exact witness ranges.', '',
                  '| edit | repeat | freshModules |', '|---|---|---|']
        for row in buffer_rows:
            if row['witness'] != 'tone':
                continue
            for i, result in enumerate(row['buffer_results'], 1):
                value = result['fresh_modules'] if result['fresh_modules_present'] else 'absent'
                lines.append(f'| {row["edit"]} | {i} | {value} |')
        lines += ['', '| edit | witness | repeat | pre sounding samples | post sounding samples | control pre | control post |',
                  '|---|---|---|---|---|---|---|']
        for row in buffer_rows:
            for i, rep in enumerate(row['repeats'], 1):
                if 'activity' not in rep and 'control_activity' not in rep:
                    continue
                fields = [row['edit'], row['witness'], i]
                for key in ('activity', 'control_activity'):
                    fields.extend(rep.get(key, {}).get(k) for k in ('pre_sounding_samples', 'post_sounding_samples'))
                lines.append('| ' + ' | '.join(map(fmt, fields)) + ' |')
    lines += ['', '## Not measured (not supported today)', '']
    lines += [f'- {u["name"]}: {u["reason"]}' for u in doc['unsupported']]
    return '\n'.join(lines) + '\n'


if __name__ == '__main__':
    main()
