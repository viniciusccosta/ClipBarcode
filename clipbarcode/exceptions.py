class NoImageException(Exception):
    pass


class LeituraFalhaException(Exception):
    def __init__(self, message):
        self.message = message


class DuplicatedLeituraException(Exception):
    def __init__(self, message, leitura=None):
        self.message = message
        self.leitura = leitura
