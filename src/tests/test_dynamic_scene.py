import sys,unittest
from pathlib import Path
import pandas as pd
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dynamic_scene import scenes,calculate

def fixture():
    rows=[]
    for frame in range(3):
        for pid,team,x in [(0,None,40+frame),(1,'attack',45+frame),(2,'attack',40+2*frame),(3,'defense',60-frame),(4,'defense',70+frame)]:
            rows.append(dict(player=pid,team=team,frame=frame,x=x,y=40+pid))
    return pd.DataFrame(rows)

class DynamicSceneTests(unittest.TestCase):
    def test_only_focus_changes_between_endpoint_scenes(self):
        actual,ref,focus,t=scenes(fixture(),1)
        self.assertAlmostEqual(t,.1)
        for team in ['Home','Away']:
            for col in actual[team].index:
                if not col.startswith(focus+'_'):self.assertEqual(actual[team][col],ref[team][col])
        self.assertNotEqual(actual['Home']['Home_2_x'],40*1.05-52.5)
        self.assertNotEqual(actual['Away']['Away_3_x'],60*1.05-52.5)
        self.assertNotEqual(actual['Home']['ball_x'],40*1.05-52.5)
    def test_start_scenes_identical(self):
        a,b,_,_=scenes(fixture(),1,0)
        for team in a:pd.testing.assert_series_equal(a[team],b[team])
    def test_stationary_focus_does_not_get_other_players_credit(self):
        df=fixture();df.loc[df.player==1,'x']=45.
        result=calculate(df,1,grid_columns=4)
        self.assertAlmostEqual(result['area']['net_m2'],0.,places=10)
        self.assertTrue(result['all_other_players_use_actual_endpoint_state'])
        self.assertFalse(result['is_causal_effect'])

if __name__=='__main__':unittest.main()
