# =============================================================================
import re

from abc import ABC, abstractmethod
from decimal import Decimal

from .datetime_tools import calculate_date
from .digito_verificador import mod10, mod11

# =============================================================================
DATA_BASE = "07/10/1997"

# =============================================================================
def new_boleto(*args, **kwargs):
    if "linha_digitavel" in kwargs:
        linha_digitavel = kwargs.get("linha_digitavel")
        linha_digitavel = re.sub('\D', '', linha_digitavel)

        if len(linha_digitavel) == 47:
            try:
                return Cobranca(linha_digitavel=linha_digitavel)
            except BoletoInvalidoException:
                raise
        elif len(linha_digitavel) == 48:
            return Arrecadacao(linha_digitavel=linha_digitavel)

    elif "cod_barras" in kwargs:
        cod_barras = kwargs.get("cod_barras")
        cod_barras = re.sub('\D', '', cod_barras)

        if len(cod_barras) == 44:
            if cod_barras[0] == "8":
                return Arrecadacao(cod_barras=cod_barras)
            else:
                return Cobranca(cod_barras=cod_barras)

    raise BoletoInvalidoException

# =============================================================================
class BoletoInvalidoException(Exception):
    pass

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

class Arrecadacao(Boleto):
    """
    Segmento do Produto:
        1. Prefeituras;
        2. Saneamento;
        3. Energia Elétrica e Gás;
        4. Telecomunicações;
        5. Órgãos Governamentais;
        6. Carnes e Assemelhados ou demais
            Empresas / Órgãos que serão identificadas através do CNPJ.
        7. Multas de trânsito
        9. Uso exclusivo do banco

    Valor Efetivo ou Referência:
        “6”- Valor a ser cobrado efetivamente em reais com dígito verificador calculado pelo módulo 10 na quarta posição do Código de Barras e valor com 11 posições (versão 2 e posteriores) sem qualquer alteração;

        “7”- Quantidade de moeda:
            Zeros- somente na impossibilidade de utilizar o valor;
            Valor a ser reajustado por um índice com dígito verificador calculado pelo módulo 10 na quarta posição do Código de Barras e valor com 11 posições (versão 2 e posteriores).

        “8”- Valor a ser cobrado efetivamente em reais com dígito verificador calculado pelo módulo 11 na quarta posição do Código de Barras e valor com 11 posições (versão 2 e posteriores) sem qualquer alteração.

        “9”- Quantidade de moeda
            Zeros- somente na impossibilidade de utilizar o valor;
            Valor a ser reajustado por um índice com dígito verificador calculado pelo módulo 11 na quarta posição do Código de Barras e valor com 11 posições (versão 2 e posteriores).
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # TODO: TALVEZ usar variáveis mais específicas
        # self.id_prod     = None     # Constante “8” para identificar arrecadação
        # self.seg_prod    = None     # 1 - Prefeitura, 2 - Saneamento, ....
        # self.id_ve_ref   = None     #
        # self.valor       = None     #
        # self.id_emp      = None     #
        # self.campo_livre = None     #

        self.dv_geral = None  #

        self.campo1 = None
        self.dv1    = None
        self.campo2 = None
        self.dv2    = None
        self.campo3 = None
        self.dv3    = None
        self.campo4 = None
        self.dv4    = None

        if "linha_digitavel" in kwargs:
            self.from_linha_digitavel(kwargs.get("linha_digitavel"))
        elif "cod_barras" in kwargs:
            self.from_cod_barras(kwargs.get("cod_barras"))
        else:
            raise BoletoInvalidoException

    def from_linha_digitavel(self, linha_digitavel):
        def validar_linha_digitavel():
            if self.campo1[2] == "8" or self.campo1[2] == "9":               # TODO: Ao invés desses "ifs" poderíamos fazer uma subclasse de Arrecadação
                dv1 = mod11(f'{self.campo1}', x10=True)
                dv2 = mod11(f'{self.campo2}', x10=True)
                dv3 = mod11(f'{self.campo3}', x10=True)
                dv4 = mod11(f'{self.campo4}', x10=True)
                dv_geral = mod11(f'{self.campo1[0:0 + 3]}{self.campo1[4:4 + 8]}{self.campo2}{self.campo3}{self.campo4}', x10=True)
            else:
                dv1 = mod10(f'{self.campo1}')
                dv2 = mod10(f'{self.campo2}')
                dv3 = mod10(f'{self.campo3}')
                dv4 = mod10(f'{self.campo4}')
                dv_geral = mod10(f'{self.campo1[0:0 + 3]}{self.campo1[4:4 + 8]}{self.campo2}{self.campo3}{self.campo4}')

            return dv1 == self.dv1 and dv2 == self.dv2 and dv3 == self.dv3 and dv4 == self.dv4 and self.dv_geral == dv_geral

        def preencher_cod_barras():
            self.cod_barras = f'{self.campo1}{self.campo2}{self.campo3}{self.campo4}'

        linha_digitavel = re.sub('\D', '', linha_digitavel)

        if len(linha_digitavel) == 48:
            self.linha_digitavel = linha_digitavel

            self.campo1 = linha_digitavel[ 0: 0+11]
            self.dv1    = linha_digitavel[11:11+ 1]
            self.campo2 = linha_digitavel[12:12+11]
            self.dv2    = linha_digitavel[23:23+ 1]
            self.campo3 = linha_digitavel[24:24+11]
            self.dv3    = linha_digitavel[35:35+ 1]
            self.campo4 = linha_digitavel[36:36+11]
            self.dv4    = linha_digitavel[47:47+ 1]

            self.dv_geral = self.campo1[3]

            if validar_linha_digitavel():
                preencher_cod_barras()
            else:
                raise BoletoInvalidoException
        else:
            raise BoletoInvalidoException

    def from_cod_barras(self, cod_barras):
        """
            +---------+---------+--------------------------------------------+
            | POSIÇÃO | TAMANHO | CONTEÚDO                                   |
            +---------+---------+--------------------------------------------+
            | 01 - 01 | 1       | Identificação do Produto                   |
            +---------+---------+--------------------------------------------+
            | 02 - 02 | 1       | Identificação do Segmento                  |
            +---------+---------+--------------------------------------------+
            | 03 - 03 | 1       | Identificação do valor real ou referência  |
            +---------+---------+--------------------------------------------+
            | 04 - 04 | 1       | Dígito verificador geral (módulo 10 ou 11) |
            +---------+---------+--------------------------------------------+
            | 05 - 15 | 11      | Valor                                      |
            +---------+---------+--------------------------------------------+
            | 16 - 19 | 4       | Identificação da Empresa/Órgão             |
            +---------+---------+--------------------------------------------+
            | 20 - 44 | 25      | Campo livre de utilização da Empresa/Orgão |
            +---------+---------+--------------------------------------------+
            | 16 - 23 | 8       | CNPJ / MF                                  |
            +---------+---------+--------------------------------------------+
            | 24 - 44 | 21      | Campo livre de utilização da Empresa/Órgão |
            +---------+---------+--------------------------------------------+
        """

        def validar_cod_barras():
            if self.campo1[2] == "8" or self.campo1[2] == "9":     # TODO: Ao invés desses "ifs" poderíamos fazer uma subclasse de Arrecadação
                dv_geral = mod11(f'{self.campo1[0:0 + 3]}{self.campo1[4:4 + 8]}{self.campo2}{self.campo3}{self.campo4}', x10=True)
            else:
                dv_geral = mod10(f'{self.campo1[0:0 + 3]}{self.campo1[4:4 + 8]}{self.campo2}{self.campo3}{self.campo4}')

            return dv_geral == self.dv_geral

        def preencher_linha_digitavel():
            if self.campo1[2] == "8" or self.campo1[2] == "9":               # TODO: Ao invés desses "ifs" poderíamos fazer uma subclasse de Arrecadação
                self.dv1 = mod11(f'{self.campo1}', x10=True)
                self.dv2 = mod11(f'{self.campo2}', x10=True)
                self.dv3 = mod11(f'{self.campo3}', x10=True)
                self.dv4 = mod11(f'{self.campo4}', x10=True)
                self.dv_geral = mod11(f'{self.campo1[0:0 + 3]}{self.campo1[4:4 + 8]}{self.campo2}{self.campo3}{self.campo4}', x10=True)
            else:
                self.dv1 = mod10(f'{self.campo1}')
                self.dv2 = mod10(f'{self.campo2}')
                self.dv3 = mod10(f'{self.campo3}')
                self.dv4 = mod10(f'{self.campo4}')
                self.dv_geral = mod10(f'{self.campo1[0:0 + 3]}{self.campo1[4:4 + 8]}{self.campo2}{self.campo3}{self.campo4}')

            self.linha_digitavel = f'{self.campo1}{self.dv1}{self.campo2}{self.dv2}{self.campo3}{self.dv3}{self.campo4}{self.dv4}'

        cod_barras = re.sub('\D', '', cod_barras)

        if len(cod_barras) == 44:
            self.cod_barras = cod_barras

            self.campo1 = cod_barras[ 0: 0+11]
            self.campo2 = cod_barras[11:11+11]
            self.campo3 = cod_barras[22:22+11]
            self.campo4 = cod_barras[33:33+11]

            self.dv_geral = self.campo1[3]

            if validar_cod_barras():
                preencher_linha_digitavel()
            else:
                raise BoletoInvalidoException
        else:
            raise BoletoInvalidoException

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
        else:
            raise BoletoInvalidoException

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

        def validar_linha_digitavel():
            dv1 = mod10(f'{self.id_banco}{self.cod_moeda}{self.campo_livre_1}')
            dv2 = mod10(f'{self.campo_livre_2}')
            dv3 = mod10(f'{self.campo_livre_3}')
            dv = mod11(f'{self.id_banco}{self.cod_moeda}{self.fator_venc}{int(round(self.valor * 100)):010}{self.campo_livre_1}{self.campo_livre_2}{self.campo_livre_3}')

            return dv1 == self.dv1 and dv2 == self.dv2 and dv3 == self.dv3 and dv == self.dv_geral

        def preencher_cod_barras():
            self.campo_livre_cod_barras = f'{self.campo_livre_1}{self.campo_livre_2}{self.campo_livre_3}'
            self.dv_cod_barras          = self.dv_geral
            self.cod_barras             = f'{self.id_banco}{self.cod_moeda}{self.dv_cod_barras}{self.fator_venc}{int(round(self.valor * 100)):010}{self.campo_livre_cod_barras}'

        linha_digitavel = re.sub('\D', '', linha_digitavel)

        if len(linha_digitavel) == 47:                          # TODO: Realizar verificações necessárias, como verificar se só possuem números e coisas similares
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
            self.valor          = float( Decimal(linha_digitavel[37:37 + 10]) / 100 )

            self.venc           = calculate_date(DATA_BASE, self.fator_venc)

            if validar_linha_digitavel():
                preencher_cod_barras()
            else:
                raise BoletoInvalidoException
        else:
            raise BoletoInvalidoException

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
                    | 20-44   | 25      | 9(25)    | Campo livre - utilizado de acordo com a especificação interna do banco emissor |
                    +---------+---------+----------+--------------------------------------------------------------------------------+
                """

        def validar_cod_barras():
            dv = mod11(f'{self.id_banco}{self.cod_moeda}{self.fator_venc}{int(round(self.valor * 100)):010}{self.campo_livre_cod_barras}')
            return dv == self.dv_cod_barras

        def preencher_linha_digitavel():
            self.campo_livre_1  = self.campo_livre_cod_barras[0:0+5]
            self.dv1            = mod10(f'{self.id_banco}{self.cod_moeda}{self.campo_livre_1}')

            self.campo_livre_2  = self.campo_livre_cod_barras[5:5+10]
            self.dv2            = mod10(f'{self.campo_livre_2}')

            self.campo_livre_3  = self.campo_livre_cod_barras[15:15+10]
            self.dv3            = mod10(f'{self.campo_livre_3}')

            self.dv_geral       = self.dv_cod_barras

            self.linha_digitavel = f'{self.id_banco}{self.cod_moeda}{self.campo_livre_1}{self.dv1}{self.campo_livre_2}{self.dv2}{self.campo_livre_3}{self.dv3}{self.dv_geral}{self.fator_venc}{int(round(self.valor * 100)):010}'

        cod_barras = re.sub('\D', '', cod_barras)

        if len(cod_barras) == 44:
            self.cod_barras = cod_barras

            self.id_banco               = cod_barras[ 0: 0 +  3]
            self.cod_moeda              = cod_barras[ 3: 3 +  1]
            self.dv_cod_barras          = cod_barras[ 4: 4 +  1]
            self.fator_venc             = cod_barras[ 5: 5 +  4]
            self.valor                  = float( Decimal(cod_barras[ 9: 9 + 10]) / 100 )
            self.campo_livre_cod_barras = cod_barras[19:19 + 25]

            self.venc                   = calculate_date(DATA_BASE, self.fator_venc)

            if validar_cod_barras():
                preencher_linha_digitavel()
            else:
                raise BoletoInvalidoException
        else:
            raise BoletoInvalidoException

# =============================================================================
"""
    https://www.boletobancario-codigodebarras.com/2016/04/linha-digitavel.html
    https://cmsarquivos.febraban.org.br/Arquivos/documentos/PDF/Layout%20-%20C%C3%B3digo%20de%20Barras%20ATUALIZADO.pdf
    https://www.macoratti.net/07/10/net_bol.htm
    https://www.banese.com.br/wps/discovirtual/download?nmInternalFolder=/Empresa_recebimento&nmFile=Composicao%20da%20Linha%20Digitavel%20e%20do%20Codigo%20de%20Barras_05062017.pdf
    https://demo.iprefeituras.com.br/uploads/noticia/16091/manual_cnab_400.pdf
    https://www.bb.com.br/docs/pub/emp/empl/dwn/Doc5175Bloqueto.pdf
    https://www.bb.com.br/docs/pub/emp/empl/dwn/Doc8122GuiaNaoComp.pdf
"""

# =============================================================================