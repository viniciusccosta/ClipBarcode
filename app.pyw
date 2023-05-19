# ======================================================================================================================
import pytesseract
import os
import json
import logging
import pyperclip

import tkinter as tk

from tkinter            import messagebox, filedialog
from PIL                import ImageGrab, ImageTk, Image, ImageDraw
from PIL.PngImagePlugin import PngImageFile
from PIL.Image          import Resampling                               # NOQA
from time               import time_ns
from pyzbar.pyzbar      import decode
from datetime_tools     import timens_to_datetime

from boleto             import new_boleto, BoletoInvalidoException

# ======================================================================================================================
RESULTS_PATH = "./history/results.json"
TYPES = {0: "Texto", 1: "Código de Barras", 2: "Nota Fiscal", 3: "QRCode"}

# ======================================================================================================================
class NoImageException(Exception):
    pass

# ======================================================================================================================
class MainWindow:
    def __init__(self, *args, **kwargs):
        # TODO: Uma forma de excluir os registros salvos.

        super().__init__(*args, **kwargs)

        self.root = tk.Tk()
        self.root.title("Clip Barcode")
        self.root.geometry("1280x720")
        self.root.iconbitmap("icon.ico")
        self.root.bind('<Configure>', self._configure_callback)

        self.last_width = 0
        self.last_height = 0

        # -------------------------------------
        # Frames:
        tk.Button(self.root, text="Ler Print", font=("Consolas", 16), command=self._lerprint_pressed).grid(pady=10)

        self.f1 = tk.Frame(self.root, )
        self.f1.grid(row=1, column=0, padx=5, pady=(0, 10), sticky="nswe")

        self.f2 = tk.Frame(self.root, )        
        self.f2.grid(row=1, column=1, columnspan=2, padx=5, pady=(0, 15), sticky="nswe")

        self.root.columnconfigure(index=1, weight=1)
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
        self.canvas = tk.Label(self.f2, bg="gray")
        self.canvas.grid(row=0, column=1, sticky="nsew")

        self.lbl_date = tk.StringVar()
        tk.Label(self.f2, textvariable=self.lbl_date, font=("Consolas", 16)).grid(row=2, column=1, sticky="nswe", pady=(15, 0))

        self.var_tipo = tk.StringVar()
        tk.Label(self.f2, textvariable=self.var_tipo, font=("Consolas", 16),).grid(row=3, column=1, sticky="nsew", pady=5)

        self.var_leitura = tk.StringVar()
        tk.Label(self.f2, text="Leitura:", font=("Consolas", 16), ).grid(row=4, sticky="nswe", pady=(15, 15))
        tk.Entry(self.f2, font=("Consolas", 16), state=tk.DISABLED, textvariable=self.var_leitura).grid(row=4, column=1, sticky="we")
        tk.Button(self.f2, text="Copiar", font=("Consolas", 12), command=self.copiar_leitura).grid(row=4, column=2, sticky="ew")

        self.f2.rowconfigure(index=0, weight=1)
        self.f2.columnconfigure(index=1, weight=1)

        # -------------------------------------
        self.cur_img = None
        self.cur_img_resized = None
        self.photoimage = None

        self._lerprint_pressed(init=True)

        # -------------------------------------

    def _fill_list(self, *args, **kwargs):
        self.listbox.delete(0, "end")

        with open("./history/results.json", 'r', encoding='UTF-8') as jsonfile:
            try:
                data = json.load(jsonfile)
                for k, v in data.items():
                    self.listbox.insert("0", f'{k}')
            except json.decoder.JSONDecodeError:
                pass    # TODO: Handle it

    def _lerprint_pressed(self, init:bool=False, *args, **kwargs):
        try:
            if ler_e_salvar():
                # Caso 1: Abriu o programa e tinha um print no "CTRL V" e Caso 3: Apertou "Ler Print" e tinha um print no "CTRL V"
                self._fill_list()
                self.listbox.selection_clear(0, tk.END)
                self.listbox.selection_set(0)
                self.listbox.event_generate("<<ListboxSelect>>")    # Simulando um "item selecionado"
            else:
                self.clear()

        except NoImageException:
            if not init:
                # Caso 4: Apertou "Ler Print", mas não tinha um print no "CTRL V"
                messagebox.showwarning("Sem Imagem", "Tire um print antes")

            # Caso 2: Abriu o programa, mas não tinha um print no "CTRL V" = Simplesmente não fazer nada

    def _item_selected(self, *args, **kwargs):
        index = self.listbox.curselection()

        if index:
            timens = self.listbox.get(index)
            cdb = retrieve_leitura(timens)

            self.update_frame_detail(timens, cdb)

    def _arrow_up(self, *args, **kwargs):
        self.selection = self.listbox.curselection()[0]

        if self.selection > 0:
            self.listbox.select_clear(self.selection)
            self.selection -= 1
            self.listbox.select_set(self.selection)
            self._item_selected(None)   # TODO: Não curti passar esse None...

    def _arrow_down(self, *args, **kwargs):
        self.selection = self.listbox.curselection()[0]

        if self.selection < self.listbox.size() - 1:
            self.listbox.select_clear(self.selection)
            self.selection += 1
            self.listbox.select_set(self.selection)
            self._item_selected(None)   # TODO: Não curti passar esse None...

    def _configure_callback(self, event, *args, **kwargs):
        if event.widget == self.canvas:                                                                 # Houve uma alteração no Canvas:
            if abs(event.width - self.last_width) > 50 or abs(event.height - self.last_height) > 50:    # Foi uma alteração de tamanho (usuário aumentou/diminui a janela ou simplesmente foi a inicialiação do GUI)
                if self.last_width != 0 and self.last_height != 0:                                      # Ignorando a inicialização do GUI
                    try:
                        res_img = self.resize_image(self.cur_img)
                        self.update_canvas(img_resized=res_img)
                    except NoImageException:
                        pass
                self.last_width  = event.width
                self.last_height = event.height

    def mainloop(self, *args, **kwargs):
        self.root.mainloop()

    def copiar_leitura(self, *args, **kwargs):
        """Envia para a Área de Transferência o que tiver no widget Leitura.
        """
        # TODO: Lidar com exceções
        pyperclip.copy(self.var_leitura.get())
        # TODO: Alterar texto do botão para "Copiado"

    def update_frame_detail(self, timens:str, cdb:dict, *args, **kwargs):
        """Atualiza todos os widgets presentes no frame "Detail"

        Args:
            timens (str): Identificação da leitura
            cdb (dict): Leitura
        """
        # TODO: Alterar texto dos botões para os originais

        if cdb:
            self.update_canvas(filename=f"./history/{timens}.png")
            self.update_date(cdb.get("data"))
            self.update_tipo(cdb.get("type"))
            self.update_leitura(cdb.get("cod_conv", ""))    # TODO: Alterar "cod_conv" para leitura, mas preserver a compatibilidade com as versões anteriores
        else:
            messagebox.showerror("EITA!", "Código de barras não localizado.")

    def update_tipo(self, value:str|None, *args, **kwargs):
        """Insere um valor no widget "Tipo".

        Args:
            value (str | None): Valor a ser inserido no widget
        """
        tipo = ""
        if value is not None:
            tipo = TYPES.get(value)
        self.var_tipo.set(tipo)

    def update_date(self, value:str, *args, **kwargs):
        """Insere um valor no widget "Date".

        Args:
            new_text (str): Valor a ser inserido no widget
        """
        self.lbl_date.set(value)

    def update_leitura(self, new_text:str, *args, **kwargs):
        """Insere um valor no widget "Leitura".

        Args:
            new_text (str): Valor a ser inserido no widget
        """
        self.var_leitura.set(new_text)

    def resize_image(self, img:PngImageFile, *args, **kwargs) -> Image.Image:
        """Realiza o redimensionamento de uma imagem, mantendo as suas proporções, conforme o tamanho do Canvas.

        Args:
            img (PngImageFile): Imagem a ser redimensionada

        Raises:
            NoImageException: Caso não haja uma imagem

        Returns:
            Image.Image: Imagem redimensionada.
        """
        if img:
            cur_width, cur_height   = img.size
            ratio                   = min(self.canvas.winfo_width() / cur_width, self.canvas.winfo_height() / cur_height)
            new_width               = int(cur_width * ratio)
            new_height              = int(cur_height * ratio)

            return img.resize((new_width, new_height), Resampling.LANCZOS)
        else:
            raise NoImageException

    def update_canvas(self, filename:str=None, img_resized:Image.Image=None, *args, **kwargs):
        """Insere uma nova imagem ao canvas:
            Ou através do nome do arquivo da imagem
            Ou através de um objeto Image.

        Args:
            filename (str, optional): Nome do arquivo de imagem da leitura salva em history/. Defaults to None.
            img_resized (Image.Image, optional): Imagem já redimensionada. Defaults to None.
        """
        self.canvas.update()

        if filename:
            try:
                self.cur_img         = Image.open(filename)
                self.cur_img_resized = self.resize_image(self.cur_img)          # Vamos redimensionar a imagem e deixar a função calcular automaticamente o tamanho
                self.photoimage      = ImageTk.PhotoImage(self.cur_img_resized)
                self.canvas["image"] = self.photoimage
            except (FileNotFoundError, FileExistsError, NoImageException):
                logging.error("Imagem não encontrada")
                messagebox.showerror("Imagem", "Imagem não encontrada")
            except ValueError:
                pass

        elif img_resized:
            self.cur_img_resized = img_resized
            self.photoimage      = ImageTk.PhotoImage(self.cur_img_resized)
            self.canvas["image"] = self.photoimage

        else:
            self.canvas["image"] = ""

    def raise_above_all(self, *args, **kwargs):
        """Coloca a janela do aplicativo por cima das outras janelas
        """
        self.root.attributes('-topmost', 1)
        self.root.attributes('-topmost', 0)

    def clear(self, *args, **kwargs):
        """Limpa todos os widgets.
        """
        self.listbox.selection_clear(0, tk.END)
        self.update_canvas()
        self.update_date("")
        self.update_tipo()
        self.update_leitura("")

# ======================================================================================================================
def check_history_path():
    """Verifica a existência do arquivo de resultados.
    Caso o arquivo não exista, ele será criado e com o nome padrão (results.json)
    """

    if not os.path.exists("./history"):
        os.mkdir("./history")
        logging.info("Pasta HISTORY criada com sucesso")
    if not os.path.exists(RESULTS_PATH):
        open(RESULTS_PATH, 'w').close()
        logging.info("Arquivo |results.json| criado com sucesso")

def check_config_path():
    """Verifica a existência do arquivo de configurações.
    Caso o arquivo não exista, ele será criado e com o nome padrão (.config)
    """

    if not os.path.exists(".config"):
        logging.warning("Arquivo de configuração inexistente, criando um novo:")
        with open(".config", "w", encoding="UTF-8") as file:
            json.dump({"TESSERACT_CMD": r'C:/Program Files/Tesseract-OCR/tesseract.exe'}, file)
            logging.info("Arquivo de configuração criado com sucesso")

def initial_config():
    """Realiza as configurações inicias da aplicação.

    - Configurações iniciais do logging
    - Conferência do arquivo de resultados
    - Conferência do arquivo de configurações
    - Configuração do Tesseract
    """
    logging.basicConfig(
        stream  = open(f'app.log', 'a', encoding='utf-8')   ,
        level   = logging.INFO, datefmt='%Y-%m-%d %H:%M:%S' ,
        format  = '%(asctime)s %(levelname)-8s %(message)s' ,
    )

    check_history_path()

    check_config_path()

    while True:
        try:
            with open(".config", "r", encoding="UTF-8") as file:
                configs = json.load(file)
                pytesseract.pytesseract.tesseract_cmd = configs.get("TESSERACT_CMD", "")

            pytesseract.get_languages()                                  # Apenas para testar se o Tesseract está no PATH
            break

        except pytesseract.pytesseract.TesseractNotFoundError:
            logging.error("Tesseract não encontrado")

            messagebox.showerror("EITA!", "Tesseract não encontrado!")
            tesseract_path = filedialog.askopenfilename(title="Onde está tesseract.exe ?")

            logging.info(f"Usuário informou |{tesseract_path}| como path para o Tesseract")

            if tesseract_path:
                with open(".config", "w", encoding="UTF-8") as file:
                    json.dump({"TESSERACT_CMD": tesseract_path}, file)
                    logging.info("Path do Tesseract salvo com sucesso")
            else:
                logging.error("Path inexistente, encerrando programa")
                exit(1)

def save_result(result: dict, img:PngImageFile):
    """Inclui uma leitura ao arquivo de resultados.

    Args:
        result (dict): Dicionário com os dados da leitura
            {
                "data": str ("%d/%m/%Y %H:%M:%S"),  
                "type": str,  
                "cod_lido": str,  
                "cod_conv": str,  
            }

        img (PngImageFile): Print em si
    """
    check_history_path()

    # Salvando a imagem primeiro:
    for k, v in result.items():
        img.save(f'./history/{k}.png')
        logging.info(f"{k}.png salvo com sucesso na pasta History")

    # Incluíndo a leitura no arquivo de resultados:
    lista_atual = {}
    with open("./history/results.json", 'r', encoding='UTF8') as jsonfile:
        try:
            lista_atual = json.load(jsonfile)
        except json.decoder.JSONDecodeError:
            pass    # Arquivo está vazio, apenas isso!

    with open("./history/results.json", 'w', encoding='UTF8') as jsonfile:
        for k, v in result.items():        
            lista_atual[k] = v
        json.dump(lista_atual, jsonfile, ensure_ascii=False)
        logging.info("Leiturada adicionada ao arquivo |results.json| com sucesso")

def ler_e_salvar():
    """A função mais importante do módulo.

    - Realiza a leitura da Área de Transferência
    - Realiza a leitura dos Códigos de Barra
    - Realiza OCR
    - Armazena a imagem no diretório específico
    - Solicita a inclusão do resultado da leitura no arquivo de resultados

    Raises:
        NoImageException: Caso não seja encontrado nenhuma imagem na Área de Transferência

    Returns:
        bool: True se tudo deu certo ou False caso contrário
    """
    # -----------------------------------------------------------
    timens = time_ns()
    agora = timens_to_datetime(timens)

    # -----------------------------------------------------------
    img = ImageGrab.grabclipboard()

    # -----------------------------------------------------------
    # Código de Barras ?
    try:
        results = decode(img)
    except (TypeError, Exception):
        raise NoImageException

    if len(results) >= 1:
        logging.info("Código de barras encontrado")

        if len(results) > 1:
            logging.error(f"Imagem só deve conter 1 código de barras e foram encontrados {len(results)}.")
            messagebox.showerror("Ops!", "O seu print só deve conter apenas 1 código de barras")
            return False

        d = results[0]
        text = d.data.decode("utf-8")

        if d.type == "I25":         # Boletos de Cobraça e Arrecadação
            logging.debug("Código de barrras do tipo I25 (boletos de cobrança e arrecadação)")
            try:
                boleto   = new_boleto(cod_barras=text)
                cod_conv = boleto.linha_digitavel
                m_type   = 1
            except BoletoInvalidoException:
                logging.error(f"Boleto Inválido: |{text}|")
                return False
        elif d.type == "CODE128":   # Código de Nota Fiscal
            logging.debug("Código de barras do tipo CODE128 (notas fiscais)")
            cod_conv = text
            m_type   = 2
        elif d.type == "QRCODE":
            logging.debug("Código de barras do tipo QRCODE")
            cod_conv = text
            m_type   = 3
        else:
            logging.warning(f"Código de barras do tipo {d.type} que ainda não é suportado")
            messagebox.showerror("Ainda não", "Código de barras não suportado")
            return False

        x, y, wi, h = d.rect.left, d.rect.top, d.rect.width, d.rect.height
        imgdraw = ImageDraw.Draw(img)
        imgdraw.rectangle(xy=(x, y, x+wi, y+h), outline="#FF0000", width=2,)
        logging.debug(f"Imagem encontrada em ({x},{y}) -> ({x+wi},{y+h})")

        result = {
            f"{timens}": {
                "data": agora.strftime("%d/%m/%Y %H:%M:%S"),
                "type": m_type,
                "cod_lido": text,
                "cod_conv": cod_conv    # TODO: Alterar "cod_conv" para leitura, mas preserver a compatibilidade com as versões anteriores
            }
        }

        save_result(result, img)

    # -----------------------------------------------------------
    # Linha Digitável:
    else:
        logging.info("Nenhum código de barras encontrado, programa tentará fazer OCR.")

        try:
            text = pytesseract.image_to_string(img, lang="por",).strip("\n")     # TODO: Tesseract está tendo dificuldades em ler números com mais de dois 0 seguidos
        except TypeError:
            raise NoImageException

        if len(text) > 1:
            logging.debug(f"OCR realizado com sucesso |{text}|")

            boleto = new_boleto(linha_digitavel=text)

            result = {
                f"{timens}": {
                    "data": agora.strftime("%d/%m/%Y %H:%M:%S"),
                    "type": 0,
                    "cod_lido": text,
                    "cod_conv": boleto.linha_digitavel if boleto else text    # TODO: Alterar "cod_conv" para leitura, mas preserver a compatibilidade com as versões anteriores # TODO: Instanciar_boleto pode retornar nulo...
                }
            }

            save_result(result, img)
        else:
            # messagebox.showwarning("Ops!", "Nada encontrado")
            logging.warning("OCR não encontrou nada")
            return False

    return True

def retrieve_leitura(timens: str) -> dict:
    """
    Retorna o resultado da leitura salvo no arquivos de resultados.

    Args:
        timens (str): Identificação da leitura, que no caso é a data e hora da leitura em milissegundos.

    Returns:
        dict: Leitura
    """
    check_history_path()

    with open("./history/results.json", 'r', encoding='UTF8') as jsonfile:
        try:
            data = json.load(jsonfile)
            return data.get(timens)

        except json.decoder.JSONDecodeError as e:
            pass  # Arquivo vazio, apenas isso!

# ======================================================================================================================
if __name__ == '__main__':
    initial_config()

    # -------------------------------------
    w = MainWindow()
    w.mainloop()
