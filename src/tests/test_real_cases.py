"""Real-case checks prevent partial tracking being promoted into full-model claims."""
import sys,unittest
from pathlib import Path
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from real_cases import calculate

def fixture():
    rows=[]
    for frame in range(3):
        for pid,team,shirt,x in [(0,None,None,10),(1,'attack',11,10+frame),(2,'defense',None,12+frame)]:
            rows.append(dict(frame=frame,player=pid,team=team,player_num=shirt,x=x,y=50))
    return pd.DataFrame(rows)

class RealCaseTests(unittest.TestCase):
    def test_native_time_and_nominal_scaling(self):
        m,_,_,_=calculate(fixture(),11)
        self.assertAlmostEqual(m['duration_s'],.1)
        self.assertAlmostEqual(m['focus_path_nominal_m'],2.1)
        self.assertAlmostEqual(m['nearest_observed_defender_start_nominal_m'],2.1)
        self.assertEqual(m['source_native_hz'],20)
    def test_partial_coverage_never_invents_full_metrics(self):
        m,_,_,_=calculate(fixture(),11)
        for key in ['xg','control_equivalent_area_m2','candidate_receiving_window_s']:self.assertIsNone(m[key])
        self.assertFalse(m['coverage']['complete_22_player_tracking'])
        self.assertFalse(m['coordinate_assumption']['actual_pitch_calibration_verified'])
    def test_source_frame_gap_rejected(self):
        df=fixture();df=df[df.frame!=1]
        with self.assertRaises(ValueError):calculate(df,11)
    def test_duplicate_player_frame_rejected(self):
        df=fixture();df=pd.concat([df,df.iloc[[0]]])
        with self.assertRaises(ValueError):calculate(df,11)

if __name__=='__main__':unittest.main()
