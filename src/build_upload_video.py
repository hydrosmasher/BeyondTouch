"""Render a silent 30-second evidence explainer from retained scientific keyframes.

Requires FFmpeg only when rebuilding the MP4, not when running/viewing BeyondTouch.
The GitHub workflow supplies that optional build tool.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import argparse,json,subprocess,shutil
from functools import lru_cache

ROOT=Path(__file__).resolve().parents[1]
@lru_cache(maxsize=1)
def supplied_frames():
    from PIL import ImageSequence
    im=Image.open(ROOT/'examples/di-maria-final/sources/pitch-control-change.gif')
    return tuple(f.convert('RGB').copy() for f in ImageSequence.Iterator(im))
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
        d.text((80,575),'Full supplied animation + attributed event analysis',font=font(29),fill='#b6cbc4')
        d.text((80,690),'Watch the evidence, then inspect the open judge demo.',font=font(27),fill='white')
    elif time<22:
        frames=supplied_frames();n=min(len(frames)-1,int((time-4)/18*len(frames)));pic=frames[n].copy();pic.thumbnail((1020,700));im.paste(pic,(35,135))
        x=1100
        a=json.loads((ROOT/'examples/di-maria-final/event-analysis.json').read_text())
        d.text((x,145),'PROVIDER SHOT CONTEXT',font=font(19),fill='#b6cbc4');d.text((x,185),f"{a['shot_xg']:.4f} xG",font=font(45),fill='#f5cb68')
        d.text((x,290),'RECORDED PASS CHAIN',font=font(19),fill='#b6cbc4');d.text((x,330),str(a['completed_passes'])+' passes',font=font(42),fill='white')
        d.text((x,425),'FIRST PASS TO SHOT',font=font(19),fill='#b6cbc4');d.text((x,465),f"{a['first_pass_to_shot_s']:.3f} s",font=font(42),fill='white')
        for j,line in enumerate(['Shot xG is not run credit.','Plot ΔPC is a separate model.','Provider clocks are not aligned.']):d.text((x,570+j*36),line,font=font(21),fill='#b6cbc4')
        logo=Image.open(ROOT/'guide/statsbomb-logo.png').convert('RGB');logo.thumbnail((320,100));d.rectangle((1090,695,1430,815),fill='white');im.paste(logo,(1100,705))
        d.text((45,827),'SUPPLIED ANIMATION · playback retimed for explanation · original plot labels preserved',font=font(20),fill='#b6cbc4')
    else:
        d.text((80,170),'Explore the real cases.',font=font(61),fill='white')
        for y,t in [(290,'1 World Cup final evidence case'),(370,'12 Premier League educational tracking sequences'),(450,'Replay, video, written analysis and source data')]:d.text((80,y),t,font=font(36),fill='#f5cb68')
        for y,t in [(570,'No Python required to view: extract the project and open START_HERE.html.'),(625,'Premier League distances and model contrasts use partial educational tracking.'),(675,'Other observed players and the ball move in the dynamic-scene model.'),(725,'Di María shot xG is StatsBomb context; raw movement metrics are unavailable.')]:d.text((80,y),t,font=font(25),fill='#b6cbc4')
        d.text((80,810),'Basel’s research + Last Row / Ricardo Tavares + Friends of Tracking',font=font(22),fill='white')
    return im

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'uploads/BeyondTouch-DiMaria.mp4');p.add_argument('--preview',type=Path);a=p.parse_args()
    if a.preview:frame(12).save(a.preview);return
    ffmpeg=shutil.which('ffmpeg')
    if not ffmpeg:
        try:
            import imageio_ffmpeg
            ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
        except ImportError:pass
    if not ffmpeg:p.exit(2,'FFmpeg is needed only to rebuild this optional MP4. The ready video is supplied in uploads/.\n')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    cmd=[ffmpeg,'-y','-f','rawvideo','-pix_fmt','rgb24','-s','1600x900','-r','5','-i','-','-an','-c:v','libx264','-preset','medium','-crf','24','-pix_fmt','yuv420p','-movflags','+faststart',str(a.output)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    for i in range(150):proc.stdin.write(frame(i/5).tobytes())
    proc.stdin.close();ret=proc.wait()
    if ret:raise SystemExit(ret)
    probe=shutil.which('ffprobe')
    result=None
    if probe:
        result=json.loads(subprocess.check_output([probe,'-v','error','-show_entries','format=duration,size:stream=codec_name,width,height,r_frame_rate','-of','json',str(a.output)],text=True))
    else:
        check=subprocess.run([ffmpeg,'-i',str(a.output)],capture_output=True,text=True).stderr
        assert '1600x900' in check and '00:00:30.00' in check and 'h264' in check
        result={'streams':[{'codec_name':'h264','width':1600,'height':900,'r_frame_rate':'5/1'}],'format':{'duration':'30.000000','size':str(a.output.stat().st_size)}}
    if result:
        result['description']='Silent explainer using the full supplied rendered animation and attributed StatsBomb event analysis; not reconstructed tracking.'
        result['source_animation_frames']=len(supplied_frames())
        (a.output.parent/'video-metadata.json').write_text(json.dumps(result,indent=2))

if __name__=='__main__':main()
