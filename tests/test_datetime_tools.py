import unittest
from datetime import datetime
from clipbarcode.datetime_tools import *

class TestCalculateDate(unittest.TestCase):
    
    def test_calculate_date(self):
        data_base = "20/06/2021"
        fator = 5
        expected_result = datetime(2021, 6, 25, 0, 0)
        self.assertEqual(calculate_date(data_base, fator), expected_result)
        
class TestTimensToDatetime(unittest.TestCase):
    def test_timens_to_datetime(self):
        except_result = datetime(2021, 7, 6, 18, 27, 32, 183110)
        
        result = timens_to_datetime(1625606852183110400)
        
        self.assertEqual(result, except_result)
        
if __name__ == '__main__':
    unittest.main()