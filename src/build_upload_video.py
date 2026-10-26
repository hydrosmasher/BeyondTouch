"""Render a silent 30-second evidence explainer from retained scientific keyframes.

Requires FFmpeg only when rebuilding the MP4, not when running/viewing BeyondTouch.
The GitHub workflow supplies that optional build tool.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import argparse,json,subprocess,shutil

ROOT=Path(__file__).resolve().parents[1]
def font(n):
    for p in ['/System/Library/Fonts/Supplemental/Arial.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']:
        try:return ImageFont.truetype(p,n)
        except OSError:pass
    return ImageFont.load_default()

def frame(time):
    im=Image.new('RGB',(1600,900),'#0c1820');d=ImageDraw.Draw(im)
    d.text((45,24),'BEYONDTOUCH',font=font(31),fill='#f5cb68')
    d.text((45,69),'Real events. Visible evidence. Reproducible measurements.',font=font(22),fill='#b6cbc4')
    d.rectangle((45,870,1555,877),fill='#294048');d.rectangle((45,870,45+1510*min(time/30,1),877),fill='#f5cb68')
    if time<4:
        d.text((80,195),'The numbers behind the run.',font=font(65),fill='white')
        d.text((80,310),'Ángel Di María’s World Cup final goal',font=font(47),fill='#f5cb68')
        d.text((80,395),'Argentina v France · 18 December 2022 · goal 36′',font=font(31),fill='white')
        d.text((80,520),'Basel’s supplied pitch-control visualizations',font=font(29),fill='#b6cbc4')
        d.text((80,575),'Three retained keyframes — not continuous tracking',font=font(29),fill='#b6cbc4')
        d.text((80,690),'Watch the evidence, then inspect the open judge demo.',font=font(27),fill='white')
    elif time<22:
        n=0 if time<10 else 1 if time<16 else 2
        values=[('-9.9 s','+0.047','−0.027'),('-3.9 s','+0.314','−0.185'),('+2.0 s','+0.209','−0.145')][n]
        p=ROOT/'examples/di-maria-final'/f'keyframe-{n+1}.png';pic=Image.open(p).convert('RGB');pic.thumbnail((1020,700));im.paste(pic,(35,135))
        x=1100
        d.text((x,145),'SOURCE GOAL MARKER',font=font(19),fill='#b6cbc4');d.text((x,185),values[0],font=font(49),fill='white')
        d.text((x,290),'DISPLAYED MAX GAIN',font=font(19),fill='#b6cbc4');d.text((x,330),values[1],font=font(48),fill='#f5cb68')
        d.text((x,425),'DISPLAYED MAX LOSS',font=font(19),fill='#b6cbc4');d.text((x,465),values[2],font=font(48),fill='#e68d99')
        lines=['Source plot annotations.','Not total area or xG.','Not exclusive runner credit.']
        if n==2:lines+=['After-goal context only.']
        for j,line in enumerate(lines):d.text((x,590+j*40),line,font=font(23),fill='#b6cbc4')
        d.text((45,827),'KEYFRAME EXPLAINER · ΔPC baseline not independently supplied · original plot labels preserved',font=font(20),fill='#b6cbc4')
    else:
        d.text((80,170),'Explore the real cases.',font=font(61),fill='white')
        for y,t in [(290,'1 World Cup final evidence case'),(370,'12 Premier League educational tracking sequences'),(450,'Replay, video, written analysis and source data')]:d.text((80,y),t,font=font(36),fill='#f5cb68')
        for y,t in [(570,'No Python required to view: extract the project and open START_HERE.html.'),(625,'Approximate Premier League distances assume a 105 × 68 m pitch.'),(675,'Partial tracking is not research-grade measurement.'),(725,'Di María raw positions, defender metres and xG remain unavailable.')]:d.text((80,y),t,font=font(25),fill='#b6cbc4')
        d.text((80,810),'Basel’s research + Last Row / Ricardo Tavares + Friends of Tracking',font=font(22),fill='white')
    return im

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'uploads/BeyondTouch-DiMaria.mp4');p.add_argument('--preview',type=Path);a=p.parse_args()
    if a.preview:frame(12).save(a.preview);return
    ffmpeg=shutil.which('ffmpeg')
    if not ffmpeg:p.exit(2,'FFmpeg is needed only to rebuild this optional MP4. The ready video is supplied in uploads/.\n')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    cmd=[ffmpeg,'-y','-f','rawvideo','-pix_fmt','rgb24','-s','1600x900','-r','5','-i','-','-an','-c:v','libx264','-preset','medium','-crf','24','-pix_fmt','yuv420p','-movflags','+faststart',str(a.output)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    for i in range(150):proc.stdin.write(frame(i/5).tobytes())
    proc.stdin.close();ret=proc.wait()
    if ret:raise SystemExit(ret)
    probe=shutil.which('ffprobe')
    if probe:
        result=json.loads(subprocess.check_output([probe,'-v','error','-show_entries','format=duration,size:stream=codec_name,width,height,r_frame_rate','-of','json',str(a.output)],text=True))
        result['description']='Silent keyframe evidence explainer, not continuous tracking replay.'
        result['source_keyframes']=3
        (a.output.parent/'video-metadata.json').write_text(json.dumps(result,indent=2))

if __name__=='__main__':main()
