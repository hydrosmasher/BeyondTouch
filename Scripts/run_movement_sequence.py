"""Run BeyondTouch metrics on an authored fixture or synchronized tracking CSVs.

python Scripts/run_movement_sequence.py --output ../outputs
python Scripts/run_movement_sequence.py --home home.csv --away away.csv \
  --runner Home_11 --receiver Home_10 --carrier Home_8 --start 0 --end 3.5
"""
import argparse
import csv
import json
from pathlib import Path
import sys
import time
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from player_influence.movement_metrics import MovementMetrics, MetricConfig
from player_influence.replay_report import write_report


def synthetic_sequence():
    """Authored 11v11 open-play fixture. No real players, outcomes or xG claims."""
    times = np.round(np.arange(0, 6.01, 0.1), 6)
    starts = {
        'Home': {1: (-48, 0), 2: (-24, -22), 3: (-26, 8), 4: (-18, 24),
                 5: (-8, -6), 6: (-3, 16), 7: (8, -18), 8: (12, 5),
                 9: (32, 15), 10: (24, 2), 11: (15, -5)},
        'Away': {1: (49, 0), 2: (34, 20), 3: (34, 8), 4: (18, -4),
                 5: (25, 3), 6: (15, 16), 7: (8, 26), 8: (3, 8),
                 9: (-1, -10), 10: (10, -23), 11: (-10, 0)}}
    changes = {('Home', 11): (30, -22), ('Home', 10): (27, 3),
               ('Home', 8): (14, 5), ('Away', 4): (31, -21), ('Away', 5): (28, -7)}
    frames = {}
    for team in ('Home', 'Away'):
        data = {'Period': np.ones(len(times), dtype=int), 'Time [s]': times}
        for pid, start in starts[team].items():
            end = changes.get((team, pid), start)
            for axis, j in [('x', 0), ('y', 1)]:
                values = np.interp(times, [0, 3.5, 6], [start[j], end[j], end[j]])
                if team == 'Home' and pid == 10 and axis == 'x':
                    values = np.interp(times, [0, 3.5, 4.3, 5.5, 6], [24, 27, 28, 34, 34])
                data[f'{team}_{pid}_{axis}'] = values
                data[f'{team}_{pid}_v{axis}'] = np.gradient(values, times)
            data[f'{team}_{pid}_speed'] = np.hypot(data[f'{team}_{pid}_vx'], data[f'{team}_{pid}_vy'])
        data['ball_x'] = np.interp(times, [0, 3.5, 4.3, 5.5, 6], [12, 14, 28, 34, 49])
        data['ball_y'] = np.interp(times, [0, 3.5, 4.3, 5.5, 6], [5, 5, 3, 3, 1])
        frames[team] = pd.DataFrame(data)
    return frames['Home'], frames['Away']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('../outputs'))
    parser.add_argument('--home', type=Path)
    parser.add_argument('--away', type=Path)
    parser.add_argument('--runner', default='Home_11')
    parser.add_argument('--receiver', default='Home_10')
    parser.add_argument('--carrier', default='Home_8')
    parser.add_argument('--team', choices=['Home', 'Away'], default='Home')
    parser.add_argument('--start', type=float, default=0)
    parser.add_argument('--end', type=float, default=3.5)
    parser.add_argument('--grid', type=int, default=50)
    parser.add_argument('--home-attacks-left', action='store_true')
    parser.add_argument('--home-gk', default='1')
    parser.add_argument('--away-gk', default='1')
    args = parser.parse_args()
    if bool(args.home) != bool(args.away):
        parser.error('Provide both --home and --away')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if args.home:
        home, away = pd.read_csv(args.home), pd.read_csv(args.away)
        provenance = 'user-supplied tracking; source/licensing must be documented by the data owner'
        shot = None
    else:
        home, away = synthetic_sequence()
        home.to_csv(output/'synthetic-home.csv', index=False)
        away.to_csv(output/'synthetic-away.csv', index=False)
        provenance = 'authored synthetic 11v11 fixture, 10 Hz, 105 x 68 m; no real-match data'
        shot = {'time_s': 5.5, 'player': 'Home_10', 'xg': None,
                'xg_source': None, 'description': 'authored shot event; scoring outcome not asserted'}
    started = time.perf_counter()
    print('Computing spatial sensitivity through Basel’s InfluenceCalculator...', flush=True)
    metrics = MovementMetrics(MetricConfig(grid_columns=args.grid)).analyze(
        home, away, runner=args.runner, receiver=args.receiver, carrier=args.carrier,
        attacking_team=args.team, start_s=args.start, end_s=args.end,
        goalkeepers=(args.home_gk, args.away_gk), home_attacks_right=not args.home_attacks_left,
        provenance=provenance, shot=shot)
    metrics['runtime_s'] = time.perf_counter()-started
    with (output/'first-sequence-metrics.json').open('w') as f:
        json.dump(metrics, f, indent=2, allow_nan=False)
    with (output/'first-sequence-evidence.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(metrics['timeline'][0]))
        writer.writeheader()
        writer.writerows(metrics['timeline'])
    write_report(output, metrics, home, away)
    print(json.dumps({k: metrics[k] for k in ['space', 'associated_defenders', 'receiver', 'receiving_window', 'accounting', 'runtime_s']}, indent=2))
    print('Replay:', output/'first-sequence-replay.html')


if __name__ == '__main__':
    main()
