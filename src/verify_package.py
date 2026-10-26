"""Audit judge assets while keeping real, rendered and synthetic evidence distinct."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote,urlsplit
import hashlib,json,math,io,struct
from PIL import Image
import pandas as pd
from real_cases import calculate
ROOT=Path(__file__).resolve().parents[1]
class Links(HTMLParser):
    def __init__(self):super().__init__();self.targets=[]
    def handle_starttag(self,tag,attrs):
        for k,v in attrs:
            if k in ('href','src') and v:self.targets.append(v)
def check_avi(path):
    b=path.read_bytes();assert b[:4]==b'RIFF' and b[8:12]==b'AVI '
    assert struct.unpack('<I',b[4:8])[0]+8==len(b)
    offset=b.index(b'movi')+4;count=0
    while b[offset:offset+4]==b'00dc':
        n=struct.unpack('<I',b[offset+4:offset+8])[0];Image.open(io.BytesIO(b[offset+8:offset+8+n])).verify();count+=1;offset+=8+n+(n%2)
    assert count>1
def same_evidence(a,b):
    if isinstance(a,dict):return isinstance(b,dict) and a.keys()==b.keys() and all(same_evidence(a[k],b[k]) for k in a)
    if isinstance(a,list):return isinstance(b,list) and len(a)==len(b) and all(same_evidence(x,y) for x,y in zip(a,b))
    if isinstance(a,float) or isinstance(b,float):return isinstance(a,(float,int)) and isinstance(b,(float,int)) and math.isclose(a,b,abs_tol=1e-8,rel_tol=1e-10)
    return a==b

def verify():
    cases=sorted((ROOT/'examples').glob('pl-[0-9][0-9]-*'));assert len(cases)==12
    for c in cases:
        required=['README.md','replay.html','data.js','metrics.json','evidence.csv','instance.json','tracking.csv.gz','story.json','story.js','model.js','model-analysis.json','preview.gif','preview.png','video.avi']
        assert all((c/n).is_file() for n in required),c
        m=json.loads((c/'metrics.json').read_text());b=json.loads((c/'data.js').read_text().split('=',1)[1].rstrip(';\n'))
        recomputed,*_=calculate(pd.read_csv(c/'tracking.csv.gz'),m['focus_shirt'])
        assert m['instance']['tracking_sha256']==hashlib.sha256((c/'tracking.csv.gz').read_bytes()).hexdigest()
        assert m['source_native_hz']==20 and m['display_hz']==50 and m['display_interpolation_only']
        for k in ['focus_path_nominal_m','focus_displacement_nominal_m','separation_at_least_3m_s']:assert math.isclose(m[k],recomputed[k],abs_tol=1e-8)
        for k in ['control_equivalent_area_m2','candidate_receiving_window_s','xg']:assert m[k] is None
        dm=json.loads((c/'model-analysis.json').read_text());assert dm['all_other_players_use_actual_endpoint_state'] and dm['ball_uses_actual_endpoint_position']
        assert not dm['is_causal_effect'] and not dm['is_full_match_pitch_control']
        assert math.isclose(dm['area']['gained_m2']-dm['area']['lost_m2'],dm['area']['net_m2'],abs_tol=1e-8)
        from tactical_chain import build as build_story
        story=json.loads((c/'story.json').read_text());assert same_evidence(story,build_story(b)),c
        assert story['causal_attraction_established'] is False
        if b.get('story_video_available'):assert (c/'story.mp4').read_bytes()[4:8]==b'ftyp'
        assert not m['coverage']['research_accuracy_verified']
        assert len(b['frames'])==m['sample_count']==len(b['evidence'])
        assert all(math.isclose(y['t']-x['t'],.05,abs_tol=1e-8) for x,y in zip(b['frames'],b['frames'][1:]))
        check_avi(c/'video.avi');assert Image.open(c/'preview.gif').n_frames>1
    wc=ROOT/'examples/di-maria-final';e=json.loads((wc/'evidence.json').read_text())
    assert e['kind']=='real_match_rendered_evidence' and not e['raw_tracking_available']
    assert e['xg']==.30340916 and e['xg_source']=='StatsBomb'
    assert e['source_tracking_hz'] is None and not e['player_dot_identity_mapping_available']
    for k in ['control_equivalent_area_m2','defender_distance_m','candidate_receiving_window_s']:assert e[k] is None
    assert [(s['displayed_max_gain'],s['displayed_max_loss']) for s in e['retained_keyframes']]==[(.047,-.027),(.314,-.185),(.209,-.145)]
    for s in e['retained_keyframes']:assert hashlib.sha256((wc/s['file']).read_bytes()).hexdigest()==s['sha256']
    assert not (wc/'event-context.json').exists()
    source_manifest=json.loads((wc/'source-media-manifest.json').read_text())
    validation=sorted((ROOT/'examples/validation').glob('[0-9][0-9]-*'));assert len(validation)==12
    for c in validation:
        m=json.loads((c/'metrics.json').read_text());assert m['instance']['real_match'] is False and m['instance']['sample_rate_hz']==50
    movie=ROOT/'uploads/BeyondTouch-DiMaria.mp4';assert movie.is_file() and movie.read_bytes()[4:8]==b'ftyp'
    meta=json.loads((ROOT/'uploads/video-metadata.json').read_text());assert math.isclose(float(meta['format']['duration']),30,abs_tol=.5)
    assert meta['streams'][0]['codec_name']=='h264'
    for p in [ROOT/'START_HERE.html',wc/'replay.html',*(c/'replay.html' for c in cases),*(c/'replay.html' for c in validation)]:
        parser=Links();parser.feed(p.read_text())
        for url in parser.targets:
            u=urlsplit(url)
            if u.scheme or not u.path:continue
            assert (p.parent/unquote(u.path)).exists(),(p,url)
    print('Verified 13 real-event cases, 12 distinct synthetic controls, native cadence, source metrics, identities, annotations, media and offline links.')
if __name__=='__main__':verify()
