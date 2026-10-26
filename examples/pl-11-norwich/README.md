# PL-11 · Liverpool 3 - 0 Norwich

**Real Premier League event · educational hand-collected trajectories · 20 Hz source**

![Replay](preview.gif)

[Video](video.avi) · [Interactive replay](replay.html) after extracting the repository

2019-08-09 · goal context: Virgil van Dijk, 28′. [Official match context](https://www.liverpoolfc.com/news/first-team/359939-liverpool-norwich-match-report-premier-league). Source play label: `Liverpool [3] - 0 Norwich`. Focus: **Jordan Henderson #14**, local source ID **12**. Henderson is the observed focus player around Liverpool’s third goal; this is not a claim of an assist.

| Observed measure | Result |
| --- | ---: |
| Source clip duration | 7.40 s |
| Focus path length | ≈ 25.68 nominal m |
| Focus displacement | ≈ 23.64 nominal m |
| Start → end nearest observed defender gap | ≈ 6.63 → 2.49 nominal m |
| Associated observed defenders’ combined path | ≈ 40.25 m |
| Time with observed gap ≥ 3 nominal m | 4.70 s |
| Observed attackers / defenders | 8 / 10 |
| Full pitch control / receiving window / xG | unavailable |

## Interpretation

These are source-window measurements, not a certified off-ball-only interval. Some focus players carry or pass the ball during the clip. Distances scale the source’s normalized coordinates onto an **assumed 105 × 68 m pitch**; actual calibration is unverified. Missing players can make nearest-observed-defender gaps too large. Associated travel is not distance caused by the focus player. The ≥3 m time is a separation-only diagnostic, **not** the full candidate receiving window from the synthetic model.

The native samples remain 20 Hz. The browser interpolates positions for a 50 Hz display; the exported animation/video is 5 fps. Interpolation does not add observations or measurement accuracy. The underlying [Last Row source](https://github.com/Friends-of-Tracking-Data-FoTD/Last-Row) explicitly warns that these trajectories lack research accuracy. Credit: Ricardo Tavares / Last Row / Friends of Tracking. No broadcast footage is redistributed.

## Evidence and reproduction

`tracking.csv.gz` is the credited source subset; `metrics.json` contains exact results and assumptions; `evidence.csv` contains native timestamped measurements; `instance.json` records source and match context; `data.js` is the replay payload. Opponents without a confirmed shirt/name remain local IDs in the replay roster. The source frame clock is not a verified broadcast clock.

From the repository root: `bash run.sh --case 11` or `run.bat --case 11`. This recalculates the real-data measurements. Synthetic pitch-control tests remain available separately.

## Moving-scene model contrast

Conditional endpoint sensitivity: **-40.65 nominal m²** over the whole pitch. All other observed players and the ball use their actual endpoint states; only the focus player is held at its initial position and velocity in the reference. This does not freeze unrelated players. It remains a partial-coverage model diagnostic, not causal or complete-match attribution. Offside/GK identities are unconfirmed. See model-analysis.json.
