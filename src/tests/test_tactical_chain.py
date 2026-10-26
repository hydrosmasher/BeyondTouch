import unittest
import numpy as np
from tactical_chain import build

def fixture(stationary=False,include_cover=True,include_finisher=True):
    roster=[{'id':1,'team':'attack','name':'Runner','shirt':10},{'id':2,'team':'defense','name':None,'shirt':None}]
    if include_cover:roster.append({'id':3,'team':'defense','name':None,'shirt':None})
    if include_finisher:roster.append({'id':4,'team':'attack','name':'Scorer','shirt':11})
    frames=[]
    for t in np.arange(101)/20:
        xy={1:(10+3*t,10),2:(12 if stationary else 12+3*min(t,1.5),10),3:(20 if stationary else 20-8*max(0,min((t-1.5)/1.5,1)),10),4:(30-5*max(0,t-3),10)}
        frames.append({'t':float(t),'players':[{'id':p['id'],'x':xy[p['id']][0]/1.05,'y':xy[p['id']][1]/.68} for p in roster]})
    return {'metrics':{'focus_player_id':1,'focus_name':'Runner','focus_path_nominal_m':15},'instance':{'scorer':'Scorer','goal_minute':20},'roster':roster,'frames':frames}
class TacticalChainTests(unittest.TestCase):
    def test_complete_geometric_pattern_never_becomes_causal_credit(self):
        s=build(fixture());self.assertTrue(s['full_candidate_chain_detected']);self.assertFalse(s['causal_attraction_established']);self.assertNotEqual(s['response']['player_id'],s['cover']['player_id']);self.assertGreaterEqual(s['cover']['start_s'],s['response']['end_s']);self.assertGreater(s['opening']['finisher_arrival']['time_s'],s['cover']['end_s'])
    def test_stationary_defenders_are_not_attracted(self):
        s=build(fixture(stationary=True));self.assertIsNone(s['response']);self.assertIsNone(s['cover']);self.assertFalse(s['full_candidate_chain_detected'])
    def test_one_defender_cannot_fill_both_roles(self):
        s=build(fixture(include_cover=False));self.assertIsNotNone(s['response']);self.assertIsNone(s['cover'])
    def test_missing_finisher_cannot_be_credited(self):
        s=build(fixture(include_finisher=False));self.assertIsNone(s['finisher_player_id']);self.assertFalse(s['full_candidate_chain_detected'])
if __name__=='__main__':unittest.main()
