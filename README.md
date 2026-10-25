# BeyondTouch

**The numbers behind the run.** Quantitative off-ball football insights with twelve synthetic demonstrations at 50 Hz.

## Judges: no Python needed

1. Select **Code → Download ZIP** and extract the ZIP.
2. Double-click **START_HERE.html**. Choose any of the twelve cases.
3. Explore the interactive replay, or watch its GIF/video and read its analysis.

You can also browse the case folders below directly on GitHub: their READMEs display an animated replay and calculated analysis. No account, server, API key, IDE or paid tool is needed for the downloaded demo. HTML must be opened after extraction; GitHub's file view does not execute it.

Start with **01** (diagonal run), compare **10** (marked receiver), then **05** (stationary-runner control).

## Developers: one command

macOS / Linux, from this folder:

```sh
bash run.sh --case 1
```

Windows: `run.bat --case 1`. Use `--all` for all twelve, or `--check` for the tests.
Recalculation requires **Python 3.12**. The launcher sets up dependencies when needed; the first setup needs internet. Details: [run locally](guide/RUN_LOCALLY.md).

## Twelve complete case folders

Every folder includes a video, browser-playable GIF, interactive replay, written analysis, exact metrics, timestamped evidence, source tracking and match/run/player identity.

| Case | Net model area m² | Associated defender m | Longest candidate window s |
| --- | ---: | ---: | ---: |
| [01 · Diagonal run toward the left channel](examples/01-diagonal-run) | +275.06 | 21.28 | 2.26 |
| [02 · Straight run behind the defensive line](examples/02-depth-run) | +317.38 | 14.91 | 2.26 |
| [03 · Check back toward midfield](examples/03-check-back) | -45.09 | 4.10 | 2.26 |
| [04 · Wide supporting run](examples/04-wide-run) | +69.10 | 21.96 | 2.26 |
| [05 · Stationary attacker negative control](examples/05-stationary-runner) | +0.00 | 21.28 | 2.26 |
| [06 · Retreat away from the attacking area](examples/06-retreat) | -74.43 | 4.97 | 2.26 |
| [07 · Double movement](examples/07-double-movement) | +334.95 | 21.28 | 2.26 |
| [08 · Defensive handover](examples/08-defensive-handover) | +282.14 | 9.22 | 2.80 |
| [09 · Away team mirrored attack](examples/09-mirrored-away) | +275.06 | 21.28 | 2.26 |
| [10 · Receiver remains tightly marked](examples/10-marked-receiver) | +272.34 | 21.28 | 0.00 |
| [11 · Run ends beyond the offside line](examples/11-offside-run) | -204.00 | 12.93 | 2.26 |
| [12 · Defenders hold their positions](examples/12-stationary-defenders) | +207.22 | 0.00 | 0.00 |

## What the numbers mean

Area measures a pitch-control model's sensitivity to advancing one runner's position and velocity. Defender travel is observed distance, not distance caused by that runner. Candidate windows use explicit onside, separation, control and lane-clearance thresholds. None is a calibrated xG value. All teams and players here are fictional. The preview videos are 5 fps; the interactive replays retain the 50 Hz tracking samples.

## Only three places to look

- **examples/** — all twelve complete demonstrations.
- **guide/** — [project report](guide/PROJECT_REPORT.docx), [developer and metric guide](guide/DEVELOPER_GUIDE.md), and [local run instructions](guide/RUN_LOCALLY.md).
- **src/** — calculation code and tests. Historical research files are under src/legacy.

## Research and current scope

Built on [Bassel Hammad's LaurieOnTracking research implementation](https://github.com/bassel-hammad/LaurieOnTracking), the work of Bassel Hammad, Mahmoud Nasr, Omar Refaat, Mohamed Hafez and Tamer Basha, and Laurie Shaw / Friends of Tracking's Spearman-style pitch control. Existing MIT notices are retained in [LICENSE](LICENSE).

New work includes quantitative metrics, input/role corrections, numerical checks, synthetic scenarios and evidence replays. Nineteen tests and twelve-case accounting/control checks are provided. Numerical stability does not establish real-match accuracy, and 50 Hz synthetic sampling does not establish VAR-camera compatibility. Narration is currently deterministic; a generative service is not connected.

[Project board](https://github.com/users/hydrosmasher/projects/2)
