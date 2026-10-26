"""Reproduce observed movement metrics from credited Last Row educational tracking.

No missing players, xG or pitch-control surfaces are synthesized for these cases.
"""
from pathlib import Path
import argparse,csv,json,math,hashlib,html,io,struct
import numpy as np
import pandas as pd
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]
SOURCE='https://github.com/Friends-of-Tracking-Data-FoTD/Last-Row'
NAMES={3:'Fabinho',4:'Virgil van Dijk',5:'Georginio Wijnaldum',7:'James Milner',8:'Naby Keïta',9:'Roberto Firmino',10:'Sadio Mané',11:'Mohamed Salah',14:'Jordan Henderson',15:'Alex Oxlade-Chamberlain',20:'Adam Lallana',23:'Xherdan Shaqiri',26:'Andy Robertson',27:'Divock Origi',32:'Joël Matip',66:'Trent Alexander-Arnold'}
# Match context is corroborated by the linked primary match reports. Source clips
# have no event-synchronized clock; source frame zero is not kickoff or pass release.
CASES=[
 (2,'bournemouth-away',8,'2019-12-07','Mohamed Salah',54,'https://www.liverpoolfc.com/matches/mens-team/results/2019','A supporting run by Naby Keïta in the sequence labelled Bournemouth 0–3 Liverpool.'),
 (3,'fulham',9,'2019-03-17','Sadio Mané',26,'https://www.premierleague.com/en/news/1088244/match-summary','Firmino is the focus during the move ending in Mané’s opener.'),
 (5,'leicester',66,'2019-12-26','Roberto Firmino',74,'https://www.premierleague.com/en/news/1545247','Alexander-Arnold’s movement in the sequence before Liverpool’s third goal.'),
 (6,'everton-opener',10,'2019-12-04','Divock Origi',6,'https://www.premierleague.com/news/1514819','Mané’s movement in the move that puts Origi through for the opener.'),
 (7,'watford',10,'2019-12-14','Mohamed Salah',38,'https://www.premierleague.com/en/news/1524772/match-summary','Mané is the focus in the counterattack leading to Salah’s first goal.'),
 (8,'wolves',66,'2019-05-12','Sadio Mané',17,'https://www.wolves.co.uk/news/mens-first-team/20190512-liverpool-2-0-wolves-match-report/','Alexander-Arnold is the focus in the sequence ending in Mané’s opening goal.'),
 (9,'everton-second',10,'2019-12-04','Xherdan Shaqiri',17,'https://www.premierleague.com/news/1514819','Mané is the focus in the move ending with Shaqiri’s goal.'),
 (10,'man-city',26,'2019-11-10','Mohamed Salah',13,'https://www.premierleague.com/en/news/1492744','Robertson is the focus in the move ending in Salah’s header.'),
 (14,'newcastle',9,'2019-09-14','Sadio Mané',40,'https://www.premierleague.com/es/news/1335098','Firmino is the focus in the sequence ending in Mané’s second goal.'),
 (15,'bournemouth-home',9,'2019-02-09','Mohamed Salah',48,'https://www.premierleague.com/en/news/1048354','Firmino is the focus in the move ending in Salah’s goal.'),
 (16,'norwich',14,'2019-08-09','Virgil van Dijk',28,'https://www.liverpoolfc.com/news/first-team/359939-liverpool-norwich-match-report-premier-league','Henderson is the observed focus player around Liverpool’s third goal; this is not a claim of an assist.'),
 (19,'southampton',11,'2019-04-05','Mohamed Salah',80,'https://www.premierleague.com/en/news/1157086','Salah’s run and carry before Liverpool take a 2–1 lead. This clip includes on-ball movement.')
]

def calculate(df,focus_number=None,*,focus_id=None,source_hz=20,field_dimen=(105,68),names=None):
    if not {'frame','player','team','x','y','player_num'}<=set(df):raise ValueError('Missing Last Row columns')
    if df.duplicated(['player','frame']).any():raise ValueError('Duplicate player/frame')
    frames=np.sort(df.frame.unique());times=(frames-frames[0])/source_hz
    scale=np.array(field_dimen,dtype=float)/100
    if len(frames)<2 or not np.all(np.diff(frames)==1):raise ValueError('Source frame gap; split the clip')
    if not np.isfinite(df[['x','y']].to_numpy()).all():raise ValueError('Missing coordinates')
    candidates=df[(df.team=='attack')&((df.player==focus_id) if focus_id is not None else (df.player_num==focus_number))].player.unique()
    if len(candidates)!=1:raise ValueError('Focus shirt must map to exactly one local player ID')
    focus=int(candidates[0]);tracks={}
    for pid,g in df.groupby('player'):
        g=g.sort_values('frame')
        if not np.array_equal(g.frame.to_numpy(),frames):raise ValueError('Changing coverage within clip')
        tracks[int(pid)]=g[['x','y']].to_numpy(float)*scale
    if focus_number is None:
        value=df.loc[df.player==focus,'player_num'].iloc[0];focus_number=None if pd.isna(value) else int(value)
    focus_name=(names.get(focus,f'Attacker {focus}') if names is not None else NAMES.get(focus_number,f'Liverpool #{focus_number}'))
    meta=df[['player','team','player_num']].drop_duplicates().set_index('player')
    defenders=[p for p in tracks if p!=0 and meta.loc[p,'team']=='defense']
    attackers=[p for p in tracks if p!=0 and meta.loc[p,'team']=='attack']
    if not defenders:raise ValueError('No observed defenders')
    def travel(p):return float(np.linalg.norm(np.diff(tracks[p],axis=0),axis=1).sum())
    nearest=sorted(defenders,key=lambda p:float(np.linalg.norm(tracks[p][0]-tracks[focus][0])))
    near=[p for p in nearest if np.linalg.norm(tracks[p][0]-tracks[focus][0])<=10][:2]
    gaps=np.min(np.stack([np.linalg.norm(tracks[p]-tracks[focus],axis=1) for p in defenders]),axis=0)
    path=travel(focus);displacement=float(np.linalg.norm(tracks[focus][-1]-tracks[focus][0]))
    clearance=float(np.diff(times)[gaps[:-1]>=3].sum())
    # This is separation time only; do not call it the full model receiving window.
    metrics={'schema_version':'real-observed-1','source_native_hz':source_hz,'display_hz':50,
      'display_interpolation_only':True,'sample_count':len(frames),'duration_s':float(times[-1]),
      'focus_player_id':focus,'focus_shirt':focus_number,'focus_name':focus_name,
      'coordinate_assumption':{'input':'0–100 normalized pitch axes','assumed_length_m':field_dimen[0],'assumed_width_m':field_dimen[1],'actual_pitch_calibration_verified':False},
      'focus_path_nominal_m':path,'focus_displacement_nominal_m':displacement,
      'directness_ratio':None if path<1e-9 else displacement/path,
      'nearest_observed_defender_start_nominal_m':float(gaps[0]),'nearest_observed_defender_end_nominal_m':float(gaps[-1]),
      'nearest_observed_defender_min_nominal_m':float(gaps.min()),'nearest_observed_defender_max_nominal_m':float(gaps.max()),
      'separation_at_least_3m_s':clearance,'separation_time_is_receiving_window':False,
      'associated_defenders':[{'source_player_id':p,'observed_path_nominal_m':travel(p),'initial_gap_nominal_m':float(np.linalg.norm(tracks[p][0]-tracks[focus][0]))} for p in near],
      'associated_defender_path_sum_nominal_m':sum(travel(p) for p in near) if near else None,
      'coverage':{'observed_attackers':len(attackers),'observed_defenders':len(defenders),'complete_22_player_tracking':len(attackers)==11 and len(defenders)==11,'research_accuracy_verified':False},
      'control_equivalent_area_m2':None,'candidate_receiving_window_s':None,'xg':None,
      'missing_metrics_reason':'Educational source warns of incomplete player coverage and insufficient research accuracy; full pitch control, onside eligibility and xG are not asserted.',
      'selection_rule':'Up to two observed defenders within 10 nominal metres at source clip start; no goalkeeper identification or causal assignment.'}
    roster=[]
    for p in sorted(tracks):
        if p==0:continue
        row=meta.loc[p];num=None if pd.isna(row.player_num) else int(row.player_num)
        name=names.get(p) if names is not None else NAMES.get(num) if row.team=='attack' and num is not None else None
        roster.append({'id':p,'team':str(row.team),'shirt':num,'name':name,'identity_basis':'source shirt number and Liverpool 2019 context' if name else 'local source ID only'})
    replay=[];evidence=[]
    for i,t in enumerate(times):
        replay.append({'t':float(t),'players':[{'id':p,'x':round(float(tracks[p][i,0]/scale[0]),5),'y':round(float(tracks[p][i,1]/scale[1]),5)} for p in sorted(tracks)]})
        evidence.append({'source_frame':int(frames[i]),'time_s':float(t),'focus_path_nominal_m':float(np.linalg.norm(np.diff(tracks[focus][:i+1],axis=0),axis=1).sum()),'nearest_observed_defender_nominal_m':float(gaps[i]),'separation_at_least_3m':bool(gaps[i]>=3)})
    return metrics,roster,replay,evidence

def font(size):
    return ImageFont.load_default(size=size)

def base_picture(bundle,index):
    m=bundle['metrics'];f=bundle['frames'][index];im=Image.new('RGB',(1120,760),'#0c1820');d=ImageDraw.Draw(im)
    from story_media import safe_text
    original_text=d.text;d.text=lambda xy,text,*a,**kw:original_text(xy,safe_text(text),*a,**kw)
    d.text((28,18),'BEYONDTOUCH / '+str(bundle['instance'].get('competition','Tracking movement')),font=font(27),fill='white')
    d.text((28,58),bundle['instance']['short_title']+' | '+bundle['instance']['date'],font=font(16),fill='#baccca')
    d.text((28,85),f"Source {m['source_native_hz']:g} Hz | declared {m['coordinate_assumption']['assumed_length_m']:g} x {m['coordinate_assumption']['assumed_width_m']:g} m | calibration unverified",font=font(14),fill='#f5cb68')
    def xy(p):return (30+p['x']*8.4,130+(100-p['y'])*5.712)
    d.rectangle((30,130,870,701),fill='#174c41',outline='#a3c1ac',width=2)
    d.line((450,130,450,701),fill='#a3c1ac',width=2);d.ellipse((377,342,523,488),outline='#a3c1ac',width=2)
    for x1,x2 in [(30,162),(738,870)]:d.rectangle((x1,246,x2,585),outline='#a3c1ac',width=2)
    trail=[xy(next(p for p in q['players'] if p['id']==m['focus_player_id'])) for q in bundle['frames'][:index+1]]
    if len(trail)>1:d.line(trail,fill='#f5cb68',width=3)
    roster={p['id']:p for p in bundle['roster']}
    for p in f['players']:
        x,y=xy(p)
        if p['id']==0:d.ellipse((x-5,y-5,x+5,y+5),fill='white',outline='black');continue
        r=roster[p['id']];color='#e27373' if r['team']=='attack' else '#769de5'
        if p['id']==m['focus_player_id']:color='#f5cb68'
        d.ellipse((x-11,y-11,x+11,y+11),fill=color,outline='#0c1820',width=2)
        if r['shirt'] is not None:d.text((x,y),str(r['shirt']),font=font(11),fill='#0c1820',anchor='mm')
    e=bundle['evidence'][index]
    for y,label,value in [(145,'CLIP TIME',f"{f['t']:.2f} s"),(245,'FOCUS',m['focus_name']),(345,'PATH SO FAR',f"≈ {e['focus_path_nominal_m']:.2f} m"),(445,'OBSERVED GAP',f"≈ {e['nearest_observed_defender_nominal_m']:.2f} m")]:
        d.text((895,y),label,font=font(13),fill='#baccca');d.text((895,y+30),value,font=font(17),fill='#f5cb68')
    d.text((30,719),'Partial coverage · illustrative measurements · no xG or causal defender attribution',font=font(15),fill='#baccca')
    return im

def picture(bundle,index):
    base=base_picture(bundle,index)
    if 'story' not in bundle:return base
    from story_media import render
    return render(base,bundle,index)

def avi(frames,path):
    pack=lambda *x:struct.pack('<'+'I'*len(x),*x)
    def chunk(tag,b):return tag+pack(len(b))+b+(b'\0' if len(b)%2 else b'')
    def listing(tag,b):return chunk(b'LIST',tag+b)
    data=[]
    for f in frames:
        b=io.BytesIO();f.resize((784,700)).save(b,format='JPEG',quality=65);data.append(b.getvalue())
    w,h,fps=784,700,5;big=max(map(len,data));avih=pack(200000,big*fps,0,16,len(data),0,1,big,w,h,0,0,0,0)
    sh=struct.pack('<4s4sIHHIIIIIIIIhhhh',b'vids',b'MJPG',0,0,0,0,1,fps,0,len(data),big,0xffffffff,0,0,0,w,h)
    sf=struct.pack('<IiiHH4sIiiII',40,w,h,1,24,b'MJPG',w*h*3,0,0,0,0)
    hd=listing(b'hdrl',chunk(b'avih',avih)+listing(b'strl',chunk(b'strh',sh)+chunk(b'strf',sf)));mov=b'';ix=b'';off=4
    for b in data:
        c=chunk(b'00dc',b);mov+=c;ix+=struct.pack('<4sIII',b'00dc',16,off,len(b));off+=len(c)
    body=b'AVI '+hd+listing(b'movi',mov)+chunk(b'idx1',ix);path.write_bytes(b'RIFF'+pack(len(body))+body)

def generate(case_number,output,with_model=True):
    spec=CASES[case_number-1];srcnum,slug,shirt,date,scorer,minute,link,description=spec
    saved=ROOT/'examples'/f'pl-{case_number:02d}-{slug}';source=saved/'tracking.csv.gz'
    df=pd.read_csv(source);m,roster,frames,evidence=calculate(df,shirt)
    instance={'id':f'PL-{case_number:02d}','kind':'real_educational_tracking','competition':'Premier League',
      'source_play':str(df.play.iloc[0]),'source_case_number':srcnum,'short_title':str(df.play.iloc[0]).replace('[','').replace(']',''),
      'date':date,'scorer':scorer,'goal_minute':minute,'focus_name':m['focus_name'],'focus_shirt':shirt,
      'description':description,'match_context_url':link,'source_url':SOURCE,'source_native_hz':20,
      'source_git_blob_sha':'77e053fba2f9569a60cd41d87a817bee0028c2c2',
      'tracking_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
      'clock_note':'Source-relative clip time only; no event-synchronized pass-release or goal frame is supplied.',
      'fixture_mapping_note':'Match context inferred from source play label, 2019 collection and known Liverpool shirt identities, corroborated with linked official reports. Exact frame-to-broadcast synchronization is unavailable.',
      'source_warning':'Ricardo Tavares / Last Row describes these as educational animations with incomplete player coverage and insufficient research accuracy.'}
    if with_model:
        from dynamic_scene import calculate as model_calculate
        dynamic=model_calculate(df,m['focus_player_id'],reference_grid_columns=75)
        m['dynamic_scene_sensitivity']={k:v for k,v in dynamic.items() if k not in ['surface','x','y']}
    else:dynamic=None
    m['instance']=instance;bundle={'instance':instance,'metrics':m,'roster':roster,'frames':frames,'evidence':evidence}
    from tactical_chain import build as build_story
    bundle['story']=build_story(bundle)
    output.mkdir(parents=True,exist_ok=True)
    (output/'story.json').write_text(json.dumps(bundle['story'],indent=2,allow_nan=False))
    (output/'story.js').write_text('window.TACTICAL_STORY='+json.dumps(bundle['story'],separators=(',',':'),allow_nan=False).replace('<','\\u003c')+';')
    (output/'metrics.json').write_text(json.dumps(m,indent=2,allow_nan=False));(output/'instance.json').write_text(json.dumps(instance,indent=2))
    (output/'data.js').write_text('window.REAL_CASE='+json.dumps(bundle,separators=(',',':'),allow_nan=False).replace('<','\\u003c')+';')
    (output/'model.js').write_text('window.DYNAMIC_MODEL='+json.dumps(dynamic,separators=(',',':'),allow_nan=False)+';')
    (output/'model-analysis.json').write_text(json.dumps(dynamic,indent=2,allow_nan=False))
    with (output/'evidence.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(evidence[0]));w.writeheader();w.writerows(evidence)
    import shutil
    shutil.copyfile(ROOT/'src/decision-overlay.js',output/'decision-overlay.js')
    (output/'replay.html').write_text((ROOT/'src/real_replay.html').read_text())
    pictures=[picture(bundle,i) for i in range(0,len(frames),4)]
    pictures[0].save(output/'preview.gif',save_all=True,append_images=pictures[1:],duration=200,loop=0,optimize=True)
    picture(bundle,len(frames)//2).save(output/'preview.png');avi(pictures,output/'video.avi')
    from refresh_stories import encode_mp4
    bundle['story_video_available']=encode_mp4(output)
    (output/'data.js').write_text('window.REAL_CASE='+json.dumps(bundle,separators=(',',':'),allow_nan=False).replace('<','\\u003c')+';')
    ds=m['associated_defender_path_sum_nominal_m'];dtext='not selected' if ds is None else f'≈ {ds:.2f} m'
    text=f'''# {instance['id']} · {instance['short_title']}

**Real Premier League event · educational hand-collected trajectories · 20 Hz source**

![Replay](preview.gif)

[Annotated video](video.avi) · [Interactive replay](replay.html) after extracting the repository

{date} · goal context: {scorer}, {minute}′. [Official match context]({link}). Source play label: `{instance['source_play']}`. Focus: **{m['focus_name']} #{shirt}**, local source ID **{m['focus_player_id']}**. {description}

| Observed measure | Result |
| --- | ---: |
| Source clip duration | {m['duration_s']:.2f} s |
| Focus path length | ≈ {m['focus_path_nominal_m']:.2f} nominal m |
| Focus displacement | ≈ {m['focus_displacement_nominal_m']:.2f} nominal m |
| Start → end nearest observed defender gap | ≈ {m['nearest_observed_defender_start_nominal_m']:.2f} → {m['nearest_observed_defender_end_nominal_m']:.2f} nominal m |
| Associated observed defenders’ combined path | {dtext} |
| Time with observed gap ≥ 3 nominal m | {m['separation_at_least_3m_s']:.2f} s |
| Observed attackers / defenders | {m['coverage']['observed_attackers']} / {m['coverage']['observed_defenders']} |
| Full pitch control / receiving window / xG | unavailable |

## Interpretation

These are source-window measurements, not a certified off-ball-only interval. Some focus players carry or pass the ball during the clip. Distances scale the source’s normalized coordinates onto an **assumed 105 × 68 m pitch**; actual calibration is unverified. Missing players can make nearest-observed-defender gaps too large. Associated travel is not distance caused by the focus player. The ≥3 m time is a separation-only diagnostic, **not** the full candidate receiving window from the synthetic model.

The native samples remain 20 Hz. The browser interpolates positions for a 50 Hz display; the exported animation/video is 5 fps. Interpolation does not add observations or measurement accuracy. The underlying [Last Row source]({SOURCE}) explicitly warns that these trajectories lack research accuracy. Credit: Ricardo Tavares / Last Row / Friends of Tracking. No broadcast footage is redistributed.

## Evidence and reproduction

`tracking.csv.gz` is the credited source subset; `metrics.json` contains exact results and assumptions; `evidence.csv` contains native timestamped measurements; `instance.json` records source and match context; `data.js` is the replay payload. Opponents without a confirmed shirt/name remain local IDs in the replay roster. The source frame clock is not a verified broadcast clock.

From the repository root: `bash run.sh --case {case_number}` or `run.bat --case {case_number}`. This recalculates the real-data measurements. Synthetic pitch-control tests remain available separately.
'''
    text+='\n## Tactical story: run, response, cover, finish\n\n'+bundle['story']['presentation_text']+'\n\n'+'\n\n'.join('**'+step['title']+' ['+step['status']+']** — '+step['text'] for step in bundle['story']['steps'])+'\n\nExact selection rules, times and player IDs: story.json. These are geometric candidates, not learned or causal defender assignments.\n'
    (output/'README.md').write_text(text)
    if dynamic:
        with (output/'README.md').open('a') as f:f.write(f"\n## Moving-scene model contrast\n\nConditional endpoint sensitivity: **{dynamic['area']['net_m2']:+.2f} nominal m²** over the whole pitch. All other observed players and the ball use their actual endpoint states; only the focus player is held at its initial position and velocity in the reference. This does not freeze unrelated players. It remains a partial-coverage model diagnostic, not causal or complete-match attribution. Offside/GK identities are unconfirmed. See model-analysis.json.\n")
    return {'id':instance['id'],'folder':saved.name,'title':instance['short_title'],'date':date,'focus':m['focus_name'],'path_nominal_m':m['focus_path_nominal_m'],'duration_s':m['duration_s'],'source_hz':20,'observed_attackers':m['coverage']['observed_attackers'],'observed_defenders':m['coverage']['observed_defenders'],'dynamic_net_m2':None if dynamic is None else dynamic['area']['net_m2']}

def main():
    p=argparse.ArgumentParser();p.add_argument('--case',type=int,choices=range(1,13));p.add_argument('--output',type=Path,default=ROOT/'outputs/examples');p.add_argument('--observations-only',action='store_true');args=p.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    rows=[]
    for n in ([args.case] if args.case else range(1,13)):
        folder=ROOT/'examples'/f'pl-{n:02d}-{CASES[n-1][1]}'
        row=generate(n,args.output/folder.name,with_model=not args.observations_only);rows.append(row);print(f"{row['id']}: {row['focus']}, ≈ {row['path_nominal_m']:.2f} nominal m; moving-scene {row['dynamic_net_m2']} nominal m²",flush=True)
    (args.output/'summary.json').write_text(json.dumps(rows,indent=2))
    links=''.join('<li><a href="'+r['folder']+'/replay.html">'+html.escape(r['title']+' · '+r['focus'])+'</a></li>' for r in rows)
    (args.output/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>BeyondTouch recalculated real cases</title><style>body{background:#0c1820;color:#eef3ec;font:18px system-ui;padding:40px}a{color:#f5cb68}li{margin:18px}</style><h1>Recalculated real Premier League cases</h1><p>Educational partial tracking. Native 20 Hz; distances assume 105 × 68 m. These are approximate observations, not full pitch control or xG.</p><ul>'+links+'</ul>')

if __name__=='__main__':main()
