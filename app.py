"""Colorado Crash Explorer | Streamlit dashboard. Run: streamlit run app.py"""
from collections import Counter
import csv
from pathlib import Path
import json
import os

import streamlit as st
import plotly.graph_objects as go

DATA = Path(__file__).resolve().parent / 'data' / 'processed'
NAVY='#102A43'
BLUE='#2076b4'
ORANGE='#f5a623'
RED='#ce4554'
TEAL='#008e82'

st.set_page_config(page_title='Colorado Crash Explorer',layout='wide')

@st.cache_data(show_spinner=False)
def read_data(filename):
    p=DATA/filename
    if not p.exists():
        return []
    with p.open(newline='',encoding='utf-8') as f:
        return list(csv.DictReader(f))

@st.cache_data(show_spinner=False)
def read_summary():
    p=DATA/'summary.json'
    return json.loads(p.read_text()) if p.exists() else {}

def included(row,years,area=None):
    return int(row['year']) in years and (area is None or row.get('area')==area)

def grouped(rows,label,value='crashes'):
    result=Counter()
    for r in rows:
        result[r[label]]+=int(r[value])
    return result

def bar_chart(labels,values,title='',horizontal=False,color=BLUE):
    fig=go.Figure()
    if horizontal:
        fig.add_trace(go.Bar(y=labels,x=values,orientation='h',marker_color=color,hovertemplate='%{y}<br>%{x:,} reported crashes<extra></extra>'))
        fig.update_layout(yaxis={'autorange':'reversed'})
    else:
        fig.add_trace(go.Bar(x=labels,y=values,marker_color=color,hovertemplate='%{x}<br>%{y:,} reported crashes<extra></extra>'))
    fig.update_layout(title=title,margin=dict(l=10,r=10,t=42,b=20),height=370,plot_bgcolor='white',paper_bgcolor='white',showlegend=False)
    fig.update_yaxes(showgrid=not horizontal,gridcolor='#edf0f5')
    fig.update_xaxes(showgrid=horizontal,gridcolor='#edf0f5')
    return fig

summary=read_summary()
if not summary:
    st.error('Processed data is missing. Run `python -m src.ingest --input-dir raw_data --output-dir data/processed`.')
    st.stop()

st.title('Colorado Crash Explorer')
st.caption('A reproducible public-data project | Colorado Department of Transportation crash listings, 2021–2026')
st.markdown('**Question:** What do reported roadway crashes reveal about when and where traffic injuries occur, and what remains unknown?')

with st.sidebar:
    st.header('Explore the data')
    area=st.selectbox('Area',['Colorado','El Paso County','Colorado Springs'])
    full_years=[y for y in summary['years'] if y < 2026]
    include_2026=st.checkbox('Include incomplete 2026 data',False)
    available=summary['years'] if include_2026 else full_years
    years=st.multiselect('Crash year',available,default=available)
    st.divider()
    st.caption('Counts describe reported crashes, not the chance of a crash. No traffic-volume or pedestrian-exposure denominator is included.')
    st.caption('Data source: CDOT, extracted from six user-provided annual XLSX files.')

if not years:
    st.info('Select at least one year.');st.stop()
if 2026 in years:
    st.warning(f'2026 is incomplete in this extract (latest recorded date: {summary.get("latest_dates",{}).get("2026","unknown")}). Do not interpret lower 2026 counts as safer roads.')

annual=[r for r in read_data('annual.csv') if included(r,years,area)]
crashes=sum(int(r['crashes']) for r in annual)
fatal=sum(int(r['fatal_crashes']) for r in annual)
injury=sum(int(r['injury_crashes']) for r in annual)
unknown=sum(int(r['unknown_outcome']) for r in annual)
col1,col2,col3,col4=st.columns(4)
col1.metric('Reported crashes',f'{crashes:,}')
col2.metric('Crashes with injury',f'{injury:,}')
col3.metric('Crashes with fatality',f'{fatal:,}')
col4.metric('Crashes with injury or fatality',f'{(injury+fatal)/crashes:.1%}' if crashes else 'N/A')
if unknown:
    st.caption(f'{unknown:,} crashes have unknown injury/fatality fields and are included in total counts.')

t1,t2,t3,t4,t5=st.tabs(['Overview','When','Conditions & crash types','El Paso map','Data quality & methods'])
with t1:
    st.subheader('Annual pattern')
    timeline=sorted(annual,key=lambda r:int(r['year']))
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=[r['year'] for r in timeline],y=[int(r['crashes']) for r in timeline],mode='lines+markers',name='Reported crashes',line={'color':BLUE,'width':3},marker={'size':9}))
    fig.update_layout(height=360,margin=dict(t=20,b=25),paper_bgcolor='white',plot_bgcolor='white',xaxis_title='Crash year',yaxis_title='Crash records',yaxis_tickformat=',')
    st.plotly_chart(fig,use_container_width=True)
    st.caption('The annual series uses each source file’s year. It is a count, not an exposure-adjusted rate. 2026 is intentionally excluded by default.')
    col1,col2=st.columns(2)
    with col1:
        s=['Fatal','Injury','No injury reported','Unknown']
        values=[fatal,injury,sum(int(r['no_injury_reported']) for r in annual),unknown]
        fig=go.Figure(go.Pie(labels=s,values=values,hole=.62,marker={'colors':[RED,ORANGE,TEAL,'#9da9b4']}))
        fig.update_layout(title='Crash outcomes (one classification per crash)',height=360,margin=dict(t=45,b=20))
        st.plotly_chart(fig,use_container_width=True)
    with col2:
        if area=='Colorado':
            county=[r for r in read_data('county_year.csv') if int(r['year']) in years]
            count=grouped(county,'county')
            items=[x for x in count.most_common(12) if x[0]!='UNKNOWN']
            st.plotly_chart(bar_chart([k for k,v in items],[v for k,v in items],title='Counties with most reported crashes',horizontal=True),use_container_width=True)
        else:
            st.info('Statewide county comparisons are available when Area is set to Colorado.')
    st.info('A location with more crashes may also have much more traffic. Rankings here show crash concentration, not relative risk.')

with t2:
    st.subheader('Time patterns')
    if area!='Colorado' and any(y < 2024 for y in years):
        st.warning('Local hour-of-day data in 2021–2023 have an unusual AM/PM distribution (especially 2022–2023), suggesting a source reporting/formatting anomaly. The HOUR chart below uses only selected years from 2024 onward. Month and weekday charts still use all selected years.')
    time=[r for r in read_data('time.csv') if included(r,years,area)]
    monthly=[r for r in read_data('monthly.csv') if included(r,years,area)]
    c1,c2=st.columns(2)
    with c1:
        hours=Counter()
        for r in time:
            if r['time_dimension']=='hour' and (area=='Colorado' or int(r['year'])>=2024):
                hours[int(r['time_value'])]+=int(r['crashes'])
        st.plotly_chart(bar_chart([f'{h:02}:00' for h in range(24)],[hours[h] for h in range(24)],'Crashes by hour (local: 2024 onward)'),use_container_width=True)
    with c2:
        months=Counter()
        for r in monthly:months[int(r['month'])]+=int(r['crashes'])
        st.plotly_chart(bar_chart(['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],[months[m] for m in range(1,13)],'Crashes by month'),use_container_width=True)
    days=Counter()
    for r in time:
        if r['time_dimension']=='weekday':days[int(r['time_value'])]+=int(r['crashes'])
    st.plotly_chart(bar_chart(['Mon','Tue','Wed','Thu','Fri','Sat','Sun'],[days[d] for d in range(7)],'Crashes by day of week'),use_container_width=True)
    st.caption('Hour/day breakdowns exclude missing or invalid values. For El Paso County and Colorado Springs, the hour chart deliberately omits 2021–2023 because those years show an unexplained time-of-day anomaly. No charts adjust for traffic volume.')

with t3:
    st.subheader('Reported conditions')
    choice=st.selectbox('Condition category',['Lighting','Weather','Road surface'])
    sub=[r for r in read_data('conditions.csv') if included(r,years,area) and r['condition_group']==choice]
    count=grouped(sub,'value')
    common=count.most_common(14)
    st.plotly_chart(bar_chart([k for k,v in common],[v for k,v in common],f'Reported crashes by {choice.lower()}',horizontal=True),use_container_width=True)
    st.caption('Do not interpret high counts under clear/dry/daylight conditions as evidence those conditions are more dangerous. Most travel may occur under them.')
    types=[r for r in read_data('crash_types.csv') if included(r,years,area)]
    count=grouped(types,'crash_type')
    common=count.most_common(12)
    st.plotly_chart(bar_chart([k for k,v in common],[v for k,v in common],'Most frequent crash types',horizontal=True,color=TEAL),use_container_width=True)
    st.subheader('School-zone flag')
    zones=[r for r in read_data('school_zone.csv') if included(r,years,area)]
    zcount=grouped(zones,'school_zone')
    st.plotly_chart(bar_chart(list(zcount),list(zcount.values()),'Crashes by school-zone designation',horizontal=True,color=ORANGE),use_container_width=True)
    st.caption('A school-zone indicator in a crash report is not proof that a crash occurred during school hours, involved a child, or occurred because of school traffic.')
    st.subheader('Non-motorist records (exploratory)')
    nm=[r for r in read_data('nonmotorist.csv') if included(r,years,area)]
    nmc=grouped(nm,'type')
    st.table([{'Type':k,'Crashes':v} for k,v in nmc.most_common()])
    st.caption('The non-motorist analysis uses the first two NM Type fields; absence from this table does not prove no pedestrian or cyclist was involved. Validate against the full CDOT data dictionary before using for safety policy.')

with t4:
    st.subheader('El Paso County location grid')
    st.caption('Map uses an approximately 1-km latitude/longitude grid; dots are cell centers, not exact crash or intersection locations. Available regardless of area selection.')
    maps=[r for r in read_data('el_paso_grid.csv') if int(r['year']) in years]
    points=Counter()
    for r in maps:
        points[(float(r['latitude_bin']),float(r['longitude_bin']))]+=int(r['crashes'])
    if points:
        fig=go.Figure(go.Scattermapbox(
            lat=[k[0] for k in points],lon=[k[1] for k in points],mode='markers',
            marker={'size':[max(5,min(22,4+v**0.5)) for v in points.values()],'color':[v for v in points.values()], 'colorscale':'YlOrRd','showscale':True,'colorbar':{'title':'Crashes'},'opacity':.72},
            text=[f'{v:,} crash records in approximate grid cell' for v in points.values()],hoverinfo='text'))
        fig.update_layout(mapbox={'style':'open-street-map','center':{'lat':38.84,'lon':-104.76},'zoom':9.2},margin={'l':0,'r':0,'t':0,'b':0},height=580)
        st.plotly_chart(fig,use_container_width=True)
    else:
        st.info('No valid coordinates for the selected years.')
    st.caption('Clusters reflect recorded density, not pedestrian risk. Coordinate precision and geocoding quality vary. Confirm locations before drawing site-specific conclusions.')

with t5:
    st.subheader('Source coverage and quality checks')
    q=[r for r in read_data('data_quality.csv') if int(r['year']) in years]
    focus=['source_rows','duplicate_cuid','invalid_dates','date_year_mismatch','missing_or_invalid_coordinates','valid_coordinates','missing_or_invalid_time','missing_outcome']
    st.dataframe([{'Year':y,**{metric:next((int(r['value']) for r in q if int(r['year'])==y and r['metric']==metric),0) for metric in focus}} for y in years],use_container_width=True,hide_index=True)
    st.markdown('**Time-of-day quality audit:** a striking shift in the share of reported crash times after noon appears in the 2021–2023 local subsets. Treat local historical hour data as unresolved rather than proof of an early-morning risk spike.')
    times=read_data('time.csv')
    local_hour_quality=[]
    for ay in years:
        for aname in ['Colorado','El Paso County','Colorado Springs']:
            rs=[r for r in times if int(r['year'])==ay and r['area']==aname and r['time_dimension']=='hour']
            total=sum(int(r['crashes']) for r in rs)
            pm=sum(int(r['crashes']) for r in rs if int(r['time_value'])>=12)
            local_hour_quality.append({'Year':ay,'Area':aname,'After-noon (%)':round(100*pm/total,1) if total else None})
    st.dataframe(local_hour_quality,use_container_width=True,hide_index=True)
    st.markdown('''**Definitions and guardrails**
    - A *fatal crash* has at least one reported death. An *injury crash* has one or more reported injuries and no reported deaths. Counts represent crashes, not injured people.
    - A *crash with injury or fatality* is not synonymous with a clinically serious injury. These extracts include separate injury-category fields, which could support future refinement.
    - Time-of-day, weather, and location patterns are descriptive associations. Exposure data (traffic volume, pedestrian counts, road length) are needed before comparing true risk.
    - This dataset captures reported motor-vehicle roadway crashes, not ordinary falls or sidewalk defects. Not every incident is reported.
    - Files were provided as annual CDOT crash extracts; 2026 is incomplete. Recent records may be updated.
    - GIS grid approximations may combine different streets and intersections. No hotspot is a policy recommendation without on-the-ground validation.
    ''')
    with st.expander('How to reproduce and extend'):
        st.code('python -m src.ingest --input-dir raw_data --output-dir data/processed\nstreamlit run app.py',language='bash')
        st.write('Source, tests, a data dictionary, and a list of responsible next steps are in the project repository.')

st.divider()


st.caption('Independent educational analysis of publicly available CDOT data. Not an official CDOT product or road-safety rating.')
