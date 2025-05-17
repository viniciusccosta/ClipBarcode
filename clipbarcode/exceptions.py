class NoImageException(Exception):
    pass


class LeituraFalhaException(Exception):
    def __init__(self, message):
        self.message = message
