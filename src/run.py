"""One entry point for real cases, dependency setup and separate synthetic tests."""
import os
import argparse
import importlib.metadata
from pathlib import Path
import subprocess
import sys
import venv

ROOT=Path(__file__).resolve().parents[1]
EXPECTED={'numpy':'2.3.5','pandas':'2.2.3','Pillow':'12.3.0'}

def ready():
    try:return all(importlib.metadata.version(k)==v for k,v in EXPECTED.items())
    except importlib.metadata.PackageNotFoundError:return False

def run(args):
    subprocess.run([sys.executable,*map(str,args)],cwd=ROOT,check=True)

def main():
    p=argparse.ArgumentParser(description='Recalculate real Premier League cases. No Python is needed to open START_HERE.html.')
    g=p.add_mutually_exclusive_group();g.add_argument('--case',type=int,choices=range(1,13));g.add_argument('--check',action='store_true');g.add_argument('--all',action='store_true')
    p.add_argument('--workers',type=int,default=2)
    p.add_argument('--synthetic',action='store_true',help='Run the separate 50 Hz full-model validation fixtures')
    g.add_argument('--input',type=Path,help='New long-form tracking CSV or CSV.gz')
    p.add_argument('--metadata',type=Path,help='Metadata JSON for a new sequence')
    p.add_argument('--output',type=Path,help='Empty output folder for an imported sequence')
    p.add_argument('--with-model',action='store_true',help='Calculate conditional PC for an imported sequence')
    args=p.parse_args()
    os.environ.setdefault('BEYONDTOUCH_LAUNCH_DIR',str(Path.cwd()))
    launch_dir=Path(os.environ['BEYONDTOUCH_LAUNCH_DIR'])
    if args.input:
        if not args.metadata or not args.output:p.error('--input requires --metadata and --output')
        args.input=(launch_dir/args.input).resolve();args.metadata=(launch_dir/args.metadata).resolve();args.output=(launch_dir/args.output).resolve()
        if args.synthetic:p.error('--input cannot be combined with --synthetic')
    elif args.with_model:p.error('--with-model requires --input')
    elif args.metadata or args.output:p.error('--metadata and --output require --input')
    if sys.version_info[:2]!=(3,12):
        p.exit(2,'Recalculation needs Python 3.12. To view all saved examples, open START_HERE.html instead.\n')
    if args.workers<1:p.error('--workers must be positive')
    if not ready():
        target=ROOT/'.venv';exe=target/('Scripts/python.exe' if sys.platform=='win32' else 'bin/python')
        if not target.exists():venv.EnvBuilder(with_pip=True).create(target)
        if not exe.is_file():p.exit(2,'The existing .venv is incomplete. Rename it and rerun, or use START_HERE.html.\n')
        version=subprocess.check_output([str(exe),'-c','import sys;print("%d.%d"%sys.version_info[:2])'],text=True).strip()
        if version!='3.12':p.exit(2,'The existing .venv is not Python 3.12. Rename it and rerun.\n')
        subprocess.run([str(exe),'-m','pip','install','-r',str(ROOT/'requirements.txt')],check=True)
        return subprocess.call([str(exe),str(Path(__file__).resolve()),*sys.argv[1:]],cwd=ROOT)
    print('BeyondTouch | Python 3.12 | '+('50 Hz synthetic validation' if args.synthetic else 'real Premier League cases · native 20 Hz'),flush=True)
    if args.check:
        run(['-m','unittest','discover','-s','src/tests','-v']);return 0
    if args.input:
        run(['src/import_sequence.py','--input',args.input,'--metadata',args.metadata,'--output',args.output]+(['--with-model'] if args.with_model else []));return 0
    out=Path('outputs')/((f'synthetic-case-{args.case:02d}' if args.case else 'synthetic') if args.synthetic else (f'case-{args.case:02d}' if args.case else 'examples'))
    cmd=(['src/Scripts/run_example_suite.py','--sample-rate','50','--output',out,'--workers',str(args.workers)] if args.synthetic else ['src/real_cases.py','--output',out])
    if args.case:cmd+=['--case',str(args.case)]
    run(cmd)
    if not args.case and args.synthetic:run(['src/Scripts/verify_example_suite.py','--results',out])
    print('\nFinished. Open this gallery in a browser:\n'+str(ROOT/out/'index.html'),flush=True)
    return 0

if __name__=='__main__':
    try:sys.exit(main())
    except subprocess.CalledProcessError as e:sys.exit(e.returncode)
