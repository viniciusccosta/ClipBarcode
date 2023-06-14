import unittest
from clipbarcode.boleto import *

class NovoBoletoTestCase(unittest.TestCase):
    def test_novo_boleto_cobranca_por_linha_digitavel(self):
        linha_digitavel = "00190.50095 40144.816069 06809.350314 3 37370000000100"
        
        boleto = new_boleto(linha_digitavel=linha_digitavel)
        
        self.assertIsInstance(boleto, Cobranca)
            
    def test_novo_boleto_arrecadacao_por_linha_digitavel(self):
        linha_digitavel = "826500000110 314400081704 924000000027 202104000015"
        
        boleto = new_boleto(linha_digitavel=linha_digitavel)
        
        self.assertIsInstance(boleto, Arrecadacao)
        
    def test_novo_boleto_cobranca_por_codigo_barras(self):
        cod_barras = '00193373700000001000500940144816060680935031'
        
        boleto = new_boleto(cod_barras=cod_barras)
        
        self.assertIsInstance(boleto, Cobranca)
        
    def test_novo_boleto_arrecadacao_por_codigo_barras(self):
        cod_barras = '82650000011314400081709240000000220210400001'
        
        boleto = new_boleto(cod_barras=cod_barras)
        
        self.assertIsInstance(boleto, Arrecadacao)
    
    def test_novo_boleto_por_linha_digitavel_invalido(self):
        linha_digitavel = "0123456789012345678901234567890123456X"
        
        with self.assertRaises(BoletoInvalidoException):
        
            new_boleto(linha_digitavel=linha_digitavel)
            
    def test_novo_boleto_por_codigo_barras_invalido(self):
        cod_barras = "0123456789012345678901234567890123456X"
        
        with self.assertRaises(BoletoInvalidoException):
        
            new_boleto(cod_barras=cod_barras)
            
class CobrancaTestCase(unittest.TestCase):
    def test_from_linha_digitavel_valido(self):
        linha_digitavel = "00190.50095 40144.816069 06809.350314 3 37370000000100"
        
        cobranca = Cobranca(linha_digitavel=linha_digitavel)
        
        self.assertEqual(cobranca.id_banco, "001")
        self.assertEqual(cobranca.cod_moeda, "9")
        self.assertEqual(cobranca.campo_livre_1, "05009")
        self.assertEqual(cobranca.dv1, "5")
        self.assertEqual(cobranca.campo_livre_2, "4014481606")
        self.assertEqual(cobranca.dv2, "9")
        self.assertEqual(cobranca.campo_livre_3, "0680935031")
        self.assertEqual(cobranca.dv3, "4")
        self.assertEqual(cobranca.dv_geral, "3")
        self.assertEqual(cobranca.fator_venc, "3737")
        self.assertEqual(cobranca.valor, 1.00)

    def test_from_linha_digitavel_invalid(self):
        linha_digitavel = "00190.50095 40144.816069 06809.350314 4 37370000000100"
        
        with self.assertRaises(BoletoInvalidoException):
            Cobranca(linha_digitavel=linha_digitavel)

    def test_from_cod_barras_valid(self):
        cod_barras = "00193373700000001000500940144816060680935031"
        
        cobranca = Cobranca(cod_barras=cod_barras)
        
        self.assertEqual(cobranca.id_banco, "001")
        self.assertEqual(cobranca.cod_moeda, "9")
        self.assertEqual(cobranca.dv_cod_barras, "3")
        self.assertEqual(cobranca.fator_venc, "3737")
        self.assertEqual(cobranca.valor, 1.0)
        self.assertEqual(cobranca.campo_livre_cod_barras, "0500940144816060680935031")

    def test_from_cod_barras_invalid(self):
        cod_barras = "00194373700000001000500940144816060680935031"
        
        with self.assertRaises(BoletoInvalidoException):
            Cobranca(cod_barras=cod_barras)

class ArrecadacaoTestCase(unittest.TestCase):
    def test_from_linha_digitavel_valido(self):
        linha_digitavel = "85870000134 7 79110328221 0 40072022125 6 74512580554 8"
        
        cobranca = Arrecadacao(linha_digitavel=linha_digitavel)
        
        self.assertEqual(cobranca.campo1, "85870000134")
        self.assertEqual(cobranca.dv1, "7")
        self.assertEqual(cobranca.campo2, "79110328221")
        self.assertEqual(cobranca.dv2, "0")
        self.assertEqual(cobranca.campo3, "40072022125")
        self.assertEqual(cobranca.dv3, "6")
        self.assertEqual(cobranca.campo4, "74512580554")
        self.assertEqual(cobranca.dv4, "8")
        self.assertEqual(cobranca.dv_geral, "7")

    def test_from_linha_digitavel_invalid(self):
        linha_digitavel = "85870000134 0 79110328221 0 40072022125 6 74512580554 8"
        
        with self.assertRaises(BoletoInvalidoException):
            Arrecadacao(linha_digitavel=linha_digitavel)

    def test_from_cod_barras_valid(self):
        cod_barras = "85870000134791103282214007202212574512580554"
        
        cobranca = Arrecadacao(cod_barras=cod_barras)
        
        self.assertEqual(cobranca.campo1, "85870000134")
        self.assertEqual(cobranca.dv1, "7")
        self.assertEqual(cobranca.campo2, "79110328221")
        self.assertEqual(cobranca.dv2, "0")
        self.assertEqual(cobranca.campo3, "40072022125")
        self.assertEqual(cobranca.dv3, "6")
        self.assertEqual(cobranca.campo4, "74512580554")
        self.assertEqual(cobranca.dv4, "8")
        self.assertEqual(cobranca.dv_geral, "7")

    def test_from_cod_barras_invalid(self):
        cod_barras = "85870000133791103282214007202212574512580554"
        
        with self.assertRaises(BoletoInvalidoException):
            Arrecadacao(cod_barras=cod_barras)

if __name__ == '__main__':
    unittest.main()