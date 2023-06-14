import unittest
from clipbarcode.digito_verificador import *

class TestMod10(unittest.TestCase):
    def test_mod10_with_valid_input(self):
        dados = "1234567890"
        expected_output = "3"
        self.assertEqual(mod10(dados), expected_output)
    
    def test_mod10_with_invalid_input(self):
        dados = "1234abcd"
        self.assertRaises(ValueError, mod10, dados)
        
class TestMod11(unittest.TestCase):
    
    def test_mod11_with_x10_false(self):
        self.assertEqual(mod11('1234567890'), '1')
        self.assertEqual(mod11('123456789'), '7')
        self.assertEqual(mod11('112223330000'), '1')
        self.assertEqual(mod11('87654321'), '2')
        self.assertEqual(mod11('99999999999'), '7')
        
    def test_mod11_with_x10_true(self):
        self.assertEqual(mod11('1234567890', True), '0')
        self.assertEqual(mod11('123456789', True), '7')
        self.assertEqual(mod11('112223330000', True), '0')
        self.assertEqual(mod11('87654321', True), '2')
        self.assertEqual(mod11('99999999999', True), '7')

if __name__ == '__main__':
    unittest.main()