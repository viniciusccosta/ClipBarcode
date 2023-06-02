# =====================================================================
import json
from peewee import *
from dateutil import parser
import os

# =====================================================================
db = SqliteDatabase('database.db')

# =====================================================================
class Leitura(Model):
    TYPES = (
        ("0", "Texto"), 
        ("1", "Código de Barras"), 
        ("2", "Nota Fiscal"), 
        ("3", "QRCode"),
    )
    
    mili        = IntegerField(unique=True)
    data        = DateTimeField()
    type        = CharField(choices=TYPES)
    cod_lido    = TextField()
    cod_conv    = TextField()
    descricao   = TextField(null=True)

    class Meta:
        database = db
        
    def get_type_display(self,):
        return dict(self.TYPES)[self.type]
    
    def __str__(self):
        max_len = 32
        campo = self.descricao if self.descricao else self.cod_lido
        
        return f'{self.id}): {campo[0:max_len]}{"..." if len(campo) > max_len else ""}'

# =====================================================================
def create_tables():
    db.connect()
    db.create_tables([Leitura,])
    db.close()
    
def from_json_to_sqlite(json_path):
    with open(json_path, 'r', encoding='UTF8') as jsonfile:
        data = json.load(jsonfile)
        
    leituras = [ 
        Leitura(
            mili=mili, 
            data=parser.parse(dic['data'], dayfirst=True), 
            type=dic['type'], 
            cod_lido=dic['cod_lido'], 
            cod_conv=dic['cod_conv'], 
            descricao=dic.get('descricao')
        ) for mili, dic in data.items()
    ]
    
    with db.atomic():
        for leitura in leituras:
            try:
                leitura.save()
            except IntegrityError as e:
                pass

def create_leitura(leitura):
    try:
        with db.atomic():
            leitura.save()
    except IntegrityError as e:
        print(e)

def update_leitura(leitura_id, **kwargs):
    try:
        with db.atomic():
            leitura = Leitura.get(Leitura.id == leitura_id)
            
            for field, value in kwargs.items():
                setattr(leitura, field, value)
            
            leitura.save()
                                
    except IntegrityError as e:
        print(e)

def delete_leitura(leitura):
    try:
        with db.atomic():
            leitura.delete_instance()
    except IntegrityError as e:
        print(e)
    
def get_leituras(reverse=True):
    try:
        field = Leitura.id
        if reverse:
            field = field.desc()
        leituras = Leitura.select().order_by(field)
        return list( leituras )
    except Exception as e:
        print(e)

# =====================================================================
if __name__ == "__main__":
    create_tables()
    
    json_path = "./history/results.json"
    from_json_to_sqlite(json_path)
    os.remove(json_path)
    
    update_leitura(1, cod_lido="ALTERADO")
    
    for i, leitura in enumerate(get_leituras(True)):
        print(leitura)

# =====================================================================