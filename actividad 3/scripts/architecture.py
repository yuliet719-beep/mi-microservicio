"""Export a readable architecture diagram without a hosted renderer dependency."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
ROOT=Path(__file__).resolve().parents[1]
fig,ax=plt.subplots(figsize=(12,5.3),constrained_layout=True)
ax.set_xlim(-.8,12.4);ax.set_ylim(-.5,5.4);ax.axis('off')
nodes={'C':(0,4.5,'Cliente'), 'A':(1.7,4.5,'service-a'), 'EB':(3.5,4.5,'Envoy B'),
       'B':(5.2,4.5,'service-b'), 'ED':(7,4.5,'Envoy Data'), 'D':(8.9,4.5,'data-service'),
       'DB':(11.1,4.5,'PostgreSQL'), 'O':(5.2,2.8,'OTel Collector'),
       'P':(2.8,1.4,'Prometheus'), 'T':(5.2,1.4,'Tempo'), 'L':(7.6,1.4,'Loki'),
       'G':(5.2,0,'Grafana'), 'X':(10.4,2.3,'Detector AIOps')}
for name,(x,y,label) in nodes.items():
    ax.add_patch(FancyBboxPatch((x-.72,y-.27),1.44,.54,boxstyle='round,pad=.06',
                 edgecolor='#007c83',facecolor='#dceef0',zorder=3))
    ax.text(x,y,label,ha='center',va='center',fontsize=9,color='#15334b',zorder=4)
def arrow(a,b,dashed=False,label=None):
    x,y,_=nodes[a];xx,yy,_=nodes[b]
    dx,dy=xx-x,yy-y
    if abs(dx)>abs(dy):
        x+=.8 if dx>0 else -.8;xx-=.8 if dx>0 else -.8
    else:
        y+=.33 if dy>0 else -.33;yy-=.33 if dy>0 else -.33
    ax.annotate('',xy=(xx,yy),xytext=(x,y),arrowprops={'arrowstyle':'->','color':'#718d9a' if dashed else '#15334b',
                 'linestyle':'--' if dashed else '-','lw':1.2},zorder=1)
    if label:
        ax.text((x+xx)/2,(y+yy)/2+.12,label,fontsize=7,ha='center',color='#15334b')
for a,b in zip(['C','A','EB','B','ED','D'],['A','EB','B','ED','D','DB']):arrow(a,b)
for a in ['A','B','D']:arrow(a,'O',True)
for b in ['P','T','L']:arrow('O',b)
for a in ['P','T','L']:arrow(a,'G')
arrow('X','D',True,'probes')
ax.text(.1,3.1,'Contexto W3C traceparent\nA -> B -> data -> SQL',fontsize=9,color='#15334b')
ax.text(.1,.1,'SANDBOX LOCAL\nGCP / AWS: pendientes',fontsize=9,color='#a33b3b')
ax.text(8.7,.7,'Envoy y AIOps exponen\nmetricas a Prometheus',fontsize=9,color='#15334b')
fig.savefig(ROOT/'evidencias/architecture.png',dpi=180);plt.close(fig)
