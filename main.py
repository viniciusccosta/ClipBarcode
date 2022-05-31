# ======================================================================================================================
import tkinter as tk
from tkinter import messagebox
from PIL import ImageGrab, ImageTk, Image
import pytesseract
import os
import json
from time import time_ns
from pyzbar.pyzbar import decode
from datetime_tools import timens_to_datetime
import pyperclip


# ======================================================================================================================
RESULTS_PATH = "./history/results.json"
TYPES = {0: "Linha Digitável", "1": "Código de Barras"}


# ======================================================================================================================
class NoImageException(Exception):
    pass


# ======================================================================================================================
def check_history_path():
    if not os.path.exists("./history"):
        os.mkdir("./history")
    if not os.path.exists(RESULTS_PATH):
        open(RESULTS_PATH, 'w').close()


def save_result(result, img):
    check_history_path()

    # Salvando a imagem primeiro:
    for k, v in result.items():
        img.save(f'./history/{k}.png')

    # Incluíndo a leitura no arquivo de resultados:
    lista_atual = {}
    with open("./history/results.json", 'r', encoding='UTF8') as jsonfile:
        try:
            lista_atual = json.load(jsonfile)
        except json.decoder.JSONDecodeError as e:
            print(e)    # TODO: Handle it

    with open("./history/results.json", 'w', encoding='UTF8') as jsonfile:
        for k, v in result.items():        
            lista_atual[k] = v
        json.dump(lista_atual, jsonfile, ensure_ascii=False)


def ler_print():
    # -----------------------------------------------------------
    timens = time_ns()
    agora = timens_to_datetime(timens)

    # -----------------------------------------------------------
    img = ImageGrab.grabclipboard()

    try:
        text = pytesseract.image_to_string(img, lang="por").strip("\n")
    except TypeError:
        raise NoImageException

    # -----------------------------------------------------------
    # Linha Digitável:
    if len(text) > 1:
        result = {
            f"{timens}": {
                "data": agora.strftime("%d/%m/%Y %H:%M:%S"),
                "type": 0,
                "cod_lido": text,
                "cod_conv": text.replace(".", "").replace(" ", "")
            }
        }
        save_result(result, img)

    # -----------------------------------------------------------
    # Código de Barras ?
    else:
        results = decode(img)

        if len(results) == 1:
            d = results[0]
            text = d.data.decode("utf-8")

            if d.type == "I25":         # Boletos de Cobraça e Convênio
                print("Boleto ?", text)
                cod_conv = text     # TODO: Converter texto lido do código de barras para linhas digitáveis
            elif d.type == "CODE128":   # Código de Nota Fiscal
                print("Nota Fiscal ?", text)
                cod_conv = text     # TODO: Fazer nada né?
            elif d.type == "QRCODE":
                print("QRCODE", text)   # QR Codes
                cod_conv = text     # TODO: Fazer nada né?
            else:
                messagebox.showerror("Ainda não", "Código de barras não suportado")
                return

            result = {
                f"{timens}": {
                    "data": agora.strftime("%d/%m/%Y %H:%M:%S"),
                    "type": 1,
                    "cod_lido": text,
                    "cod_conv": cod_conv
                }
            }

            save_result(result, img)
        elif len(results) > 1:
            messagebox.showerror("Ops!", "O seu print só deve conter apenas 1 código de barras")
        else:
            messagebox.showerror("Cadê?", "Código de barras não localizado!")


def get_leitura(timens):
    check_history_path()

    with open("./history/results.json", 'r', encoding='UTF8') as jsonfile:
        try:
            data = json.load(jsonfile)
            return data.get(timens,)

        except json.decoder.JSONDecodeError as e:
            pass  # TODO: Handle it


# ======================================================================================================================
class MainWindow:
    def __init__(self, root, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.root = root
        self.root.title("Clip Barcode")
        self.root.minsize(1500, 720)

        # -------------------------------------
        # Frames:
        self.f1 = tk.Frame(self.root, )
        self.f2 = tk.Frame(self.root, )
        tk.Button(self.root, text="Ler Print", font=("Consolas", 16), command=self._ler_print_pressed).grid(pady=10)

        self.f1.grid(row=1, column=0, padx=5, pady=(0, 10), sticky="nswe")
        self.f2.grid(row=1, column=1, columnspan=2, padx=5, pady=(0, 10), sticky="nswe")

        cols, rows = self.root.grid_size()
        for c in range(cols):
            self.root.columnconfigure(index=c, weight=1)

        self.root.rowconfigure(index=1, weight=1)

        # -------------------------------------
        # List Frame:
        self.listbox = tk.Listbox(self.f1, font=("Consolas", 14), selectmode="SINGLE", activestyle=tk.NONE)
        self.listbox.bind('<<ListboxSelect>>', self._item_selected)
        self.listbox.bind("<Down>", self._arrow_down)
        self.listbox.bind("<Up>", self._arrow_up)
        self.listbox.grid(sticky="nsew", )

        self._fill_list()

        cols, rows = self.f1.grid_size()
        for r in range(rows):
            self.f1.rowconfigure(index=r, weight=1)
        for c in range(cols):
            self.f1.columnconfigure(index=c, weight=1)

        # -------------------------------------
        # Detail Frame:

        self.canvas = tk.Label(self.f2, bg="gray", width=1110, height=1)
        self.canvas.grid(row=0, rowspan=10, column=1, columnspan=6, sticky="nsew", )

        self.lbl_date = tk.StringVar()
        tk.Label(self.f2, textvariable=self.lbl_date, font=("Consolas", 16)).grid(row=10, column=1, columnspan=6, sticky="nswe")

        self.entry_cod_lido = tk.StringVar()
        tk.Label(self.f2, text="Código Lido:", font=("Consolas", 16), ).grid(row=12, sticky="nswe")
        tk.Entry(self.f2, font=("Consolas", 16), state=tk.DISABLED, textvariable=self.entry_cod_lido).grid(row=12, column=1, columnspan=6, sticky="we")
        tk.Button(self.f2, text="Copiar", font=("Consolas", 12), command=self.copiar_codlido).grid(row=12, column=7, )

        self.entry_cod_conv = tk.StringVar()
        tk.Label(self.f2, text="Código Convertido:", font=("Consolas", 16), ).grid(row=13, sticky="nswe")
        tk.Entry(self.f2, font=("Consolas", 16), state=tk.DISABLED, textvariable=self.entry_cod_conv).grid(row=13, column=1, columnspan=6, sticky="we")
        tk.Button(self.f2, text="Copiar", font=("Consolas", 12), command=self.copiar_codconv).grid(row=13, column=7, )

        cols, rows = self.f2.grid_size()
        for r in range(16):
            self.f2.rowconfigure(index=r, weight=1)
        for c in range(cols):
            self.f2.columnconfigure(index=c, weight=1)

        # -------------------------------------
        self.photoimage = None
        self.update_canvas("ocr.png")           # TODO: A primeira imagem não está sendo redimensionada, provavelmente porque a interface ainda não está pronta

        self._ler_print_pressed(init=True)

        # -------------------------------------

    def _fill_list(self):
        self.listbox.delete(0, "end")

        with open("./history/results.json", 'r', encoding='UTF-8') as jsonfile:
            try:
                data = json.load(jsonfile)
                for k, v in data.items():
                    self.listbox.insert("0", f'{k}')
            except json.decoder.JSONDecodeError:
                pass    # TODO: Handle it

    def _ler_print_pressed(self, init=False):
        try:
            ler_print()

            self._fill_list()
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(0)
            self.listbox.event_generate("<<ListboxSelect>>")
            # Caso 1: Abriu o programa e tinha um print no "CTRL V"
            # Caso 3: Apertou "Ler Print" e tinha um print no "CTRL V"

        except NoImageException:
            if not init:
                # Caso 4: Apertou "Ler Print", mas não tinha um print no "CTRL V"
                messagebox.showwarning("Sem Imagem", "Tire um print antes")

            # Caso 2: Abriu o programa, mas não tinha um print no "CTRL V"

    def _item_selected(self, event):
        index = self.listbox.curselection()

        if index:
            timens = self.listbox.get(index)
            cdb = get_leitura(timens)

            self.update_frame_detail(timens, cdb)

    def _arrow_up(self, event):
        self.selection = self.listbox.curselection()[0]

        if self.selection > 0:
            self.listbox.select_clear(self.selection)
            self.selection -= 1
            self.listbox.select_set(self.selection)
            self._item_selected(None)   # TODO: Não curti passar esse None...

    def _arrow_down(self, event):
        self.selection = self.listbox.curselection()[0]

        if self.selection < self.listbox.size() - 1:
            self.listbox.select_clear(self.selection)
            self.selection += 1
            self.listbox.select_set(self.selection)
            self._item_selected(None)   # TODO: Não curti passar esse None...

    def copiar_codlido(self):
        # TODO: Lidar com exceções
        pyperclip.copy(self.entry_cod_lido.get())
        # TODO: Alterar texto do botão para "Copiado"

    def copiar_codconv(self):
        # TODO: Lidar com exceções
        pyperclip.copy(self.entry_cod_conv.get())
        # TODO: Alterar texto do botão para "Copiado"

    def update_frame_detail(self, timens, cdb):
        # TODO: Alterar texto dos botões para os originais

        if cdb:
            self.update_canvas(f"./history/{timens}.png")
            self.update_date(cdb.get("data"))
            self.update_entry_codlido(cdb.get("cod_lido", ""))
            self.update_entry_codconv(cdb.get("cod_conv", ""))
        else:
            messagebox.showerror("EITA!", "Código de barras não localizado.")

    def update_date(self, new_text):
        self.lbl_date.set(new_text)

    def update_entry_codlido(self, new_text):
        self.entry_cod_lido.set(new_text)

    def update_entry_codconv(self, new_text):
        self.entry_cod_conv.set(new_text)

    def update_canvas(self, filename):
        def get_resize_params(size):
            des_widht = self.canvas.winfo_width()
            cur_width, cur_height = size
            h = int((cur_height * des_widht) / cur_width)

            return int(des_widht), int(h)

        try:
            cur_img = Image.open(filename)

            new_w, new_h = get_resize_params(cur_img.size)
            if new_h > 0 and new_h > 0:
                cur_img_resized = cur_img.resize((new_w, new_h), Image.ANTIALIAS)   # TODO: Lidar com o warning de que ANTIALIAS está depreciado
                self.photoimage = ImageTk.PhotoImage(cur_img_resized)
            else:
                self.photoimage = ImageTk.PhotoImage(cur_img)

            self.canvas["image"] = self.photoimage
        except (FileNotFoundError, FileExistsError, Exception) as e:
            messagebox.showerror("Imagem", "Imagem não encontrada")

    def raise_above_all(self):
        self.root.attributes('-topmost', 1)
        self.root.attributes('-topmost', 0)


# ======================================================================================================================
if __name__ == '__main__':
    try:
        pytesseract.get_languages()             # Apenas para testar se o Tesseract está no PATH
    except pytesseract.pytesseract.TesseractNotFoundError:
        # TODO: ASK FOR FULL PATH OF TESSERACT
        # TODO: Arquivo ".config" para só termos que setar o path do tesseract uma única vez
        pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

    # -------------------------------------
    check_history_path()

    # -------------------------------------
    tk_root = tk.Tk()
    w = MainWindow(tk_root)
    tk_root.mainloop()
