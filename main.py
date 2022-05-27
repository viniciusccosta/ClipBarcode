# ======================================================================================================================
import datetime
import tkinter as tk
from PIL import ImageGrab
import pytesseract
import os
import json
from time import time_ns


# ======================================================================================================================
RESULTS_PATH = "./history/results.json"
TYPES = {0: "Linha Digitável", "1": "Código de Barras"}


# ======================================================================================================================
def check_history_path():
    if not os.path.exists("./history"):
        os.mkdir("./history")
    if not os.path.exists(RESULTS_PATH):
        open(RESULTS_PATH, 'w').close()


def save_result(result, img):
    check_history_path()

    # Salvando a imagem primeiro:
    img.save(f'./history/{result["id"]}.png')

    # Incluíndo a leitura no arquivo de resultados:
    lista_atual = []
    with open("./history/results.json", 'r') as jsonfile:
        try:
            lista_atual = json.load(jsonfile)
        except json.decoder.JSONDecodeError as e:
            pass    # TODO: Handle it

    with open("./history/results.json", 'w') as jsonfile:
        lista_atual.append(result)
        json.dump(lista_atual, jsonfile)


def timens_to_datetime(nanoseconds):    # TODO: Enviar para o próprio arquivo de "tempo"
    timestamp_microseconds = nanoseconds / 1000
    timestamp_seconds = timestamp_microseconds / 1000000
    return datetime.datetime.fromtimestamp(timestamp_seconds)


def ler_print():
    # -----------------------------------------------------------
    timens = time_ns()
    agora = timens_to_datetime(timens)

    # -----------------------------------------------------------
    img = ImageGrab.grabclipboard()
    try:
        text = pytesseract.image_to_string(img).strip("\n")
    except TypeError:
        return  # TODO: Avisar usuário que não existe nenhuma image no CTRL V

    # -----------------------------------------------------------
    # Linha Digitável:
    if len(text) > 1:
        result = {
            "id": timens,
            "data": agora.strftime("%d/%m/%Y %H:%M:%S"),
            "type": 0,
            "cod_lido": text,
            "cod_conv": text.replace(".", "").replace(" ", "")
        }
        save_result(result, img)

    # -----------------------------------------------------------
    # Código de Barras ?
    else:
        print("Será que o print é de um código de barras então?")


# ======================================================================================================================
class MainWindow:
    def __init__(self, root, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.root = root
        self.root.minsize(1500, 720)

        # -------------------------------------
        # Frames:
        self.f1 = tk.Frame(self.root, )
        self.f2 = tk.Frame(self.root, )
        tk.Button(self.root, text="Ler Print", font=("Consolas", 16), command=self.btn_ler_print_pressed).grid(pady=10)

        self.f1.grid(row=1, column=0, padx=5, pady=(0, 10), sticky="nswe")
        self.f2.grid(row=1, column=1, columnspan=2, padx=5, pady=(0, 10), sticky="nswe")

        cols, rows = self.root.grid_size()
        for c in range(cols):
            self.root.columnconfigure(index=c, weight=1)

        self.root.rowconfigure(index=1, weight=1)

        # -------------------------------------
        # List Frame:
        self.listbox = tk.Listbox(self.f1, font=("Consolas", 14), selectmode="SINGLE", )
        self.listbox.grid(sticky="nsew", )

        self._fill_list()

        cols, rows = self.f1.grid_size()
        for r in range(rows):
            self.f1.rowconfigure(index=r, weight=1)
        for c in range(cols):
            self.f1.columnconfigure(index=c, weight=1)

        # -------------------------------------
        # Detail Frame:

        tk.Frame(self.f2, bg="yellow").grid(row=0, rowspan=10, column=1, columnspan=6, sticky="nsew")

        tv_data = tk.StringVar()
        tv_data.set("27/05/2022 16:43:11")
        tk.Label(self.f2, textvariable=tv_data, font=("Consolas", 16)).grid(row=10, column=1, columnspan=6,
                                                                            sticky="nswe")

        tk.Label(self.f2, text="Código Lido:", font=("Consolas", 16), ).grid(row=12, sticky="nswe")
        tk.Entry(self.f2, font=("Consolas", 16), ).grid(row=12, column=1, columnspan=6, sticky="we")
        tk.Button(self.f2, text="Copiar", font=("Consolas", 12)).grid(row=12, column=7, )

        tk.Label(self.f2, text="Código Convertido:", font=("Consolas", 16), ).grid(row=13, sticky="nswe")
        tk.Entry(self.f2, font=("Consolas", 16), ).grid(row=13, column=1, columnspan=6, sticky="we")
        tk.Button(self.f2, text="Copiar", font=("Consolas", 12)).grid(row=13, column=7, )

        cols, rows = self.f2.grid_size()
        for r in range(16):
            self.f2.rowconfigure(index=r, weight=1)
        for c in range(cols):
            self.f2.columnconfigure(index=c, weight=1)

    def _fill_list(self):
        self.listbox.delete(0, "end")

        with open("./history/results.json", 'r') as jsonfile:
            try:
                data = json.load(jsonfile)
                for cdb in data:
                    self.listbox.insert("0", f'{cdb.get("data")}: {cdb.get("cod_lido")}')
            except json.decoder.JSONDecodeError:
                pass    # TODO: Handle it

    def btn_ler_print_pressed(self):
        ler_print()
        self._fill_list()


# ======================================================================================================================
if __name__ == '__main__':
    try:
        pytesseract.get_languages()
    except pytesseract.pytesseract.TesseractNotFoundError:
        # TODO: ASK FOR FULL PATH OF TESSERACT
        pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

    check_history_path()

    tk_root = tk.Tk()
    MainWindow(tk_root)
    tk_root.mainloop()
