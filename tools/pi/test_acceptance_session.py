#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Device-off acceptance-session tests. Never launch an engine or open devices."""
import unittest
from collections import deque
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


class FakeStream:
    """In-memory v0 stream, no process or hardware."""
    def __init__(self, *, fail_edit=None, dropouts=0, defer=True):
        self.gen = 0
        self.fail_edit = fail_edit
        self.dropouts = dropouts
        self.defer = defer
        self.inbox = deque([dict(v=0, session="fake", type="hello", protocol=0,
                                 engine={"sha": "a"*12}, capabilities=["configDeferred"],
                                 audio=audio())])

    def push(self, **fields):
        self.inbox.append(dict(v=0, session="fake", **fields))

    def receive(self, deadline):
        if self.inbox:
            return self.inbox.popleft()
        return dict(v=0, session="fake", type="status", gen=str(self.gen),
                    status={"audio": audio(self.dropouts)})

    def send(self, command, deadline):
        request_id = command["id"]
        if request_id == self.fail_edit:
            self.push(re=request_id, ok=False, code="invalid", gen=str(self.gen))
            return
        if request_id == "edit-2" and self.defer:
            self.push(re=request_id, ok=False, code="busy", deferred=True,
                      deferId="defer-1", gen=str(self.gen))
            self.gen += 1
            self.push(type="configDeferred", deferId="defer-1", moduleId=2,
                      outcome="applied", generation=str(self.gen))
            return
        if command["type"] in ("loadGraph", "applyGraph", "connect", "disconnect",
                               "addModule", "removeModule"):
            self.gen += 1
        self.push(re=request_id, ok=True, gen=str(self.gen))


class FakeStreamTests(unittest.TestCase):
    def session(self, **kwargs):
        return runner.Session(FakeStream(**kwargs),
                              runner.XrunCounter("owner-output", 256, 48000), "a"*40)

    def test_full_fake_stream_counts_one_hundred(self):
        with patch("subprocess.Popen") as spawn:
            session = self.session()
            session.execute()
            self.assertEqual(session.ledger.completed, 100)
            self.assertEqual(session.meter.count, 0)
            self.assertEqual(len(session.deferred_ids), 1)
            self.assertTrue(session.ledger.rows[1]["deferred"])
            spawn.assert_not_called()

    def test_refusal_and_xruns_do_not_pass(self):
        session = self.session(fail_edit="edit-5")
        with self.assertRaises(ValueError):
            session.execute()
        self.assertEqual(session.ledger.completed, 4)
        with self.assertRaises(ValueError):
            self.session(dropouts=1).execute()

    def test_missing_deferral_does_not_pass(self):
        with self.assertRaisesRegex(ValueError, "no actual correlated config deferral"):
            self.session(defer=False).execute()

    def test_dry_run_no_process_and_no_measured_claim(self):
        with patch("subprocess.Popen") as spawn:
            code, report = runner.run(runner.parse_args(["--dry-run", "--buffer", "256"]))
            self.assertEqual(code, 0)
            self.assertEqual(report["completed_edits"], 0)
            self.assertIsNone(report["xruns"])
            self.assertIsNone(report["visible_stutter"])
            self.assertEqual(len(report["planned_edits"]), 100)
            self.assertEqual(len(report["cn_transition_costs"]), 2)
            spawn.assert_not_called()


if __name__ == "__main__":
    unittest.main()
