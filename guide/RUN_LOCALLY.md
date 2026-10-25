# Run locally

## Without Python — judges start here

Download the repository ZIP from GitHub using **Code → Download ZIP**, extract it,
then double-click **START_HERE.html**. Choose any of the twelve cards. The interactive
replays and GIFs work from the extracted folder with no server, account or API key.
Do not open HTML while it is still inside the ZIP.

On GitHub itself, open an examples folder to read its analysis and watch preview.gif.
Each folder also includes video.avi. The GIF is the browser-compatible playback
alternative if your media player does not support Motion-JPEG AVI. Preview exports
are 5 fps; the interactive replay retains all 301 samples of the 50 Hz tracking.

## macOS / Linux — calculate

Open Terminal in the project folder. On this Mac the checkout is:

```sh
cd "$HOME/Desktop/BeyondTouch"
git pull --ff-only
bash run.sh --check
bash run.sh --case 1
open outputs/case-01/index.html
```

`git pull` applies only to a Git clone. If you downloaded a ZIP, download the latest
ZIP and replace your extracted copy after preserving any personal changes.
On Linux, open the printed gallery path with your browser instead of the macOS
`open` command. First-case calculation takes longer than opening the saved demo.

For all twelve cases:

```sh
bash run.sh --all
open outputs/examples/index.html
```

The launcher selects Python 3.12. It can use an existing python3.12 installation or
the Codex-bundled Python 3.12 runtime on this Mac. A default Python 3.15 installation
is not used. If neither Python 3.12 runtime exists, install Python 3.12 from
https://www.python.org/downloads/ and rerun. No IDE or notebook platform is needed.
The first calculation installs the three pinned dependencies into .venv when the
selected interpreter does not already have them. That setup needs internet access.
If installed versions already match, it uses them without installing anything.

Use `--workers 1` to reduce CPU and memory use. Recalculating all twelve runs baseline
and reference grids and can take several minutes. Generated results go to outputs/;
saved judge examples stay in examples/.

## Windows

Install Python 3.12, extract the repository, open Command Prompt in that folder:

```bat
run.bat --check
run.bat --case 1
```

Open outputs\case-01\index.html. Use `run.bat --all` for all twelve cases.

## Troubleshooting

If dependencies cannot install, use START_HERE.html to view the supplied results.
If .venv belongs to another Python version, rename it before rerunning; the launcher
does not delete it. If an organizational browser blocks local scripts, the case
README and preview.gif still contain the saved analysis and visual demonstration.
No GPU, Azure key, FFmpeg, GitHub Desktop or paid service is required.
