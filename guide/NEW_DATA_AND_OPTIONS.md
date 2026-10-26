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

## Guided spatial review (default)

The replay starts with observed movement and no arrow fan. Click **Start guided
review here**. At each source checkpoint it pauses, shows **Space A**, then
**Space B**, and an optional third distinct pocket, one at a time. After those
comparisons it reveals the actual next 1.5 seconds of source movement and pauses
again. Use Pause review, Next space, Reveal actual movement or Free replay.

Choose Attacking team, Defending team or Both teams. Green marks the one proposed
pocket and the attacker's illustrative route. Pink shows the straight-line distance
from the current nearest observed defender to that same pocket. This is a possible
covering comparison, not a predicted defender response or marking assignment.
All other represented players resume their observed motion during reveal.

Two spaces are shown by default. Up to three can be selected when sufficiently
distinct in the current geometry. Candidate endpoints must stay inside the pitch,
have at least 2 m separation from the nearest observed defender and be at least
3 m apart from previously selected pockets. If the inputs do not support two
such pockets, fewer are shown rather than inventing available space. These point
and route checks do not establish offside eligibility or actual tactical safety.

Under the hood, six heading-relative movement candidates are evaluated, but they
are never displayed as a permanent fan. The one-second step length is speed × 1 s
limited to 2–6 m. For a stationary runner, the declared attack direction supplies
the heading. Segment clearance samples 13 points against current observed defenders.
Candidates use this transparent utility to order the comparisons:

```
0.7 × min(minimum sampled defender gap / 8 m, 1)
+ 0.3 × ((forward progress / step length + 1) / 2)
```

That value is not a success probability, xG, optimal decision or trained policy.
No future observed frame is used to score a source snapshot. Later source movement
is revealed afterward as evidence, not as a forecast. The review helps both teams
explore what might develop; it does not claim to know what will happen. Pass and
shot choices still need reliable possession/events and are not fabricated.

Attacking direction is explicitly supplied for imports. The Liverpool demos start
with left as a display default; check the direction against the source orientation.
The observer may change it in the replay.

## Files and implementation

- `src/import_sequence.py`: CSV validation, unit/origin conversion, identity mapping.
- `src/real_cases.py`: native-rate observed metrics.
- `src/decision_options.py`: snapshot candidate geometry and audit JSON.
- `src/guided_review.py`: select 2–3 distinct pockets and schedule pause/compare/reveal.
- `src/guided-review.js`: interactive review controller and team perspectives.
- `src/decision-overlay.js`: equivalent browser snapshot arithmetic.
- `decision-options.json`: native-frame candidate evidence for imported data.
- `instance.json`: source checksum, metadata and original-to-internal actor mapping.

Add `--with-model` to an import for the optional conditional pitch-control endpoint
surface, using the declared native rate and pitch dimensions. This remains a model
contrast with explicit goalkeeper/offside assumptions, not causal match impact.
Without that flag the surface stays unavailable. Goal xG and the full receiving
window are not invented from incomplete inputs.

## Try a held-out real input

```sh
bash run.sh --input data_templates/heldout-bayern.csv.gz --metadata data_templates/heldout-bayern-metadata.json --output outputs/my-import/sequence
```

This real Last Row sequence was not in the original twelve-case demo. The source
label mentions Bayern–Liverpool; its date and scorer are not independently matched.
It is not presented as a Premier League case or validation of predictive accuracy.
Source credit and original dataset provenance are retained. Raw broadcast video
still needs a separate video-to-tracking computer-vision adapter.
