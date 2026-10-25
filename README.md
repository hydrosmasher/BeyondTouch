# BeyondTouch

**The numbers behind the run.**

BeyondTouch turns off-ball movement into spatial and physical evidence with an
interactive replay. The current suite uses **50 Hz synthetic tracking (0.02 s intervals)**. This version includes **12 labelled synthetic examples**,
19 unit/regression tests, generated results and measured numerical sensitivity.

- Open **docs/index.html** for the gallery. Each replay identifies its match
  instance, run, simulated clock, fictional teams and player IDs.
- Read **reports/BeyondTouch-project-report.docx** for a single simple report.
- Follow **LOCAL_SETUP.md** to install and reproduce everything.

- Developer and explanation instructions: [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md).
- Linked project board: [BeyondTouch](https://github.com/users/hydrosmasher/projects/2).

## What is measured

Control-equivalent area gained/lost/net (m²), associated defender travel (m),
high-speed travel, motion relative to defensive-unit translation, receiver
separation (m), and candidate receiving-window duration (s). Shot xG is unavailable;
it is not invented or assigned to a runner.

## Results

All twelve are authored scenarios, not real match findings. Net m² is a frozen-state
model sensitivity. Defender metres are observed association, not forced effort.
Window duration depends on declared heuristics. Grid difference compares 50 and
75 columns; it is not real-world accuracy.

| ID | Movement | Net m² | Defender m | Window s | Grid difference m² |
| --- | --- | ---: | ---: | ---: | ---: |
| BT-SYN-01 | Diagonal run toward the left channel | +275.06 | 21.28 | 2.26 | 0.03 |
| BT-SYN-02 | Straight run behind the defensive line | +317.38 | 14.91 | 2.26 | 0.09 |
| BT-SYN-03 | Check back toward midfield | -45.09 | 4.10 | 2.26 | 2.46 |
| BT-SYN-04 | Wide supporting run | +69.10 | 21.96 | 2.26 | 0.29 |
| BT-SYN-05 | Stationary attacker negative control | +0.00 | 21.28 | 2.26 | 0.00 |
| BT-SYN-06 | Retreat away from the attacking area | -74.43 | 4.97 | 2.26 | 3.44 |
| BT-SYN-07 | Double movement | +334.95 | 21.28 | 2.26 | 0.05 |
| BT-SYN-08 | Defensive handover | +282.14 | 9.22 | 2.80 | 0.03 |
| BT-SYN-09 | Away team mirrored attack | +275.06 | 21.28 | 2.26 | 0.04 |
| BT-SYN-10 | Receiver remains tightly marked | +272.34 | 21.28 | 0.00 | 0.03 |
| BT-SYN-11 | Run ends beyond the offside line | -204.00 | 12.93 | 2.26 | 0.07 |
| BT-SYN-12 | Defenders hold their positions | +207.22 | 0.00 | 0.00 | 0.05 |

The runner is shirt 11, receiver 10 and carrier 8 for the attacking side. Full
rosters and source information are in data/examples/*/instance.json. Aster FC and
Boreal FC are fictional. No real player names or real match identities are asserted.

## Improvements

- Possession-aware Home/Away roles and team-rotation regression check.
- Missing-player, invalid-ball, duplicate-time, visibility and gap rejection.
- Offside filtering in spatial surfaces and receiver availability.
- Fractional cell overlap at penalty-area boundaries.
- Smaller 0.02 s integration step; 0.01 s sensitivity check for example 01.
- Finer 75-column reference for every example; reaction-time sensitivity for 01.
- Explicit residual accounting, without claiming additive causal player credit.

Numerical stability is distinct from empirical accuracy. These fixtures do not
calibrate the model against professional match outcomes or ground-truth attribution.
Stationary, mirrored, tightly marked and offside controls are included deliberately.

## Quick start

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python Scripts/run_example_suite.py --sample-rate 50 --output outputs/examples --workers 2
python Scripts/verify_example_suite.py --results outputs/examples
```

Open outputs/examples/index.html. Windows instructions are in LOCAL_SETUP.md.
GitHub Desktop, Node, FFmpeg, a GPU and Azure keys are not needed for this stage.
Generated examples are tracked separately from source fixtures. To host the saved
replays, use GitHub Pages from main /docs; no Azure service is added by doing so.

Tracking cadence, spatial grid resolution and model integration step are separate settings. The 50 Hz suite has 301 samples per six-second replay and 175 samples in each 0–3.48 s analysis window. Regenerating velocities at the new cadence can change model results; more synthetic samples alone do not establish real-world accuracy. Use `--sample-rate 25` in a separate output folder for a cadence comparison.

## Current limits

Explanations are deterministic evidence summaries; Azure generative narration is
not connected. The model freezes other players in its counterfactual and cannot
establish how a defender would react. The reported residual includes defender and
ball motion and nonlinear interactions. Availability thresholds and reaction-time
parameters are explicit assumptions, not calibrated probabilities.

No real match dataset was present in the linked Basel repository. PFF requires an
access request, Metrica is anonymized, and Last Row warns of insufficient research
accuracy. We have not substituted those data or relabelled synthetic results.
Hackathon eligibility for extending prior thesis work has not been confirmed.

## Credits

Research: Bassel Hammad, Mahmoud Nasr, Omar Refaat, Mohamed Hafez and Tamer Basha,
*Quantifying Off-Ball Attacking Influence Using Additive Pitch Control Attribution*.
Original framework: Laurie Shaw / Friends of Tracking and Spearman-style pitch
control. Source: https://github.com/bassel-hammad/LaurieOnTracking
(snapshot tree f743a859a031420828db10c6fef768424a4547d8, downloaded 2026-10-21).

Original MIT notices remain in LICENSE. New work includes interpretable metrics,
role/input corrections, numerical sensitivity, synthetic examples and evidence
replays. Historical tutorial scripts are retained but need additional dependencies
and datasets; they are outside the verified metrics entry points.
