# SPDX-License-Identifier: GPL-3.0-only
"""Owner record: redaction, parsing and summary stay device-off and private."""
import getpass
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location('owner_record', ROOT / 'tools' / 'owner_record.py')
owner_record = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(owner_record)


class OwnerRecordTests(unittest.TestCase):
    def test_redacts_home_and_repo(self):
        text = owner_record.redact(f'{Path.home()}/x and {owner_record.ROOT}/y')
        self.assertNotIn(str(Path.home()), text)
        if len(getpass.getuser()) >= 3:
            self.assertNotIn(getpass.getuser(), text)

    def test_probe_line_parsed(self):
        line = 'noise\nmodule_cpu_probe {"render_ns": {"max": 1, "p99": 1}}\n'
        self.assertEqual(owner_record.probe_json(line)['render_ns']['max'], 1)
        with self.assertRaises(ValueError):
            owner_record.probe_json('nothing')

    def test_io_modules_are_not_probed(self):
        ids = owner_record.module_ids()
        self.assertIn('essentials.vco', ids)
        self.assertFalse([i for i in ids if i.startswith(owner_record.SKIP_PREFIXES)])

    def test_summary_lists_failures(self):
        meta = {'git': {'sha': 'a' * 40, 'dirty': False}, 'tier': 'quick', 'started_utc': 's',
                'finished_utc': 'f', 'system': {'os': 'Linux', 'machine': 'aarch64', 'release': 'r'}}
        steps = [{'name': 'ctest', 'status': 'failed', 'seconds': 1},
                 {'name': 'module_cpu.essentials.vco', 'status': 'passed', 'seconds': 1,
                  'result': {'render_ns': {'max': 1333333, 'p99': 266666}, 'allocations': 0, 'faults': 0}}]
        text = owner_record.summarize(meta, steps)
        self.assertIn('**Failed:** ctest', text)
        self.assertIn('worst 50.0% of period', text)

    def test_tiers_never_pass_device_flags(self):
        source = (ROOT / 'tools' / 'owner_record.py').read_text(encoding='utf-8')
        for flag in ('--confirm-audio', '--confirm-midi', '--confirm-lan'):
            self.assertNotIn(f"'{flag}'", source)


if __name__ == '__main__':
    unittest.main()
