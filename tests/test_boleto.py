import unittest

from clipbarcode.boleto import Arrecadacao, Cobranca, new_boleto
from clipbarcode.exceptions import BoletoInvalidoException


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
        cod_barras = "00193373700000001000500940144816060680935031"

        boleto = new_boleto(cod_barras=cod_barras)

        self.assertIsInstance(boleto, Cobranca)

    def test_novo_boleto_arrecadacao_por_codigo_barras(self):
        cod_barras = "82650000011314400081709240000000220210400001"

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
        self.assertEqual(
            cobranca.linha_digitavel, "00190500954014481606906809350314337370000000100"
        )

    def test_from_linha_digitavel_issue_23(self):
        linha_digitavel = "03399.00672 93710.100970 64014.701011 8 93830000015898"  # Esse código de barras retornar inválido no issue-23

        cobranca = Cobranca(linha_digitavel=linha_digitavel)
        self.assertEqual(cobranca.id_banco, "033")
        self.assertEqual(cobranca.cod_moeda, "9")
        self.assertEqual(cobranca.dv_cod_barras, "8")
        self.assertEqual(cobranca.fator_venc, "9383")
        self.assertEqual(cobranca.valor, 158.98)
        self.assertEqual(cobranca.campo_livre_cod_barras, "9006793710100976401470101")

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

    def test_from_cod_barras_em_massa(self):
        valores_teste = {
            "00193938500000219600000002941725010172680217": "00190000090294172501801726802174393850000021960",
            "00192938700000109900000003212913000005411917": "00190000090321291300200054119177293870000010990",
            "03398937900000228499006793710100972695750101": "03399006729371010097026957501013893790000022849",
            "03396938000000141769006793710100975873840101": "03399006729371010097058738401015693800000014176",
            "03395938800000049009006793710100978656940101": "03399006729371010097086569401010593880000004900",
            "03392939000000158999006793710100986823200101": "03399006729371010098868232001013293900000015899",
            "03394937200000060009934553100000004597470101": "03399934535310000000845974701018493720000006000",
            "07092936900000491980000240220188102011107059": "07090000204022018810220111070593293690000049198",
            "07091936900000332610000240220188102011207045": "07090000204022018810220112070451193690000033261",
            "07094936900000271890000240220188102011307031": "07090000204022018810220113070310493690000027189",
            "07791000000000000000001101001305209547518072": "07790001160100130520895475180725100000000000000",
            "07792937900000050000001112047370601011601523": "07790001161204737060110116015230293790000005000",
            "07791937900000050000001112047370601011605193": "07790001161204737060110116051938193790000005000",
            "34191937700003249401090003078630919425850000": "34191090080307863091494258500001193770000324940",
            "34199937900000337481090011322531575331036000": "34191090081132253157253310360002993790000033748",
            "03398938300000158989006793710100976401470101": "03399006729371010097064014701011893830000015898",  # Issue 23
            "03396939300000158989006793710100986849070101": "03399006729371010098868490701015693930000015898",  # Issue 37
        }

        for cod_barras, linha_digitavel_esperado in valores_teste.items():
            cobranca = Cobranca(cod_barras=cod_barras)

            self.assertEqual(cobranca.linha_digitavel, linha_digitavel_esperado)

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


if __name__ == "__main__":
    unittest.main()
