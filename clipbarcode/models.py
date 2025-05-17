import logging

from dateutil import parser
from peewee import (
    CharField,
    DateTimeField,
    DoesNotExist,
    IntegerField,
    IntegrityError,
    Model,
    TextField,
)

from clipbarcode.database import db

logger = logging.getLogger(__name__)


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

    def get_type_display(self):
        return dict(self.TYPES)[self.type]

    @classmethod
    def create_leitura(cls, leitura):
        try:
            with db.atomic():
                leitura.save()
        except IntegrityError as e:
            print(e)

    @classmethod
    def update_leitura(cls, leitura_id, **kwargs):
        try:
            with db.atomic():
                leitura = Leitura.get(Leitura.id == leitura_id)

                for field, value in kwargs.items():
                    setattr(leitura, field, value)

                leitura.save()
        except IntegrityError as e:
            print(e)

    @classmethod
    def delete_leitura(cls, leitura):
        try:
            with db.atomic():
                leitura.delete_instance()
        except IntegrityError as e:
            print(e)

    @classmethod
    def get_leituras(cls, reverse=True):
        try:
            field = Leitura.id
            if reverse:
                field = field.desc()
            leituras = Leitura.select().order_by(field)
            return list(leituras)
        except Exception as e:
            print(e)

    @classmethod
    def get_by_code(cls, cod_lido):
        try:
            leitura = Leitura.get(Leitura.cod_lido == cod_lido)
            return leitura
        except DoesNotExist:
            pass
        except Exception as e:
            print(e)

    @classmethod
    def from_json_to_sqlite(cls, json_content):
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

    def __str__(self):
        max_len = 32
        campo = self.descricao if self.descricao else self.cod_lido

        return f'{self.id}): {campo[0:max_len]}{"..." if len(campo) > max_len else ""}'


class AppSettings(Model):
    themename = TextField(default="darkly", null=False)

    class Meta:
        database = db

    @classmethod
    def get_settings(cls, key):
        try:
            settings = cls.get_by_id(0)
        except AppSettings.DoesNotExist:
            print("Settings not found, creating default settings.")
            settings = cls.create(id=0)
            settings.save()

        return getattr(settings, key)

    @classmethod
    def set_settings(cls, key, value):
        try:
            settings = cls.get_by_id(0)
        except AppSettings.DoesNotExist:
            print("Settings not found, creating default settings.")
            settings = cls.create(id=0)

        setattr(settings, key, value)
        settings.save()
