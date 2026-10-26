import unittest,tempfile,json,copy
from pathlib import Path
import pandas as pd
from import_sequence import load_tracking,generate
from decision_options import analyze

class NewDataTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.path=self.root/'input.csv'
        self.meta={'case_id':'TEST','match_title':'Test sequence','source_name':'Test fixture, not a real match','native_hz':50,'pitch_length_m':110,'pitch_width_m':70,'coordinates':'metres','attack_direction':'right','focus_player_id':'runner'}
        self.rows=[{'time_s':1000+i/50,'player_id':pid,'team':team,'x':x+(i*.1 if pid=='runner' else 0),'y':35} for i in range(6) for pid,team,x in [('runner','attack',10),('D','defense',20),('ball','ball',10)]];self.write()
    def tearDown(self):self.temp.cleanup()
    def write(self):pd.DataFrame(self.rows).to_csv(self.path,index=False)
    def test_new_rate_dimensions_and_unknown_names_are_preserved(self):
        b=generate(self.path,self.meta,self.root/'out'/'case');self.assertEqual(b['metrics']['source_native_hz'],50);self.assertAlmostEqual(b['metrics']['focus_path_nominal_m'],.5);self.assertEqual(b['instance']['original_time_origin_s'],1000);self.assertEqual(b['metrics']['coordinate_assumption']['assumed_length_m'],110);self.assertEqual(b['metrics']['focus_name'],'runner');self.assertIsNone(b['story']['finisher_player_id']);self.assertTrue((self.root/'out/case/decision-options.json').exists())
    def test_duplicate_observation_rejected(self):
        self.rows.append(self.rows[0]);self.write()
        with self.assertRaisesRegex(ValueError,'Duplicate'):load_tracking(self.path,self.meta)
    def test_cadence_mismatch_rejected(self):
        self.meta['native_hz']=25
        with self.assertRaisesRegex(ValueError,'cadence'):load_tracking(self.path,self.meta)
    def test_ball_required_and_no_output_overwrite(self):
        self.rows=[r for r in self.rows if r['team']!='ball'];self.write()
        with self.assertRaisesRegex(ValueError,'ball'):load_tracking(self.path,self.meta)
    def test_future_observations_do_not_change_current_options(self):
        b=generate(self.path,self.meta,self.root/'out'/'case');before=analyze(b,'right')['nodes'][1];changed=copy.deepcopy(b)
        for f in changed['frames'][2:]:
            for p in f['players']:p['x']=90;p['y']=90
        self.assertEqual(before,analyze(changed,'right')['nodes'][1]);self.assertFalse(before.get('uses_future_observations',False))
    def test_supplied_finisher_is_not_claimed_as_a_verified_goal(self):
        self.meta['finisher_player_id']='runner';b=generate(self.path,self.meta,self.root/'out'/'case')
        self.assertEqual(b['story']['steps'][-1]['status'],'supplied_context');self.assertFalse(b['story']['causal_attraction_established'])
    def test_boundary_options_are_not_ranked_as_feasible(self):
        b=generate(self.path,self.meta,self.root/'out'/'case')
        for f in b['frames']:
            next(p for p in f['players'] if p['id']==b['metrics']['focus_player_id'])['x']=99.9
        node=analyze(b,'right')['nodes'][0];forward=next(o for o in node['options'] if o['id']=='continue');self.assertFalse(forward['inside_pitch']);self.assertIsNone(forward['heuristic_score'])
    def test_existing_output_is_preserved(self):
        out=self.root/'existing';out.mkdir();marker=out/'my-work.txt';marker.write_text('keep')
        with self.assertRaisesRegex(ValueError,'empty'):generate(self.path,self.meta,out)
        self.assertEqual(marker.read_text(),'keep')
    def test_changing_actor_coverage_is_rejected(self):
        self.rows=[r for r in self.rows if not (r['player_id']=='D' and r['time_s']==1000.02)];self.write()
        with self.assertRaisesRegex(ValueError,'coverage'):load_tracking(self.path,self.meta)
    def test_pc_scene_uses_declared_native_rate_and_dimensions(self):
        from dynamic_scene import scenes
        df,names,ids,focus,finisher,hz,dim,origin=load_tracking(self.path,self.meta)
        actual,reference,name,t=scenes(df,focus,source_hz=hz,field_dimen=dim)
        self.assertAlmostEqual(actual['Home'][name+'_x'],-44.5);self.assertAlmostEqual(actual['Home'][name+'_vx'],5);self.assertAlmostEqual(t,.1)
    def test_non_decimal_native_interval_is_not_rounded_for_replay(self):
        self.meta['native_hz']=60
        for i in range(6):
            for row in self.rows[i*3:i*3+3]:row['time_s']=1000+i/60
        self.write();b=generate(self.path,self.meta,self.root/'out'/'case');self.assertAlmostEqual(b['frames'][1]['t'],1/60,places=12)

if __name__=='__main__':unittest.main()
