"""Portable evidence report and animated replay. No external assets or AI calls."""
import html
import json
import math
from pathlib import Path


def write_report(output, metrics, home, away):
    frames = []
    for i in range(len(home)):
        players = []
        for team, df in [('Home', home), ('Away', away)]:
            row = df.iloc[i]
            for col in df.columns:
                if col.startswith(team+'_') and col.endswith('_x'):
                    pid = col[:-2]
                    x, y = float(row[col]), float(row[pid+'_y'])
                    if math.isfinite(x) and math.isfinite(y):
                        players.append({'id': pid, 'team': team, 'x': x, 'y': y})
        frames.append({'t': float(home.iloc[i]['Time [s]']), 'players': players,
                       'ball': [float(home.iloc[i]['ball_x']), float(home.iloc[i]['ball_y'])]})
    bundle = {'metrics': metrics, 'frames': frames}
    payload = json.dumps(bundle, allow_nan=False).replace('<', '\\u003c')
    report = TEMPLATE.replace('__BUNDLE__', payload)
    (output/'first-sequence-replay.html').write_text(report)
    write_gif(output/'first-sequence-replay.gif', bundle)
    m = metrics
    area = m['space']['attacking_half']
    d = sum(x['distance_m'] for x in m['associated_defenders'])
    text = f"""# BeyondTouch — first sequence

Source: {m['provenance']}

Run: {m['players']['runner']} | receiver: {m['players']['receiver']} | {m['window']['start_s']}–{m['window']['end_s']} seconds

- Control-equivalent attacking area gained: {area['gained_m2']:.2f} m²
- Control-equivalent attacking area lost: {area['lost_m2']:.2f} m²
- Net control-equivalent attacking area: {area['net_m2']:.2f} m²
- Net control-equivalent penalty-area change: {m['space']['penalty_area']['net_m2']:.2f} m²
- Selected nearby defenders' observed travel: {d:.2f} m
- Receiver separation: {m['receiver']['start_separation_m']:.2f} → {m['receiver']['release_separation_m']:.2f} m
- Candidate receiving window total: {m['receiving_window']['total_s']:.2f} s
- Longest continuous candidate window: {m['receiving_window']['longest_continuous_s']:.2f} s
- Shot xG: unavailable; no value estimated or attributed
- Unattributed team change: {m['accounting']['unattributed_net_m2']:.2f} m²

Space values compare run endpoints, advancing the runner's position and velocity while freezing all other state at run start. They are not a sum of repeatedly counted area and are not causal credit.

The replay includes context after pass release, but the run metrics end at release. Commentary is a deterministic evidence summary, not a connected generative AI model.

## Limitations
""" + '\n'.join('- '+x for x in m['limitations'])
    (output/'first-sequence-summary.md').write_text(text)


def write_gif(path, bundle):
    from PIL import Image, ImageDraw, ImageFont
    font_path = '/System/Library/Fonts/Supplemental/Arial.ttf'
    try:
        title_font = ImageFont.truetype(font_path, 27)
        font = ImageFont.truetype(font_path, 17)
        small = ImageFont.truetype(font_path, 13)
    except OSError:
        title_font = font = small = ImageFont.load_default()
    m = bundle['metrics']
    length, width = m['config']['field_length_m'], m['config']['field_width_m']
    def point(x, y):
        return (round(30+(x+length/2)*8), round(115+(width/2-y)*8))
    pictures = []
    sample_dt = bundle['frames'][1]['t'] - bundle['frames'][0]['t']
    step = max(1, round(0.2/sample_dt))
    for frame in bundle['frames'][::step]:
        im = Image.new('RGB', (1120, 720), '#0c1820')
        draw = ImageDraw.Draw(im)
        draw.text((30, 20), 'BEYONDTOUCH / Movement evidence', font=title_font, fill='#f0f4ee')
        identity = m.get('instance', {})
        source_label = ('SYNTHETIC · '+str(identity.get('sample_rate_hz',round(1 / (bundle['frames'][1]['t']-bundle['frames'][0]['t']))))+' Hz · '+identity.get('match_id','FIXTURE')+' / '+identity.get('run_id','RUN 01'))
        draw.text((30, 62), source_label, font=small, fill='#a9bbb9')
        draw.rectangle([point(-length/2, width/2), point(length/2, -width/2)], fill='#164b40', outline='#99c4a9', width=2)
        draw.line([point(0,width/2), point(0,-width/2)], fill='#99c4a9', width=2)
        x,y=point(0,0)
        draw.ellipse((x-73,y-73,x+73,y+73), outline='#99c4a9',width=2)
        for sign in (-1,1):
            p1=point(sign*length/2,20.16);p2=point(sign*(length/2-16.5),-20.16)
            draw.rectangle((min(p1[0],p2[0]),min(p1[1],p2[1]),max(p1[0],p2[0]),max(p1[1],p2[1])),outline='#99c4a9',width=2)
        past=[f for f in bundle['frames'] if f['t']<=frame['t']]
        for pid,color in [(m['players']['runner'],'#f5cb68'),(m['players']['receiver'],'#7de5e0')]:
            trail=[point(p['x'],p['y']) for f in past for p in f['players'] if p['id']==pid]
            if len(trail)>1: draw.line(trail,fill=color,width=3)
        for p in frame['players']:
            x,y=point(p['x'],p['y'])
            color='#db7a76' if p['team']=='Away' else '#e7efea'
            if p['id']==m['players']['runner']:color='#f5cb68'
            if p['id']==m['players']['receiver']:color='#7de5e0'
            draw.ellipse((x-10,y-10,x+10,y+10),fill=color,outline='#0a1820',width=2)
            draw.text((x-7,y-8),p['id'].split('_')[1],font=small,fill='#0a1820')
        x,y=point(*frame['ball']);draw.ellipse((x-5,y-5,x+5,y+5),fill='white',outline='black',width=2)
        evidence=min(m['timeline'],key=lambda e:abs(e['time_s']-min(frame['t'],m['window']['end_s'])))
        x=895
        for yy, label, value in [(130,'REPLAY',f"{frame['t']:.1f} s"),
                                 (225,'RUNNER',m['players']['runner']),
                                 (320,'RECEIVER GAP',f"{evidence['nearest_defender_m']:.2f} m"),
                                 (415,'WINDOW', 'OPEN' if evidence['candidate_window'] else 'CLOSED')]:
            draw.text((x,yy),label,font=small,fill='#a9bbb9')
            draw.text((x,yy+28),value,font=title_font,fill='#f5cb68')
        state='Before release: run metrics measured' if frame['t']<=m['window']['end_s'] else 'After release: replay context only'
        draw.text((30,680),state+' · xG unavailable · no causal defender attribution',font=font,fill='#a9bbb9')
        pictures.append(im)
    pictures[0].save(path,save_all=True,append_images=pictures[1:],duration=round(step*sample_dt*1000),loop=0,optimize=True)


TEMPLATE = r'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>BeyondTouch — first sequence evidence</title>
<style>
:root{color-scheme:dark;--bg:#0c1820;--panel:#13252c;--line:#294048;--ink:#eef3ec;--muted:#acbeba;--gold:#f5cb68}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px system-ui,sans-serif}main{max-width:1380px;margin:auto;padding:32px}header{display:flex;justify-content:space-between;align-items:center;gap:20px;border-bottom:1px solid var(--line);padding-bottom:22px}h1{font-size:30px;letter-spacing:-1px;margin:0}h2{font-size:21px;margin:0 0 12px}p{line-height:1.6;color:var(--muted)}.eyebrow{font-size:11px;letter-spacing:2px;color:var(--gold);text-transform:uppercase}.badge{border:1px solid var(--gold);padding:8px 12px;border-radius:25px;font-size:12px;color:var(--gold)}.layout{display:grid;grid-template-columns:1.8fr 1fr;gap:24px;margin:24px 0}.panel,.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:22px}.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:20px 0}.value{font-size:29px;color:var(--gold);margin:8px 0}.label{font-size:12px;color:var(--muted)}canvas{width:100%;height:auto;display:block;border-radius:8px;background:#164b40}.controls{display:flex;align-items:center;gap:12px;margin-top:16px;flex-wrap:wrap}button,select{background:#20383d;border:1px solid #425b5e;border-radius:7px;color:var(--ink);padding:9px 14px;cursor:pointer}button.primary{background:var(--gold);color:#14252b;border-color:var(--gold)}input[type=range]{flex:1;min-width:100px;accent-color:var(--gold)}.legend{display:flex;gap:18px;font-size:12px;color:var(--muted);margin:12px 0}.row{display:flex;justify-content:space-between;border-bottom:1px solid var(--line);padding:10px 0;gap:10px}.row b{color:var(--gold)}.explain{border-left:3px solid var(--gold);padding-left:16px}.small{font-size:12px;color:var(--muted);line-height:1.6}.wide{margin:20px 0}details{margin-top:12px}summary{cursor:pointer;color:var(--gold)}table{width:100%;border-collapse:collapse;font-size:13px}td,th{text-align:left;padding:10px;border-bottom:1px solid var(--line)}a{color:var(--gold)}@media(max-width:850px){.layout{grid-template-columns:1fr}.cards{grid-template-columns:1fr 1fr}main{padding:18px}header{align-items:flex-start;flex-direction:column}}
</style><main><header><div><div class="eyebrow">First working sequence / evidence laboratory</div><h1>BeyondTouch</h1><p style="margin-bottom:0">The numbers behind the run.</p></div><span class="badge" id="source-badge">Synthetic fixture · 11v11 · 10 Hz</span></header>
<div class="cards" id="cards"></div><div class="layout"><section class="panel"><div class="eyebrow">01 / Replay</div><h2>Movement, response, opportunity.</h2><canvas id="pitch" width="1050" height="680" aria-label="Football sequence replay showing Home players, Away players, runner trails and ball"></canvas><div class="legend"><span style="color:#f5cb68">● Runner 11</span><span style="color:#7de5e0">● Receiver 10</span><span>● Home</span><span style="color:#db7a76">● Away</span></div><div class="controls"><button class="primary" id="play">Play</button><button id="restart">Restart</button><input type="range" id="seek" min="0" max="60" value="0" aria-label="Replay frame"><b id="clock">0.0 s</b><select id="speed" aria-label="Playback speed"><option value="0.5">0.5×</option><option value="1" selected>1×</option><option value="2">2×</option></select></div><div class="controls"><label><input type="checkbox" id="heat"> Show runner's endpoint control-change map</label></div><p class="small" id="phase"></p><p class="small">The optional map compares run start and release. It is a fixed counterfactual sensitivity map, not a live pressure map. Gold = increased control; pink = decreased control.</p></section>
<aside class="panel"><div class="eyebrow">02 / Evidence at this moment</div><h2>The receiving opportunity</h2><div id="live"></div><p class="small">After release, evidence remains fixed at the last run sample; subsequent animation is context only.</p><hr style="border:0;border-top:1px solid var(--line);margin:24px 0"><div class="eyebrow">03 / Evidence summary</div><p class="explain" id="narrative"></p><p class="small">Deterministic summary from calculated metrics. A generative AI service is not connected yet.</p></aside></div>
<section class="panel wide"><div class="eyebrow">04 / Associated defender travel</div><h2>Observed effort, without claiming causality.</h2><table><thead><tr><th>Defender</th><th>Travel</th><th>Above speed threshold</th><th>Relative to unit translation</th></tr></thead><tbody id="defenders"></tbody></table><p class="small" id="selection"></p></section>
<section class="panel wide"><div class="eyebrow">05 / Model accounting</div><div id="accounting"></div><p class="small">Individual attacker sensitivities are not an exact additive decomposition. The residual includes defender movement, ball movement and nonlinear interactions.</p><details><summary>Definitions, thresholds and limitations</summary><div id="definitions"></div></details></section>
<p class="small">Built on Bassel Hammad and coauthors' movement-attribution research and Laurie Shaw / Friends of Tracking pitch-control implementation. Synthetic scenario is authored for integration testing, not proof of real-match accuracy.</p></main>
<script>
const bundle=__BUNDLE__,m=bundle.metrics,frames=bundle.frames;
const $=id=>document.getElementById(id),fmt=(v,n=2)=>Number(v).toFixed(n),signed=v=>(v>=0?'+':'')+fmt(v);
if(m.instance){const p=document.createElement('p');p.className='small';p.textContent=m.instance.match_label+' · '+m.instance.run_id+' · '+m.instance.title+' · '+m.instance.match_clock+' · Runner '+m.players.runner+', receiver '+m.players.receiver+', carrier '+m.players.carrier+'. Player names and teams are synthetic, not real identities.';document.querySelector('header').after(p);}
if(m.instance)$('source-badge').textContent='Synthetic fixture · 11v11 · '+m.instance.sample_rate_hz+' Hz';
const totalTravel=m.associated_defenders.reduce((s,d)=>s+d.distance_m,0);
$('cards').innerHTML=[['Net attacking control-equivalent area',signed(m.space.attacking_half.net_m2)+' m²','Single-run endpoint model sensitivity'],['Nearby defenders’ observed travel',fmt(totalTravel)+' m','Not distance caused by the runner'],['Receiver separation at release',fmt(m.receiver.release_separation_m)+' m','Start: '+fmt(m.receiver.start_separation_m)+' m'],['Longest candidate receiving window',fmt(m.receiving_window.longest_continuous_s)+' s','Total qualifying time: '+fmt(m.receiving_window.total_s)+' s']].map(x=>`<div class="card"><div class="label">${x[0]}</div><div class="value">${x[1]}</div><div class="small">${x[2]}</div></div>`).join('');
$('narrative').textContent=`During ${fmt(m.window.duration_s,1)} seconds, ${m.players.runner} travelled ${fmt(m.runner_distance.distance_m)} m. The receiver's nearest-defender gap changed from ${fmt(m.receiver.start_separation_m)} to ${fmt(m.receiver.release_separation_m)} m. The longest threshold-defined receiving window was ${fmt(m.receiving_window.longest_continuous_s)} s. Moving only the runner's position and velocity in the spatial model changed attacking control-equivalent area by ${signed(m.space.attacking_half.net_m2)} m². These observations do not establish that the runner caused the defensive response.`;
$('defenders').innerHTML=m.associated_defenders.map(d=>`<tr><td>${d.player}</td><td>${fmt(d.distance_m)} m</td><td>${fmt(d.high_speed_distance_m)} m</td><td>${fmt(d.distance_relative_to_unit_translation_m)} m</td></tr>`).join('');
$('selection').textContent=m.defender_selection+'. High-speed threshold: '+m.config.high_speed_m_s+' m/s. Unit translation is the average motion of all observed outfield defenders.';
const row=(k,v)=>`<div class="row"><span>${k}</span><b>${v}</b></div>`;
$('accounting').innerHTML=row('Observed team net change',signed(m.accounting.observed_team_net_m2)+' m²')+row('Sum of individual attacker sensitivities',signed(m.accounting.sum_individual_attacker_net_m2)+' m²')+row('Unattributed change',signed(m.accounting.unattributed_net_m2)+' m²')+row('Runner: area gained / lost',fmt(m.space.attacking_half.gained_m2)+' / '+fmt(m.space.attacking_half.lost_m2)+' m²')+row('Runner: penalty-area net change',signed(m.space.penalty_area.net_m2)+' m²')+row('Subsequent shot xG',m.shot_context?.xg==null?'Unavailable — not estimated':fmt(m.shot_context.xg));
$('definitions').innerHTML='<p class="small">'+m.provenance+'</p><p class="small">Receiving condition: onside; nearest defender ≥ '+m.config.receiver_clearance_m+' m; receiver control ≥ '+m.config.receiver_control_threshold+'; straight passing-lane clearance ≥ '+m.config.passing_lane_clearance_m+' m. Left-interval duration at tracking sample resolution. Grid: '+m.grid.columns+' × '+m.grid.rows+'. Cell area: '+fmt(m.grid.cell_area_m2)+' m². Field: '+m.config.field_length_m+' × '+m.config.field_width_m+' m.</p><ul class="small">'+m.limitations.map(s=>'<li>'+s+'</li>').join('')+'</ul>';
if(!m.provenance.startsWith('authored synthetic'))$('source-badge').textContent='User-supplied tracking';
const canvas=$('pitch'),ctx=canvas.getContext('2d'),L=m.config.field_length_m,W=m.config.field_width_m;
const X=x=>(x+L/2)/L*canvas.width,Y=y=>(W/2-y)/W*canvas.height;
let frameIndex=0,playing=false,last=null,elapsed=0;
$('seek').max=frames.length-1;
function draw(){let f=frames[frameIndex];ctx.clearRect(0,0,canvas.width,canvas.height);ctx.fillStyle='#164b40';ctx.fillRect(0,0,canvas.width,canvas.height);
if($('heat').checked){let grid=m.surfaces.runner_delta,dx=canvas.width/m.grid.columns,dy=canvas.height/m.grid.rows;for(let i=0;i<grid.length;i++)for(let j=0;j<grid[i].length;j++){let v=grid[i][j];ctx.fillStyle=v>=0?`rgba(245,203,104,${Math.min(.8,Math.abs(v)*1.8)})`:`rgba(232,107,134,${Math.min(.8,Math.abs(v)*1.8)})`;ctx.fillRect(j*dx,canvas.height-(i+1)*dy,dx+.5,dy+.5);}}
ctx.strokeStyle='#9cc0aa';ctx.lineWidth=2;ctx.strokeRect(1,1,canvas.width-2,canvas.height-2);ctx.beginPath();ctx.moveTo(X(0),0);ctx.lineTo(X(0),canvas.height);ctx.stroke();ctx.beginPath();ctx.arc(X(0),Y(0),9.15/L*canvas.width,0,Math.PI*2);ctx.stroke();for(let s of [-1,1]){let a=X(s*L/2),b=X(s*(L/2-16.5));ctx.strokeRect(Math.min(a,b),Y(20.16),Math.abs(a-b),40.32/W*canvas.height);}
for(let [pid,color] of [[m.players.runner,'#f5cb68'],[m.players.receiver,'#7de5e0']]){ctx.strokeStyle=color;ctx.lineWidth=3;ctx.beginPath();let started=false;for(let z=0;z<=frameIndex;z++){let p=frames[z].players.find(p=>p.id===pid);if(p){if(!started)ctx.moveTo(X(p.x),Y(p.y));else ctx.lineTo(X(p.x),Y(p.y));started=true;}}ctx.stroke();}
for(let p of f.players){let color=p.team==='Home'?'#eef3ec':'#db7a76';if(p.id===m.players.runner)color='#f5cb68';if(p.id===m.players.receiver)color='#7de5e0';ctx.fillStyle=color;ctx.strokeStyle='#0a1820';ctx.lineWidth=2;ctx.beginPath();ctx.arc(X(p.x),Y(p.y),11,0,Math.PI*2);ctx.fill();ctx.stroke();ctx.fillStyle='#0a1820';ctx.font='bold 12px system-ui';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(p.id.split('_')[1],X(p.x),Y(p.y));}
ctx.fillStyle='white';ctx.beginPath();ctx.arc(X(f.ball[0]),Y(f.ball[1]),5,0,Math.PI*2);ctx.fill();ctx.stroke();
let t=Math.min(f.t,m.window.end_s),e=m.timeline.reduce((a,b)=>Math.abs(a.time_s-t)<Math.abs(b.time_s-t)?a:b);
$('live').innerHTML=row('Nearest-defender gap',fmt(e.nearest_defender_m)+' m')+row('Receiver location control',fmt(e.receiver_control*100,1)+'%')+row('Straight-lane clearance',fmt(e.lane_clearance_m)+' m')+row('Onside at this sample',e.onside?'Yes':'No')+row('Candidate receiving window',e.candidate_window?'OPEN':'CLOSED');
$('clock').textContent=fmt(f.t,2)+' s';$('seek').value=frameIndex;$('phase').textContent=f.t<=m.window.end_s?'Run analysis window: before pass release.':'After pass release: replay context only. Shot xG is unavailable.';}
function stop(){playing=false;$('play').textContent='Play';last=null;elapsed=0;}
function tick(now){if(playing){if(last!==null)elapsed+=(now-last)/1000*Number($('speed').value);last=now;while(frameIndex<frames.length-1&&elapsed>=frames[frameIndex+1].t-frames[frameIndex].t){elapsed-=frames[frameIndex+1].t-frames[frameIndex].t;frameIndex++;draw();}if(frameIndex===frames.length-1)stop();}requestAnimationFrame(tick);}
$('play').onclick=()=>{if(playing)stop();else{if(frameIndex===frames.length-1)frameIndex=0;playing=true;last=null;$('play').textContent='Pause';draw();}};
$('restart').onclick=()=>{stop();frameIndex=0;draw();};$('seek').oninput=()=>{stop();frameIndex=Number($('seek').value);draw();};$('heat').onchange=draw;draw();requestAnimationFrame(tick);
</script></html>'''
