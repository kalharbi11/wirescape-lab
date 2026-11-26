# SPDX-License-Identifier: GPL-3.0-only
"""A62 E7 CN: distinct buffer cases, state witness and marked reply evidence."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import marks as mk  # noqa: E402
import probe  # noqa: E402
import run  # noqa: E402


class BufferCases(unittest.TestCase):
    def test_smaller_retains_existing_load_and_larger_adds_only_slew(self):
        small, large = probe.buffer_edits()
        self.assertEqual((small['name'], large['name']),
                         ('setBufferFrames smaller', 'setBufferFrames larger'))
        self.assertEqual(small['cmd'], ('setBufferFrames', {'frames': 128}))
        self.assertEqual(large['cmd'], ('setBufferFrames', {'frames': 512}))
        self.assertEqual(small.get('setup') or probe.base(), probe.base())
        self.assertEqual(small.get('extra_witnesses', {}), {})
        self.assertEqual(large['extra_witnesses'], {9: 'slew'})
        base, setup = probe.base(), large['setup']
        for key in ('modules', 'connections', 'outputs'):
            self.assertEqual(setup[key][:len(base[key])], base[key])
        added = {m['id']: m for m in setup['modules'][len(base['modules']):]}
        self.assertEqual(added[94]['module'], 'essentials.scale_offset')
        self.assertEqual(added[94]['parameters'], {'offset': 1})
        self.assertEqual(added[95]['module'], 'essentials.slew')
        self.assertEqual(added[95]['parameters'], {'rise': 10, 'fall': 10})
        self.assertEqual(added[96]['module'], 'essentials.output')
        self.assertIn(probe.sig(94, 'control', 95, 'control'), setup['connections'])
        self.assertIn(probe.sig(95, 'control', 96, 'audio'), setup['connections'])
        self.assertEqual(setup['outputs'][-1], {'module': 96, 'port': 'audio', 'bus_channel': 9})
        self.assertIn('setBufferFrames', [case['name'] for case in probe.edits()])


class BufferReply(unittest.TestCase):
    def setUp(self):
        self.mark = mk.Mark('edit', 'setBufferFrames', True, '3', 800, 803)
        self.patch = probe.base()

    def test_kept_engine_omits_fresh_modules(self):
        reply = {'ok': True, 'gen': '3', 'result': None}
        self.assertEqual(run.buffer_reply(reply, self.mark, False, self.patch),
                         {'ok': True, 'code': None, 'fresh_modules_present': False,
                          'fresh_modules': None})
        reply['result'] = {'freshModules': []}
        with self.assertRaises(ValueError):
            run.buffer_reply(reply, self.mark, False, self.patch)

    def test_rebuild_records_exact_identity_including_empty_list(self):
        reply = {'ok': True, 'gen': '3', 'result': {'freshModules': []}}
        self.assertEqual(run.buffer_reply(reply, self.mark, True, self.patch)['fresh_modules'], [])
        items = [{'moduleId': 11, 'module': 'host.keyboard'}]
        reply['result']['freshModules'] = items
        self.assertEqual(run.buffer_reply(reply, self.mark, True, self.patch)['fresh_modules'], items)
        for invalid in ([{'moduleId': 11, 'module': 'essentials.vco'}],
                        [{'moduleId': 999, 'module': 'host.keyboard'}],
                        items * 2, None):
            reply['result']['freshModules'] = invalid
            with self.assertRaises(ValueError):
                run.buffer_reply(reply, self.mark, True, self.patch)
        reply['result'] = None
        with self.assertRaises(ValueError):
            run.buffer_reply(reply, self.mark, True, self.patch)

    def test_reply_must_agree_with_marks(self):
        with self.assertRaises(ValueError):
            run.buffer_reply({'ok': True, 'gen': '4'}, self.mark, False, self.patch)


class BufferActivity(unittest.TestCase):
    def test_silence_is_distinguished_from_continuing_activity(self):
        edit, late = 2 * run.RATE, 2 * run.RATE + run.BLOCK
        signal = [0.25] * (late + run.RATE)
        result = run.buffer_activity(signal, edit, late)
        self.assertEqual(result['pre_peak_fs'], 0.25)
        self.assertEqual(result['post_peak_fs'], 0.25)
        self.assertEqual(result['pre_sounding_samples'], run.RATE // 2)
        self.assertEqual(result['post_sounding_samples'], run.RATE)
        muted = signal[:late] + [0.0] * run.RATE
        self.assertEqual(run.buffer_activity(muted, edit, late)['post_sounding_samples'], 0)


if __name__ == '__main__':
    unittest.main()
