"""Pause / compare one spatial option at a time / reveal observed continuation."""
import numpy as np
from decision_options import analyze

def spaces(bundle,index,direction,max_count=2):
    node=analyze(bundle,direction,indices=[index])['nodes'][0];m=bundle['metrics'];L=m['coordinate_assumption']['assumed_length_m'];W=m['coordinate_assumption']['assumed_width_m'];roster={p['id']:p for p in bundle['roster']};frame=bundle['frames'][index]
    ranked=sorted((o for o in node['options'] if o['inside_pitch'] and o['endpoint_defender_gap_m'] is not None and o['endpoint_defender_gap_m']>=2),key=lambda o:(-o['heuristic_score'],o['id']));chosen=[]
    for option in ranked:
        target=np.array(option['target_normalized_xy'])*[L/100,W/100]
        if any(np.linalg.norm(target-np.array(s['target_normalized_xy'])*[L/100,W/100])<3 for s in chosen):continue
        defenders=[(p['id'],np.array([p['x']*L/100,p['y']*W/100])) for p in frame['players'] if p['id'] in roster and roster[p['id']]['team']=='defense']
        defender,pos=min(defenders,key=lambda d:(float(np.linalg.norm(d[1]-target)),d[0]))
        selected={**option,'space_label':'Space '+chr(65+len(chosen)),'snapshot_time_s':frame['t'],'source_index':index,'origin_normalized_xy':node['origin_normalized_xy'],'cover_defender_id':defender,'cover_defender_normalized_xy':(pos/[L/100,W/100]).tolist(),'cover_distance_m':float(np.linalg.norm(pos-target)),'assumption':'Compare current geometry only; future defender reactions and scoring outcomes are unknown.'};chosen.append(selected)
        if len(chosen)>=max_count:break
    return chosen

def plan(bundle,direction=None,max_count=2,interval_s=1.5,hold_s=2.5):
    direction=direction or bundle['instance'].get('attack_direction','left');frames=bundle['frames'];times=np.array([f['t'] for f in frames]);end=float(times[-1]);result=[];clock=0.
    for start in np.arange(0,end,interval_s):
        i=int(np.searchsorted(times,start+1e-8,side='right')-1);i=max(0,i)
        for option in spaces(bundle,i,direction,max_count):
            result.append({'phase':'option','video_start_s':clock,'duration_s':hold_s,'source_start_s':float(times[i]),'source_end_s':float(times[i]),'space':option});clock+=hold_s
        stop=min(end,float(start+interval_s));result.append({'phase':'reveal','video_start_s':clock,'duration_s':stop-float(start),'source_start_s':float(start),'source_end_s':stop,'space':None});clock+=stop-float(start)
    return result

def at_time(segments,time):
    segment=next((s for s in segments if time<s['video_start_s']+s['duration_s']-1e-9),segments[-1]);u=max(0,min(segment['duration_s'],time-segment['video_start_s']));source=segment['source_start_s'] if segment['phase']=='option' else min(segment['source_end_s'],segment['source_start_s']+u)
    return segment,source

def pictures(bundle,fps=5):
    from real_cases import picture
    segments=plan(bundle);times=np.array([f['t'] for f in bundle['frames']]);result=[]
    for segment in segments:
        if segment['phase']=='option':
            variant={**bundle,'active_space':segment['space'],'review_phase':'option'};im=picture(variant,segment['space']['source_index']);result.extend([im]*max(1,round(segment['duration_s']*fps)))
        else:
            for t in np.arange(segment['source_start_s'],segment['source_end_s'],1/fps):
                i=max(0,int(np.searchsorted(times,t+1e-8,side='right')-1));result.append(picture({**bundle,'review_phase':'reveal'},i))
    return result

def save_media(bundle,folder):
    """Render each unique review image once; holds use GIF/encoder durations."""
    from pathlib import Path
    import shutil,subprocess,tempfile
    from real_cases import picture
    folder=Path(folder);times=np.array([f['t'] for f in bundle['frames']]);images=[];durations=[]
    for segment in plan(bundle):
        if segment['phase']=='option':
            images.append(picture({**bundle,'active_space':segment['space'],'review_phase':'option'},segment['space']['source_index']));durations.append(2500)
        else:
            for t in np.arange(segment['source_start_s'],segment['source_end_s'],.2):
                i=max(0,int(np.searchsorted(times,t+1e-8,side='right')-1));images.append(picture({**bundle,'review_phase':'reveal'},i));durations.append(200)
    if not images:return False
    images[0].save(folder/'preview.gif',save_all=True,append_images=images[1:],duration=durations,loop=0,optimize=True)
    encoder=shutil.which('ffmpeg')
    if not encoder:
        try:
            import imageio_ffmpeg
            encoder=imageio_ffmpeg.get_ffmpeg_exe()
        except ImportError:return False
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp);lines=[]
        for i,(im,ms) in enumerate(zip(images,durations)):
            name=f'frame-{i:04d}.png';im.resize((784,700)).save(root/name);lines.extend(["file '"+name+"'",'duration '+str(ms/1000)])
        lines.append("file 'frame-"+str(len(images)-1).zfill(4)+".png'");(root/'timeline.txt').write_text('\n'.join(lines))
        subprocess.run([encoder,'-y','-loglevel','error','-f','concat','-safe','0','-i',str(root/'timeline.txt'),'-r','5','-an','-c:v','libx264','-preset','veryfast','-pix_fmt','yuv420p','-crf','23','-movflags','+faststart',str(folder/'story.mp4')],check=True)
    return True
