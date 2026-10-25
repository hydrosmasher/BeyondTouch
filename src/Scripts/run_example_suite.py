"""Twelve authored fixtures, provenance, replays and measured numerical sensitivity."""
import argparse
import csv
from dataclasses import replace
from concurrent.futures import ProcessPoolExecutor, as_completed
import html
import json
from pathlib import Path
import sys
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parent))
from run_movement_sequence import synthetic_sequence
from player_influence.movement_metrics import MovementMetrics, MetricConfig
from player_influence.replay_report import write_report

CASES = [
 ('diagonal','Diagonal run toward the left channel','An attacker moves away from a central receiver while nearby defenders shift.'),
 ('depth','Straight run behind the defensive line','Compare a depth run with a diagonal run.'),
 ('checkback','Check back toward midfield','A support movement can trade advanced space for proximity to the ball.'),
 ('width','Wide supporting run','A wider receiving option changes a different part of the surface.'),
 ('stationary','Stationary attacker negative control','Zero runner state change must produce zero isolated movement sensitivity.'),
 ('retreat','Retreat away from the attacking area','An active run can have negative attacking spatial sensitivity.'),
 ('double','Double movement','Distance follows a multi-leg path, not endpoint displacement.'),
 ('handover','Defensive handover','The initially closest defender stops following; a second defender changes position.'),
 ('away','Away team mirrored attack','Swapping teams and rotating the pitch should preserve scalar metrics.'),
 ('blocked','Receiver remains tightly marked','A run need not produce a usable candidate receiving window.'),
 ('offside','Run ends beyond the offside line','Offside positioning should not receive unrestricted attacking control credit.'),
 ('hold','Defenders hold their positions','Observed defender travel is zero even when the attacker moves.')
]


def fixture(index, sample_rate_hz=50):
    if sample_rate_hz not in (25, 50):
        raise ValueError('Supported synthetic fixture rates are 25 or 50 Hz')
    key,title,description=CASES[index]
    h,a=synthetic_sequence()
    # Evaluate authored piecewise-linear trajectories at the requested rate.
    # Synthetic sampling does not add real observations or prove camera compatibility.
    times=np.round(np.arange(6 * sample_rate_hz + 1) / sample_rate_hz,8)
    def resample(df):
        import pandas as pd
        return pd.DataFrame({col: np.interp(times,df['Time [s]'],df[col]) for col in df.columns})
    h,a=resample(h),resample(a)
    def path(df,player,knots,xs,ys):
        for axis,values in [('x',xs),('y',ys)]:
            df[player+'_'+axis]=np.interp(times,knots,values)
    def move(df,player,x,y):
        path(df,player,[0,3.5,6],[df[player+'_x'].iloc[0],x,x],[df[player+'_y'].iloc[0],y,y])
    if key=='depth':move(h,'Home_11',32,-5);move(a,'Away_4',33,-4)
    if key=='checkback':move(h,'Home_11',8,-3);move(a,'Away_4',14,-3)
    if key=='width':move(h,'Home_11',17,-29);move(a,'Away_4',20,-26)
    if key=='stationary':move(h,'Home_11',15,-5)
    if key=='retreat':move(h,'Home_11',0,-5);move(a,'Away_4',13,-4)
    if key=='double':path(h,'Home_11',[0,1.2,2.2,3.5,6],[15,21,18,24,24],[-5,-8,-10,-16,-16])
    if key=='handover':
        path(a,'Away_4',[0,1.5,3.5,6],[18,25,25,25],[-4,-10,-10,-10])
        move(a,'Away_5',30,-15)
    if key=='blocked':
        for axis in ['x','y']:a['Away_5_'+axis]=h['Home_10_'+axis]+1
    if key=='offside':move(h,'Home_11',40,-5);move(a,'Away_4',31,-4)
    if key=='hold':
        for p in range(1,12):
            for axis in ['x','y']:a[f'Away_{p}_{axis}']=a[f'Away_{p}_{axis}'].iloc[0]
    for df,team in [(h,'Home'),(a,'Away')]:
        for p in range(1,12):
            pid=f'{team}_{p}'
            for axis in ['x','y']:df[pid+'_v'+axis]=np.gradient(df[pid+'_'+axis],times)
            df[pid+'_speed']=np.hypot(df[pid+'_vx'],df[pid+'_vy'])
    team='Home'
    if key=='away':
        def swap(df,old,new):
            df=df.rename(columns=lambda s:s.replace(old+'_',new+'_')).copy()
            for col in df.columns:
                if col.endswith(('_x','_y','_vx','_vy')):df[col]=-df[col]
            return df
        h,a=swap(a,'Away','Home'),swap(h,'Home','Away');team='Away'
    n=index+1
    instance={'scenario_id':f'BT-SYN-{n:02d}','match_id':f'SIM-MATCH-{n:02d}',
              'match_label':f'Aster FC vs Boreal FC — synthetic match {n:02d}',
              'run_id':f'BT-SYN-{n:02d}-RUN-01','title':title,'description':description,
              'match_clock':f'{10+n:02d}:00.00–{10+n:02d}:03.48 (simulated)',
              'real_match':False,'competition':None,'real_player_names':None,
              'source':'Scripts/run_example_suite.py fixture()','sample_rate_hz':sample_rate_hz,
              'sample_interval_s':1 / sample_rate_hz,
              'sampling_note':'Authored synthetic trajectories evaluated at this rate; not camera-derived tracking.',
              'source_match_note':'Authored scenario, not reconstructed from a real match.',
              'roster':{f'{t}_{p}':{'team':'Aster FC' if t=='Home' else 'Boreal FC','shirt_number':p,'real_name':None,'synthetic':True} for t in ['Home','Away'] for p in range(1,12)}}
    # Keep 3.48 s at both rates for a like-for-like window ending before release.
    return h,a,team,instance


def process_case(index,output,reference_grid,sample_rate_hz=50):
    h,a,team,instance=fixture(index,sample_rate_hz)
    path=Path(output)/instance['scenario_id'];path.mkdir(parents=True,exist_ok=True)
    kwargs=dict(runner=team+'_11',receiver=team+'_10',carrier=team+'_8',attacking_team=team,
                start_s=0,end_s=3.48,provenance='authored synthetic 11v11 fixture; no real match or named real players')
    baseline=MovementMetrics().analyze(h,a,**kwargs);baseline['instance']=instance
    reference=MovementMetrics(MetricConfig(grid_columns=reference_grid)).analyze(h,a,**kwargs)
    coarse=baseline['space']['attacking_half']['net_m2'];fine=reference['space']['attacking_half']['net_m2']
    tolerance=max(3.,abs(fine)*.05)
    sensitivity={'reference_grid_columns':reference_grid,'reference_grid_rows':reference['grid']['rows'],
                 'baseline_net_m2':coarse,'reference_net_m2':fine,'absolute_difference_m2':abs(coarse-fine),
                 'relative_difference_pct':None if abs(fine)<1e-6 else 100*abs(coarse-fine)/abs(fine),
                 'numerical_stability_tolerance_m2':tolerance,'within_declared_tolerance':abs(coarse-fine)<=tolerance,
                 'meaning':'Numerical grid sensitivity, not real-world accuracy or a confidence interval.'}
    baseline['numerical_sensitivity']=sensitivity
    if index==0:
        variations=[]
        for label,config in [('finer-time-integration',replace(MetricConfig(),integration_step_s=.01)),
                             ('faster-defender-reaction',replace(MetricConfig(),reaction_time_def_s=.8)),
                             ('slower-defender-reaction',replace(MetricConfig(),reaction_time_def_s=1.2))]:
            alt=MovementMetrics(config).analyze(h,a,**kwargs)
            variations.append({'setting':label,'net_m2':alt['space']['attacking_half']['net_m2'],
                               'window_s':alt['receiving_window']['longest_continuous_s']})
        baseline['assumption_sensitivity']=variations
    h.to_csv(path/'home.csv',index=False);a.to_csv(path/'away.csv',index=False)
    (path/'instance.json').write_text(json.dumps(instance,indent=2))
    (path/'first-sequence-metrics.json').write_text(json.dumps(baseline,indent=2,allow_nan=False))
    (path/'reference-metrics.json').write_text(json.dumps(reference,indent=2,allow_nan=False))
    with (path/'first-sequence-evidence.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(baseline['timeline'][0]));w.writeheader();w.writerows(baseline['timeline'])
    write_report(path,baseline,h,a)
    return {'id':instance['scenario_id'],'run_id':instance['run_id'],'title':instance['title'],
            'match':instance['match_label'],'runner':kwargs['runner'],'receiver':kwargs['receiver'],
            'carrier':kwargs['carrier'],'net_m2':coarse,'penalty_net_m2':baseline['space']['penalty_area']['net_m2'],
            'defender_m':sum(d['distance_m'] for d in baseline['associated_defenders']),
            'separation_start_m':baseline['receiver']['start_separation_m'],
            'separation_end_m':baseline['receiver']['release_separation_m'],
            'window_s':baseline['receiving_window']['longest_continuous_s'],
            'grid_delta_m2':abs(coarse-fine),'grid_stable':sensitivity['within_declared_tolerance']}


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=Path('outputs/examples'))
    p.add_argument('--workers',type=int,default=2);p.add_argument('--reference-grid',type=int,default=75)
    p.add_argument('--sample-rate',type=int,choices=(25,50),default=50,
                   help='Synthetic tracking samples per second (default: 50); unrelated to pitch-control grid columns')
    p.add_argument('--case',type=int,choices=range(1,len(CASES)+1),
                   help='Recalculate one numbered case instead of the complete suite')
    args=p.parse_args();output=args.output.resolve();output.mkdir(parents=True,exist_ok=True)
    rows=[]
    selected=[args.case-1] if args.case else list(range(len(CASES)))
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        tasks={pool.submit(process_case,i,str(output),args.reference_grid,args.sample_rate):i for i in selected}
        for f in as_completed(tasks):
            row=f.result();rows.append(row);print(f"{len(rows)}/{len(selected)} {row['id']} {row['title']}: {row['net_m2']:+.2f} m²; grid difference {row['grid_delta_m2']:.2f} m²",flush=True)
    rows.sort(key=lambda r:r['id'])
    (output/'summary.json').write_text(json.dumps(rows,indent=2,allow_nan=False))
    with (output/'summary.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    items=''.join(f'<tr><td><a href="{r["id"]}/first-sequence-replay.html">{r["id"]}</a></td><td>{html.escape(r["title"])}</td><td>{r["runner"]}</td><td>{r["net_m2"]:+.2f}</td><td>{r["defender_m"]:.2f}</td><td>{r["window_s"]:.2f}</td><td>{r["grid_delta_m2"]:.2f}</td></tr>' for r in rows)
    page='''<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>BeyondTouch example gallery</title><style>body{background:#0c1820;color:#eef3ec;font:16px system-ui;margin:40px auto;max-width:1250px;padding:20px}p{line-height:1.7;color:#b6c5c1}a{color:#f5cb68}table{width:100%;border-collapse:collapse;font-size:14px}th,td{padding:14px 10px;border-bottom:1px solid #294048;text-align:left}th{color:#f5cb68}.scroll{overflow:auto}h1{font-size:40px}</style><h1>BeyondTouch</h1><h2>__CASE_COUNT__ movement examples with evidence</h2><p>All examples are authored synthetic matches between fictional Aster FC and Boreal FC. Click a run ID for its replay, match and player labels, source, and numerical evidence. These examples test numerical behaviour, not empirical real-match accuracy. xG is unavailable.</p><p>__SAMPLE_RATE__ Hz synthetic tracking · run window 0–3.48 s · 50-column baseline grid vs 75-column reference · 0.02 s numerical integration · offside filtering · fractional penalty-area cell overlap.</p><div class="scroll"><table><thead><tr><th>Run</th><th>Movement</th><th>Runner</th><th>Net model m²</th><th>Defender travel m</th><th>Window s</th><th>Grid difference m²</th></tr></thead><tbody>'''+items+'''</tbody></table></div><p>Net model m² is the isolated runner state sensitivity. Defender travel is associated observed distance, not distance caused. Window duration depends on declared thresholds. Negative-control and mirrored examples are included deliberately.</p>'''
    (output/'index.html').write_text(page.replace('__SAMPLE_RATE__',str(args.sample_rate)).replace('__CASE_COUNT__',str(len(rows))))
    print('Gallery:',output/'index.html',flush=True)


if __name__=='__main__':main()
