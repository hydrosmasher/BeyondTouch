import sys
from pathlib import Path
import unittest
from types import SimpleNamespace
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Scripts'))
from player_influence.movement_metrics import area_metrics, distance_metrics, window_durations, MovementMetrics, MetricConfig, rectangle_overlap_weights
from player_influence.pitch_control import PitchControlCalculator
from player_influence.influence_calculator import InfluenceCalculator
from run_movement_sequence import synthetic_sequence


class MetricTests(unittest.TestCase):
    def test_area_has_physical_units_and_signed_accounting(self):
        out=area_metrics(np.array([[.5,-.25,np.nan]]),4)
        self.assertEqual(out, {'gained_m2':2.,'lost_m2':1.,'net_m2':1.})

    def test_area_region_mask(self):
        self.assertEqual(area_metrics(np.array([[.5,-.25]]),4,np.array([[False,True]]))['net_m2'],-1.)

    def test_distance_and_speed_use_actual_time(self):
        out=distance_metrics(np.array([[0,0],[3,4],[6,8]]),np.array([0,1,3]),4)
        self.assertEqual(out['distance_m'],10)
        self.assertEqual(out['high_speed_distance_m'],5)

    def test_window_includes_partial_interval_but_not_last_sample(self):
        out=window_durations([0,1,2,2.5],[True,False,True,True])
        self.assertEqual(out,{'total_s':1.5,'longest_continuous_s':1.0})

    def test_no_window(self):
        self.assertEqual(window_durations([0,.1,.2],[False]*3)['total_s'],0)

    def test_missing_player_not_placed_at_center(self):
        row=pd.Series({'Home_2_x':np.nan,'Home_2_y':np.nan,'Home_2_vx':np.nan,'Home_2_vy':np.nan})
        result=InfluenceCalculator(None,None)._backfill_interpolated_row(row)
        self.assertTrue(np.isnan(result['Home_2_x']))
        self.assertNotIn('Home_2',InfluenceCalculator(None,None)._get_active_players(result))

    def test_pitch_control_team_swap_and_rotation_symmetry(self):
        home,away=synthetic_sequence()
        h,a=home.iloc[0],away.iloc[0]
        pc=PitchControlCalculator(['1','1'],field_dimen=(105,68),n_grid_cells_x=6)
        actual,_,_=pc.calculate_surface(h,a,False,'Home')
        def swap(row,old,new):
            out=row.rename(index=lambda s:s.replace(old+'_',new+'_'))
            for col in out.index:
                if col.endswith(('_x','_y','_vx','_vy')): out[col]=-out[col]
            return out
        rotated,_,_=pc.calculate_surface(swap(a,'Away','Home'),swap(h,'Home','Away'),False,'Away')
        np.testing.assert_allclose(actual,rotated[::-1,::-1],atol=1e-9)

    def test_frozen_runner_has_zero_influence(self):
        h,a=synthetic_sequence()
        h=h.iloc[:2].copy();a=a.iloc[:2].copy()
        for df in (h,a):
            for col in df.columns:
                if col not in ('Time [s]','Period'):df[col]=df[col].iloc[0]
        calc=InfluenceCalculator(SimpleNamespace(tracking_home=h,tracking_away=a),
                                 PitchControlCalculator(['1','1'],field_dimen=(105,68),n_grid_cells_x=6))
        result=calc._analyze_time_transition(h,a,h.index[0],0,.1)
        self.assertEqual(result['player_influences']['Home_11']['net_influence'],0)

    def test_carrier_cannot_receive_off_ball_credit(self):
        h,a=synthetic_sequence()
        with self.assertRaisesRegex(ValueError,'distinct'):
            MovementMetrics().analyze(h,a,runner='Home_8',receiver='Home_10',carrier='Home_8',attacking_team='Home',start_s=0,end_s=3.5)

    def test_gap_is_rejected_instead_of_inventing_distance(self):
        h,a=synthetic_sequence();h=h.drop(index=[2,3,4]);a=a.drop(index=[2,3,4])
        with self.assertRaisesRegex(ValueError,'gap'):
            MovementMetrics().analyze(h,a,runner='Home_11',receiver='Home_10',carrier='Home_8',attacking_team='Home',start_s=0,end_s=3.5)

    def test_fractional_cell_overlap_recovers_exact_penalty_area(self):
        for n in [20,50,75]:
            pc=PitchControlCalculator(['1','1'],field_dimen=(105,68),n_grid_cells_x=n)
            dx=105/len(pc.xgrid);dy=68/len(pc.ygrid)
            weights=rectangle_overlap_weights(pc.xgrid,pc.ygrid,dx,dy,36,52.5,-20.16,20.16)
            self.assertAlmostEqual(float(weights.sum()*dx*dy),16.5*40.32,places=8)

    def test_area_weights_outside_unit_interval_rejected(self):
        with self.assertRaises(ValueError):area_metrics(np.ones((1,1)),1,np.array([[1.1]]))

    def test_invalid_ball_rejected(self):
        h,a=synthetic_sequence();h.loc[5,'ball_x']=np.nan
        with self.assertRaisesRegex(ValueError,'Ball position'):
            MovementMetrics().analyze(h,a,runner='Home_11',receiver='Home_10',carrier='Home_8',attacking_team='Home',start_s=0,end_s=3.5)

    def test_visibility_change_in_middle_rejected(self):
        h,a=synthetic_sequence();h['Home_99_x']=np.nan;h['Home_99_y']=np.nan
        h.loc[5,['Home_99_x','Home_99_y']]=[0,0]
        with self.assertRaisesRegex(ValueError,'visibility'):
            MovementMetrics().analyze(h,a,runner='Home_11',receiver='Home_10',carrier='Home_8',attacking_team='Home',start_s=0,end_s=3.5)

    def test_duplicate_times_rejected(self):
        h,a=synthetic_sequence();h.loc[1,'Time [s]']=0
        with self.assertRaisesRegex(ValueError,'strictly increasing'):
            MovementMetrics().analyze(h,a,runner='Home_11',receiver='Home_10',carrier='Home_8',attacking_team='Home',start_s=0,end_s=3.5)

    def test_asynchronous_teams_rejected(self):
        h,a=synthetic_sequence();a.loc[2,'Time [s]']+=.01
        with self.assertRaisesRegex(ValueError,'synchronized'):
            MovementMetrics().analyze(h,a,runner='Home_11',receiver='Home_10',carrier='Home_8',attacking_team='Home',start_s=0,end_s=3.5)


if __name__=='__main__':unittest.main()
