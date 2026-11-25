#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Device-off acceptance-session tests. Never launch an engine or open devices."""
import unittest
from unittest.mock import patch

import acceptance_session as runner


def audio(count=0, **changes):
    return dict(state="running", deviceId="owner-output", deviceName="owner-output",
                bufferFrames=256, sampleRate=48000, dropouts=count, **changes)


class AcceptanceTests(unittest.TestCase):
    def test_guard_refuses_without_confirm_before_spawn(self):
        with patch("subprocess.Popen") as spawn:
            with self.assertRaises(SystemExit) as failure:
                runner.parse_args(["--device", "owner-output", "--buffer", "256"])
            self.assertNotEqual(failure.exception.code, 0)
            spawn.assert_not_called()

    def test_midi_requires_separate_confirm(self):
        with patch("subprocess.Popen") as spawn:
            with self.assertRaises(SystemExit):
                runner.parse_args(["--confirm-audio", "--midi", "--device",
                                   "owner-output", "--buffer", "256"])
            spawn.assert_not_called()

    def test_plan_counts_only_edits(self):
        edits = runner.edit_plan()
        self.assertEqual(len(edits), 100)
        self.assertEqual(len({edit["id"] for edit in edits}), 100)
        self.assertTrue({"setParam", "applyGraph", "connect", "disconnect",
                         "addModule", "removeModule"} <= {edit["type"] for edit in edits})
        self.assertFalse({"hello", "loadGraph", "panic", "setBufferFrames"} &
                         {edit["type"] for edit in edits})

    def test_count_only_successful_unique_correlated_edits(self):
        ledger = runner.EditLedger()
        ledger.record("edit-1", "setParam", {"re": "edit-1", "ok": True}, 2.5)
        self.assertEqual(ledger.completed, 1)
        with self.assertRaises(ValueError):
            ledger.record("edit-1", "setParam", {"re": "edit-1", "ok": True}, 1)
        with self.assertRaises(ValueError):
            ledger.record("edit-2", "setParam", {"re": "wrong", "ok": True}, 1)
        with self.assertRaises(ValueError):
            ledger.record("edit-2", "setParam", {"re": "edit-2", "ok": False}, 1)
        self.assertEqual(ledger.completed, 1)

    def test_deferred_counts_only_after_correlated_applied(self):
        ledger = runner.EditLedger()
        reply = {"re": "edit-1", "ok": False, "code": "busy",
                 "deferred": True, "deferId": "7"}
        with self.assertRaises(ValueError):
            ledger.record("edit-1", "applyGraph", reply, 1)
        event = {"type": "configDeferred", "deferId": "7", "moduleId": 2,
                 "outcome": "applied"}
        ledger.record("edit-1", "applyGraph", reply, 1,
                      completion=event, module_id=2)
        self.assertEqual(ledger.completed, 1)

    def test_xrun_is_cumulative_not_sum_of_samples(self):
        meter = runner.XrunCounter("owner-output", 256)
        for count in (0, 0, 1, 1, 3, 3):
            meter.observe(audio(count))
        self.assertEqual(meter.count, 3)

    def test_xrun_invalid_or_unavailable_never_zero(self):
        for bad in (None, True, -1, "0", 0.0):
            with self.subTest(bad=bad):
                meter = runner.XrunCounter("owner-output", 256)
                with self.assertRaises(ValueError):
                    meter.observe(audio(bad))
        meter = runner.XrunCounter("owner-output", 256)
        with self.assertRaises(ValueError):
            meter.observe({"state": "running", "deviceId": "owner-output",
                           "bufferFrames": 256})
        meter.observe(audio(2))
        with self.assertRaises(ValueError):
            meter.observe(audio(1))

    def test_device_loss_or_wrong_buffer_is_failure(self):
        for field, value in (("state", "device-lost"), ("deviceId", "other"),
                             ("bufferFrames", 128)):
            status = audio()
            status[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                runner.XrunCounter("owner-output", 256).observe(status)


if __name__ == "__main__":
    unittest.main()
