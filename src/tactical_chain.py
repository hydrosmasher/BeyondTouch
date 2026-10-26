"""Auditable movement-pattern candidates, not learned or causal defender assignments."""
import numpy as np

PARAMS={'response_window_s':1.5,'cover_window_s':1.5,'minimum_focus_displacement_m':3.,'minimum_defender_displacement_m':2.,'maximum_initial_focus_gap_m':12.,'maximum_final_focus_gap_m':12.,'minimum_direction_cosine':.5,'minimum_cover_approach_m':2.,'maximum_cover_anchor_gap_m':8.,'minimum_opening_m':2.,'maximum_finisher_anchor_gap_m':10.}

def build(bundle):
    m=bundle['metrics'];frames=bundle['frames'];roster={p['id']:p for p in bundle['roster']};t=np.array([f['t'] for f in frames]);tracks={p['id']:np.array([[next(q for q in f['players'] if q['id']==p['id'])['x']*1.05,next(q for q in f['players'] if q['id']==p['id'])['y']*.68] for f in frames]) for p in frames[0]['players']}
    focus=m['focus_player_id'];defs=sorted(p for p in roster if roster[p]['team']=='defense');scorer=next((p for p in roster if roster[p].get('name')==bundle['instance']['scorer']),None)
    label=lambda p:roster[p].get('name') or f"observed defender D{p}" if p in defs else roster[p].get('name') or f"player {p}"
    def point(p,i):return [round(float(v),5) for v in tracks[p][i]]
    def dist(a,b):return float(np.linalg.norm(a-b))
    response=None
    # Earliest qualifying window, then closest initial defender; do not select by goal or xG.
    for a in range(0,len(t)-30,5):
        b=a+30;fv=tracks[focus][b]-tracks[focus][a];fl=float(np.linalg.norm(fv))
        if fl<PARAMS['minimum_focus_displacement_m']:continue
        candidates=[]
        for d in defs:
            dv=tracks[d][b]-tracks[d][a];dl=float(np.linalg.norm(dv));g0=dist(tracks[d][a],tracks[focus][a]);g1=dist(tracks[d][b],tracks[focus][b]);cos=float(np.dot(fv,dv)/(fl*dl)) if dl>1e-9 else -1.
            if dl>=2 and g0<=12 and g1<=12 and cos>=.5:candidates.append((g0,d,dl,cos,g1))
        if candidates:
            g0,d,dl,cos,g1=min(candidates);response={'player_id':d,'label':label(d),'start_index':a,'end_index':b,'start_s':float(t[a]),'end_s':float(t[b]),'focus_displacement_nominal_m':fl,'defender_displacement_nominal_m':dl,'initial_focus_gap_nominal_m':g0,'final_focus_gap_nominal_m':g1,'direction_cosine':cos,'anchor_nominal_xy':point(d,a)};break
    cover=None;opening=None
    if response:
        anchor=np.array(response['anchor_nominal_xy']);d1=response['player_id'];a=response['end_index']
        for c in range(a,len(t)-30,5):
            e=c+30;candidates=[]
            for d in defs:
                if d==d1:continue
                g0=dist(tracks[d][c],anchor);g1=dist(tracks[d][e],anchor)
                if g0-g1>=2 and g1<=8:candidates.append((g1,d,g0,g1))
            if candidates:
                _,d,g0,g1=min(candidates);cover={'player_id':d,'label':label(d),'start_index':c,'end_index':e,'start_s':float(t[c]),'end_s':float(t[e]),'anchor_nominal_xy':anchor.tolist(),'anchor_gap_before_nominal_m':g0,'anchor_gap_after_nominal_m':g1,'approach_nominal_m':g0-g1,'vacated_anchor_nominal_xy':point(d,c)};break
        if cover:
            c,e=cover['start_index'],cover['end_index'];anchor=np.array(cover['vacated_anchor_nominal_xy']);gap=lambda i:min(dist(tracks[d][i],anchor) for d in defs)
            before,after=gap(c),gap(e);gain=after-before
            opening={'start_s':float(t[c]),'end_s':float(t[e]),'anchor_nominal_xy':anchor.tolist(),'nearest_observed_defender_before_nominal_m':before,'nearest_observed_defender_after_nominal_m':after,'gap_increase_nominal_m':gain,'opening_threshold_met':gain>=2,'finisher_player_id':scorer,'finisher_arrival':None}
            if scorer is not None:
                distances=np.linalg.norm(tracks[scorer][e:]-anchor,axis=1);i=e+int(np.argmin(distances));approach=dist(tracks[scorer][e],anchor)-dist(tracks[scorer][i],anchor)
                opening['finisher_arrival']={'time_s':float(t[i]),'minimum_anchor_gap_nominal_m':dist(tracks[scorer][i],anchor),'approach_after_cover_nominal_m':approach,'same_zone_entry_supported':bool(gain>=2 and dist(tracks[scorer][i],anchor)<=10 and approach>=2 and i>e)}
    same=bool(opening and opening['finisher_arrival'] and opening['finisher_arrival']['same_zone_entry_supported']);steps=[]
    steps.append({'title':'1 · The attacking movement','status':'observed','time_s':0.,'text':f"{m['focus_name']} covers approximately {m['focus_path_nominal_m']:.2f} nominal metres across this clip. The source does not label an off-ball-only interval."})
    steps.append({'title':'2 · Defender response','status':'candidate' if response else 'not_detected','time_s':response['start_s'] if response else None,'text':(f"Between {response['start_s']:.2f}–{response['end_s']:.2f} s, {response['label']} moves {response['defender_displacement_nominal_m']:.2f} nominal m in a similar direction to the focus; their gap changes from {response['initial_focus_gap_nominal_m']:.2f} to {response['final_focus_gap_nominal_m']:.2f} nominal m. This is a candidate tracking response, not proof of attraction." if response else 'No defender meets the declared nearby, same-direction response rule. Do not describe this clip as a proven decoy run.')})
    steps.append({'title':'3 · The covering movement','status':'candidate' if cover else 'not_detected','time_s':cover['start_s'] if cover else None,'text':(f"After that response, {cover['label']} moves {cover['approach_nominal_m']:.2f} nominal m closer to the first defender’s earlier location ({cover['start_s']:.2f}–{cover['end_s']:.2f} s). This is a geometric covering candidate; no marking responsibility is supplied." if cover else 'No later defender meets the covering rule. A second covering defender must not be invented.')})
    if opening:
        text=f"At the covering defender’s earlier location, nearest-observed-defender clearance changes from {opening['nearest_observed_defender_before_nominal_m']:.2f} to {opening['nearest_observed_defender_after_nominal_m']:.2f} nominal m. "
        text+=(f"{bundle['instance']['scorer']} subsequently approaches that same location at {opening['finisher_arrival']['time_s']:.2f} s, supporting a candidate space-use chain." if same else 'The complete link from this location to the finisher is not supported by the declared rule.')
    else:text='The full run → response → cover → finisher chain is not established for this source clip.'
    steps.append({'title':'4 · Space and the finisher','status':'candidate' if same else 'not_established','time_s':opening['finisher_arrival']['time_s'] if same else None,'text':text})
    steps.append({'title':'5 · Goal context','status':'context','time_s':None,'text':f"The match context identifies {bundle['instance']['scorer']} as the scorer at {bundle['instance']['goal_minute']}′. The source clip has no synchronized shot marker, so this does not validate the preceding causal chain."})
    summary=(f"Watch {m['focus_name']} first, then the highlighted defender movements. " + (f"A nearby defender moves with the run and a second defender later approaches the first defender’s earlier position. " if cover else f"A nearby defender moves in a similar direction, but a subsequent cover is not detected. " if response else 'The data do not establish the proposed defender-attraction pattern. ')+(f"The scorer then approaches the second defender’s earlier location: this is a candidate tactical chain, not proof that the run caused the goal." if same else f"The goal is by {bundle['instance']['scorer']}; the full space-creation link remains unconfirmed. Present this as a limited case, not a proven chain."))
    return {'schema_version':'tactical-chain-1','method':'transparent_geometric_candidate_rules','learned_model':False,'causal_attraction_established':False,'full_candidate_chain_detected':same,'source_native_hz':20,'coordinate_units':'nominal metres, assumed 105 x 68 m','thresholds':PARAMS,'selection':'earliest qualifying response window, nearest initial defender; then earliest later cover, nearest anchor at cover end','focus_player_id':focus,'finisher_player_id':scorer,'response':response,'cover':cover,'opening':opening,'steps':steps,'presentation_text':summary,'warning':'Partial educational tracking; ball/marking intent and event-synchronized shot time unavailable. Absence of a detected pattern is not proof of its absence in the match.'}
