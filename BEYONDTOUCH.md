# BeyondTouch methods

See README.md for the current 12-example implementation and LOCAL_SETUP.md for reproduction. The single-fixture entry point is retained as an earlier 10 Hz demonstration.

The suite uses authored 50 Hz synthetic tracking, not real match data. Runner area is an endpoint pitch-control sensitivity under a single-runner counterfactual, not causal attribution. Defender travel is observed polyline distance, not energy or distance caused by the runner. Receiving windows use explicit separation, onside, pitch-control and lane criteria. xG is unavailable without an independently sourced model or supplied shot values.

Read the current per-case numerical_sensitivity fields for grid-stability results. These are numerical diagnostics, not empirical accuracy. Parameter sensitivity is reported for case 01. The report explains the assumptions and limitations.

Bassel Hammad’s research and LaurieOnTracking implementation are credited in README.md and the retained MIT licence.
