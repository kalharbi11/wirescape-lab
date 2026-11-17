# SPDX-License-Identifier: GPL-3.0-only
"""M2 #139: synthetic applyGraph routing, mark/reply, provenance and capture guards.

No sidecar subprocess or physical audio/MIDI/LAN work occurs in these tests.
"""
from __future__ import annotations

import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch as mock_patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import engine as eng
import marks as mk
import probe
import run


class ApplyGraphVariants(unittest.TestCase):
    def test_all_eight_a2_edit_forms_and_historical_cases(self):
        edits = probe.edits()
        self.assertEqual(len(edits), 29)
        self.assertEqual(len({e['name'] for e in edits}), 29)
        self.assertEqual(len([e for e in edits if e['cmd'][0] == 'loadGraph']), 8)
        variant = {e['name']: e for e in edits if e['cmd'][0] == 'applyGraph'}
        self.assertEqual(set(variant), {'applyGraph ' + k for k in probe.APPLYGRAPH_KINDS})
        self.assertEqual(probe.UNSUPPORTED, [])
        for name, edit in variant.items():
            with self.subTest(name=name):
                self.assertEqual(edit['cmd'][0], 'applyGraph')
                patch_doc = edit['cmd'][1]['patch']
                setup_doc = edit['setup']
                self.assertEqual(patch_doc['future_continuity'],
                                 setup_doc['future_continuity'])
                self.assertEqual(patch_doc['ui'], setup_doc['ui'])
                self.assertEqual([s.label for s in run.script(edit, setup_doc)
                                  if s.method], ['load', 'note', 'edit'])
                self.assertEqual(run.script(edit, setup_doc)[-1].method, 'applyGraph')
                self.assertEqual(probe.base()['modules'][0]['id'], 1)

    def test_only_one_expected_change_and_restored_id(self):
        variants = {e['name'].split(' ', 1)[1]: e for e in probe.edits()
                    if e['cmd'][0] == 'applyGraph'}
        before = variants['identical']['setup']
        self.assertEqual(variants['identical']['cmd'][1]['patch'], before)
        for kind in ('Groove steps', 'Groove length', 'voice count',
                     'OSC In row', 'one parameter', 'deleted module'):
            edit = variants[kind]
            self.assertEqual(edit['setup'], before, kind)
            self.assertNotEqual(edit['cmd'][1]['patch'], before, kind)
        restored = variants['restored module']
        self.assertNotIn(90, [m['id'] for m in restored['setup']['modules']])
        self.assertIn(90, [m['id'] for m in restored['cmd'][1]['patch']['modules']])
        self.assertEqual(len(before['connections']),
                         len(variants['deleted module']['cmd'][1]['patch']['connections']))
        self.assertEqual(before, copy.deepcopy(variants['identical']['setup']))


class MarkedResult(unittest.TestCase):
    MARK = mk.Mark('edit', 'applyGraph', True, '2', 800, 803)

    def test_live_restart_replaced_and_partial_unapplied(self):
        for path in ('live', 'restart'):
            reply = {'ok': True, 'gen': '2', 'result': {
                'path': path, 'replaced': [60],
                'unapplied': [{'moduleId': 60, 'paramId': 'run'}]}}
            got = run.applygraph_reply(reply, self.MARK, '1')
            self.assertEqual(got['path'], path)
            self.assertEqual(got['replaced'], [60])
            self.assertEqual(got['unapplied'], [{'moduleId': 60, 'paramId': 'run'}])
            self.assertEqual(self.MARK.width, 4)  # b1 + 1 - b0, not wall time

    def test_refused_request_records_code_and_no_graph_result(self):
        mark = mk.Mark('edit', 'applyGraph', False, '1', 800, 800)
        got = run.applygraph_reply({'ok': False, 'gen': '1', 'code': 'refused'},
                                   mark, '1')
        self.assertEqual(got, dict(ok=False, code='refused', path=None,
                                   replaced=None, unapplied=None))
        self.assertEqual(mark.width, 1)

    def test_malformed_partial_replies_and_bad_generation_fail_closed(self):
        base = {'ok': True, 'gen': '2', 'result': {
            'path': 'live', 'replaced': [], 'unapplied': []}}
        mutants = [
            {'result': {'path': 'muted', 'replaced': [], 'unapplied': []}},
            {'result': {'path': 'live', 'unapplied': []}},
            {'result': {'path': 'live', 'replaced': [True], 'unapplied': []}},
            {'result': {'path': 'live', 'replaced': [], 'unapplied': [{'moduleId': 1}]}},
            {'result': {'path': 'live', 'replaced': [], 'unapplied': 'bad'}},
            {'gen': '1'},
        ]
        for changes in mutants:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                run.applygraph_reply({**base, **changes}, self.MARK, '1')
        with self.assertRaises(ValueError):
            run.applygraph_reply(base, self.MARK._replace(ok=False), '1')
        with self.assertRaises(ValueError):
            run.applygraph_reply(base, self.MARK._replace(re='unknown'), '1')
        with self.assertRaises(ValueError):
            run.applygraph_reply(base, self.MARK, '2')

    def test_shared_marks_always_define_alignment_bracket(self):
        a = mk.Mark('load', 'loadGraph', True, '1', 60, 64)
        b = mk.Mark('load', 'loadGraph', True, '1', 58, 62)
        edit = self.MARK
        al = mk.align_offset([a, mk.Mark('note', 'noteOn', True, '1', 450, 450), edit],
                             [b, mk.Mark('note', 'noteOn', True, '1', 449, 449)], 'load')
        self.assertLessEqual(al.lo, al.offset)
        self.assertLessEqual(al.offset, al.hi)
        self.assertEqual(al.uncertainty, a.width + b.width)


class HistoricalFacts(unittest.TestCase):
    def test_original_119_rows_and_source_pin_remain_intact(self):
        root = Path(__file__).resolve().parents[3]
        doc = __import__('json').loads(
            (root / 'facts/dsp/edit_continuity.json').read_text(encoding='utf-8'))
        self.assertEqual(len(doc['rows']), 119)
        self.assertEqual(doc['provenance']['lab_commit'],
                         '4b6a45a72d83c2fa28aa455d9fecc91ee5d862ad')
        self.assertEqual(doc['repeats'], 3)
        self.assertEqual(len(doc['unsupported']), 8)
        self.assertTrue(all(x['name'].startswith('applyGraph ') for x in doc['unsupported']))
        self.assertIn('Lab commit', (root / 'facts/dsp/edit_continuity.md')
                      .read_text(encoding='utf-8'))


class RunnerGuards(unittest.TestCase):
    def test_capability_absent_aborts_before_any_command(self):
        class NoApply:
            sent = False
            hello = {'type': 'hello', 'capabilities': []}
            def __init__(self, *args, **kwargs): pass
            def statuses(self, *args): raise AssertionError('must not pace an unsupported edit')
            def close(self): return 'failed=0'
        script = run.script(next(e for e in probe.edits()
                                 if e['name'] == 'applyGraph identical'), None)
        with mock_patch.object(eng, 'Engine', NoApply):
            with self.assertRaisesRegex(RuntimeError, 'does not advertise applyGraph'):
                eng.run('/not-executed', script)

    def test_binary_hash_is_actual_bytes_without_absolute_path(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'engine'
            p.write_bytes(b'not a real engine, never executed')
            self.assertEqual(run.binary_hash(str(p)),
                             hashlib.sha256(p.read_bytes()).hexdigest())


if __name__ == '__main__':
    unittest.main()
