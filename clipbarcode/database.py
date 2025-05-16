# =====================================================================
from dateutil import parser
from peewee import *

from clipbarcode.utils import resource_path

# =====================================================================
db = SqliteDatabase(resource_path("database.db"))


# =====================================================================
class Leitura(Model):
    TYPES = (
        ("0", "Texto"),
        ("1", "Código de Barras"),
        ("2", "Nota Fiscal"),
        ("3", "QRCode"),
    )

    mili = IntegerField(unique=True)
    data = DateTimeField()
    type = CharField(choices=TYPES)
    cod_lido = TextField()
    cod_conv = TextField()
    descricao = TextField(null=True)

    class Meta:
        database = db

    def get_type_display(
        self,
    ):
        return dict(self.TYPES)[self.type]

    def __str__(self):
        max_len = 32
        campo = self.descricao if self.descricao else self.cod_lido

        return f'{self.id}): {campo[0:max_len]}{"..." if len(campo) > max_len else ""}'


class Preferencia(Model):
    themename = TextField(default="darkly")

    class Meta:
        database = db


# =====================================================================
def create_tables():
    db.connect()
    db.create_tables(
        [
            Leitura,
            Preferencia,
        ],
        safe=True,
    )
    Preferencia.get_or_create(id=0)
    db.close()


# =====================================================================
def from_json_to_sqlite(json_content):
    leituras = [
        Leitura(
            mili=mili,
            data=parser.parse(dic["data"], dayfirst=True),
            type=dic["type"],
            cod_lido=dic["cod_lido"],
            cod_conv=dic["cod_conv"],
            descricao=dic.get("descricao"),
        )
        for mili, dic in json_content.items()
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
        return list(leituras)
    except Exception as e:
        print(e)


def get_leitura_por_cod_lido(cod_lido):
    try:
        leitura = Leitura.get(Leitura.cod_lido == cod_lido)
        return leitura
    except DoesNotExist:
        pass
    except Exception as e:
        print(e)


# =====================================================================
def update_preferencia(**kwargs):
    try:
        with db.atomic():
            preferencia = Preferencia.get(Preferencia.id == 0)

            for field, value in kwargs.items():
                setattr(preferencia, field, value)

            preferencia.save()

    except IntegrityError as e:
        print(e)


def get_preferencia():
    try:
        preferencia = Preferencia.get(Preferencia.id == 0)
        return preferencia
    except Exception as e:
        print(e)


# =====================================================================
