# View and run BeyondTouch

## Judge demo without Python

Download **Code → Download ZIP**, extract it, and double-click **START_HERE.html**.
Start with Di María’s World Cup final evidence, then open the twelve Premier League
cards. Every case folder has a README analysis and saved animation viewable directly
on GitHub. No server, account, API key, IDE or installation is needed to view the
extracted demo. The single upload MP4 and PNG are in uploads/.

The World Cup case presents the full supplied animations, sequence 94 video and
three annotated checkpoints, with independently sourced shot context. No tracking
positions are reconstructed from those rendered plots. Premier League cases use educational trajectories and approximate nominal
distances, not research-grade data.

## From the start on this Mac

```sh
cd "$HOME/Desktop/BeyondTouch" && git pull --ff-only && bash run.sh --all && open outputs/examples/index.html
```

This updates the Git clone and recalculates the twelve **real Premier League cases**.
To open the saved demo immediately, use `open START_HERE.html` in the project folder.
The launcher selects Python 3.12, including the existing Codex-bundled runtime on
this Mac; the default Python 3.15 is not used. Otherwise install Python 3.12 from
https://www.python.org/downloads/. The launcher installs the pinned NumPy, pandas
and Pillow versions into .venv when needed. Initial dependency installation needs
internet; viewing the supplied demo does not.

If Git reports a reference race, let other fetches finish, then use `git fetch origin`
and `git merge --ff-only origin/main`. Do not reset or delete personal changes. A ZIP
download is updated by downloading the latest ZIP.

## Calculation options

```sh
bash run.sh --case 1
bash run.sh --check
bash run.sh --synthetic --all
```

`--case 1` writes outputs/case-01/. `--all` writes outputs/examples/.
`--synthetic --all` runs the separate full-model 50 Hz fixtures into outputs/synthetic/
and can take several minutes. They are authored validation tests, not match findings.
The Di María tracking was not supplied; recalculation does not invent new metrics
for it. Source annotations remain in examples/di-maria-final/evidence.json.

Linux: open the printed path in your browser instead of using macOS `open`.
Windows with Python 3.12: `run.bat --all`, `run.bat --case 1`, `run.bat --check`, or
`run.bat --synthetic --all` from Command Prompt in the extracted folder.

## Sampling and video

Real calculations retain native **20 Hz** samples. Browser positions interpolate
for **50 Hz display only**; preview GIFs/AVIs are 5 fps. Synthetic fixtures remain
50 Hz. These are different settings. FFmpeg is only needed to rebuild the optional
promotional MP4 using `python src/build_upload_video.py`; the ready MP4 is supplied.
