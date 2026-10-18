import unittest
from src.metrics import date_from_excel, severity,valid_point,non_motorist_category

class TestMetrics(unittest.TestCase):
    def test_excel_dates(self):
        self.assertEqual(str(date_from_excel(45292)), '2024-01-01')
        self.assertIsNone(date_from_excel('n/a'))
    def test_severity_exclusive(self):
        self.assertEqual(severity('1','2'),'Fatal')
        self.assertEqual(severity('0','2'),'Injury')
        self.assertEqual(severity('0','0'),'No injury reported')
        self.assertEqual(severity('','0'),'Unknown')
    def test_geo(self):
        self.assertTrue(valid_point('38.84','-104.82'))
        self.assertFalse(valid_point('0','0'))
    def test_nonmotorist(self):
        self.assertEqual(non_motorist_category('Pedestrian',''),'Pedestrian recorded')
        self.assertEqual(non_motorist_category('',''),'Not identified in selected fields')
if __name__=='__main__':unittest.main()
