"""Build a free static Plotly preview for GitHub Pages without a server."""
import csv
import json
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'/'processed'

def read(n):
    with (DATA/n).open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))

annual=read('annual.csv')
condition=read('conditions.csv')
county=read('county_year.csv')
time=read('time.csv')
quality=read('data_quality.csv')

def counts(rows,keys):
 c=Counter()
 for r in rows:
  c[tuple(r[k] for k in keys)]+=int(r['crashes'])
 return [dict(zip(keys,k),crashes=v) for k,v in c.items()]

payload={
 'annual':annual,
 'weather':counts([r for r in condition if r['condition_group']=='Weather'],['year','area','value']),
 'hour':counts([r for r in time if r['time_dimension']=='hour'],['year','area','time_value']),
 'county':counts(county,['year','county']),
 'quality':quality,
}
html='''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Colorado Crash Explorer · Road Safety Through Data</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
:root{--ink:#102A43;--blue:#2879be;--muted:#50657a;--paper:#f4f8fb}
*{box-sizing:border-box}body{font:16px/1.5 ui-sans-serif,system-ui,-apple-system,Segoe UI,sans-serif;background:var(--paper);color:var(--ink);margin:0}
header{background:linear-gradient(110deg,#0e2e4b,#14638a);color:white;padding:50px max(24px,calc((100vw - 1140px)/2)) 44px}
h1{font-size:clamp(27px,4vw,44px);letter-spacing:-1.1px;margin:8px 0 8px}.eyebrow{text-transform:uppercase;letter-spacing:2px;font-size:12px;font-weight:700;color:#b6ebf4}
.subtitle{color:#d0e6f0;max-width:850px;margin:0}.wrap{max-width:1140px;margin:auto;padding:26px 22px 60px}
.controls{display:flex;flex-wrap:wrap;align-items:end;gap:20px;background:white;padding:18px 20px;border-radius:15px;box-shadow:0 2px 18px #102A430a}
label{display:block;font-size:13px;font-weight:700;margin-bottom:6px}select{padding:9px 12px;min-width:210px;border:1px solid #d4e1ea;border-radius:8px;font-size:14px;background:white;color:var(--ink)}
.yr{display:flex;gap:10px;flex-wrap:wrap;align-items:center}.yr label{font-weight:500;border:1px solid #e4edf3;padding:8px 10px;border-radius:7px;margin:0;cursor:pointer}
.yr input{accent-color:#2879be}.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:18px 0}.card{background:white;padding:18px;border-radius:12px;border:1px solid #e5edf2}
.kpi{font-size:clamp(22px,3vw,31px);font-weight:750;letter-spacing:-.7px}.lab{color:var(--muted);font-size:13px;font-weight:600}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}.plot{background:white;padding:14px;border-radius:13px;border:1px solid #e8eff5;min-height:390px}
.notice{background:#fffaf0;border-left:4px solid #e0a12f;padding:13px 17px;margin:18px 0;border-radius:8px;font-size:14px}
footer{margin-top:24px;color:var(--muted);font-size:13px}a{color:#206998}
@media(max-width:800px){.cards{grid-template-columns:repeat(2,1fr)}.grid{grid-template-columns:1fr}.plot{min-height:350px}}
</style></head><body>
<header><div class="eyebrow">A public-data · Python · community safety project</div><h1>Colorado Crash Explorer</h1>
<p class="subtitle">Explore reported motor-vehicle crashes from CDOT's 2021–2026 listings. This interactive preview is generated from Python-processed summaries, with no backend or API key required.</p></header>
<div class="wrap"><div class="controls"><div><label for="area">Geography</label><select id="area"><option>Colorado</option><option>El Paso County</option><option>Colorado Springs</option></select></div>
<div><label>Choose calendar years</label><div class="yr" id="years"></div></div></div>
<div id="notice" class="notice"></div>
<div class="cards"><div class="card"><div class="lab">Reported crashes</div><div id="kTotal" class="kpi"></div></div>
<div class="card"><div class="lab">Crashes with injury</div><div id="kInjury" class="kpi"></div></div>
<div class="card"><div class="lab">Crashes with fatality</div><div id="kFatal" class="kpi"></div></div>
<div class="card"><div class="lab">Injury / fatality crash share</div><div id="kPct" class="kpi"></div></div></div>
<div class="grid"><div id="annual" class="plot"></div><div id="outcomes" class="plot"></div><div id="hour" class="plot"></div><div id="weather" class="plot"></div></div>
<footer><p><strong>How to read:</strong> Counts are not traffic- or pedestrian-exposure-adjusted risk. The 2026 extract is partial and preliminary. The El Paso and Colorado Springs 2021–2023 hour fields show a major unexplained AM/PM anomaly and are excluded from local hourly graphs. Weather frequencies also reflect travel patterns and cannot establish causality.</p>
<p>This view is an independent educational derivative of <a href="https://www.codot.gov/safety/traffic-safety/data-analysis/crash-data">CDOT statewide crash listings</a>. It does not measure non-crash sidewalk trips. For source code, data quality, map and tests, see the repository README and Python Streamlit app.</p></footer></div>
<script>
const DATA=__PAYLOAD__;
const fmt=n=>Math.round(n).toLocaleString('en-US');
const yearsEl=document.getElementById('years');
for(let y=2021;y<=2026;y++){let lab=document.createElement('label');lab.innerHTML=`<input type="checkbox" value="${y}" ${y<2026?'checked':''}> ${y}${y===2026?'*':''}`;yearsEl.append(lab)}
const getYears=()=>Array.from(yearsEl.querySelectorAll('input:checked')).map(x=>+x.value);
const areaEl=document.getElementById('area');
const layout=(title,extra={})=>({title:{text:title,font:{size:17,color:'#102a43'},x:.03},font:{family:'Arial,sans-serif',color:'#263b50'},paper_bgcolor:'white',plot_bgcolor:'white',margin:{t:70,b:65,l:55,r:20},height:360,...extra});
function render(){
 const area=areaEl.value, years=getYears(),r=DATA.annual.filter(x=>x.area===area&&years.includes(+x.year)),total=r.reduce((a,x)=>a+(+x.crashes),0),inj=r.reduce((a,x)=>a+(+x.injury_crashes),0),fat=r.reduce((a,x)=>a+(+x.fatal_crashes),0);
 document.getElementById('kTotal').textContent=fmt(total);document.getElementById('kInjury').textContent=fmt(inj);document.getElementById('kFatal').textContent=fmt(fat);document.getElementById('kPct').textContent=total?((inj+fat)/total*100).toFixed(1)+'%':'—';
 const badTime=area!=='Colorado'&&years.some(y=>y<2024);
 document.getElementById('notice').textContent=(years.includes(2026)?'2026 is a partial, provisional year. ':'')+(badTime?'Local hourly charts exclude 2021–2023 because those source times show an unexplained AM/PM anomaly. ':'')+'Crashes are counts, not risk estimates; ordinary sidewalk trip/fall incidents are outside this dataset.';
 Plotly.react('annual',[{x:r.map(x=>x.year),y:r.map(x=>+x.crashes),type:'scatter',mode:'lines+markers',marker:{color:'#2076b4',size:10},line:{width:3}}],layout('Reported crashes by year',{xaxis:{title:'Source year',type:'category'},yaxis:{title:'Crash records',gridcolor:'#eaf0f5'}}),{responsive:true,displaylogo:false});
 Plotly.react('outcomes',[{labels:['Fatal crash','Injury crash','No injury reported','Unknown'],values:[fat,inj,r.reduce((a,x)=>a+(+x.no_injury_reported),0),r.reduce((a,x)=>a+(+x.unknown_outcome),0)],type:'pie',hole:.53,marker:{colors:['#c94857','#f2ab3f','#008c85','#9bacb7']},textinfo:'percent',hovertemplate:'%{label}: %{value:,}<extra></extra>'}],layout('Crash-level outcomes'),{responsive:true,displaylogo:false});
 let filtered=DATA.hour.filter(x=>x.area===area && years.includes(+x.year) && (area==='Colorado'||+x.year>=2024));
 let ct={};filtered.forEach(x=>{ct[+x.time_value]=(ct[+x.time_value]||0)+x.crashes});
 Plotly.react('hour',[{x:Array.from({length:24},(_,i)=>i),y:Array.from({length:24},(_,i)=>ct[i]||0),type:'bar',marker:{color:'#2879be'}}],layout('Crashes by hour'+(area!=='Colorado'?' (2024+)':''),{xaxis:{title:'Hour (24-hour)',dtick:2},yaxis:{title:'Crash records',gridcolor:'#eaf0f5'}}),{responsive:true,displaylogo:false});
 let wc={};DATA.weather.filter(x=>x.area===area&&years.includes(+x.year)).forEach(x=>{wc[x.value]=(wc[x.value]||0)+x.crashes});
 let top=Object.entries(wc).sort((a,b)=>b[1]-a[1]).slice(0,8).reverse();
 Plotly.react('weather',[{y:top.map(x=>x[0]),x:top.map(x=>x[1]),type:'bar',orientation:'h',marker:{color:'#008d82'}}],layout('Recorded weather at crash time',{margin:{t:65,b:45,l:105,r:20},xaxis:{title:'Crash records',gridcolor:'#eaf0f5'}}),{responsive:true,displaylogo:false});
}
yearsEl.addEventListener('change',render);areaEl.addEventListener('change',render);render();
</script></body></html>'''
html=html.replace('__PAYLOAD__',json.dumps(payload,separators=(',',':')))
(ROOT/'docs'/'index.html').write_text(html,encoding='utf-8')
print('GitHub Pages dashboard generated',len(html),'bytes')
