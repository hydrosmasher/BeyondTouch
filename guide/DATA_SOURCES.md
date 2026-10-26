# Sources and provenance

## Di María final visualizations

Ángel Di María, Argentina v France, 18 December 2022, goal 36′. Event identity was
provided after the user’s meeting with Bassel Hammad and corroborated with
[FIFA](https://www.fifa.com/en/tournaments/mens/worldcup/articles/argentina-france-2022-final-greatest-games).
Three retained keyframes preserve the supplied plot annotations; SHA-256 values are
in evidence.json. Raw tracking, grid values, player-dot mapping and the exact ΔPC
differencing definition were not supplied. Only displayed extrema are transcribed.
No new movement m² or defender travel is assigned from these images. Independent shot xG context is documented below.

## Premier League educational trajectories

Source: [Ricardo Tavares / Last Row / Friends of Tracking](https://github.com/Friends-of-Tracking-Data-FoTD/Last-Row).
Original: datasets/positional_data/liverpool_2019.csv.
Verified original Git blob: `77e053fba2f9569a60cd41d87a817bee0028c2c2`.
Original SHA-256: `6ad9c2a9e6aa6780f20587230877d772239cda4fdbcad77d1306028f6c59d9ce`.

Twelve Premier League sequences were selected from the nineteen-play 2019 collection.
The author permits dataset use with source credit and describes it as educational,
manually collected and incomplete, with insufficient accuracy for research. Native
cadence is 20 Hz; coordinates are normalized 0–100. These third-party data are not
relicensed under BeyondTouch’s MIT code notice.

Each case records its source subset SHA-256, exact play label, local IDs, shirt
mappings, match context, and official report link. Context is matched using the play
label and known Liverpool shirt identities; precise broadcast synchronization is
unavailable. Scores describe the source goal-state, not the final result. Unconfirmed
opponents remain local IDs. Nominal distances assume an unverified 105 × 68 m pitch.

The Chelsea score-state can be ambiguous across competitions, so it was excluded.
Other non-Premier-League source sequences are not silently relabelled. Selected
source play numbers and context references are recorded in src/real_cases.py.

## Synthetic validation and code

The twelve authored 50 Hz fixtures are under examples/validation/, with fictional
teams and synthetic player IDs. They are tests, not real matches or calibration data.
Research code extends [Basel’s LaurieOnTracking implementation](https://github.com/bassel-hammad/LaurieOnTracking),
Laurie Shaw / Friends of Tracking and Spearman-style pitch control. Research authors:
Bassel Hammad, Mahmoud Nasr, Omar Refaat, Mohamed Hafez and Tamer Basha. Existing code
notices remain in LICENSE and historical files.

## Independent World Cup event analysis

[StatsBomb Open Data](https://github.com/hudl/open-data), match 3869685,
shot ef86f4d9-7acd-4ed0-a5ec-9129079e8fbe: shot xG 0.30340916.
Derived analysis records five completed passes and 9.757 seconds between the first
pass and the shot. This event clock is not synchronized with Basel’s plot clock.
Shot xG is not off-ball run attribution. Only derived analysis is included; raw
event data are not redistributed. The source logo and provider agreement are in
guide/. Provider terms are distinct from the code license.

## Conditional moving-scene model

For each Premier League source clip, all other observed players and the ball retain
their actual endpoint states. Only the focus player’s state is substituted with its
initial observed state in the reference. These conditional model contrasts use
partial educational observations, nominal pitch dimensions and generic player
parameters. They are neither calibrated full-match pitch control nor causal credit.
Each model-analysis.json includes a 50-versus-75-column numerical sensitivity check.
