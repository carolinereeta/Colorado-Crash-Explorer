from __future__ import annotations
import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from zipfile import ZipFile
from lxml import etree
from .metrics import date_from_excel, severity, valid_point, non_motorist_category

NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
FIELDS = {0: 'cuid', 5: 'date_raw', 6: 'time', 8:'city', 9:'county', 10:'latitude', 11:'longitude', 15:'location', 16:'road_description',
22:'crash_type', 25:'killed', 26:'injured', 32:'vehicles',35:'school_zone', 38:'road_condition', 39:'lighting', 40:'weather',
89:'nonmotorist_1', 90:'nonmotorist_2', 107:'record_status'}
FIELD_INDICES = set(FIELDS)

def col_index(reference):
    index = 0
    for c in reference:
        if not ('A' <= c <= 'Z'):
            break
        index = index * 26 + ord(c) - ord('A') + 1
    return index - 1

def parse_shared_strings(z):
    strings=[]
    with z.open('xl/sharedStrings.xml') as source:
        for _, element in etree.iterparse(source,events=('end',),tag=NS+'si'):
            strings.append(''.join(element.itertext()))
            element.clear()
            while element.getprevious() is not None:
                del element.getparent()[0]
    return strings

def iter_selected_rows(path):
    with ZipFile(path) as z:
        strings=parse_shared_strings(z)
        with z.open('xl/worksheets/sheet1.xml') as source:
            for _, element in etree.iterparse(source,events=('end',),tag=NS+'row'):
                if element.get('r') == '1':
                    element.clear()
                    continue
                selected={}
                for cell in element:
                    if cell.tag != NS+'c':
                        continue
                    index=col_index(cell.get('r',''))
                    if index not in FIELD_INDICES:
                        continue
                    v=cell.find(NS+'v')
                    value=v.text if v is not None else ''
                    if cell.get('t') == 's' and value:
                        value=strings[int(value)]
                    elif cell.get('t') == 'inlineStr':
                        value=''.join(cell.itertext())
                    selected[FIELDS[index]]=value
                yield selected
                element.clear()
                while element.getprevious() is not None:
                    del element.getparent()[0]

def write_csv(output, name, headers, rows):
    file=output/name
    with file.open('w',newline='',encoding='utf-8') as handle:
        w=csv.writer(handle)
        w.writerow(headers)
        w.writerows(rows)
    print('Wrote',file,flush=True)

def run(input_dir: Path, out: Path):
    out.mkdir(parents=True,exist_ok=True)
    paths=sorted(input_dir.glob('CDOTRM_CD_Crash_Listing*20??*.xlsx'))
    if not paths:
        raise SystemExit('No matching CDOT .xlsx files found in '+str(input_dir))
    seen=set()
    counts=Counter()
    monthly=Counter()
    hourly=Counter()
    conditions=Counter()
    crash_types=Counter()
    counties=Counter()
    geo=Counter()
    nonmotorist=Counter()
    school_zones=Counter()
    quality=Counter()
    maxdate={}
    for path in paths:
        m=re.search(r'20\d\d',path.name)
        if not m:continue
        year=int(m.group())
        added=0
        for r in iter_selected_rows(path):
            quality[(year,'source_rows')]+=1
            uid=(year,r.get('cuid'))
            if r.get('cuid') and uid in seen:
                quality[(year,'duplicate_cuid')]+=1
                continue
            if r.get('cuid'):seen.add(uid)
            date=date_from_excel(r.get('date_raw'))
            if not date:
                quality[(year,'invalid_dates')]+=1
            elif date.year!=year:
                quality[(year,'date_year_mismatch')]+=1
            elif year not in maxdate or date>maxdate[year]:
                maxdate[year]=date
            county=(r.get('county') or 'UNKNOWN').strip().upper()
            city=(r.get('city') or 'UNSPECIFIED').strip().upper()
            killed=r.get('killed')
            injured=r.get('injured')
            sev=severity(killed,injured)
            nonm=non_motorist_category(r.get('nonmotorist_1'),r.get('nonmotorist_2'))
            areas=['Colorado']
            if county=='EL PASO':areas.append('El Paso County')
            if city=='COLORADO SPRINGS':areas.append('Colorado Springs')
            counts[(year,'crashes')]+=1
            counts[(year,f'severity:{sev}')]+=1
            if sev=='Unknown':quality[(year,'missing_outcome')]+=1
            counties[(year,county,sev)]+=1
            for area in areas:
                counts[(year,area,'crashes')]+=1
                counts[(year,area,sev)]+=1
                if nonm != 'Not identified in selected fields':
                    nonmotorist[(year,area,nonm,sev)]+=1
                sz=(r.get('school_zone') or '').strip().lower()
                szlabel=('Flagged school zone' if sz in ('1','true','yes') else 'Not flagged school zone' if sz in ('0','false','no') else 'Unknown school-zone flag')
                school_zones[(year,area,szlabel,sev)]+=1
                if date and date.year==year:
                    monthly[(year,area,date.month,sev)]+=1
                    hourly[(year,area,date.weekday(),sev,'weekday')]+=1
                t=r.get('time') or ''
                hm=re.match(r'^(\d\d?):(\d\d)',t)
                if hm and int(hm.group(1))<=23:
                    hourly[(year,area,int(hm.group(1)),sev,'hour')]+=1
                else:
                    quality[(year,'missing_or_invalid_time')]+=1 if area=='Colorado' else 0
                for label,key in [('Weather',r.get('weather')),('Road surface',r.get('road_condition')),('Lighting',r.get('lighting'))]:
                    conditions[(year,area,label,(key or 'Unknown').strip() or 'Unknown',sev)]+=1
                ct=(r.get('crash_type') or 'Unknown').strip() or 'Unknown'
                crash_types[(year,area,ct,sev)]+=1
            lat,lon=r.get('latitude'),r.get('longitude')
            if valid_point(lat,lon):
                quality[(year,'valid_coordinates')]+=1
                if county=='EL PASO':
                    # Approximate 1km spatial bins (not road segments or risk rates).
                    latbin=round(float(lat),2)
                    lonbin=round(float(lon),2)
                    geo[(year,latbin,lonbin,sev)]+=1
            else:
                quality[(year,'missing_or_invalid_coordinates')]+=1
            if r.get('record_status'):
                quality[(year,'record_status:'+r['record_status'])]+=1
            added+=1
        print('Processed',path.name,added,'retained crashes, latest observed',maxdate.get(year),flush=True)
    years=sorted({key[0] for key in counts})
    area_names=['Colorado','El Paso County','Colorado Springs']
    write_csv(out,'annual.csv',['year','area','crashes','fatal_crashes','injury_crashes','no_injury_reported','unknown_outcome','fatal_plus_injury_pct'],[
        [year,area,counts[(year,area,'crashes')],counts[(year,area,'Fatal')],counts[(year,area,'Injury')],counts[(year,area,'No injury reported')],counts[(year,area,'Unknown')],round(100*(counts[(year,area,'Fatal')]+counts[(year,area,'Injury')])/counts[(year,area,'crashes')],2) if counts[(year,area,'crashes')] else 0]
        for year in years for area in area_names])
    write_csv(out,'county_year.csv',['year','county','severity','crashes'],[[*k,v] for k,v in sorted(counties.items())])
    write_csv(out,'monthly.csv',['year','area','month','severity','crashes'],[[*k,v] for k,v in sorted(monthly.items())])
    write_csv(out,'time.csv',['year','area','time_value','severity','time_dimension','crashes'],[[*k,v] for k,v in sorted(hourly.items(),key=lambda x:tuple(map(str,x[0])))])
    write_csv(out,'conditions.csv',['year','area','condition_group','value','severity','crashes'],[[*k,v] for k,v in sorted(conditions.items())])
    write_csv(out,'crash_types.csv',['year','area','crash_type','severity','crashes'],[[*k,v] for k,v in sorted(crash_types.items())])
    write_csv(out,'school_zone.csv',['year','area','school_zone','severity','crashes'],[[*k,v] for k,v in sorted(school_zones.items())])
    write_csv(out,'nonmotorist.csv',['year','area','type','severity','crashes'],[[*k,v] for k,v in sorted(nonmotorist.items())])
    write_csv(out,'el_paso_grid.csv',['year','latitude_bin','longitude_bin','severity','crashes'],[[*k,v] for k,v in sorted(geo.items())])
    write_csv(out,'data_quality.csv',['year','metric','value'],[[*k,v] for k,v in sorted(quality.items())])
    summary={'years': years,'rows_source':sum(quality[(y,'source_rows')] for y in years),'crashes_retained':sum(counts[(y,'crashes')] for y in years),
      'latest_dates':{str(y):str(maxdate[y]) for y in years if y in maxdate},'annual':{str(y):{area:counts[(y,area,'crashes')] for area in area_names} for y in years},
      'notes':['Counts reflect reported crashes in these supplied extracts, not exposure-adjusted risk.',
       '2026 is partial and should not be compared directly with full years.','Severe crashes means at least one injury or fatality, not an injury severity grade.','Non-motorist categories rely on two selected NM Type fields and may be incomplete.',
       'Missing or invalid dates are excluded from month breakdowns but included in annual filename-year totals.']}
    (out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--input-dir',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,default=Path('data/processed'))
    args=parser.parse_args()
    run(args.input_dir,args.output_dir)
