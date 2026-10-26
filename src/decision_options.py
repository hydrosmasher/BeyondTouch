"""Current-state geometric movement options; no future observations or trained policy."""
import math
import numpy as np

LABELS=[('continue',0.),('cut_left',math.pi/4),('cut_right',-math.pi/4),('wide_left',math.pi/2),('wide_right',-math.pi/2),('check_back',math.pi)]

def analyze(bundle,attack_direction,indices=None):
    if attack_direction not in ('left','right'):raise ValueError('Attack direction must be declared as left or right')
    m=bundle['metrics'];L=m['coordinate_assumption']['assumed_length_m'];W=m['coordinate_assumption']['assumed_width_m'];focus=m['focus_player_id'];roster={p['id']:p for p in bundle['roster']};frames=bundle['frames'];nodes=[];sign=1 if attack_direction=='right' else -1
    for i in (range(len(frames)) if indices is None else indices):
        f=frames[i]
        pos={p['id']:np.array([p['x']*L/100,p['y']*W/100]) for p in f['players']};origin=pos[focus];velocity=np.zeros(2)
        if i:
            old=next(p for p in frames[i-1]['players'] if p['id']==focus);dt=f['t']-frames[i-1]['t'];velocity=(origin-np.array([old['x']*L/100,old['y']*W/100]))/dt
        speed=float(np.linalg.norm(velocity));heading=math.atan2(velocity[1],velocity[0]) if speed>=.5 else (0 if sign==1 else math.pi)
        distance=min(6.,max(2.,speed));options=[];defenders=[v for p,v in pos.items() if p in roster and roster[p]['team']=='defense']
        for label,offset in LABELS:
            theta=heading+offset;target=origin+distance*np.array([math.cos(theta),math.sin(theta)]);inside=bool(0<=target[0]<=L and 0<=target[1]<=W)
            samples=np.linspace(origin,target,13);clearance=min((float(np.linalg.norm(samples-d,axis=1).min()) for d in defenders),default=None);endpoint=min((float(np.linalg.norm(target-d)) for d in defenders),default=None)
            progress=float(sign*(target[0]-origin[0]));score=None if not inside or clearance is None else .7*min(clearance/8,1)+.3*((progress/distance+1)/2)
            options.append({'id':label,'label':label.replace('_',' '),'target_normalized_xy':(target/[L/100,W/100]).tolist(),'distance_m':distance,'progress_m':progress,'minimum_segment_defender_gap_m':clearance,'endpoint_defender_gap_m':endpoint,'inside_pitch':inside,'heuristic_score':score,'status':'outside_pitch' if not inside else 'crowded' if clearance is not None and clearance<1.5 else 'candidate','children':[{'id':'continue_to_endpoint','assumption':'Defenders remain at their observed current positions; no response is predicted.'},{'id':'reassess_next_frame','assumption':'Recompute options from new observations rather than a fabricated future.'}]})
        ranked=sorted((o for o in options if o['heuristic_score'] is not None),key=lambda o:(-o['heuristic_score'],o['id']))
        nodes.append({'time_s':f['t'],'source_index':i,'heading_from':'past_and_current_motion' if speed>=.5 else 'declared_attack_direction','observed_speed_m_s':speed,'horizon_s':1.,'origin_normalized_xy':(origin/[L/100,W/100]).tolist(),'options':options,'top_geometric_option':ranked[0]['id'] if ranked else None})
    return {'schema_version':'movement-options-1','attack_direction':attack_direction,'uses_future_observations':False,'trained_decision_tree':False,'probabilities_available':False,'method':'six current-state movement branches, one-second heading-based endpoints','score_definition':'0.7 * min(segment clearance / 8 m, 1) + 0.3 * ((forward progress / step length + 1) / 2)','assumptions':['Step length = observed speed × 1 s, limited to 2–6 m; not a biomechanical feasibility guarantee.','Clearance samples 13 points on a straight segment against observed current defender positions.','Missing defenders, possession, onside eligibility, acceleration and future defender responses are not resolved.','Scores are relative geometric utilities, not success probabilities, xG or optimal decisions.','All six movement branches apply to the focus; pass and shot options require reliable possession/event inputs and are not invented.'],'nodes':nodes}
