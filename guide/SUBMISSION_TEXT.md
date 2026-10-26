# Submission text

## Tagline

Follow the run. Reveal the response. BeyondTouch turns real football movement into visual stories, transparent metrics and explanations grounded in evidence.

## Description

A goal is the final moment of a much larger story. BeyondTouch helps explain the movement that came before it: the attacking run, a nearby defender’s response, a possible covering movement, and the space the finisher may exploit.

The working demo features twelve real Premier League sequences from Liverpool’s 2019 matches. Coloured player paths, direction arrows, timed captions and interactive story cards make each sequence easy to follow. Every case identifies its match, focus player, source data, available measurements and uncertainties.

Building on pitch-control research coauthored by team member Bassel Hammad, BeyondTouch combines approximate run distances, observed defender travel, separation measurements and conditional pitch-control comparisons. Transparent rules identify candidate response and covering patterns; explanations distinguish those interpretations from observed movement and independently verified goal context. A successful finish is never treated as proof that one run caused the goal.

The source trajectories are educational, manually collected and partial. Calculations retain their native 20 Hz samples; the interactive display and submission video interpolate for smooth presentation at 50 Hz or 50 fps. Interpolation adds display frames, not measurement accuracy. Current explanations are generated deterministically from the structured evidence.

Judges can extract the project and open START_HERE.html without Python, accounts or API keys. Developers receive reproducible source data, calculation code, tests and a guide explaining every step from the supplied observations to the final story.
