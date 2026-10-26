"""Validated long-form tracking import. Raw video requires a separate CV adapter."""
from pathlib import Path
import argparse,json,hashlib,math,csv,shutil,html
from urllib.parse import urlsplit
import numpy as np
import pandas as pd
from real_cases import calculate,picture,avi,ROOT
from tactical_chain import build as build_story
from decision_options import analyze as build_options

def load_tracking(path,config):
    if not isinstance(config,dict):raise ValueError('Metadata must be a JSON object')
    required=['case_id','match_title','source_name','native_hz','pitch_length_m','pitch_width_m','coordinates','attack_direction','focus_player_id']
    missing=[x for x in required if x not in config]
    if missing:raise ValueError('Missing metadata: '+', '.join(missing))
    if config['attack_direction'] not in ('left','right'):raise ValueError('attack_direction must be left or right')
    for key in ['source_url','match_context_url']:
        if config.get(key) and urlsplit(str(config[key])).scheme not in ['http','https']:raise ValueError(key+' must be an http(s) URL')
    hz=float(config['native_hz']);L=float(config['pitch_length_m']);W=float(config['pitch_width_m'])
    if not math.isfinite(hz) or not 1<=hz<=250 or not 50<=L<=130 or not 30<=W<=100:raise ValueError('Unsupported cadence or pitch dimensions')
    df=pd.read_csv(path,dtype={'player_id':str},compression='infer',keep_default_na=False)
    need={'time_s','player_id','team','x','y'}
    if not need<=set(df):raise ValueError('CSV needs '+', '.join(sorted(need)))
    if df.empty or (df.player_id.str.strip()=='').any():raise ValueError('Empty tracking or actor ID')
    for col in ['time_s','x','y']:df[col]=pd.to_numeric(df[col],errors='raise')
    if not np.isfinite(df[['time_s','x','y']].to_numpy(float)).all():raise ValueError('Coordinates and time must be finite')
    if not set(df.team)<=set(['attack','defense','ball']):raise ValueError('team must be attack, defense or ball relative to the focus team')
    if df.duplicated(['time_s','player_id']).any():raise ValueError('Duplicate player/time')
    if (df.groupby('player_id').team.nunique()!=1).any():raise ValueError('An actor changes team')
    times=np.sort(df.time_s.unique())
    if len(times)<2 or not np.allclose(np.diff(times),1/hz,atol=1e-6,rtol=0):raise ValueError('Times must have constant declared native cadence; split gaps before import')
    for pid,g in df.groupby('player_id'):
        if not np.array_equal(np.sort(g.time_s.unique()),times):raise ValueError('Changing actor coverage: '+pid)
        for col in ['name','shirt']:
            if col in g and g[col].nunique()!=1:raise ValueError('Changing actor identity: '+pid)
    balls=df.loc[df.team=='ball','player_id'].unique()
    if len(balls)!=1:raise ValueError('Exactly one tracked ball actor is required')
    focus=str(config['focus_player_id']);finisher=config.get('finisher_player_id');finisher=None if finisher in [None,''] else str(finisher)
    meta=df.drop_duplicates('player_id').set_index('player_id')
    if focus not in meta.index or meta.loc[focus,'team']!='attack':raise ValueError('Focus must be an observed attacker')
    if not (df.team=='defense').any():raise ValueError('At least one observed defender is required')
    if finisher is not None and (finisher not in meta.index or meta.loc[finisher,'team']!='attack'):raise ValueError('Configured finisher must be an observed attacker, or omitted')
    ids={balls[0]:0};ids.update({p:i+1 for i,p in enumerate(sorted(p for p in meta.index if p!=balls[0]))})
    if config['coordinates']=='normalized_0_100':xy=df[['x','y']].to_numpy(float)*[L/100,W/100]
    elif config['coordinates']=='metres':
        xy=df[['x','y']].to_numpy(float)
        if config.get('origin','bottom_left')=='centre':xy=xy+[L/2,W/2]
        elif config.get('origin','bottom_left')!='bottom_left':raise ValueError('origin must be bottom_left or centre')
    else:raise ValueError('coordinates must be metres or normalized_0_100')
    if ((xy<[-5,-5])|(xy>[L+5,W+5])).any():raise ValueError('Coordinates exceed pitch + 5 m buffer; verify units/origin')
    out=pd.DataFrame({'frame':np.rint((df.time_s-times[0])*hz).astype(int),'player':df.player_id.map(ids),'team':df.team.replace({'ball':'ball'}),'x':xy[:,0]*100/L,'y':xy[:,1]*100/W,'player_num':pd.to_numeric(df['shirt'],errors='raise') if 'shirt' in df and (df.shirt!='').all() else np.nan})
    # Missing shirt numbers are valid; parse each present value without inventing one.
    if 'shirt' in df:out['player_num']=pd.to_numeric(df.shirt.replace('',np.nan),errors='raise')
    if out.player_num.notna().any() and ((out.player_num.dropna()%1!=0).any()):raise ValueError('Shirt numbers must be integers when supplied')
    names={ids[p]:str(meta.loc[p,'name']) for p in meta.index if 'name' in meta and str(meta.loc[p,'name']).strip()}
    return out,names,ids,ids[focus],None if finisher is None else ids[finisher],hz,(L,W),float(times[0])

def generate(path,config,output,with_model=False):
    df,names,ids,focus,finisher,hz,dim,time_origin=load_tracking(path,config)
    m,roster,frames,evidence=calculate(df,focus_id=focus,source_hz=hz,field_dimen=dim,names=names)
    reverse={v:k for k,v in ids.items()}
    for p in roster:p['source_id']=reverse[p['id']];p['identity_basis']='supplied tracking metadata; not independently verified'
    focus_name=names.get(focus,reverse[focus]);m['focus_name']=focus_name
    source_hash=hashlib.sha256(Path(path).read_bytes()).hexdigest();scorer=names.get(finisher,reverse.get(finisher,'unconfirmed'))
    if finisher is not None and finisher not in names:names[finisher]=scorer;next(p for p in roster if p['id']==finisher)['name']=scorer
    instance={'id':str(config['case_id']),'kind':'imported_tracking','competition':config.get('competition','not supplied'),'short_title':str(config['match_title']),'date':str(config.get('date') or 'not supplied'),'focus_name':focus_name,'focus_shirt':m['focus_shirt'],'scorer':scorer,'goal_minute':config.get('goal_minute','unconfirmed'),'description':str(config.get('description','New user-supplied tracking sequence.')),'match_context_url':config.get('match_context_url',''),'source_url':config.get('source_url',''),'source_name':str(config['source_name']),'source_warning':config.get('source_warning','User supplied data; calibration and completeness are not independently verified.'),'source_native_hz':hz,'source_sha256':source_hash,'original_time_origin_s':time_origin,'attack_direction':config['attack_direction'],'finisher_player_id':finisher,'declared_pitch_dimensions_m':list(dim),'source_actor_mapping':ids,'clock_note':'Source-relative replay; no automatically inferred shot or possession event.'}
    m['instance']=instance;m['missing_metrics_reason']='Full calibrated pitch control, possession and shot context were not supplied; unavailable metrics are not invented.'
    dynamic=None
    if with_model:
        from dynamic_scene import calculate as model_calculate
        dynamic=model_calculate(df,focus,source_hz=hz,field_dimen=dim,reference_grid_columns=75)
        m['dynamic_scene_sensitivity']={k:v for k,v in dynamic.items() if k not in ['surface','x','y']}
    bundle={'instance':instance,'metrics':m,'roster':roster,'frames':frames,'evidence':evidence,'story_video_available':False};bundle['story']=build_story(bundle)
    if finisher is None:
        bundle['story']['steps'][-1].update(status='unavailable',text='No scorer or synchronized shot event was supplied. This sequence is analyzed without a claimed goal.')
        bundle['story']['presentation_text']=bundle['story']['presentation_text'].replace('The goal is by unconfirmed; the full space-creation link remains unconfirmed.','No finisher was supplied; the full link to a scoring action remains unconfirmed.')
    if finisher is not None:
        bundle['story']['steps'][-1].update(status='supplied_context',text='The metadata names '+scorer+' as the finisher. This identity and any goal context are supplied, not independently verified; no synchronized shot is inferred.')
        bundle['story']['presentation_text']=bundle['story']['presentation_text'].replace('The goal is by '+scorer,'The configured finisher is '+scorer).replace('The scorer then','The configured finisher then')
    bundle['decision_options']=build_options(bundle,config['attack_direction'])
    output=Path(output)
    if output.exists() and any(output.iterdir()):raise ValueError('Output folder must be empty; choose a new path to preserve existing work')
    output.mkdir(parents=True,exist_ok=True)
    for name,obj in [('metrics.json',m),('instance.json',instance),('story.json',bundle['story']),('decision-options.json',bundle['decision_options'])]:(output/name).write_text(json.dumps(obj,indent=2,allow_nan=False))
    (output/'data.js').write_text('window.REAL_CASE='+json.dumps(bundle,separators=(',',':'),allow_nan=False).replace('<','\\u003c')+';');(output/'model.js').write_text('window.DYNAMIC_MODEL='+json.dumps(dynamic,separators=(',',':'),allow_nan=False)+';')
    (output/'model-analysis.json').write_text(json.dumps(dynamic,indent=2,allow_nan=False))
    shutil.copyfile(ROOT/'src/decision-overlay.js',output/'decision-overlay.js')
    (output/'replay.html').write_text((ROOT/'src/real_replay.html').read_text().replace('href="tracking.csv.gz"','href="'+('input.csv.gz' if str(path).endswith('.gz') else 'input.csv')+'"'))
    with (output/'evidence.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(evidence[0]));w.writeheader();w.writerows(evidence)
    step=max(1,round(hz/5));pictures=[picture(bundle,i) for i in range(0,len(frames),step)];pictures[0].save(output/'preview.gif',save_all=True,append_images=pictures[1:],duration=round(step/hz*1000),loop=0);picture(bundle,len(frames)//2).save(output/'preview.png');avi(pictures,output/'video.avi')
    shutil.copyfile(path,output/('input.csv.gz' if str(path).endswith('.gz') else 'input.csv'));(output/'input-metadata.json').write_text(json.dumps(config,indent=2))
    (output/'README.md').write_text('# '+instance['short_title']+'\n\nOpen replay.html. Source: '+instance['source_name']+'; input SHA256 '+source_hash+'.\n\n'+bundle['story']['presentation_text']+'\n\nOptions are geometric snapshot alternatives, not probabilities or predicted defender responses. The imported sequence retains native '+str(hz)+' Hz.\n')
    if not (output.parent/'index.html').exists():(output.parent/'index.html').write_text('<!doctype html><meta charset="utf-8"><p><a href="'+html.escape(output.name,quote=True)+'/replay.html">Open imported sequence</a></p>')
    return bundle

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',required=True,type=Path);p.add_argument('--metadata',required=True,type=Path);p.add_argument('--output',required=True,type=Path);p.add_argument('--with-model',action='store_true');a=p.parse_args()
    try:b=generate(a.input,json.loads(a.metadata.read_text()),a.output,with_model=a.with_model)
    except (ValueError,KeyError,OSError) as e:p.exit(2,'Import rejected: '+str(e)+'\n')
    print('Imported',b['instance']['id'],'at',b['metrics']['source_native_hz'],'Hz. Open',a.output/'replay.html')
if __name__=='__main__':main()
