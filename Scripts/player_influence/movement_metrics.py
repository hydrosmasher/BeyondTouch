"""BeyondTouch movement evidence. Units are metres, seconds and probability-weighted m².

Uses Basel's InfluenceCalculator and the inherited Spearman pitch-control engine.
Counterfactual results are model sensitivities, not causal player credit.
"""
from dataclasses import dataclass, asdict
from types import SimpleNamespace
import numpy as np

from .influence_calculator import InfluenceCalculator
from .pitch_control import PitchControlCalculator
import Metrica_PitchControl as mpc


@dataclass(frozen=True)
class MetricConfig:
    field_length_m: float = 105.0
    field_width_m: float = 68.0
    grid_columns: int = 50
    high_speed_m_s: float = 5.5
    defender_start_radius_m: float = 10.0
    receiver_clearance_m: float = 3.0
    receiver_control_threshold: float = 0.65
    passing_lane_clearance_m: float = 1.5
    max_tracking_gap_s: float = 0.25
    integration_step_s: float = 0.02
    reaction_time_att_s: float = 0.7
    reaction_time_def_s: float = 1.0
    exclude_offside: bool = True


def position(row, player):
    return np.array([row[player + '_x'], row[player + '_y']], dtype=float)


def player_ids(row, team):
    return [c[:-2] for c in row.index if c.startswith(team + '_') and c.endswith('_x')
            and np.isfinite(position(row, c[:-2])).all()]


def area_metrics(delta, cell_area, mask=None):
    values = np.asarray(delta, dtype=float)
    if mask is not None:
        if np.asarray(mask).dtype == bool:
            values = values[mask]
        else:
            weights = np.asarray(mask, dtype=float)
            if weights.shape != values.shape or np.any((weights < 0) | (weights > 1)):
                raise ValueError('Area weights must be grid-shaped fractions in [0,1]')
            values = values * weights
    values = values[np.isfinite(values)]
    return {'gained_m2': float(np.maximum(values, 0).sum() * cell_area),
            'lost_m2': float(-np.minimum(values, 0).sum() * cell_area),
            'net_m2': float(values.sum() * cell_area)}


def rectangle_overlap_weights(xgrid, ygrid, dx, dy, xmin, xmax, ymin, ymax):
    """Exact cell overlap with rectangular regions, avoiding centre-mask boundary error."""
    wx = np.maximum(0, np.minimum(xgrid+dx/2, xmax)-np.maximum(xgrid-dx/2, xmin))/dx
    wy = np.maximum(0, np.minimum(ygrid+dy/2, ymax)-np.maximum(ygrid-dy/2, ymin))/dy
    return np.clip(wy[:, None]*wx[None, :], 0, 1)


def distance_metrics(points, times, high_speed):
    lengths = np.linalg.norm(np.diff(points, axis=0), axis=1)
    speeds = lengths / np.diff(times)
    return {'distance_m': float(lengths.sum()),
            'high_speed_distance_m': float(lengths[speeds >= high_speed].sum()),
            'peak_segment_speed_m_s': float(speeds.max(initial=0))}


def window_durations(times, flags):
    """Left-interval rule: sample i represents [time_i, time_i+1)."""
    durations = np.diff(times)
    total, longest, current = 0.0, 0.0, 0.0
    for dt, flag in zip(durations, flags[:-1]):
        if flag:
            current += float(dt)
            total += float(dt)
            longest = max(longest, current)
        else:
            current = 0.0
    return {'total_s': total, 'longest_continuous_s': longest}


class MovementMetrics:
    def __init__(self, config=None):
        self.config = config or MetricConfig()

    def analyze(self, home, away, *, runner, receiver, carrier, attacking_team,
                start_s, end_s, goalkeepers=('1', '1'), home_attacks_right=True,
                provenance='unknown', shot=None):
        """Analyze a run ending at pass release. Frames after release are replay context.

        Inputs use Basel's metric-centred tracking columns, with vx/vy in m/s.
        Events must identify the carrier; the runner must be off-ball for this window.
        Shot xG is optional supplied context, never inferred or assigned to the runner.
        """
        c = self.config
        if c.integration_step_s <= 0 or c.integration_step_s > 0.04:
            raise ValueError('integration_step_s must be in (0, 0.04]')
        if attacking_team not in ('Home', 'Away') or start_s >= end_s:
            raise ValueError('Valid team and increasing analysis window required')
        if len({runner, receiver, carrier}) != 3:
            raise ValueError('Runner, receiver and carrier must be distinct')
        if any(not p.startswith(attacking_team + '_') for p in (runner, receiver, carrier)):
            raise ValueError('Selected players must belong to the attacking team')
        for df in (home, away):
            t = df['Time [s]'].to_numpy(float)
            if len(t) < 2 or not np.all(np.diff(t) > 0):
                raise ValueError('Tracking times must be strictly increasing and unique')
            if t[0] > start_s or t[-1] < end_s:
                raise ValueError('Tracking does not cover the analysis window')
        times = home['Time [s]'].to_numpy(float)
        if not np.array_equal(times, away['Time [s]'].to_numpy(float)):
            raise ValueError('Home/Away tracking timestamps must be synchronized')
        selected = (times >= start_s - 1e-9) & (times <= end_s + 1e-9)
        times = times[selected]
        if len(times) < 2 or abs(times[0]-start_s) > 1e-8 or abs(times[-1]-end_s) > 1e-8:
            raise ValueError('Run boundaries must coincide with tracking samples')
        if np.diff(times).max() > c.max_tracking_gap_s + 1e-9:
            raise ValueError('Tracking gap exceeds allowed maximum; do not interpolate across it')
        h, a = home.loc[selected].copy(), away.loc[selected].copy()
        if h['Period'].nunique() != 1 or a['Period'].nunique() != 1:
            raise ValueError('Analysis cannot cross a period boundary')
        attack, defense = (h, a) if attacking_team == 'Home' else (a, h)
        defending_team = 'Away' if attacking_team == 'Home' else 'Home'
        for df, team in ((attack, attacking_team), (defense, defending_team)):
            if not np.isfinite(df[['ball_x', 'ball_y']].to_numpy(float)).all():
                raise ValueError('Ball position must be finite')
            active = player_ids(df.iloc[0], team)
            for p in active:
                for suffix in ('x', 'y', 'vx', 'vy'):
                    if not np.isfinite(df[p + '_' + suffix].to_numpy(float)).all():
                        raise ValueError('Incomplete active-player tracking: ' + p)
            for _, row in df.iterrows():
                if set(player_ids(row, team)) != set(active):
                    raise ValueError('Substitution/visibility change inside run; split the window')
        if any(p not in player_ids(attack.iloc[0], attacking_team) for p in (runner, receiver, carrier)):
            raise ValueError('Selected player is absent')
        direction = (1 if home_attacks_right else -1) * (1 if attacking_team == 'Home' else -1)
        params = mpc.default_model_params()
        params.update(int_dt=c.integration_step_s, reaction_time=c.reaction_time_att_s,
                      reaction_time_def=c.reaction_time_def_s)
        pc = PitchControlCalculator(goalkeepers, params=params, homeTeamStartLeft=home_attacks_right,
                                    field_dimen=(c.field_length_m, c.field_width_m),
                                    n_grid_cells_x=c.grid_columns, exclude_offside=c.exclude_offside)
        loader = SimpleNamespace(tracking_home=h, tracking_away=a)
        calculator = InfluenceCalculator(loader, pc, attacking_team)
        # One complete run comparison, not a sum over intervals that could re-count space.
        result = calculator._analyze_time_transition(h, a, h.index[0], start_s, end_s)
        surface = result['player_influences'][runner]['delta_PC']
        xx, yy = np.meshgrid(pc.xgrid, pc.ygrid)
        dx = c.field_length_m/len(pc.xgrid)
        dy = c.field_width_m/len(pc.ygrid)
        left, right = c.field_length_m/2-16.5, c.field_length_m/2
        if direction < 0: left, right = -right, -left
        box_mask = rectangle_overlap_weights(pc.xgrid, pc.ygrid, dx, dy, left, right, -20.16, 20.16)
        area = area_metrics(surface, pc.cell_area_m2)
        box_area = area_metrics(surface, pc.cell_area_m2, box_mask)
        observed = area_metrics(result['ΔPC_actual'], pc.cell_area_m2)
        individual_sum = float(np.nansum(result['ΔPC_sum']) * pc.cell_area_m2)
        residual = observed['net_m2'] - individual_sum
        defenders = player_ids(defense.iloc[0], defending_team)
        outfield = [p for p in defenders if p != defending_team + '_' + str(goalkeepers[0 if defending_team == 'Home' else 1])]
        if not outfield or len(defenders) < 2:
            raise ValueError('Need outfield defenders and a second-last-defender offside line')
        tracks = {p: defense[[p+'_x', p+'_y']].to_numpy(float) for p in outfield}
        runner_points = attack[[runner+'_x', runner+'_y']].to_numpy(float)
        unit_positions = np.stack(list(tracks.values()), axis=1).mean(axis=1)
        near = sorted(outfield, key=lambda p: np.linalg.norm(tracks[p][0]-runner_points[0]))
        near = [p for p in near if np.linalg.norm(tracks[p][0]-runner_points[0]) <= c.defender_start_radius_m][:2]
        defender_rows = []
        for p in near:
            relative = tracks[p] - (unit_positions - unit_positions[0])
            d = distance_metrics(tracks[p], times, c.high_speed_m_s)
            d['player'] = p
            d['distance_relative_to_unit_translation_m'] = float(np.linalg.norm(np.diff(relative, axis=0), axis=1).sum())
            d['initial_distance_to_runner_m'] = float(np.linalg.norm(tracks[p][0]-runner_points[0]))
            defender_rows.append(d)
        evidence = []
        for i, t in enumerate(times):
            ar, dr = attack.iloc[i], defense.iloc[i]
            recv = position(ar, receiver)
            d_positions = np.array([position(dr, p) for p in defenders])
            separation = float(np.linalg.norm(d_positions-recv, axis=1).min())
            ball = np.array([ar['ball_x'], ar['ball_y']], float)
            line = max(0., float(np.sort(direction*d_positions[:, 0])[-2]), direction*ball[0])
            onside = bool(direction*recv[0] <= line + 0.2)
            aps = mpc.initialise_players(ar, attacking_team, pc.params, str(goalkeepers[0 if attacking_team=='Home' else 1]), True)
            dps = mpc.initialise_players(dr, defending_team, pc.params, str(goalkeepers[0 if defending_team=='Home' else 1]), False)
            if c.exclude_offside:
                aps = [p for p in aps if direction*p.position[0] <= line+0.2]
            probability = float(mpc.calculate_pitch_control_at_target(recv, aps, dps, ball, pc.params)[0])
            segment = recv-ball
            denom = np.dot(segment, segment)
            if denom > 1e-9:
                u = np.clip((d_positions-ball) @ segment / denom, 0, 1)
                lane_clearance = float(np.linalg.norm(d_positions-(ball+u[:, None]*segment), axis=1).min())
            else:
                lane_clearance = 0.0
            eligible = bool(onside and separation >= c.receiver_clearance_m
                            and probability >= c.receiver_control_threshold
                            and lane_clearance >= c.passing_lane_clearance_m)
            evidence.append({'time_s': float(t), 'nearest_defender_m': separation,
                             'receiver_control': probability, 'onside': onside,
                             'lane_clearance_m': lane_clearance, 'candidate_window': eligible})
        shot_context = None
        if shot is not None:
            if shot['time_s'] < end_s:
                raise ValueError('Context shot must occur after run end')
            xg = shot.get('xg')
            if xg is not None and (not 0 <= xg <= 1 or not shot.get('xg_source')):
                raise ValueError('Supplied xG needs range [0,1] and a named source')
            shot_context = {**shot, 'attributed_to_runner': False}
        gains = evidence[-1]['nearest_defender_m'] - evidence[0]['nearest_defender_m']
        return {'schema_version': '1.0', 'provenance': provenance,
                'players': {'runner': runner, 'receiver': receiver, 'carrier': carrier},
                'attacking_team': attacking_team,
                'window': {'start_s': start_s, 'end_s': end_s, 'duration_s': end_s-start_s,
                           'off_ball_basis': 'supplied constant carrier identity through pass release'},
                'config': asdict(c), 'model_parameters': pc.params,
                'grid': {'columns': len(pc.xgrid), 'rows': len(pc.ygrid), 'cell_area_m2': pc.cell_area_m2},
                'space': {'attacking_half': area, 'penalty_area': box_area,
                          'method': 'single-run endpoint sensitivity; runner position AND velocity updated; all other state frozen at start'},
                'accounting': {'observed_team_net_m2': observed['net_m2'],
                               'sum_individual_attacker_net_m2': individual_sum,
                               'unattributed_net_m2': residual,
                               'note': 'Residual includes defenders, ball, nonlinear interactions and other state changes; not synergy alone.'},
                'runner_distance': distance_metrics(runner_points, times, c.high_speed_m_s),
                'associated_defenders': defender_rows,
                'defender_selection': 'up to two nearest outfield defenders within start radius; association is not causation',
                'receiver': {'start_separation_m': evidence[0]['nearest_defender_m'],
                             'release_separation_m': evidence[-1]['nearest_defender_m'],
                             'separation_change_m': gains,
                             'start_control': evidence[0]['receiver_control'],
                             'release_control': evidence[-1]['receiver_control']},
                'receiving_window': {**window_durations(times, [e['candidate_window'] for e in evidence]),
                                     'method': 'left-interval samples satisfying onside, separation, control and straight-lane clearance thresholds; not pass completion probability'},
                'shot_context': shot_context, 'timeline': evidence,
                'surfaces': {'x': pc.xgrid.tolist(), 'y': pc.ygrid.tolist(),
                             'baseline': np.nan_to_num(result['PC_baseline'], nan=0).tolist(),
                             'runner_delta': np.nan_to_num(surface, nan=0).tolist()},
                'limitations': ['Synthetic trajectories are authored, not an empirical validation on real matches.',
                                'Frozen-player counterfactuals measure model sensitivity, not causal defender responses.',
                                'Offside filtering uses centre positions and 0.2 m tolerance; player body parts are not tracked.',
                                'Regional area uses fractional cell overlap; spatial integration still depends on grid resolution.',
                                'Defender travel is observed distance, not energy or distance caused by the runner.',
                                'Window duration is threshold-dependent; the geometric lane rule omits ball flight interception.',
                                'No xG model is trained or inferred.']}
