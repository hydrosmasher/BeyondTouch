"""Refresh narratives and annotated media from saved real tracking, without refitting PC."""
from pathlib import Path
import json,subprocess,shutil,argparse
from tactical_chain import build
from real_cases import ROOT,picture,avi

def encode_mp4(folder,input_file=None):
    ffmpeg=shutil.which('ffmpeg')
    if not ffmpeg:
        try:
            import imageio_ffmpeg
            ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
        except ImportError:return False
    subprocess.run([ffmpeg,'-y','-loglevel','error','-i',str(input_file or folder/'video.avi'),'-an','-c:v','libx264','-pix_fmt','yuv420p','-crf','23','-movflags','+faststart',str(folder/'story.mp4')],check=True)
    return True

def refresh(folder):
    bundle=json.loads((folder/'data.js').read_text().split('=',1)[1].rstrip(';\n'));bundle['story']=build(bundle)
    (folder/'story.json').write_text(json.dumps(bundle['story'],indent=2,allow_nan=False));(folder/'story.js').write_text('window.TACTICAL_STORY='+json.dumps(bundle['story'],separators=(',',':'),allow_nan=False).replace('<','\\u003c')+';')
    pictures=[picture(bundle,i) for i in range(0,len(bundle['frames']),4)]
    pictures[0].save(folder/'preview.gif',save_all=True,append_images=pictures[1:],duration=200,loop=0,optimize=True)
    picture(bundle,len(bundle['frames'])//2).save(folder/'preview.png');avi(pictures,folder/'video.avi')
    from guided_review import save_media
    bundle['story_video_available']=save_media(bundle,folder)
    (folder/'data.js').write_text('window.REAL_CASE='+json.dumps(bundle,separators=(',',':'),allow_nan=False).replace('<','\\u003c')+';')
    shutil.copyfile(ROOT/'src/guided-review.js',folder/'guided-review.js')
    shutil.copyfile(ROOT/'src/decision-overlay.js',folder/'decision-overlay.js')
    (folder/'replay.html').write_text((ROOT/'src/real_replay.html').read_text().replace('href="../index.html"','href="../../START_HERE.html"'))
    readme=(folder/'README.md').read_text();readme=readme.split('\n## Tactical story:')[0]
    readme+='\n## Tactical story: run, response, cover, finish\n\n'+bundle['story']['presentation_text']+'\n\n'+'\n\n'.join('**'+s['title']+' ['+s['status']+']** — '+s['text'] for s in bundle['story']['steps'])+'\n\nSee story.json for thresholds, selected source IDs and exact timestamps. Arrows and trails show observed motion; tactical responsibilities remain unconfirmed.\n'
    if bundle['story_video_available']:readme+='\n[Annotated story MP4](story.mp4) · [AVI fallback](video.avi)\n'
    (folder/'README.md').write_text(readme)
    print(folder.name,bundle['story']['full_candidate_chain_detected'],flush=True)

def main():
    from concurrent.futures import ProcessPoolExecutor
    folders=sorted((ROOT/'examples').glob('pl-[0-9][0-9]-*'))
    with ProcessPoolExecutor(max_workers=2) as pool:list(pool.map(refresh,folders))
if __name__=='__main__':main()
