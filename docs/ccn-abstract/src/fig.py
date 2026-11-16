import csv,collections,json,numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from PIL import Image
import os; HERE=os.path.dirname(os.path.abspath(__file__)); B=os.path.join(HERE,'..','..','..','experiments','pilot','v2')+'/'
r=list(csv.DictReader(open(B+'results_all/per_clip_strict.csv')))
shapes=['straight','c90','c180','c270','spiral']; lab=['Straight\n(control)','90°','180°','270°','Spiral']
ok=('impetus','no_bias','centrifugal')
def wilson(k,n,z=1.96):
    p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; h=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/d; return c-h,c+h
ltx=[];ci=[]
for s in shapes:
    v=[x for x in r if x['shape']==s and x['label_strict'] in ok]; k=sum(x['label_strict']=='impetus' for x in v)
    ltx.append(100*k/len(v)); lo,hi=wilson(k,len(v)); ci.append((100*k/len(v)-100*lo,100*hi-100*k/len(v))); print(s,k,len(v))
q=list(csv.DictReader(open(B+'vjepa2/vjepa_probe.csv'))); d={(x['item_id'],x['view'],x['future']):x for x in q}
vj=[]
for s in shapes:
    c=[x for x in q if x['shape']==s and x['view']=='crop12' and x['future']=='correct']
    vj.append(100*np.mean([float(d[(x['item_id'],'crop12','impetus')]['surprise_ball'])<float(x['surprise_ball']) for x in c]))
print(vj)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':7,'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':0.6})
fig=plt.figure(figsize=(3.35,3.45),dpi=300)
a=fig.add_axes([0.0,0.505,1.0,0.495])
im=Image.open(B+'results_all/sheets/A1_tube_c270_v200_s1.jpg'); W,H=im.size
crop=im.crop((0,800,640,1135)); a.imshow(crop); a.axis('off')
a.text(0.01,0.97,'A',transform=a.transAxes,fontsize=9,fontweight='bold',va='top',color='k')
a.text(0.99,0.03,'green: true path   dark green: impetus foil   magenta: LTX samples',transform=a.transAxes,ha='right',va='bottom',fontsize=5.5,color='k',bbox=dict(fc='white',ec='none',alpha=.8,pad=1.5))
ax=fig.add_axes([0.13,0.10,0.85,0.27])
x=np.arange(5); w=0.36
ax.bar(x-w/2-0.01,ltx,w,color='#2a78d6',label='LTX-Video: generated path curves',yerr=np.array(ci).T,error_kw=dict(lw=0.6,capsize=1.5,ecolor='#333'))
ax.bar(x+w/2+0.01,vj,w,color='#eb6834',label='V-JEPA 2: prefers curving exit')
ax.plot([2],[33],'kD',ms=4,label='Humans, drawn (1980)'); ax.plot([4],[51],'kD',ms=4)
ax.plot([4.0],[26],'ks',ms=3.5,mfc='white',mew=0.8,label='Humans, 6-choice (1983)')
ax.set_xticks(x); ax.set_xticklabels(lab); ax.set_ylim(0,100); ax.set_yticks([0,50,100]); ax.set_ylabel('% curving responses')
ax.yaxis.grid(True,lw=0.3,color='#ddd'); ax.set_axisbelow(True)
ax.text(-0.14,1.33,'B',transform=ax.transAxes,fontsize=9,fontweight='bold')
h,l=ax.get_legend_handles_labels(); o=[2,0,3,1]
ax.legend([h[i] for i in o],[l[i] for i in o],fontsize=5.6,frameon=False,loc='lower left',bbox_to_anchor=(-0.12,1.02),ncol=2,handlelength=1.2,columnspacing=0.8)
for i,v in enumerate(vj):
    if v==0: ax.text(i+w/2+0.01,1.5,'0',ha='center',fontsize=5.5,color='#eb6834')
fig.savefig(os.path.join(HERE,'..','figure1.png'),dpi=300)
