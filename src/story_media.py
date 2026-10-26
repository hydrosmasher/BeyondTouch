"""Render observed trails and arrows; no defender destinations are simulated."""
import math,textwrap,unicodedata
from functools import lru_cache
def safe_text(text):
    for a,b in [("≈","approx."),("×","x"),("–"," to "),("→"," -> "),("’","\'"),("·","|")]:text=str(text).replace(a,b)
    return unicodedata.normalize("NFKD",str(text)).encode("ascii","ignore").decode()
from PIL import Image,ImageDraw,ImageFont
@lru_cache(maxsize=24)
def media_font(n):return ImageFont.load_default(size=n)

COLORS={'runner':'#f5cb68','response':'#ff9d5c','cover':'#59d9e8','finisher':'#cf9cff'}
def draw_arrow(d,a,b,color,width=4):
    if math.dist(a,b)<3:return
    d.line([a,b],fill=color,width=width);angle=math.atan2(b[1]-a[1],b[0]-a[0]);L=11
    d.polygon([b,(b[0]-L*math.cos(angle-.5),b[1]-L*math.sin(angle-.5)),(b[0]-L*math.cos(angle+.5),b[1]-L*math.sin(angle+.5))],fill=color)
def render(base,bundle,index):
    out=Image.new('RGB',(1120,1000),'#0c1820');out.paste(base,(0,0));d=ImageDraw.Draw(out);original_text=d.text;d.text=lambda xy,text,*a,**kw:original_text(xy,safe_text(text),*a,**kw);font=media_font
    story=bundle['story'];option=bundle.get('active_space');frames=bundle['frames'];t=frames[index]['t'];xy=lambda p:(30+p['x']*8.4,130+(100-p['y'])*5.712)
    roles=[(story['focus_player_id'],'RUN',COLORS['runner'])]
    if story['response']:roles.append((story['response']['player_id'],'D1',COLORS['response']))
    if story['cover']:roles.append((story['cover']['player_id'],'D2',COLORS['cover']))
    if story['finisher_player_id'] is not None and story['finisher_player_id']!=story['focus_player_id']:roles.append((story['finisher_player_id'],'FIN',COLORS['finisher']))
    if option:roles=[(story['focus_player_id'],'RUN',COLORS['runner']),(option['cover_defender_id'],'DEF','#e898d0')]
    for pid,label,color in roles:
        points=[xy(next(p for p in f['players'] if p['id']==pid)) for f in frames[max(0,index-round(1.5*bundle['metrics']['source_native_hz'])):index+1]]
        if len(points)>1:d.line(points,fill=color,width=4);draw_arrow(d,points[max(0,len(points)-1-round(.4*bundle['metrics']['source_native_hz']))],points[-1],color)
        x,y=points[-1];d.ellipse((x-14,y-14,x+14,y+14),outline=color,width=3);d.text((x+15,y-20),label,font=font(13),fill=color,stroke_width=2,stroke_fill='#0c1820')
    if not option and story['cover'] and t>=story['cover']['end_s']:
        x,y=story['cover']['anchor_nominal_xy'];x,y=30+x*8,130+(68-y)*8.4
        d.ellipse((x-24,y-24,x+24,y+24),outline=COLORS['cover'],width=2);d.text((x+25,y),'D1 earlier location',font=font(12),fill=COLORS['cover'],stroke_width=1,stroke_fill='#0c1820')
    option=bundle.get('active_space')
    if option:
        origin=option['origin_normalized_xy'];target=option['target_normalized_xy'];a=(30+origin[0]*8.4,130+(100-origin[1])*5.712);z=(30+target[0]*8.4,130+(100-target[1])*5.712)
        d.ellipse((z[0]-20,z[1]-20,z[0]+20,z[1]+20),fill='#267255',outline='#77e0ab',width=3);draw_arrow(d,a,z,'#77e0ab',3)
        px,py=option['cover_defender_normalized_xy'];draw_arrow(d,(30+px*8.4,130+(100-py)*5.712),z,'#e898d0',2)
        d.text((z[0]+24,z[1]-14),option['space_label'],font=font(15),fill='#77e0ab',stroke_width=1,stroke_fill='#0c1820')
    active=next((s for s in reversed(story['steps'][:4]) if s['time_s'] is not None and t>=s['time_s']),story['steps'][0])
    if option:active={'title':'PAUSED | '+option['space_label']+' | compare before reveal','status':'what-if','text':f"Attacker: this pocket has {option['endpoint_defender_gap_m']:.2f} m separation from the nearest observed defender. Defence: source ID {option['cover_defender_id']} is {option['cover_distance_m']:.2f} m from this pocket. That line is an illustrative cover distance, not a predicted response. Next, reveal what actually happened."}
    elif bundle.get('review_phase')=='reveal':active={**active,'title':'OBSERVED CONTINUATION | '+active['title']}
    d.rectangle((20,735,1100,980),fill='#13252c',outline='#294048',width=1)
    d.text((35,750),active['title'].upper()+' | '+active['status'].replace('_',' ').upper(),font=font(20),fill='#f5cb68')
    for n,line in enumerate(textwrap.wrap(active['text'].replace('–',' to ').replace('’',"'"),width=111)):d.text((35,790+n*25),line,font=font(17),fill='#edf3ef')
    d.text((35,915),'Gold RUN  |  Orange D1 response candidate  |  Cyan D2 cover candidate  |  Purple FIN scorer',font=font(15),fill='#baccca')
    d.text((35,946),'Paused: one hypothetical space at a time. Pink: illustrative cover distance. Then reveal observed play.',font=font(14),fill='#baccca')
    return out
