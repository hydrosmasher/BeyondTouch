"""Conditional endpoint attribution with all other observed actors at actual time.

This is a model-state contrast, not a simulation of how a match would have unfolded.
Partial Last Row coverage and nominal pitch scaling remain explicit limitations.
"""
from pathlib import Path
import sys
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parent/'Scripts'))
from player_influence.pitch_control import PitchControlCalculator
from player_influence.movement_metrics import area_metrics
import Metrica_PitchControl as mpc

def scenes(df,focus_id,frame_index=-1):
    frames=np.sort(df.frame.unique());selected=int(frames[frame_index]);times=(frames-frames[0])/20.
    rows={'Home':{'ball_x':0.,'ball_y':0.},'Away':{'ball_x':0.,'ball_y':0.}}
    reference=None;focus_name=None
    for pid,g in df.groupby('player'):
        g=g.sort_values('frame');p=g[['x','y']].to_numpy(float)*[1.05,.68]-[52.5,34]
        if not np.array_equal(g.frame.to_numpy(),frames):raise ValueError('Incomplete actor trajectory')
        v=np.gradient(p,times,axis=0);i=int(np.where(frames==selected)[0][0])
        if int(pid)==0:
            for row in rows.values():row.update(ball_x=float(p[i,0]),ball_y=float(p[i,1]))
            continue
        team='Home' if g.team.iloc[0]=='attack' else 'Away';name=f'{team}_{int(pid)}'
        rows[team].update({name+'_x':float(p[i,0]),name+'_y':float(p[i,1]),name+'_vx':float(v[i,0]),name+'_vy':float(v[i,1])})
        if int(pid)==int(focus_id):
            if team!='Home':raise ValueError('Focus must be an observed attacker')
            focus_name=name;reference=(p[0],v[0])
    if reference is None:raise ValueError('Focus is absent')
    actual={k:pd.Series(v) for k,v in rows.items()};counter={k:v.copy() for k,v in actual.items()}
    p,v=reference
    for suffix,value in [('x',p[0]),('y',p[1]),('vx',v[0]),('vy',v[1])]:counter['Home'][focus_name+'_'+suffix]=float(value)
    return actual,counter,focus_name,float(times[np.where(frames==selected)[0][0]])

def calculate(df,focus_id,grid_columns=50,reference_grid_columns=None):
    actual,counter,focus_name,time=scenes(df,focus_id)
    params=mpc.default_model_params();params.update(int_dt=.02,reaction_time=.7,reaction_time_def=1.)
    pc=PitchControlCalculator(('unconfirmed','unconfirmed'),params=params,field_dimen=(105,68),n_grid_cells_x=grid_columns,exclude_offside=False)
    observed=pc.calculate_surface(actual['Home'],actual['Away'],attacking_half_only=False,attacking_team='Home')[0]
    reference=pc.calculate_surface(counter['Home'],counter['Away'],attacking_half_only=False,attacking_team='Home')[0]
    delta=observed-reference
    result={'schema_version':'moving-scene-1','method':'actual_endpoint_minus_same_endpoint_with_only_focus_state_held_at_source_start',
            'source_frame_time_s':time,'focus_source_id':int(focus_id),'focus_model_id':focus_name,
            'all_other_players_use_actual_endpoint_state':True,'ball_uses_actual_endpoint_position':True,
            'only_focus_reference_time_s':0.,'focus_reference_state':'first observed position AND velocity',
            'is_causal_effect':False,'is_full_match_pitch_control':False,'domain':'whole nominal pitch',
            'area':area_metrics(delta,pc.cell_area_m2),'grid':{'columns':len(pc.xgrid),'rows':len(pc.ygrid),'cell_area_m2':pc.cell_area_m2},
            'surface':delta.tolist(),'x':pc.xgrid.tolist(),'y':pc.ygrid.tolist(),
            'assumptions':['105 × 68 m nominal scaling; actual calibration unverified.',
                           'Only observed players are included; missing players are not invented.',
                           'Goalkeeper identity is unconfirmed, so observed actors use generic outfield model parameters.',
                           'Offside filtering is disabled because reliable complete offside state is unavailable.',
                           'The focus reference is an artificial model-state contrast; ball and other players do not react to it.',
                           'Result is a conditional model sensitivity, not real-match causal credit, xG or physical space ownership.']}
    if reference_grid_columns:
        ref=calculate(df,focus_id,reference_grid_columns)
        diff=abs(result['area']['net_m2']-ref['area']['net_m2']);tol=max(3.,.05*abs(ref['area']['net_m2']))
        result['numerical_sensitivity']={'reference_grid_columns':reference_grid_columns,'reference_net_m2':ref['area']['net_m2'],'absolute_difference_m2':diff,'tolerance_m2':tol,'within_declared_tolerance':diff<=tol,'meaning':'Grid stability only; does not resolve source inaccuracy or missing players.'}
    return result
