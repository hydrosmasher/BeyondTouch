# BeyondTouch

**The numbers behind the run.** Follow the run, defender-response candidate, covering candidate and finisher with coloured paths, direction arrows and auditable story cards. Real football events, replayable evidence and transparent movement metrics.

## Judges start here — no Python needed

1. **Code → Download ZIP**, then extract it.
2. Double-click **START_HERE.html**.
3. Start with **Di María’s World Cup final goal**, then explore the **12 Premier League sequences**.

The case READMEs also show animations and analysis directly on GitHub. The extracted HTML demo needs no server, account, API key or IDE.

## Featured real match

[Ángel Di María · Argentina v France · 2022 World Cup final](examples/di-maria-final) includes Basel’s retained rendered evidence and source-annotated ΔPC values. The full supplied animations are included, plus independently sourced StatsBomb shot context: 0.3034 xG, five completed passes and 9.757 s from first pass to shot. Shot context is not run credit. [One upload video](uploads/BeyondTouch-Liverpool-50fps.mp4) · [One upload picture](uploads/BeyondTouch-Liverpool.png).

## Twelve real Premier League sequences

Each folder contains a replay, animation, video, written analysis, raw source subset and recalculable metrics. Scores are source goal-states, not final results.

| Case | Focus player | Approximate path in nominal m |
| --- | --- | ---: |
| [PL-01 · Bournemouth 0 - 3 Liverpool](examples/pl-01-bournemouth-away) | Naby Keïta | ≈ 35.66 |
| [PL-02 · Fulham 0 - 1 Liverpool](examples/pl-02-fulham) | Roberto Firmino | ≈ 49.70 |
| [PL-03 · Leicester 0 - 3 Liverpool](examples/pl-03-leicester) | Trent Alexander-Arnold | ≈ 25.54 |
| [PL-04 · Liverpool 1 - 0 Everton](examples/pl-04-everton-opener) | Sadio Mané | ≈ 54.88 |
| [PL-05 · Liverpool 1 - 0 Watford](examples/pl-05-watford) | Sadio Mané | ≈ 70.17 |
| [PL-06 · Liverpool 1 - 0 Wolves](examples/pl-06-wolves) | Trent Alexander-Arnold | ≈ 37.79 |
| [PL-07 · Liverpool 2 - 0 Everton](examples/pl-07-everton-second) | Sadio Mané | ≈ 72.86 |
| [PL-08 · Liverpool 2 - 0 Man City](examples/pl-08-man-city) | Andy Robertson | ≈ 39.46 |
| [PL-09 · Liverpool 2 - 1 Newcastle](examples/pl-09-newcastle) | Roberto Firmino | ≈ 30.67 |
| [PL-10 · Liverpool 3 - 0 Bournemouth](examples/pl-10-bournemouth-home) | Roberto Firmino | ≈ 51.54 |
| [PL-11 · Liverpool 3 - 0 Norwich](examples/pl-11-norwich) | Jordan Henderson | ≈ 25.68 |
| [PL-12 · Southampton 1 - 2 Liverpool](examples/pl-12-southampton) | Mohamed Salah | ≈ 77.78 |

Last Row’s source trajectories are educational, manually collected, native **20 Hz**, and may omit players. Distances assume a 105 × 68 m pitch and are not calibrated measurements. The browser interpolates at 50 Hz for display only. Complete-match pitch-control area, the full receiving-window test and xG remain unavailable for these Premier League cases. A conditional endpoint model contrast now keeps all other observed players and the ball at their actual states; only the focus changes in the reference. Source coverage and calibration limits remain explicit.

## Developers — one command

```sh
bash run.sh --all
```

This recalculates the **12 real Premier League cases**. Use `--case 1` for one, `--check` for tests, or `--synthetic --all` for the separate 50 Hz full-model validation suite. Windows: `run.bat --all`. Python 3.12 is required only for recalculation. [Run instructions](guide/RUN_LOCALLY.md).

## Three places to look

- **examples/** — Di María evidence, 12 real Premier League cases and a separate validation folder.
- **guide/** — [project report](guide/PROJECT_REPORT.docx), [developer and metric guide](guide/DEVELOPER_GUIDE.md), [data sources](guide/DATA_SOURCES.md).
- **src/** — calculation code, tests and historical research files.

## Credits and scope

Research foundation: Bassel Hammad, Mahmoud Nasr, Omar Refaat, Mohamed Hafez and Tamer Basha; [LaurieOnTracking](https://github.com/bassel-hammad/LaurieOnTracking), Laurie Shaw / Friends of Tracking and Spearman-style pitch control. Real Premier League educational data: [Ricardo Tavares / Last Row / Friends of Tracking](https://github.com/Friends-of-Tracking-Data-FoTD/Last-Row). Match context uses official FIFA, Premier League and club reports linked in each case.

Existing MIT notices cover the retained code as stated in LICENSE; third-party data and supplied visualizations retain their own provenance. The project does not claim real-match causal player credit, calibrated xG or VAR compatibility. Explanations are deterministic; a generative service is not connected. [Project board](https://github.com/users/hydrosmasher/projects/2).

StatsBomb event analysis is credited with its logo in the featured case. Only derived analysis is included, not raw event redistribution. See guide/STATSBOMB_LICENSE.pdf.

## Explain a sequence

Each Liverpool case now has `story.json` with five explanation steps and explicit candidate/not-detected statuses. Gold RUN, orange D1, cyan D2 and purple FIN paths are observed trajectories. The story rule finds six covering candidates and no complete finisher chain in the twelve current clips. This distinction is exposed rather than turning correlation into a causal goal explanation. The [developer guide](guide/DEVELOPER_GUIDE.md#judge-walkthrough-from-video-to-explanation) explains the entire input → metrics → rules/model → explanation → video pipeline and includes judge questions.

## Submission media

Use the Liverpool–Everton [50 fps video](uploads/BeyondTouch-Liverpool-50fps.mp4) and [matching picture](uploads/BeyondTouch-Liverpool.png). This is interpolated presentation of 20 Hz educational tracking, with half-speed playback for readability. It is not 50 Hz captured tracking. [Media details](uploads/README.md).

## Runner options and new tracking inputs

Every Premier League replay now shows six possible movement arrows and a decision-tree view of the current snapshot. These are transparent geometric alternatives, not learned decisions, success probabilities or predicted defender reactions. Choose the correct attacking direction in the replay.

Import a new sequence without editing code:

```sh
bash run.sh --input /path/tracking.csv --metadata /path/sequence-metadata.json --output /path/new-empty-output
```

The importer supports declared native sampling rates, pitch dimensions, units and stable string actor IDs. It rejects gaps, duplicates and missing required observations. See [input format and options guide](guide/NEW_DATA_AND_OPTIONS.md), [metadata template](data_templates/sequence-metadata.json) and [held-out real source example](data_templates/heldout-bayern-metadata.json). This imports tracking data; raw broadcast video needs a separate computer-vision adapter.
