"""50 fps interpolated presentation of real 20 Hz observations; no new tracking."""
from pathlib import Path
import argparse,json,math,subprocess,shutil,hashlib
from functools import lru_cache
from PIL import Image,ImageDraw,ImageFont
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
CASE=ROOT/'examples/pl-04-everton-opener'
FPS=50;DURATION=27;SIZE=(1920,1080)
COLORS={'RUN':'#f5cb68','D1':'#ff9d5c','D2':'#59d9e8','FIN':'#cf9cff'}

def load():
    b=json.loads((CASE/'data.js').read_text().split('=',1)[1].rstrip(';\n'))
    times=np.array([f['t'] for f in b['frames']]);ids=[p['id'] for p in b['frames'][0]['players']]
    tracks={pid:np.array([[next(p for p in f['players'] if p['id']==pid)[k] for k in ['x','y']] for f in b['frames']])*[1.05,.68] for pid in ids}
    return b,times,tracks
B,T,TRACKS=load();S=B['story'];M=B['metrics'];ROSTER={p['id']:p for p in B['roster']}
@lru_cache(maxsize=32)
def font(n):return ImageFont.load_default(size=n)
def txt(d,xy,s,n=22,fill='#edf3ef',**kw):
    from story_media import safe_text
    d.text(xy,safe_text(s),font=font(n),fill=fill,**kw)
def at(pid,t):return np.array([np.interp(t,T,TRACKS[pid][:,j]) for j in range(2)])
def xy(p):return (55+p[0]*10,315+(68-p[1])*10)
def arrow(d,a,z,color):
    if math.dist(a,z)<3:return
    d.line([a,z],fill=color,width=5);angle=math.atan2(z[1]-a[1],z[0]-a[0]);L=16
    d.polygon([z,(z[0]-L*math.cos(angle-.5),z[1]-L*math.sin(angle-.5)),(z[0]-L*math.cos(angle+.5),z[1]-L*math.sin(angle+.5))],fill=color)
def frame(video_time,poster=False,source_time=None,active_space=None,review_phase=None):
    t=2.6 if poster else source_time if source_time is not None else min(M['duration_s'],max(0.,(video_time-3)/2))
    if poster:
        from guided_review import spaces
        options=spaces(B,min(len(B['frames'])-1,int(t*20)),'left');active_space=options[0] if options else None;review_phase='option'
    im=Image.new('RGB',SIZE,'#0c1820');d=ImageDraw.Draw(im)
    txt(d,(50,27),'BEYONDTOUCH',37,COLORS['RUN']);txt(d,(50,90),'Pause. Compare spaces. Reveal the play.',46)
    txt(d,(50,156),'Liverpool v Everton | 4 December 2019 | Mane movement / Origi goal context',23,'#baccca')
    path_now=float(np.interp(t,T,[e['focus_path_nominal_m'] for e in B['evidence']]))
    stats=[(50,'PATH SO FAR',f"{path_now:.2f} m",'Observed source movement only'),(425,'POCKET SEPARATION' if active_space else 'NATIVE SOURCE',f"{active_space['endpoint_defender_gap_m']:.2f} m" if active_space else '20 Hz','Current snapshot, not a prediction'),(800,'COVER DISTANCE' if active_space else 'PRESENTATION',f"{active_space['cover_distance_m']:.2f} m" if active_space else '50 fps','Current geometry' if active_space else 'Interpolated display')]
    for x,label,value,note in stats:
        d.rounded_rectangle((x,200,x+350,285),radius=12,fill='#13252c',outline='#294048');txt(d,(x+14,208),label,15,'#baccca');txt(d,(x+14,229),value,30,COLORS['RUN']);txt(d,(x+14,264),note,13,'#baccca')
    # Pitch at ten pixels per nominal metre, using source orientation.
    d.rectangle((55,315,1105,995),fill='#174c41',outline='#a8cbb2',width=2);d.line((580,315,580,995),fill='#a8cbb2',width=2)
    d.ellipse((488.5,563.5,671.5,746.5),outline='#a8cbb2',width=2)
    for x1,x2 in [(55,220),(940,1105)]:d.rectangle((x1,453.4,x2,856.6),outline='#a8cbb2',width=2)
    roles=[(S['focus_player_id'],'RUN'),(S['response']['player_id'],'D1'),(S['cover']['player_id'],'D2'),(S['finisher_player_id'],'FIN')]
    if active_space:roles=[(S['focus_player_id'],'RUN'),(active_space['cover_defender_id'],'DEF')];COLORS['DEF']='#e898d0'
    for pid,role in roles:
        points=[xy(at(pid,float(q))) for q in np.r_[np.arange(max(0,t-1.5),t,.05),t]]
        if len(points)>1:d.line(points,fill=COLORS[role],width=5)
        arrow(d,xy(at(pid,max(0,t-.4))),xy(at(pid,t)),COLORS[role])
    if not active_space and t>=S['cover']['end_s']:
        x,y=xy(S['cover']['anchor_nominal_xy']);d.ellipse((x-30,y-30,x+30,y+30),outline=COLORS['D2'],width=2);txt(d,(x+35,y-15),'D1 earlier location',15,COLORS['D2'],stroke_width=1,stroke_fill='#0c1820')
    for pid in TRACKS:
        x,y=xy(at(pid,t));ball=pid==0;role=next((r for p,r in roles if p==pid),None)
        color='white' if ball else COLORS[role] if role else '#e27373' if ROSTER[pid]['team']=='attack' else '#769de5';radius=5 if ball else 12
        d.ellipse((x-radius,y-radius,x+radius,y+radius),fill=color,outline='#0c1820',width=2)
        if role:txt(d,(x+15,y-24),role,17,color,stroke_width=2,stroke_fill='#0c1820')
        elif not ball and ROSTER[pid]['shirt'] is not None:txt(d,(x,y),str(ROSTER[pid]['shirt']),11,'#0c1820',anchor='mm')
    if active_space:
        origin=np.array(active_space['origin_normalized_xy'])*[1.05,.68];target=np.array(active_space['target_normalized_xy'])*[1.05,.68];a,z=xy(origin),xy(target)
        d.ellipse((z[0]-24,z[1]-24,z[0]+24,z[1]+24),fill='#267255',outline='#77e0ab',width=3);arrow(d,a,z,'#77e0ab')
        defender=np.array(active_space['cover_defender_normalized_xy'])*[1.05,.68];arrow(d,xy(defender),z,'#e898d0');txt(d,(z[0]+29,z[1]),active_space['space_label'],20,'#77e0ab',stroke_width=1,stroke_fill='#0c1820')
    txt(d,(70,329),f'Source clip: {t:.2f} s',19,stroke_width=2,stroke_fill='#0c1820')
    txt(d,(70,962),'Green: one possible space | Pink: illustrative cover distance' if active_space else 'Observed continuation: all represented players keep moving',18,stroke_width=2,stroke_fill='#0c1820')
    d.rounded_rectangle((1170,30,1870,995),radius=20,fill='#13252c',outline='#294048',width=2)
    txt(d,(1200,57),'THE NUMBERS BEHIND THE RUN',25,COLORS['RUN']);txt(d,(1200,102),'Real movement. Clear evidence.',31)
    txt(d,(1200,158),'50 fps | 20 Hz source | pauses before each reveal',20,'#baccca')
    if active_space:
        steps=[('ATTACKING VIEW | '+active_space['space_label'],f"This pocket has {active_space['endpoint_defender_gap_m']:.2f} m defender separation.",'One possible space; not an optimal decision.','#77e0ab'),('DEFENDING VIEW',f"Observed defender {active_space['cover_defender_id']} is {active_space['cover_distance_m']:.2f} m away.",'Pink line = illustrative cover distance.','#e898d0'),('NEXT: COMPARE, THEN REVEAL','Another space is shown separately, not all at once.','Then watch what the attacker actually did.',COLORS['RUN']),('WHAT THE MODEL CAN SAY','Snapshot geometry, not predicted reactions.','Future observed movement is not used to score.',COLORS['FIN'])];active=0
    else:
        steps=[('OBSERVED CONTINUATION','Watch the actual attacker and defender movements.','These are source observations, not a simulation.',COLORS['RUN']),('ATTACKING VIEW','Compare the run with the spaces just shown.','The alternatives did not change the recorded play.','#77e0ab'),('DEFENDING VIEW','Watch who shifts and which pockets stay open.','Do not infer marking intent from motion alone.','#e898d0'),('NEXT DECISION POINT','Pause again, compare spaces, then reveal.','No permanent fan of arrows on the pitch.',COLORS['FIN'])];active=0
    for i,(title,a,z,color) in enumerate(steps):
        y=215+i*157;d.rounded_rectangle((1195,y,1845,y+137),radius=12,fill='#203a3e' if i==active else '#102128',outline=color if i==active else '#294048',width=3 if i==active else 1)
        txt(d,(1210,y+17),title,23,color);txt(d,(1210,y+58),a,20);txt(d,(1210,y+94),z,18,'#baccca')
    txt(d,(1200,868),'Explore 12 real Premier League cases.',23);txt(d,(1200,908),'Replay + metrics + story + source evidence',19,'#baccca')
    txt(d,(1200,948),'Extract the project. Open START_HERE.html.',19,COLORS['RUN'])
    txt(d,(50,1028),'Educational partial tracking | nominal 105 x 68 m | source: Last Row / Ricardo Tavares / Friends of Tracking',18,'#baccca')
    txt(d,(50,1054),'50 fps is interpolated presentation, not 50 Hz tracking or VAR validation. Model foundations: Bassel Hammad and coauthors.',16,'#baccca')
    return im

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--preview',type=Path);a=parser.parse_args()
    if a.preview:frame(0,poster=True).save(a.preview);return
    import imageio_ffmpeg
    exe=shutil.which('ffmpeg') or imageio_ffmpeg.get_ffmpeg_exe();out=ROOT/'uploads/BeyondTouch-Liverpool-50fps.mp4'
    out.parent.mkdir(exist_ok=True)
    cmd=[exe,'-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r','50','-i','-','-an','-c:v','libx264','-preset','veryfast','-crf','22','-pix_fmt','yuv420p','-movflags','+faststart',str(out)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    from guided_review import plan,at_time
    segments=plan(B,'left',max_count=2);duration=segments[-1]['video_start_s']+segments[-1]['duration_s']+6;count=round(FPS*duration)
    for n in range(count):
        segment,t=at_time(segments,max(0,n/FPS-3));proc.stdin.write(frame(n/FPS,source_time=t,active_space=segment['space'],review_phase=segment['phase']).tobytes())
    proc.stdin.close();assert proc.wait()==0
    frame(0,poster=True).save(ROOT/'uploads/BeyondTouch-Liverpool.png')
    probe=subprocess.run([exe,'-i',str(out)],capture_output=True,text=True).stderr
    assert '1920x1080' in probe and '50 fps' in probe 
    meta={'case_id':'PL-04','match':'Liverpool v Everton','date':'2019-12-04','focus':'Sadio Mane','goal_context':'Divock Origi 6th minute','width':1920,'height':1080,'codec':'h264','pixel_format':'yuv420p','output_fps':50,'source_tracking_hz':20,'positions_interpolated_before_rendering':True,'playback_source_speed':1,'review_mode':'pause_compare_one_space_at_a_time_reveal','max_options_per_pause':2,'duration_s':count/FPS,'encoded_frames':count,'source_sha256':B['instance']['tracking_sha256'],'mp4_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'no_causal_attribution':True}
    (ROOT/'uploads/Liverpool-50fps-metadata.json').write_text(json.dumps(meta,indent=2))
if __name__=='__main__':main()
