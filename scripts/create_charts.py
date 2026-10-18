"""Generate static figure files used in README and presentations."""
from pathlib import Path
from collections import Counter
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'/'processed'
ASSETS=ROOT/'assets'
ASSETS.mkdir(exist_ok=True)

def get(n):
    with (DATA/n).open(newline='',encoding='utf8') as f:
        return list(csv.DictReader(f))

BLUE='#1262a1'; GOLD='#c68525'; RED='#b9424b'; INK='#1a3349'
plt.rcParams.update({'figure.facecolor':'white','axes.spines.top':False,'axes.spines.right':False,'font.size':11})

annual=[r for r in get('annual.csv') if int(r['year'])<=2025]
fig,ax=plt.subplots(figsize=(9.6,4.3))
for area,color in [('Colorado',BLUE),('El Paso County',GOLD),('Colorado Springs',RED)]:
    rs=sorted([r for r in annual if r['area']==area],key=lambda r:int(r['year']))
    ys=[int(r['crashes']) for r in rs]
    ax.plot([int(r['year']) for r in rs],ys,marker='o',markersize=7,linewidth=2.2,label=area,color=color)
ax.set_title('Reported roadway crashes · 2021–2025',fontweight='bold',loc='left',color=INK,pad=18)
ax.set_ylabel('Crash records (not traffic-adjusted risk)')
ax.set_xticks([2021,2022,2023,2024,2025]);ax.grid(axis='y',alpha=.18)
ax.legend(frameon=False,ncol=3,loc='upper center',bbox_to_anchor=(.5,-.13))
fig.tight_layout();fig.savefig(ASSETS/'yearly_trends.png',dpi=160,bbox_inches='tight');plt.close(fig)

fig,ax=plt.subplots(figsize=(8.6,4.4))
time=get('time.csv')
for area,color in [('Colorado',BLUE),('Colorado Springs',RED)]:
    ct=Counter()
    for r in time:
        if 2024<=int(r['year'])<=2025 and r['area']==area and r['time_dimension']=='hour':ct[int(r['time_value'])]+=int(r['crashes'])
    s=sum(ct.values())
    ax.plot(range(24),[100*ct[i]/s for i in range(24)],marker='o',markersize=3,linewidth=2,label=area,color=color)
ax.set_title('When reported crashes occur · 2024–2025',fontweight='bold',color=INK,loc='left',pad=18)
ax.set_xlabel('Hour of day');ax.set_ylabel('Share of area crashes with valid time (%)')
ax.set_xticks(range(0,24,2));ax.grid(axis='y',alpha=.18);ax.legend(frameon=False)
fig.tight_layout();fig.savefig(ASSETS/'hourly_profiles.png',dpi=160,bbox_inches='tight');plt.close(fig)

quality=get('data_quality.csv')
ct=Counter({(int(r['year']),r['metric']):int(r['value']) for r in quality})
years=list(range(2021,2027))
coverage=[100*ct[(y,'valid_coordinates')]/ct[(y,'source_rows')] for y in years]
fig,ax=plt.subplots(figsize=(8.2,4.1))
bars=ax.bar([str(y) for y in years],coverage,color=BLUE,width=.58)
for bar,val in zip(bars,coverage):ax.text(bar.get_x()+bar.get_width()/2,bar.get_height()+1.0,f'{val:.1f}%',ha='center',fontsize=10)
ax.set_ylim(0,112);ax.set_title('Coordinate completeness changes across years',fontweight='bold',color=INK,loc='left',pad=17)
ax.set_ylabel('Source rows with coordinates inside CO bounds (%)');ax.grid(axis='y',alpha=.12)
fig.tight_layout();fig.savefig(ASSETS/'geocoding_quality.png',dpi=160,bbox_inches='tight');plt.close(fig)
print('Charts created in',ASSETS)
