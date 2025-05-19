import json
from datetime import datetime

from clipbarcode.models import Leitura


def test_tables_exists(db):
    """Test if the Leitura table exists in the database."""
    assert Leitura.table_exists()


def test_from_json_to_sqlite(db):
    """Test importing readings from JSON into the database."""
    # Arranging:
    json_content = {
        "1625606852183110400": {
            "data": "28/02/2022",
            "type": "0",
            "cod_lido": "text",
            "cod_conv": "conv",
            "descricao": "descricao",
        },
        "1747617928000000000": {
            "data": "19/05/2025",
            "type": "1",
            "cod_lido": "cod_lido",
            "cod_conv": "cod_conv",
            "descricao": "descricao",
        },
    }

    # Act:
    Leitura.from_json_to_sqlite(json_content)

    # Assert:
    leituras = sorted(Leitura.get_leituras(), key=lambda x: x.mili)
    assert len(leituras) == 2

    primeiro = json_content["1625606852183110400"]
    assert leituras[0].data.strftime("%d/%m/%Y") == primeiro["data"]
    assert leituras[0].type == primeiro["type"]
    assert leituras[0].cod_lido == primeiro["cod_lido"]
    assert leituras[0].cod_conv == primeiro["cod_conv"]
    assert leituras[0].descricao == primeiro["descricao"]

    segundo = json_content["1747617928000000000"]
    assert leituras[1].data.strftime("%d/%m/%Y") == segundo["data"]
    assert leituras[1].type == segundo["type"]
    assert leituras[1].cod_lido == segundo["cod_lido"]
    assert leituras[1].cod_conv == segundo["cod_conv"]
    assert leituras[1].descricao == segundo["descricao"]


def test_create_leitura_boleto_cobranca(db):
    """Test creating a boleto cobrança reading."""
    # Arranging:
    leitura = Leitura(
        mili=1625606852183110400,
        data=datetime(2021, 7, 6, 18, 27, 32, 183110),
        type="1",
        cod_lido="00190.50095 40144.816069 06809.350314 3 37370000000100",
        cod_conv="00193373700000001000500940144816060680935031",
        descricao="Boleto de cobrança qualquer",
    )

    # Act:
    Leitura.create_leitura(leitura)

    # Assert:
    leitura_db = Leitura.get(Leitura.mili == 1625606852183110400)
    assert len(Leitura.get_leituras()) == 1
    assert leitura_db.mili == leitura.mili
    assert leitura_db.data == leitura.data
    assert leitura_db.type == leitura.type
    assert leitura_db.cod_lido == leitura.cod_lido
    assert leitura_db.cod_conv == leitura.cod_conv
    assert leitura_db.descricao == leitura.descricao


def test_update_leitura(db):
    """Test updating a reading's description."""
    # Arranging:
    leitura = Leitura(
        mili=1625606852183110400,
        data=datetime(2021, 7, 6, 18, 27, 32, 183110),
        type="1",
        cod_lido="00190.50095 40144.816069 06809.350314 3 37370000000100",
        cod_conv="00193373700000001000500940144816060680935031",
        descricao="Boleto de cobrança qualquer",
    )
    Leitura.create_leitura(leitura)

    # Act:
    Leitura.update_leitura(leitura.id, descricao="Atualizando descrição")

    # Assert:
    updated_leitura = Leitura.get(Leitura.mili == 1625606852183110400)
    assert updated_leitura.descricao == "Atualizando descrição"


def test_delete_leitura(db):
    """Test deleting a reading."""

    # Arranging:
    leitura = Leitura(
        mili=1625606852183110400,
        data=datetime(2021, 7, 6, 18, 27, 32, 183110),
        type="1",
        cod_lido="00190.50095 40144.816069 06809.350314 3 37370000000100",
        cod_conv="00193373700000001000500940144816060680935031",
        descricao="Boleto de cobrança qualquer",
    )
    Leitura.create_leitura(leitura)

    # Act:
    Leitura.delete_leitura(leitura)

    # Assert:
    assert Leitura.get_or_none(Leitura.mili == 1625606852183110400) is None
    assert len(Leitura.get_leituras()) == 0


def test_get_leituras(db):
    """Test retrieving all readings."""

    # Arrange:
    leitura = Leitura(
        mili=1625606852183110400,
        data=datetime(2021, 7, 6, 18, 27, 32, 183110),
        type="1",
        cod_lido="00190.50095 40144.816069 06809.350314 3 37370000000100",
        cod_conv="00193373700000001000500940144816060680935031",
        descricao="Boleto de cobrança qualquer",
    )
    Leitura.create_leitura(leitura)

    # Act:
    leituras = Leitura.get_leituras()

    # Assert:
    assert len(leituras) == 1
    assert leituras[0].mili == leitura.mili
    assert leituras[0].descricao == leitura.descricao
    assert leituras[0].type == leitura.type
    assert leituras[0].cod_lido == leitura.cod_lido
    assert leituras[0].cod_conv == leitura.cod_conv
    assert leituras[0].data == leitura.data
