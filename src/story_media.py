"""Render observed trails and arrows; no defender destinations are simulated."""
import math,textwrap
from PIL import Image,ImageDraw,ImageFont
COLORS={'runner':'#f5cb68','response':'#ff9d5c','cover':'#59d9e8','finisher':'#cf9cff'}
def draw_arrow(d,a,b,color,width=4):
    if math.dist(a,b)<3:return
    d.line([a,b],fill=color,width=width);angle=math.atan2(b[1]-a[1],b[0]-a[0]);L=11
    d.polygon([b,(b[0]-L*math.cos(angle-.5),b[1]-L*math.sin(angle-.5)),(b[0]-L*math.cos(angle+.5),b[1]-L*math.sin(angle+.5))],fill=color)
def render(base,bundle,index):
    out=Image.new('RGB',(1120,1000),'#0c1820');out.paste(base,(0,0));d=ImageDraw.Draw(out);font=lambda n:ImageFont.load_default(size=n)
    story=bundle['story'];frames=bundle['frames'];t=frames[index]['t'];xy=lambda p:(30+p['x']*8.4,130+(100-p['y'])*5.712)
    roles=[(story['focus_player_id'],'RUN',COLORS['runner'])]
    if story['response']:roles.append((story['response']['player_id'],'D1',COLORS['response']))
    if story['cover']:roles.append((story['cover']['player_id'],'D2',COLORS['cover']))
    if story['finisher_player_id'] is not None and story['finisher_player_id']!=story['focus_player_id']:roles.append((story['finisher_player_id'],'FIN',COLORS['finisher']))
    for pid,label,color in roles:
        points=[xy(next(p for p in f['players'] if p['id']==pid)) for f in frames[max(0,index-30):index+1]]
        if len(points)>1:d.line(points,fill=color,width=4);draw_arrow(d,points[max(0,len(points)-9)],points[-1],color)
        x,y=points[-1];d.ellipse((x-14,y-14,x+14,y+14),outline=color,width=3);d.text((x+15,y-20),label,font=font(13),fill=color,stroke_width=2,stroke_fill='#0c1820')
    if story['cover'] and t>=story['cover']['start_s']:
        x,y=story['cover']['anchor_nominal_xy'];x,y=30+x*8,130+(68-y)*8.4
        d.ellipse((x-24,y-24,x+24,y+24),outline=COLORS['cover'],width=2);d.text((x+25,y),'D1 earlier location',font=font(12),fill=COLORS['cover'],stroke_width=1,stroke_fill='#0c1820')
    active=next((s for s in reversed(story['steps'][:4]) if s['time_s'] is not None and t>=s['time_s']),story['steps'][0])
    d.rectangle((20,735,1100,980),fill='#13252c',outline='#294048',width=1)
    d.text((35,750),active['title'].upper()+' | '+active['status'].replace('_',' ').upper(),font=font(20),fill='#f5cb68')
    for n,line in enumerate(textwrap.wrap(active['text'].replace('–',' to ').replace('’',"'"),width=111)):d.text((35,790+n*25),line,font=font(17),fill='#edf3ef')
    d.text((35,915),'Gold RUN  |  Orange D1 response candidate  |  Cyan D2 cover candidate  |  Purple FIN scorer',font=font(15),fill='#baccca')
    d.text((35,946),'Arrows show observed motion over 0.4 s; trails show 1.5 s. Association does not establish causation.',font=font(14),fill='#baccca')
    return out
