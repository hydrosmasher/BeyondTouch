# BeyondTouch — first sequence

Source: authored synthetic 11v11 fixture, 10 Hz, 105 x 68 m; no real-match data

Run: Home_11 | receiver: Home_10 | 0–3.5 seconds

- Control-equivalent attacking area gained: 381.05 m²
- Control-equivalent attacking area lost: 87.51 m²
- Net control-equivalent attacking area: 293.54 m²
- Net control-equivalent penalty-area change: 67.44 m²
- Selected nearby defenders' observed travel: 21.40 m
- Receiver separation: 1.41 → 8.60 m
- Candidate receiving window total: 2.20 s
- Longest continuous candidate window: 2.20 s
- Shot xG: unavailable; no value estimated or attributed
- Unattributed team change: -181.63 m²

Space values compare run endpoints, advancing the runner's position and velocity while freezing all other state at run start. They are not a sum of repeatedly counted area and are not causal credit.

The replay includes context after pass release, but the run metrics end at release. Commentary is a deterministic evidence summary, not a connected generative AI model.

## Limitations
- Synthetic trajectories are authored, not an empirical validation on real matches.
- Frozen-player counterfactuals measure model sensitivity, not causal defender responses.
- Pitch-control surface does not filter offside players; candidate receiver onside is checked separately.
- Grid-cell centres approximate region boundaries; area depends on grid resolution.
- Defender travel is observed distance, not energy or distance caused by the runner.
- Window duration is threshold-dependent; the geometric lane rule omits ball flight interception.
- No xG model is trained or inferred.