# =============================================================================
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

# =============================================================================
DATA_BASE = "07/10/1997"


# =============================================================================
def mod10(dados):
    # TODO: Transferir para módulo próprio

    fatores       = [2, 1]                                                      # [2, 1]
    multiplicador = [fatores[i % len(fatores)] for i in range(len(dados))]      # [2, 1, 2, 1, 2, 1,...] só que está da esquerda para direita nesse caso
    multiplicador = multiplicador[::-1]                                         # Agora sim, está da direita para esquerda!

    # ---------------------------------------------------------------------------
    digitos = []

    for i in range(len(multiplicador)):
        produto = int(dados[i]) * multiplicador[i]
        digitos += [int(i) for i in str(produto)]                               # Separando dígitos do resultado da múltiplicação (resultado = 18 --> 1+8,)

    soma  = sum(digitos)

    # ---------------------------------------------------------------------------
    resto = soma % 10

    if resto == 0:  # Observação: Utilizar o dígito "0" para o resto 0 (zero). Exemplo:
        dv = 0
    else:
        dv = 10 - resto

    # ---------------------------------------------------------------------------
    return str(dv)


def mod11(dados):
    # TODO: Transferir para módulo próprio

    fatores       = [i for i in range(2, 10)]                                   # [2, 3, 4, 5, 6, 7, 8, 9]
    multiplicador = [fatores[i % len(fatores)] for i in range(len(dados))]      # [2, 3, 4, 5, 6, 7, 8, 9, 2, 3, 4, 5, 6, 7, 8, 9,...] só que está da esquerda para direita nesse caso
    multiplicador = multiplicador[::-1]                                         # Agora sim, está da direita para esquerda!

    # ---------------------------------------------------------------------------
    soma = 0

    for i in range(len(multiplicador)):
        produto = int(dados[i]) * multiplicador[i]
        soma += produto

    # ---------------------------------------------------------------------------
    resto = soma % 11

    if resto <= 1 or resto >= 10:   # Observação: para o código de barras, sempre que o resto for 0, 1 ou 10, deverá ser utilizado o dígito 1
        dv = 1
    else:
        dv = 11 - resto

    # ---------------------------------------------------------------------------
    return str(dv)


def calculate_date(fator):
    # TODO: Não sinto que esse método pertença a esse módulo...
    return datetime.strptime(DATA_BASE, "%d/%m/%Y") + timedelta(days=int(fator))


def instanciar_boleto(*args, **kwargs):
    if "linha_digitavel" in kwargs:
        linha_digitavel = kwargs.get("linha_digitavel")
        linha_digitavel = linha_digitavel.strip("").replace(" ", "").replace(".", "")

        if len(linha_digitavel) == 47:
            return Cobranca(linha_digitavel=linha_digitavel)
        elif len(linha_digitavel) == 48:
            return Arrecadacao(linha_digitavel=linha_digitavel)

    elif "cod_barras" in kwargs:
        cod_barras = kwargs.get("cod_barras")
        cod_barras = cod_barras.strip("").replace(" ", "").replace(".", "")

        if len(cod_barras) == 44:
            if cod_barras[0] == "8":                        # TODO: Verificar se é isso mesmo
                return Arrecadacao(cod_barras=cod_barras)
            else:
                return Cobranca(cod_barras=cod_barras)


# =============================================================================
class Boleto(ABC):
    def __init__(self, *args, **kwargs):
        self.linha_digitavel = None
        self.cod_barras = None

    @abstractmethod
    def from_linha_digitavel(self, linha_digitavel):
        pass

    @abstractmethod
    def from_cod_barras(self, cod_barras):
        pass

    @abstractmethod
    def validate_linha_digitavel(self):
        pass

    @abstractmethod
    def validate_cod_barras(self):
        pass


class Arrecadacao(Boleto):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def from_linha_digitavel(self, linha_digitavel):
        pass

    def from_cod_barras(self, cod_barras):
        pass

    def validate_linha_digitavel(self):
        pass

    def validate_cod_barras(self):
        pass


class Cobranca(Boleto):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ------------------------------
        self.id_banco = None

        self.cod_moeda = None

        self.campo_livre_1 = None
        self.dv1 = None

        self.campo_livre_2 = None
        self.dv2 = None

        self.campo_livre_3 = None
        self.dv3 = None

        self.dv_geral = None

        self.fator_venc = None

        self.valor = None

        # ------------------------------
        self.dv_cod_barras = None

        self.campo_livre_cod_barras = None

        # ------------------------------
        self.venc = None

        # ------------------------------
        if "linha_digitavel" in kwargs:
            self.from_linha_digitavel(kwargs.get("linha_digitavel"))
        elif "cod_barras" in kwargs:
            self.from_cod_barras(kwargs.get("cod_barras"))

    def from_linha_digitavel(self, linha_digitavel):
        """
            +---------+---------+--------------------------------------+
            | Posição | Tamanho | Conteúdo                             |
            +---------+---------+--------------------------------------+
            | 01-03   | 3       | Identificação do Banco               |
            +---------+---------+--------------------------------------+
            | 04-04   | 1       | Código de Moeda (9 - Real)           |
            +---------+---------+--------------------------------------+
            | 05-09   | 5       | Posições 1 a 5 do campo livre        |
            +---------+---------+--------------------------------------+
            | 10-10   | 1       | Dígito verificador do primeiro campo |
            +---------+---------+--------------------------------------+
            | 11-20   | 10      | Posições 6 a 15 do campo livre       |
            +---------+---------+--------------------------------------+
            | 21-21   | 1       | Dígito verificador do segundo campo  |
            +---------+---------+--------------------------------------+
            | 22-31   | 10      | Posições 16 a 25 do campo livre      |
            +---------+---------+--------------------------------------+
            | 32-32   | 1       | Dígito verificador do terceiro campo |
            +---------+---------+--------------------------------------+
            | 33-33   | 1       | Dígito verificador geral             |
            +---------+---------+--------------------------------------+
            | 34-37   | 4       | Fator de Vencimento                  |
            +---------+---------+--------------------------------------+
            | 38-47   | 10      | Valor nominal do título              |
            +---------+---------+--------------------------------------+
        """

        def converter_para_cod_barras():
            self.campo_livre_cod_barras = f'{self.campo_livre_1}{self.campo_livre_2}{self.campo_livre_3}'
            self.dv_cod_barras          = self.dv_geral
            self.cod_barras             = f'{self.id_banco}{self.cod_moeda}{self.dv_cod_barras}{self.fator_venc}{int(self.valor * 100):010}{self.campo_livre_cod_barras}'

        linha_digitavel = linha_digitavel.strip("").replace(" ", "").replace(".", "")

        if len(linha_digitavel) == 47:                          # TODO: Realizar verificações necessárias
            self.linha_digitavel = linha_digitavel

            self.id_banco       = linha_digitavel[ 0: 0 +  3]
            self.cod_moeda      = linha_digitavel[ 3: 3 +  1]
            self.campo_livre_1  = linha_digitavel[ 4: 4 +  5]
            self.dv1            = linha_digitavel[ 9: 9 +  1]
            self.campo_livre_2  = linha_digitavel[10:10 + 10]
            self.dv2            = linha_digitavel[20:20 +  1]
            self.campo_livre_3  = linha_digitavel[21:21 + 10]
            self.dv3            = linha_digitavel[31:31 +  1]
            self.dv_geral       = linha_digitavel[32:32 +  1]
            self.fator_venc     = linha_digitavel[33:33 +  4]
            self.valor          = int(linha_digitavel[37:37 + 10]) / 100

            self.venc           = calculate_date(self.fator_venc)

            if self.validate_linha_digitavel():
                converter_para_cod_barras()
            else:
                print("CÓDIGO INVÁLIDO")    # TODO: Lidar apropriadamente, talvez "raise DigitoVerificadorInvalido"

        elif len(linha_digitavel) == 44:
            pass

        else:
            print("BOLETO NÃO VÁLIDO")      # TODO: Lidar apropriadamente, talvez "raise CodigoBarrasNaoSuportado"

    def from_cod_barras(self, cod_barras):
        """
                    +---------+---------+----------+--------------------------------------------------------------------------------+
                    | Posição | Tamanho | Picture  | Conteúdo                                                                       |
                    +---------+---------+----------+--------------------------------------------------------------------------------+
                    | 01-03   | 3       | 9(3)     | Identificação do banco                                                         |
                    +---------+---------+----------+--------------------------------------------------------------------------------+
                    | 04-04   | 1       | 9        | Código moeda (9-Real)                                                          |
                    +---------+---------+----------+--------------------------------------------------------------------------------+
                    | 05-05   | 1       | 9        | Dígito verificador do código de barras (DV)                                    |
                    +---------+---------+----------+--------------------------------------------------------------------------------+
                    | 06-09   | 4       | 9(4)     | Fator de vencimento                                                            |
                    +---------+---------+----------+--------------------------------------------------------------------------------+
                    | 10-19   | 10      | 9(08)v99 | Valor nominal do título                                                        |
                    +---------+---------+----------+--------------------------------------------------------------------------------+
                    | 20-44   | 25      | 9(25)    | Campo livre – utilizado de acordo com a especificação interna do banco emissor |
                    +---------+---------+----------+--------------------------------------------------------------------------------+
                """

        def conveter_para_linha_digitavel():
            self.campo_livre_1  = self.campo_livre_cod_barras[0:0+5]
            self.dv1            = mod10(f'{self.id_banco}{self.cod_moeda}{self.campo_livre_1}')

            self.campo_livre_2  = self.campo_livre_cod_barras[5:5+10]
            self.dv2            = mod10(f'{self.campo_livre_2}')

            self.campo_livre_3  = self.campo_livre_cod_barras[15:15+10]
            self.dv3            = mod10(f'{self.campo_livre_3}')

            self.dv_geral       = self.dv_cod_barras

            self.linha_digitavel = f'{self.id_banco}{self.cod_moeda}{self.campo_livre_1}{self.dv1}{self.campo_livre_2}{self.dv2}{self.campo_livre_3}{self.dv3}{self.dv_geral}{self.fator_venc}{int(self.valor*100):010}'

        cod_barras = cod_barras.strip("").replace(" ", "").replace(".", "")

        if len(cod_barras) == 44:       # TODO: Realizar verificações necessárias, como se só tem números e etc
            self.cod_barras = cod_barras

            self.id_banco               = cod_barras[ 0: 0 +  3]
            self.cod_moeda              = cod_barras[ 3: 3 +  1]
            self.dv_cod_barras          = cod_barras[ 4: 4 +  1]
            self.fator_venc             = cod_barras[ 5: 5 +  4]
            self.valor                  = int(cod_barras[ 9: 9 + 10]) / 100
            self.campo_livre_cod_barras = cod_barras[19:19 + 25]

            self.venc                   = calculate_date(self.fator_venc)

            if self.validate_cod_barras():
                conveter_para_linha_digitavel()
            else:
                print("CÓDIGO INVÁLIDO")    # TODO: Lidar apropriadamente, talvez "raise DigitoVerificadorInvalido"

        # TODO: Código de Barras são só 44 posições né?

    def validate_linha_digitavel(self):
        dv1 = mod10(f'{self.id_banco}{self.cod_moeda}{self.campo_livre_1}')
        dv2 = mod10(f'{self.campo_livre_2}')
        dv3 = mod10(f'{self.campo_livre_3}')
        dv  = mod11(f'{self.id_banco}{self.cod_moeda}{self.fator_venc}{int(self.valor * 100):010}{self.campo_livre_1}{self.campo_livre_2}{self.campo_livre_3}')

        return dv1 == self.dv1 and dv2 == self.dv2 and dv3 == self.dv3 and dv == self.dv_geral

    def validate_cod_barras(self):
        dv = mod11(f'{self.id_banco}{self.cod_moeda}{self.fator_venc}{int(self.valor*100):010}{self.campo_livre_cod_barras}')
        return dv == self.dv_cod_barras


# =============================================================================
if __name__ == "__main__":
    lds = [
        "00190.50095 40144.816069 06809.350314 3 37370000000100",
        "34191.09065 02457.162937 81685.860009 2 89610000016806",
        "34191.09065 30793.282937 81685.860009 7 90220000019288",
        "34191.09065 02457.162937 81685.860009 2 89610000016806",
        "03399.08626 34700.020372 46356.601016 3 89860000300000",
        "03399.08626 34700.020026 53245.601017 1 89860000300000",
        "23791.99405 90000.002346 95002.498301 1 89860000292619",
        "00190.00009 02803.164017 29488.511667 4 00000000000000",
        "23791.40904 90000.000118 69011.464208 5 90170000072890",

    ]
    cdb = [
        "00193373700000001000500940144816060680935031",
        "34192896100000168061090602457162938168586000",
        "34197902200000192881090630793282938168586000",
        "34192896100000168061090602457162938168586000",
        "03393898600003000009086234700020374635660101",
        "03391898600003000009086234700020025324560101",
        "23791898600002926191994090000002349500249830",
        "00194000000000000000000002803164012948851166",
        "23795901700000728901409090000000116901146420",

    ]

    for c_index in range(len(lds)):
        c1 = Cobranca(linha_digitavel=lds[c_index])
        c2 = Cobranca(cod_barras=cdb[c_index])

        for k, c1v in c1.__dict__.items():
            c2v = c2.__dict__.get(k)
            print(c1v == c2v, k, c1v, c2v, sep="|")

"""
    https://www.boletobancario-codigodebarras.com/2016/04/linha-digitavel.html
    https://cmsarquivos.febraban.org.br/Arquivos/documentos/PDF/Layout%20-%20C%C3%B3digo%20de%20Barras%20ATUALIZADO.pdf
    https://www.macoratti.net/07/10/net_bol.htm
    https://www.banese.com.br/wps/discovirtual/download?nmInternalFolder=/Empresa_recebimento&nmFile=Composicao%20da%20Linha%20Digitavel%20e%20do%20Codigo%20de%20Barras_05062017.pdf
    https://demo.iprefeituras.com.br/uploads/noticia/16091/manual_cnab_400.pdf
    https://www.bb.com.br/docs/pub/emp/empl/dwn/Doc5175Bloqueto.pdf
"""
