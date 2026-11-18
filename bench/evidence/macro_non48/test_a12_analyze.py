#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Pure A12 classifier boundary + negative cases; no artifacts or rendering."""
import math
import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
import a12_analyze as a


def spectrum(peak=1.,rival=0.5,global_peak=5.,near_rival=0.):
    mag=np.zeros(101,dtype=float)
    mag[44]=peak      # 440 Hz selected, target 440 Hz
    mag[39]=rival     # outside +/-3 of selected, inside 80-120% target
    mag[46]=near_rival # ignored if inside +/-3
    mag[80]=global_peak # global maximum is outside 80-120%
    hz=np.arange(101,dtype=float)*10
    return mag,hz

class KnownAnswer(unittest.TestCase):
    def test_source_pins_thresholds_and_model_labels(self):
        self.assertEqual(a.RUN,44229365015)
        self.assertEqual(len(a.MODEL_NAMES),24)
        self.assertEqual(a.MODEL_NAMES[6],'String Machine')
        self.assertEqual(a.MODEL_NAMES[7],'Chiptune')
        self.assertEqual(a.MODEL_NAMES[12],'Additive')
        self.assertEqual(a.MODEL_NAMES[15],'Speech')
        self.assertEqual(a.DOMINANCE_DB,1.0)
        self.assertEqual(a.MAX_DOWN_DB,40.)
        self.assertEqual(a.PITCH_TOLERANCE_CENTS,2.)
        self.assertEqual(len(a.BASE_SHA),40)
        self.assertEqual(len(a.HEAD_SHA),40)

    def test_both_margins_defined_and_no_estimator_substitution(self):
        mag,hz=spectrum()
        row=a.classify_spectrum(mag,hz,440.)
        self.assertTrue(row['pitch_defined'])
        self.assertEqual(row['selected_fft_bin'],44)
        self.assertAlmostEqual(row['dominance_db'],20*math.log10(2),places=10)
        self.assertAlmostEqual(row['level_vs_global_db'],20*math.log10(1/5),places=10)
        self.assertAlmostEqual(row['dominance_margin_vs_1dB'],20*math.log10(2)-1,places=10)
        self.assertAlmostEqual(row['level_margin_vs_minus40dB'],40-20*math.log10(5),places=10)
        self.assertEqual(a.pitch_decision(row,-2.0),'pass')
        self.assertEqual(a.pitch_decision(row,2.0),'pass')
        self.assertEqual(a.pitch_decision(row,2.00001),'fail')
        self.assertEqual(a.pitch_decision(row,float('nan')),'fail')
        self.assertEqual(a.pitch_decision(row,None),'fail')

    def test_excluded_near_bins_are_not_competitors(self):
        mag,hz=spectrum(rival=0.05,near_rival=.999999)
        row=a.classify_spectrum(mag,hz,440.)
        self.assertTrue(row['pitch_defined'])
        self.assertAlmostEqual(row['largest_competing_magnitude'],0.05)

    def test_dominance_negative_just_below_one_db(self):
        mag,hz=spectrum(rival=10**(-0.99/20))
        row=a.classify_spectrum(mag,hz,440.)
        self.assertFalse(row['pitch_defined'])
        self.assertEqual(row['reason'],'dominance_below_1dB')
        self.assertLess(row['dominance_margin_vs_1dB'],0)
        self.assertGreater(row['level_margin_vs_minus40dB'],0)
        self.assertEqual(a.pitch_decision(row,2000),'pitch_not_defined')

    def test_boundary_one_db_inclusive(self):
        mag,hz=spectrum(rival=10**(-1/20))
        row=a.classify_spectrum(mag,hz,440.)
        self.assertTrue(row['pitch_defined'])
        self.assertAlmostEqual(row['dominance_margin_vs_1dB'],0,places=10)

    def test_level_negative_below_minus_forty_db(self):
        mag,hz=spectrum(rival=0.5,global_peak=10**(40.01/20))
        row=a.classify_spectrum(mag,hz,440.)
        self.assertFalse(row['pitch_defined'])
        self.assertEqual(row['reason'],'level_more_than_40dB_below_global')
        self.assertGreater(row['dominance_margin_vs_1dB'],0)
        self.assertLess(row['level_margin_vs_minus40dB'],0)

    def test_level_boundary_minus_forty_inclusive(self):
        mag,hz=spectrum(global_peak=100)
        row=a.classify_spectrum(mag,hz,440.)
        self.assertTrue(row['pitch_defined'])
        self.assertAlmostEqual(row['level_margin_vs_minus40dB'],0,places=10)

    def test_dc_excluded_global_max(self):
        mag,hz=spectrum(global_peak=5)
        mag[0]=1e10
        row=a.classify_spectrum(mag,hz,440.)
        self.assertTrue(row['pitch_defined'])
        self.assertEqual(row['global_max_excluding_dc'],5)

    def test_silence_does_not_certify_pitch(self):
        mag,hz=spectrum(peak=0,rival=0,global_peak=0)
        row=a.classify_spectrum(mag,hz,440.)
        self.assertFalse(row['pitch_defined'])
        self.assertIsNone(row['dominance_margin_vs_1dB'])
        self.assertIsNone(row['level_margin_vs_minus40dB'])
        self.assertEqual(a.pitch_decision(row,0),'pitch_not_defined')

    def test_corrupted_spectrum_refused(self):
        mag,hz=spectrum()
        mag[44]=float('nan')
        with self.assertRaises(ValueError):a.classify_spectrum(mag,hz,440.)

    def test_original_pcm_is_left_channel_last_eighty_percent(self):
        pcm=np.zeros((2*48000,2),dtype='<f4')
        # Deterministic 440Hz source, right channel at distinct frequency must not interfere.
        frame=np.arange(len(pcm))
        pcm[:,0]=(0.5*np.cos(2*np.pi*440*frame/48000)).astype('float32')
        pcm[:,1]=(0.25*np.cos(2*np.pi*800*frame/48000)).astype('float32')
        result=a.classify_pcm_48(pcm.tobytes(),440)
        self.assertTrue(result['pitch_defined'])
        self.assertEqual(result['selected_fft_bin'],int(440/(48000/(len(pcm)*.8))))
        with self.assertRaisesRegex(ValueError,'size mismatch'):
            a.classify_pcm_48(pcm.tobytes()[:-8],440)

if __name__=='__main__':unittest.main()
