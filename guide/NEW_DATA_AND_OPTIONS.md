# New tracking data and the runner-options tree

## Run a completely new sequence

From the project folder, with the same Python 3.12 environment used by BeyondTouch:

```sh
bash run.sh --input /absolute/path/tracking.csv --metadata /absolute/path/sequence-metadata.json --output /absolute/path/new-output
```

The output folder must be empty. The command preserves the input, validates it,
computes observed metrics, creates tactical explanations and a decision-options
JSON, and generates an offline replay, picture, GIF and AVI. Open the printed
replay.html path. No new source-code edits or training are required.

Copy `data_templates/sequence-metadata.json` and edit every relevant field.
`tracking-header.csv` supplies the column names only; it is not fake match data.
CSV and `.csv.gz` inputs are accepted. Relative input paths are resolved from the
folder where you launch the command. Metadata is configuration, not instructions
to execute code.

## CSV contract

One row per observed actor per native sample:

| Column | Requirement |
| --- | --- |
| time_s | Numeric source time in seconds, common to every actor |
| player_id | Stable string ID, including one distinct ID for the ball |
| team | attack, defense or ball, relative to the focus team |
| x, y | Finite coordinates in the declared units and origin |
| name | Optional, constant for each actor; unknown names remain unknown |
| shirt | Optional integer, constant for each actor; blank is accepted |

Every included actor must occur at every source time. Split sequences at gaps or
coverage changes. Omitted actors are not invented. Duplicate observations, changed
identity/team, nonfinite coordinates, incompatible units, invalid focus/finisher,
missing ball and cadence mismatches are rejected with an explanation.

Declare the native rate honestly (1–250 Hz supported), pitch length and width,
and attacking direction. Input may use metres with bottom-left or centre origin,
or normalized 0–100 axes. Metres with bottom-left origin mean x increases to the
right and y increases upward. Maximum accepted buffer is 5 m outside the pitch;
this catches common unit/origin errors, but is not calibration validation.

Names, dates, scorer context and calibration are not independently verified by an
import. Scorer/goal events may be omitted. The system does not identify players or
recover trajectories from raw broadcast video. Video-to-tracking computer vision
would be a separate upstream adapter. Existing provider-specific wide formats need
conversion to this documented long-form schema.

## What the options mean

The new panel shows six dashed movement arrows at every native source snapshot:
continue, cut left/right, go wide left/right, and check back. Left/right turns are
relative to current motion. For a stationary runner the declared attacking
direction supplies the reference heading. Change the direction selector if needed;
for legacy Liverpool clips the initial selector is left, a display default that
must be checked against the match orientation. Imported sequences use their
explicitly declared direction.

The one-second step length is speed × 1 s limited to 2–6 m. This is a demonstration
assumption, not a biomechanical feasibility guarantee. Each straight segment is
sampled at 13 points against current observed defender positions. Out-of-pitch
branches are invalid. Segments with a gap below 1.5 m are labelled crowded.

The score is a transparent geometric utility:

```
0.7 × min(minimum sampled defender gap / 8 m, 1)
+ 0.3 × ((forward progress / step length + 1) / 2)
```

A higher value means more clearance and/or progress under this rule. It is not
success probability, xG, trained decision-tree output, tactical optimality or a
prediction of defender reactions. Missing defenders can overstate clearance.
The tree exposes two leaves for each branch: continue under the current snapshot
assumption, or reassess after the next observation. It does not fabricate a future
match. Pass and shot choices are deliberately unavailable without reliable
possession and event information.

Solid trails remain actual source movement; dashed arrows are alternatives.
Defenders keep moving in the observed replay. They are held at the current
snapshot only while comparing hypothetical segments. No future source frame is
used to score a native-frame option: heading uses the current and preceding
observations. Browser interpolation for display does not add measurements.

## Files and implementation

- `src/import_sequence.py`: validates and converts new long-form tracking.
- `src/real_cases.py`: shared observed metrics, now parameterized by rate, dimensions
  and explicit focus ID rather than a fixed Liverpool shirt.
- `src/tactical_chain.py`: rate-aware candidate response/cover explanations.
- `src/decision_options.py`: Python option analysis and audit JSON for new data.
- `src/decision-overlay.js`: equivalent live computation for the replay.
- `decision-options.json`: every imported native snapshot and its branches.
- `instance.json`: source checksum, supplied context and mapping from source IDs
  to the replay's internal numeric IDs. IDs are not actual shirt numbers.

Imported sequences generate observed metrics and decision alternatives. Add
`--with-model` to calculate the conditional full-pitch PC endpoint overlay too;
this uses the declared native cadence and pitch dimensions. It uses the same
explicit generic goalkeeper/offside assumptions as the educational demo. Without
that optional flag the endpoint surface remains unavailable. The full receiving-window test and shot xG likewise
remain unavailable unless separately supported by trustworthy inputs.

## Try the held-out real input

```sh
bash run.sh --input data_templates/heldout-bayern.csv.gz --metadata data_templates/heldout-bayern-metadata.json --output outputs/my-import/sequence
```

This is a real Last Row sequence withheld from the original twelve examples. Its
source label mentions Bayern–Liverpool; date and scorer are not independently
matched. It is not presented as a new Premier League case or validation of the
options scoring. Source credit and original dataset provenance are retained.
