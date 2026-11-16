# SPDX-License-Identifier: GPL-3.0-only
"""MIDI name selection checks; no audio or MIDI devices are opened."""
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import run


class MidiPortTests(unittest.TestCase):
    def test_numbered_output_and_engine_input_can_differ(self):
        args = run.parser().parse_args([
            "--confirm-midi",
            "--midi-port", "Wirescape Bench 2",
            "--engine-midi-port", "Wirescape Bench 1",
        ])
        device = {"id": "bench-input", "name": "Wirescape Bench 1"}
        with patch.dict(sys.modules, {"mido": Mock()}) as modules:
            with patch.object(run.os, "name", "nt"):
                source = run.MidiSource(args, Mock())
                source.start()
            modules["mido"].open_output.assert_called_once_with("Wirescape Bench 2")
        self.assertEqual(run.engine_midi_device([device], args.engine_midi_port), device)

    def test_engine_input_override_is_optional(self):
        self.assertIsNone(run.parser().parse_args([]).engine_midi_port)
        device = {"id": "bench-input", "name": "Wirescape Bench"}
        self.assertEqual(run.engine_midi_device([device], "Wirescape Bench"), device)

    def test_missing_engine_input_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "--engine-midi-port"):
            run.engine_midi_device([], "Wirescape Bench 1")

    def test_ambiguous_engine_input_is_rejected(self):
        devices = [{"id": "a", "name": "Wirescape Bench 1"},
                   {"id": "b", "name": "Wirescape Bench 2"}]
        with self.assertRaisesRegex(RuntimeError, "not uniquely visible"):
            run.engine_midi_device(devices, "Wirescape Bench")


if __name__ == "__main__":
    unittest.main()
