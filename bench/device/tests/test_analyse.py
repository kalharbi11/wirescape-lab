# SPDX-License-Identifier: GPL-3.0-only
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
from analyse import detect_clicks,detect_dropouts,detect_stuck_notes,align_reference

RATE=48000


class DetectorTests(unittest.TestCase):
    def test_click_impulse(self):
        x=np.zeros(RATE//2)
        x[6000:]=.08*np.sin(2*np.pi*440*np.arange(len(x)-6000)/RATE)
        x[10000]+=.95
        self.assertTrue(any(abs(t-10000/RATE)<.003 for t in detect_clicks(x,RATE)))

    def test_no_click_on_tone(self):
        x=.1*np.sin(2*np.pi*440*np.arange(RATE)/RATE)
        self.assertEqual(detect_clicks(x,RATE),[])

    def test_zero_run_dropout(self):
        x=.1*np.sin(2*np.pi*440*np.arange(RATE)/RATE)
        x[20000:21000]=0
        self.assertTrue(any(abs(d["start_s"]-20000/RATE)<.002 for d in detect_dropouts(x,RATE)))

    def test_legitimate_silence(self):
        x=np.r_[np.zeros(RATE//5),.1*np.sin(2*np.pi*440*np.arange(RATE//5)/RATE),np.zeros(RATE//5)]
        self.assertEqual(detect_dropouts(x,RATE),[])

    def test_stuck_note(self):
        t=np.arange(RATE*2)/RATE
        x=.1*np.sin(2*np.pi*440*t)
        self.assertTrue(detect_stuck_notes(x,RATE,1.,release_s=.2))

    def test_released_note(self):
        t=np.arange(RATE*2)/RATE
        x=.1*np.sin(2*np.pi*440*t)
        x[int(1.1*RATE):]=0
        self.assertFalse(detect_stuck_notes(x,RATE,1.,release_s=.2))

    def test_alignment(self):
        np.random.seed(7)
        ref=np.random.randn(RATE//3)*.02
        cap=np.r_[np.zeros(213),ref,np.zeros(200)]
        data=align_reference(ref,cap,RATE)
        self.assertTrue(data["available"])
        self.assertAlmostEqual(data["latency_ms"],213/RATE*1000,places=2)
        self.assertGreater(data["correlation"],.99)


if __name__=="__main__":
    unittest.main()
