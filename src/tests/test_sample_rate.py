"""Ensure sample-rate changes affect tracking rather than just display labels."""
import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'Scripts'))
from run_example_suite import fixture

class SampleRateTests(unittest.TestCase):
    def test_default_is_50_hz_with_301_synchronized_samples(self):
        home,away,_,meta=fixture(0)
        self.assertEqual(meta['sample_rate_hz'],50)
        self.assertEqual(meta['sample_interval_s'],.02)
        self.assertEqual(len(home),301)
        np.testing.assert_allclose(np.diff(home['Time [s]']),.02,atol=1e-8)
        np.testing.assert_array_equal(home['Time [s]'],away['Time [s]'])
        self.assertEqual(((home['Time [s]']>=0)&(home['Time [s]']<=3.48)).sum(),175)

    def test_shared_positions_match_25_hz_at_same_times(self):
        h50,a50,_,_=fixture(0,50)
        h25,a25,_,m25=fixture(0,25)
        self.assertEqual(m25['sample_rate_hz'],25)
        for hi,lo in [(h50,h25),(a50,a25)]:
            cols=[c for c in lo if c.endswith(('_x','_y'))]
            np.testing.assert_allclose(hi[cols].iloc[::2],lo[cols],atol=1e-10)

    def test_unknown_rate_rejected(self):
        with self.assertRaises(ValueError):fixture(0,30)

if __name__=='__main__':unittest.main()
