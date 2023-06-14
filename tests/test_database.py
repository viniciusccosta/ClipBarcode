import unittest
from datetime import datetime

from clipbarcode.database import *

class DbTestCase(unittest.TestCase):
    def setUp(self):
        db.create_tables([Leitura,])
    
    def tearDown(self):
        db.drop_tables([Leitura,])
        db.close()
    
    def test_tables_exists(self):
        self.assertTrue(Leitura.table_exists())
    
    def test_from_json_to_sqlite(self):
        json_content = {
            "1": {
                "data": "28/02/2022",
                "type": "0",
                "cod_lido": "text",
                "cod_conv": "conv",
                "descricao": "descricao"
            },
            "2": {
                "data": "28/02/2022",
                "type": "1",
                "cod_lido": "cod_lido",
                "cod_conv": "cod_conv",
                "descricao": "descricao"
            }
        }

        from_json_to_sqlite(json_content)
        
        self.assertEqual(Leitura.select().count(), 2)
    
    def test_create_leitura_boleto_cobranca(self):
        leitura = Leitura (
            mili      = 1625606852183110400,
            data      = datetime(2021, 7, 6, 18, 27, 32, 183110),
            type      = '1', 
            cod_lido  = '00190.50095 40144.816069 06809.350314 3 37370000000100', 
            cod_conv  = '00193373700000001000500940144816060680935031', 
            descricao = 'Boleto de cobrança qualquer',
        )
        
        create_leitura(leitura)
        
        self.assertEqual(Leitura.select().count(), 1)
                    
    def test_update_leitura(self):
        leitura = Leitura (
            mili      = 1625606852183110400,
            data      = datetime(2021, 7, 6, 18, 27, 32, 183110),
            type      = '1', 
            cod_lido  = '00190.50095 40144.816069 06809.350314 3 37370000000100', 
            cod_conv  = '00193373700000001000500940144816060680935031', 
            descricao = 'Boleto de cobrança qualquer',
        )
        create_leitura(leitura)
        
        update_leitura(leitura.id, descricao='Atualizando descrição')
        
        self.assertEqual(Leitura.get(Leitura.mili==1625606852183110400).descricao, 'Atualizando descrição')
    
    def test_delete_leitura(self):
        leitura = Leitura (
            mili      = 1625606852183110400,
            data      = datetime(2021, 7, 6, 18, 27, 32, 183110),
            type      = '1', 
            cod_lido  = '00190.50095 40144.816069 06809.350314 3 37370000000100', 
            cod_conv  = '00193373700000001000500940144816060680935031', 
            descricao = 'Boleto de cobrança qualquer',
        )
        create_leitura(leitura)
        
        delete_leitura(leitura)
        
        self.assertEqual(Leitura.select().count(), 0)
                          
    def test_get_leituras(self):
        leitura = Leitura (
            mili      = 1625606852183110400,
            data      = datetime(2021, 7, 6, 18, 27, 32, 183110),
            type      = '1', 
            cod_lido  = '00190.50095 40144.816069 06809.350314 3 37370000000100', 
            cod_conv  = '00193373700000001000500940144816060680935031', 
            descricao = 'Boleto de cobrança qualquer',
        )
        create_leitura(leitura)
        
        leituras = get_leituras()
        
        self.assertEqual(len(leituras), 1)
