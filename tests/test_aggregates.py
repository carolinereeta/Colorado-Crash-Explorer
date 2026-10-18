"""Regression checks: the published CSV aggregates must reconcile."""
from pathlib import Path
import csv
import unittest
from collections import Counter
P=Path(__file__).resolve().parents[1]/'data'/'processed'

def rows(name):
    with (P/name).open(encoding='utf8',newline='') as f:
        return list(csv.DictReader(f))

class TestPublishedData(unittest.TestCase):
    def test_outcomes_reconcile(self):
        for r in rows('annual.csv'):
            total=sum(int(r[c]) for c in ('fatal_crashes','injury_crashes','no_injury_reported','unknown_outcome'))
            self.assertEqual(total,int(r['crashes']),r)
    def test_areas_nested(self):
        d={(int(r['year']),r['area']):int(r['crashes']) for r in rows('annual.csv')}
        for y in range(2021,2027):
            self.assertLessEqual(d[y,'Colorado Springs'],d[y,'El Paso County'])
            self.assertLessEqual(d[y,'El Paso County'],d[y,'Colorado'])
    def test_school_zone_matches_annual(self):
        d=Counter()
        for r in rows('school_zone.csv'):d[(r['year'],r['area'])]+=int(r['crashes'])
        for r in rows('annual.csv'):
            self.assertEqual(d[r['year'],r['area']],int(r['crashes']))
    def test_all_year_rows_match_source(self):
        import json
        s=json.loads((P/'summary.json').read_text())
        self.assertEqual(s['rows_source'],sum(int(r['crashes']) for r in rows('annual.csv') if r['area']=='Colorado'))
        self.assertEqual(s['years'],list(range(2021,2027)))

if __name__=='__main__':unittest.main()
