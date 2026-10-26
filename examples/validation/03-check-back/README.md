# 03 · Check back toward midfield

**Synthetic simulation · 50 Hz tracking · no real match or real player names.**

![Movement replay](preview.gif)

[Download video (AVI)](video.avi) · [Interactive replay](replay.html) after downloading/extracting the repository

## Instance

Aster FC vs Boreal FC — synthetic match 03 · `SIM-MATCH-03` · `BT-SYN-03-RUN-01`

Simulated clock: 13:00.00–13:03.48 (simulated). Runner **Home_11**, carrier **Home_8**, candidate receiver **Home_10**. Shirt numbers are fictional identities. Source: authored trajectories in `src/Scripts/run_example_suite.py`. The analysis covers 0–3.48 s; the remaining replay is context.

## What happens

A support movement can trade advanced space for proximity to the ball.

## Calculated analysis

| Measure | Result | Meaning |
| --- | ---: | --- |
| Net attacking control-equivalent area | -45.09 m² | Single-runner endpoint model sensitivity |
| Area gained / lost | 28.47 / 73.56 m² | Both signs retained, net = gained − lost |
| Net penalty-area sensitivity | -1.21 m² | Boundary cells weighted by fractional overlap |
| Runner travel | 7.24 m | Sample-to-sample path length |
| Associated defender travel, combined | 4.10 m | Observed distance, not distance caused by the runner |
| Receiver gap, start → analysis end | 1.41 → 8.62 m | Nearest-defender distance |
| Longest candidate receiving window | 2.26 s | Threshold-defined opportunity |
| Total qualifying time | 2.26 s | Sum of qualifying sample intervals |
| Grid difference | 2.46 m² | Baseline 50 vs reference 75 columns |
| Declared grid-stability check | Pass | Numerical sensitivity, not match accuracy |

### Selected defenders

Up to two nearest outfield defenders within 10 m at the run start are retained for the whole window.

| Player | Travel m | High-speed travel m | Relative to defensive-unit translation m |
| --- | ---: | ---: | ---: |
| Away_4 | 4.10 | 0.00 | 4.31 |

## How to interpret it

The runner's position and velocity advance to the run end while other state stays frozen at the start. The resulting area is a model sensitivity, not causal credit. Defender distances are measured observations in this authored simulation. A receiving window needs onside position, ≥3 m receiver separation, ≥0.65 model control, and ≥1.5 m straight-lane clearance. xG and metabolic energy are unavailable. Values are rounded here; exact values and parameters are in metrics.json.

## Files and reproduction

`preview.gif` and `video.avi` are silent 5 fps previews. `replay.html` retains all 301 tracking frames. `metrics.json` contains the full analysis; `evidence.csv` contains 175 rows at 0.02 s intervals; `tracking-home.csv.gz` and `tracking-away.csv.gz` contain the source positions and velocities; `instance.json` records identities and provenance. Gzip compression is lossless.

From the repository root: `bash run.sh --case 3` on macOS/Linux, or `run.bat --case 3` on Windows. See [run instructions](../../../guide/RUN_LOCALLY.md) and [metric definitions](../../../guide/DEVELOPER_GUIDE.md).
