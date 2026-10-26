"""Produce portable source and real-case-only judge ZIPs from the current checkout."""
from pathlib import Path
import zipfile,re
ROOT=Path(__file__).resolve().parents[1]
def main():
    out=ROOT/'outputs/releases';out.mkdir(parents=True,exist_ok=True)
    files=[p for p in sorted(ROOT.rglob('*')) if p.is_file() and not any(x in {'.git','.venv','outputs','__pycache__'} for x in p.relative_to(ROOT).parts)]
    for name,judge in [('BeyondTouch-full-project.zip',False),('BeyondTouch-judge-demo.zip',True)]:
        with zipfile.ZipFile(out/name,'w',zipfile.ZIP_DEFLATED) as z:
            for p in files:
                rel=p.relative_to(ROOT)
                if judge and (rel.parts[0] in {'src','.github','data_templates'} or rel.parts[:2]==('examples','validation') or p.name in ['run.sh','run.bat','requirements.txt','.gitignore']):continue
                if judge and rel.as_posix()=='START_HERE.html':
                    s=re.sub(r'<section class="note" style="margin-top:28px"><details><summary>Open the 12 synthetic full-model validation cases</summary>.*?</section>','',p.read_text(),flags=re.S);z.writestr('BeyondTouch/START_HERE.html',s)
                else:z.write(p,Path('BeyondTouch')/rel)
        with zipfile.ZipFile(out/name) as z:assert z.testzip() is None
if __name__=='__main__':main()
