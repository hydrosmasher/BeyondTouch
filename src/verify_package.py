"""Validate the offline judge deliverable, identities, cadence, links and media."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote,urlsplit
import io,json,math,struct
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
class Links(HTMLParser):
    def __init__(self):super().__init__();self.targets=[]
    def handle_starttag(self,tag,attrs):
        for k,v in attrs:
            if k in ('href','src') and v:self.targets.append(v)

def verify():
    cases=sorted((ROOT/'examples').glob('[0-9][0-9]-*'))
    assert len(cases)==12
    required=['README.md','replay.html','data.js','metrics.json','evidence.csv','instance.json',
              'preview.gif','preview.png','video.avi','tracking-home.csv.gz','tracking-away.csv.gz']
    for case in cases:
        assert all((case/n).is_file() for n in required),case
        m=json.loads((case/'metrics.json').read_text());payload=json.loads((case/'data.js').read_text().split('=',1)[1].rstrip(';\n'))
        b=payload[m['instance']['scenario_id']]
        assert m['instance']['real_match'] is False and m['instance']['sample_rate_hz']==50
        assert len(m['timeline'])==175 and len(b['frames'])==301
        assert b['metrics']['instance']['run_id']==m['instance']['run_id']
        assert all(math.isclose(y['t']-x['t'],.02,abs_tol=1e-8) for x,y in zip(b['frames'],b['frames'][1:]))
        gif=Image.open(case/'preview.gif');assert gif.n_frames==31
        raw=(case/'video.avi').read_bytes();assert raw[:4]==b'RIFF' and raw[8:12]==b'AVI '
        assert struct.unpack('<I',raw[4:8])[0]+8==len(raw)
        offset=raw.index(b'movi')+4;count=0
        while raw[offset:offset+4]==b'00dc':
            n=struct.unpack('<I',raw[offset+4:offset+8])[0]
            Image.open(io.BytesIO(raw[offset+8:offset+8+n])).verify()
            count+=1;offset+=8+n+(n%2)
        assert count==31
    for p in [ROOT/'START_HERE.html',*(c/'replay.html' for c in cases)]:
        parser=Links();parser.feed(p.read_text())
        for url in parser.targets:
            parts=urlsplit(url)
            if parts.scheme or not parts.path:continue
            assert (p.parent/unquote(parts.path)).exists(),(p,url)
    print('Verified 12 complete case folders: identities, 50 Hz cadence, 175 evidence rows, 301 replay frames, all video frames and local HTML links.')

if __name__=='__main__':verify()
