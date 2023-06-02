# ======================================================================================================================
import pytesseract
import os
import logging
import pyperclip
import datetime

import tkinter as tk

from tkinter            import messagebox, filedialog
from PIL                import ImageGrab, ImageTk, Image, ImageDraw
from PIL.PngImagePlugin import PngImageFile
from PIL.Image          import Resampling                               # NOQA
from time               import time_ns
from pyzbar.pyzbar      import decode
from dotenv             import load_dotenv, set_key

from datetime_tools     import timens_to_datetime
from boleto             import new_boleto, BoletoInvalidoException

import database

# ======================================================================================================================
HISTORY_PATH = "./history"

# ======================================================================================================================
class NoImageException(Exception): pass

class LeituraFalhaException(Exception):
    def __init__(self, message):
        self.message = message

# ======================================================================================================================
class MainWindow:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.root = tk.Tk()
        self.root.title("Clip Barcode")
        self.root.geometry("1280x720")
        self.root.iconbitmap("icon.ico")
        self.root.bind('<Configure>', self._on_configure_callback)

        self.last_width = 0
        self.last_height = 0

        # -------------------------------------
        # Frames:
        tk.Button(self.root, text="Ler Print", font=("Consolas", 16), command=self._on_ler_print_click).grid(pady=10)

        self.f1 = tk.Frame(self.root, )
        self.f1.grid(row=1, column=0, padx=5, pady=(0, 10), sticky="nswe")
        self.root.columnconfigure(index=0, weight=0, minsize=410)

        self.f2 = tk.Frame(self.root)
        self.f2.grid(row=1, column=1, padx=5, pady=(0, 15), sticky="nswe")
        self.root.columnconfigure(index=1, weight=1)
        
        self.root.rowconfigure(index=1, weight=1)

        # -------------------------------------
        # List Frame:
        self.listbox = tk.Listbox(self.f1, font=("Consolas", 14), selectmode="SINGLE", activestyle=tk.NONE)
        self.listbox.bind('<<ListboxSelect>>', self._on_item_selected)
        self.listbox.bind("<Down>", self._on_arrow_down_click)
        self.listbox.bind("<Up>", self._on_arrow_up_click)
        self.listbox.bind("<Delete>", self._on_del_click)
        self.listbox.pack(fill="both", expand=True)

        self.leituras  = None
        self.cur_index = None
        self._fill_list()

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
        self.btn_copiar_leitura = tk.Button(self.f2, text="Copiar", font=("Consolas", 12), command=self.on_copiar_leitura_click)
        self.btn_copiar_leitura.grid(row=4, column=2, sticky="ew")

        self.var_descricao = tk.StringVar()
        tk.Label(self.f2, text="Descrição:", font=("Consolas", 16), ).grid(row=5, sticky="nsew", pady=(15,15))
        self.entry_descricao = tk.Entry(self.f2, font=("Consolas", 16), state=tk.DISABLED, textvariable=self.var_descricao)
        self.entry_descricao.grid(row=5, column=1, sticky="we")
        self.btn_descricao = tk.Button(self.f2, text="Editar", font=("Consolas", 12), command=self._on_btn_descricao_click)
        self.btn_descricao.grid(row=5, column=2, sticky="ew")
        
        self.f2.rowconfigure(index=0, weight=1)
        self.f2.columnconfigure(index=1, weight=1)

        # -------------------------------------
        self.cur_img         = None
        self.cur_img_resized = None
        self.photoimage      = None

        self._hot_read()
        # -------------------------------------

    def _fill_list(self, *args, **kwargs):
        """Método responsável por atualiza a lista com as leituras e atualiza o listbox.
        """
        self.leituras = database.get_leituras()
        
        self.listbox.delete(0, tk.END)
        
        for leitura in self.leituras:
            self.listbox.insert(tk.END, str(leitura))

    def _hot_read(self):
        """Método responsável por tentar realizar uma leitura logo na inicialização da aplicação.
        """
        try:
            leitura, img = realizar_leitura()
            salvar_leitura(leitura, img)
            
            self._fill_list()
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(0)
            self.listbox.event_generate("<<ListboxSelect>>")    # Simulando um "item selecionado"

        except Exception:
            pass
                
        self.listbox.focus()
    
    def _on_ler_print_click(self, *args, **kwargs):
        """Método responsável por lidar com o evento do Botão "Ler Print" ao ser pressionado.
        """
        try:
            leitura, img = realizar_leitura()
            salvar_leitura(leitura, img)
            
            self._fill_list()
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(0)
            self.listbox.event_generate("<<ListboxSelect>>")    # Simulando um "item selecionado"

        except NoImageException:
            messagebox.showwarning("Sem Imagem", "Tire um print antes")
        
        except LeituraFalhaException as e:
            messagebox.showwarning("Ops", e.message)
                
        self.listbox.focus()

    def _on_item_selected(self, *args, **kwargs):
        """Método responsável por lidar com os eventos de um item selecionado na Listbox.
        
        Esse evento também é chamado caso o TkInter entenda que nenhum item foi selecionado.
        """
        
        cur_selection = self.listbox.curselection()
        if cur_selection:
            selected_index = cur_selection[0]
            self.cur_index = selected_index
            leitura        = self.leituras[self.cur_index]
            
            self.update_frame_detail(leitura)
            
            self.btn_descricao.configure(text="Editar")
            self.entry_descricao.config(state="disabled")

    def _on_arrow_up_click(self, *args, **kwargs):
        """Método responsável por lidar com o evento do botão "Setinha Para Cima" pressionado no Lisbox
        """
        cur_selection = self.listbox.curselection()
        
        if cur_selection:
            self.selected_index = cur_selection[0]

            if self.selected_index > 0:
                self.listbox.select_clear(self.selected_index)
                self.selected_index -= 1
                self.listbox.select_set(self.selected_index)
                self.listbox.event_generate("<<ListboxSelect>>")    # Simulando um "item selecionado"

    def _on_arrow_down_click(self, *args, **kwargs):
        """Método responsável por lidar com o evento do botão "Setinha Para Baixo" pressionado no Lisbox
        """
        cur_selection = self.listbox.curselection()
        
        if cur_selection:
            self.selected_index = cur_selection[0]

            if self.selected_index < self.listbox.size() - 1:
                self.listbox.select_clear(self.selected_index)
                self.selected_index += 1
                self.listbox.select_set(self.selected_index)
                self.listbox.event_generate("<<ListboxSelect>>")    # Simulando um "item selecionado"

    def _on_del_click(self, *args, **kwargs):
        """Método responsável por lidar com o evento do botão "Delete" pressionado no Lisbox
        """
        ans = messagebox.askyesno(title="Excluir", message="Excluir registro ?")
        
        if ans:
            cur_selection = self.listbox.curselection()
            
            if cur_selection:
                selected_index = cur_selection[0]
                leitura        = self.leituras[selected_index]
                delete_leitura(leitura)
                self._fill_list()
                self.clear()
            else:
                messagebox.showerror("Erro", "Não foi possível excluir o registro")
                
    def on_copiar_leitura_click(self, *args, **kwargs):
        """Método responsável por lidar com o evento do botão "Copiar" pressionado.
        No caso, envia para a Área de Transferência o que tiver no widget Leitura.
        """
        pyperclip.copy(self.var_leitura.get())
        self.btn_copiar_leitura.config(text="Copiado")
        self.root.after(1000, lambda : self.btn_copiar_leitura.config(text="Copiar"))

    def _on_btn_descricao_click(self, *args, **kwargs):
        """
        Método responsável por lidar com o evento do botão "Editar/Salvar" pressionado.
        
        O mesmo botão tem 2 funções:
        1) Quando está com "Editar" e o usuário clicou, iremos habilitar os campos para que o usuário possa editar o EditText
        2) Quando está com "Salvar", iremos salvar as informações e desabilitar o EditText.
        """
        
        match (self.btn_descricao.cget("text")):
            case "Editar":
                self.btn_descricao.configure(text="Salvar")
                self.entry_descricao.config(state="normal")
                
            case "Salvar":
                self.btn_descricao.configure(text="Editar")
                self.entry_descricao.config(state="disabled")
                
                cur_selection = self.listbox.curselection()
                if cur_selection:
                    self.cur_index = cur_selection[0]
                
                leitura = self.leituras[self.cur_index]
                
                update_value(leitura, descricao=self.var_descricao.get())
                self._fill_list()
                # TODO: Selecionar algum item da listbox (o anterior, o próximo, o primeiro...)
    
    def _on_configure_callback(self, event, *args, **kwargs):
        """Callback para qualquer evento de configuração da Janela.
        Utilizaremos para saber se usuário alterou o tamanho da janela e assim recalcularmos o tamanho da imagem dentro do canvas.

        Args:
            event ():
        """
        if event.widget == self.canvas:                                                                 # Houve uma alteração no Canvas:
            if abs(event.width - self.last_width) > 50 or abs(event.height - self.last_height) > 50:    # Foi uma alteração de tamanho (usuário aumentou/diminui a janela ou simplesmente foi a inicialiação do GUI)
                if self.last_width != 0 and self.last_height != 0:                                      # Ignorando a inicialização do GUI
                    try:
                        res_img = self.resize_image_to_canvas(self.cur_img)
                        self.update_canvas(img_resized=res_img)
                    except NoImageException:
                        pass
                self.last_width  = event.width
                self.last_height = event.height
    
    def mainloop(self, *args, **kwargs):
        """Mainloop do TkInter
        """
        self.root.mainloop()

    def update_frame_detail(self, leitura: database.Leitura, *args, **kwargs):
        """Atualiza todos os widgets presentes no frame "Detail"

        Args:
            leitura(database.Leitura): Instância da class Leitura que contém todos os dados necessários para atualizar os widgets.
        """

        self.update_canvas(filename=os.path.join(HISTORY_PATH, f"{leitura.mili}.png"))
        self.update_widget_data(leitura.data)
        self.update_tipo(leitura.get_type_display())
        self.update_widget_leitura(leitura.cod_conv)
        self.update_widget_descricao(leitura.descricao)

    def update_tipo(self, tipo:str, *args, **kwargs):
        """Insere um valor no widget "Tipo".

        Args:
            tipo (str): Valor a ser inserido no widget
        """
        self.var_tipo.set(tipo)

    def update_widget_data(self, value:datetime.datetime=None, *args, **kwargs):
        """Insere um valor no widget "Date".

        Args:
            new_text (str): Valor a ser inserido no widget
        """
        if value:
            self.lbl_date.set(value.strftime("%d/%m/%Y %H:%M:%S"))
        else:
            self.lbl_date.set('')

    def update_widget_leitura(self, new_text:str, *args, **kwargs):
        """Insere um valor no widget "Leitura".

        Args:
            new_text (str): Valor a ser inserido no widget
        """
        self.var_leitura.set(new_text)

    def update_widget_descricao(self, new_text:str, *args, **kwargs):
        """Insere um valor no widget "Descrição".

        Args:
            new_text (str): Valor a ser inserido no widget
        """
        self.var_descricao.set(new_text if new_text else "")

    def resize_image_to_canvas(self, img:PngImageFile, *args, **kwargs) -> Image.Image:
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
                self.cur_img_resized = self.resize_image_to_canvas(self.cur_img)          # Vamos redimensionar a imagem e deixar a função calcular automaticamente o tamanho
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

    def clear(self, *args, **kwargs):
        """Limpa todos os widgets.
        """
        self.listbox.selection_clear(0, tk.END)
        self.update_canvas()
        self.update_widget_data()
        self.update_tipo('')
        self.update_widget_leitura('')

# ======================================================================================================================
def initial_config():
    """Realiza as configurações inicias da aplicação.

    - Logging
    - SQLite
    - Diretório de Imagens
    - Tesseract
    - Variáveis de Ambiente
    """

    # ------------------------------------------
    load_dotenv()
    
    # ------------------------------------------
    # Logging:
    logging.basicConfig(
        stream  = open(f'.log', 'a', encoding='utf-8')   ,
        level   = logging.INFO, datefmt='%Y-%m-%d %H:%M:%S' ,
        format  = '%(asctime)s %(levelname)-8s %(message)s' ,
    )

    # ------------------------------------------
    # Banco de Dados:
    json_path = os.path.join(HISTORY_PATH, "results.json")
    
    database.create_tables()
    try:
        database.from_json_to_sqlite(json_path)
        os.remove(json_path)    # Excluindo json após transferir as leituras para DB
    except FileNotFoundError:
        pass
    except Exception as e:
        print(e)
    
    # ------------------------------------------
    # Diretório de Imagens:
    if not os.path.exists(HISTORY_PATH):
        os.mkdir(HISTORY_PATH)
        logging.info("Pasta HISTORY criada com sucesso")

    # ------------------------------------------
    # Tesseract:  
    while True:
        try:
            pytesseract.pytesseract.tesseract_cmd = os.environ.get('TESSERACT_CMD', r'C:/Program Files/Tesseract-OCR/tesseract.exe')
            pytesseract.get_languages()                                  # Apenas para testar se o Tesseract está no PATH
            break
        except pytesseract.pytesseract.TesseractNotFoundError:
            pass
        
        logging.error("Tesseract não encontrado")
        messagebox.showerror("Erro", "Tesseract não encontrado!")

        tesseract_path = filedialog.askopenfilename(title="Onde está tesseract.exe ?")
        logging.info(f"Usuário informou |{tesseract_path}| como path para o Tesseract")

        if tesseract_path:
            set_key('.env', 'TESSERACT_CMD', tesseract_path)
            logging.info("Path do Tesseract salvo com sucesso")
        else:
            logging.error("Encerrando programa pois o usuário não informou um path!")
            exit(1)

def salvar_leitura(leitura: database.Leitura, img:PngImageFile):
    """Salva a leitura no banco de dados juntamente com o print.

    Args:
        result (database.Leitura): Instância da classe Leitura com os dados da leitura
        img (PngImageFile): Print em si
    """
    
    # Salvando a imagem:
    img.save(os.path.join(HISTORY_PATH, f"{leitura.mili}.png"))
    logging.info(f"{leitura.mili}.png salvo com sucesso na pasta History")

    # Incluíndo a leitura no arquivo de resultados:
    database.create_leitura(leitura)

def update_value(leitura: database.Leitura, **kwargs):
    """Faz uma requisição ao banco de dados para atualizar determinada leitura.

    Args:
        leitura (database.Leitura):
        **kwargs (dict): Dicionário com os campos e valores a serem atualizados
    """
    database.update_leitura(leitura.id, **kwargs)

def delete_leitura(leitura: database.Leitura):
    """Faz a exclusão do print do diretório de imagens e faz uma requisição ao banco de dados para a exclusão da leitura.

    Args:
        leitura (database.Leitura): 
    """
    os.remove(os.path.join(HISTORY_PATH, f"{leitura.mili}.png"))
    database.delete_leitura(leitura)

def realizar_leitura():
    """Faz a leitura da imagem que estiver na Área de Transferência.

    - Procura inicialmente por um Códigos de Barra
    - Caso não identifique nenhum código de barras, realiza OCR

    Raises:
        NoImageException: Caso não seja encontrado nenhuma imagem na Área de Transferência
        LeituraFalhaException: Caso qualquer problema ocorra ao realizar a leitura
    """
    
    # -----------------------------------------------------------
    timens = time_ns()
    agora  = timens_to_datetime(timens)

    # -----------------------------------------------------------
    img = ImageGrab.grabclipboard()

    # -----------------------------------------------------------
    # Código de Barras:
    try:
        results = decode(img)
    except (TypeError, Exception):
        raise NoImageException
    
    if len(results) >= 1:
        logging.info("Código de barras encontrado")

        if len(results) > 1:
            texto = "O seu print só deve conter apenas 1 código de barras"
            logging.error(texto)
            raise LeituraFalhaException(texto)

        d = results[0]
        text = d.data.decode("utf-8")

        match(d.type):
            case "I25":         # Boletos de Cobraça e Arrecadação
                logging.debug("Código de barrras do tipo I25 (boletos de cobrança e arrecadação)")
                try:
                    boleto   = new_boleto(cod_barras=text)
                    cod_conv = boleto.linha_digitavel
                    m_type   = 1
                except BoletoInvalidoException:
                    texto = f"Boleto Inválido: |{text}|"
                    logging.error(texto)
                    raise LeituraFalhaException(texto)
            case "CODE128":     # Código de Nota Fiscal
                logging.debug("Código de barras do tipo CODE128 (notas fiscais)")
                cod_conv = text
                m_type   = 2
            case "QRCODE":      # QRCode
                logging.debug("Código de barras do tipo QRCODE")
                cod_conv = text
                m_type   = 3
            case _:             # Nenhum dos tipos anteriores
                texto = f"O código de barras do tipo {d.type} não é suportado"
                logging.warning(texto)
                raise LeituraFalhaException(texto)

        x, y, wi, h = d.rect.left, d.rect.top, d.rect.width, d.rect.height
        imgdraw = ImageDraw.Draw(img)
        imgdraw.rectangle(xy=(x, y, x+wi, y+h), outline="#FF0000", width=2,)
        logging.debug(f"Imagem encontrada em ({x},{y}) -> ({x+wi},{y+h})")

        leitura = database.Leitura (
            mili     = f"{timens}",
            data     = agora,
            type     = m_type,
            cod_lido = text,
            cod_conv = cod_conv,
        )

        return(leitura, img)

    # -----------------------------------------------------------
    # OCR:
    else:
        logging.info("Nenhum código de barras encontrado, programa tentará fazer OCR.")

        try:
            text = pytesseract.image_to_string(img, lang="por",).strip("\n")     # TODO: Tesseract está tendo dificuldades em ler números com mais de dois 0 seguidos
        except TypeError:
            raise NoImageException
        
        if len(text) <= 0:
            texto = "OCR não encontrou nada"
            logging.warning(texto)
            raise LeituraFalhaException(texto)

        logging.debug(f"OCR realizado com sucesso |{text}|")

        boleto = new_boleto(linha_digitavel=text)

        leitura = database.Leitura(
            mili     = f"{timens}",
            data     = agora,
            type     = 0,
            cod_lido = text,
            cod_conv = boleto.linha_digitavel if boleto else text
        )

        return(leitura, img)

# ======================================================================================================================
if __name__ == '__main__':
    initial_config()

    # -------------------------------------
    w = MainWindow()
    w.mainloop()
