import unittest,copy
import numpy as np
from guided_review import spaces,plan,at_time

def fixture():
    return {'metrics':{'focus_player_id':1,'source_native_hz':20,'duration_s':2,'coordinate_assumption':{'assumed_length_m':105,'assumed_width_m':68}},'instance':{'attack_direction':'right'},'roster':[{'id':1,'team':'attack'},{'id':2,'team':'defense'}],'frames':[{'t':i/20,'players':[{'id':1,'x':40+i*.1,'y':50},{'id':2,'x':80,'y':50}]} for i in range(41)]}
class GuidedReviewTests(unittest.TestCase):
    def test_spaces_are_few_distinct_and_have_defending_context(self):
        chosen=spaces(fixture(),0,'right',3);self.assertGreaterEqual(len(chosen),1);self.assertLessEqual(len(chosen),3)
        for a in chosen:
            self.assertEqual(a['cover_defender_id'],2);self.assertGreaterEqual(a['endpoint_defender_gap_m'],2)
            for b in chosen:
                if a is b:continue
                delta=(np.array(a['target_normalized_xy'])-b['target_normalized_xy'])*[1.05,.68];self.assertGreaterEqual(float(np.linalg.norm(delta)),3-1e-8)
    def test_pause_holds_source_then_reveals_actual_continuation(self):
        timeline=plan(fixture());self.assertEqual(timeline[0]['phase'],'option');seg,t=at_time(timeline,1);self.assertEqual(t,seg['source_start_s']);self.assertEqual(seg['source_start_s'],seg['source_end_s']);reveals=[s for s in timeline if s['phase']=='reveal'];self.assertTrue(reveals);self.assertTrue(all(s['source_end_s']>s['source_start_s'] for s in reveals))
    def test_future_defenders_do_not_change_a_paused_choice(self):
        b=fixture();before=spaces(b,1,'right',2);other=copy.deepcopy(b)
        for frame in other['frames'][2:]:frame['players'][1]['x']=1
        self.assertEqual(before,spaces(other,1,'right',2))
