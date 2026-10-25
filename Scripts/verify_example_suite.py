"""Check generated suite accounting and negative controls. No model fitting."""
import argparse
import json
from pathlib import Path
import math
import csv

def verify(root):
    rows=json.loads((root/'summary.json').read_text())
    assert len(rows)>=12 and len({r['id'] for r in rows})==len(rows)
    lookup={r['id']:r for r in rows}
    for row in rows:
        m=json.loads((root/row['id']/'first-sequence-metrics.json').read_text())
        assert m['instance']['real_match'] is False
        assert m['instance']['real_player_names'] is None
        assert m['instance']['run_id']==row['run_id']
        hz=m['instance']['sample_rate_hz']
        assert hz in (25,50)
        assert math.isclose(m['instance']['sample_interval_s'],1/hz)
        timeline=m['timeline']
        assert len(timeline)==round(m['window']['duration_s']*hz)+1
        assert all(math.isclose(b['time_s']-a['time_s'],1/hz,abs_tol=1e-8)
                   for a,b in zip(timeline,timeline[1:]))
        for name in ('home.csv','away.csv'):
            with (root/row['id']/name).open() as f: tracking=list(csv.DictReader(f))
            assert len(tracking)==6*hz+1
            assert all(math.isclose(float(b['Time [s]'])-float(a['Time [s]']),1/hz,abs_tol=1e-8)
                       for a,b in zip(tracking,tracking[1:]))
        a=m['space']['attacking_half'];assert math.isclose(a['gained_m2']-a['lost_m2'],a['net_m2'],abs_tol=1e-8)
        a=m['accounting'];assert math.isclose(a['observed_team_net_m2']-a['sum_individual_attacker_net_m2'],a['unattributed_net_m2'],abs_tol=1e-8)
        assert 0<=m['receiving_window']['longest_continuous_s']<=m['window']['duration_s']+1e-8
        assert m['config']['exclude_offside'] and m['config']['integration_step_s']==.02
        assert (root/row['id']/'first-sequence-replay.html').is_file()
    assert abs(lookup['BT-SYN-05']['net_m2'])<1e-9, 'Stationary runner must have zero sensitivity'
    assert abs(lookup['BT-SYN-12']['defender_m'])<1e-9, 'Stationary defenders must have zero travel'
    assert abs(lookup['BT-SYN-10']['window_s'])<1e-9, 'Tightly marked receiver must have no window'
    assert math.isclose(lookup['BT-SYN-01']['net_m2'],lookup['BT-SYN-09']['net_m2'],abs_tol=1e-8), 'Team rotation symmetry'
    print(f"Verified {len(rows)} labelled examples, metric accounting, stationary controls, blocked receiver and team symmetry.")

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--results',type=Path,default=Path('outputs/examples'))
    verify(p.parse_args().results)
