# Locale (ttkbootstrap)
try:
    import locale
    import os

    os.environ["LC_ALL"] = "en_US.UTF-8"
    locale.setlocale(locale.LC_ALL, "")
except locale.Error as e:
    print("Failed to set locale to environment's LC_ALL")
    print(f"Error: {e}")
except Exception as e:
    print("Failed to set locale")
    print(f"Error: {e}")

# Tesseract:
try:
    import sys

    if getattr(sys, "frozen", False):
        tessdata_path = os.path.join(sys._MEIPASS, "tessdata")
        os.environ["TESSDATA_PREFIX"] = tessdata_path
except Exception as e:
    print(f"Failed to set TESSDATA_PREFIX: {e}")

# Imports:
import datetime
import logging
import queue
import threading
import tkinter as tk
from time import time_ns

import pyperclip
import ttkbootstrap as ttk
from PIL import Image, ImageDraw, ImageGrab, ImageTk
from PIL.Image import Resampling
from PIL.PngImagePlugin import PngImageFile
from pyzbar.pyzbar import Decoded, decode
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.localization.msgcat import MessageCatalog

from clipbarcode.boleto import BoletoInvalidoException, new_boleto
from clipbarcode.config import initialize_system
from clipbarcode.constants import CURRENT_VERSION, HISTORY_PATH, LABEL_FONTNAME
from clipbarcode.datetime_tools import timens_to_datetime
from clipbarcode.exceptions import (
    DuplicatedLeituraException,
    LeituraFalhaException,
    NoImageException,
)
from clipbarcode.models import AppSettings, Leitura
from clipbarcode.toplevels import AjudaToplevel, SobreToplevel
from clipbarcode.update import check_for_updates
from clipbarcode.utils import resource_path

logger = logging.getLogger(__name__)


# Main Window:
class App(ttk.Window):
    def __init__(self, themename="darkly", alpha=0.99, *args, **kwargs):
        super().__init__(themename=themename, alpha=alpha, *args, **kwargs)

        self.title(f"Clip Barcode {CURRENT_VERSION}")
        self.geometry("1280x720")
        self.iconbitmap(resource_path("assets/icon.png"))
        self.place_window_center()
        self.position_center()

        self.last_width = 0
        self.last_height = 0

        # self.bind("<Destroy>", self._on_close)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # TODO: SystemTray onde ao clicar no ícone ativa/desativa a leitura automática

        # TODO: create_widget function

        # -------------------------------------
        menubar = ttk.Menu()
        self.config(menu=menubar)

        # Themes:
        theme_menu = ttk.Menu()
        themes = [
            "darkly",
            "yeti",
            "superhero",
            "vapor",
            "cosmo",
            "journal",
            "sandstone",
        ]
        avaiable_themes = [t for t in self.style.theme_names() if t in themes]
        for theme_name in sorted(avaiable_themes):
            theme_menu.add_command(
                label=theme_name,
                command=lambda t=theme_name: self.change_theme(t),
            )

        menubar.add_cascade(label="Temas", menu=theme_menu)

        # TODO: Configurações:
        # TODO: Ativar/Desativar leitura automática

        # Ajuda:
        help_menu = ttk.Menu()
        help_menu.add_command(label="Ajuda", command=self._on_ajuda_click)
        help_menu.add_separator()
        help_menu.add_command(label="Sobre", command=self._on_sobre_click)
        menubar.add_cascade(label="Ajuda", menu=help_menu)

        # -------------------------------------
        # Frames:
        self.btn_ler_print = ttk.Button(
            self, text="Ler Print", command=self._on_ler_print_click
        )
        self.btn_ler_print.grid(
            row=0, column=0, padx=(10, 5), pady=(20, 10), sticky="nsew"
        )

        self.f1 = ttk.Frame(self)
        self.f1.grid(row=1, column=0, padx=(10, 5), pady=(10, 10), sticky="nswe")
        self.columnconfigure(index=0, weight=0, minsize=410)

        self.f2 = ttk.Frame(self)
        self.f2.grid(row=1, column=1, padx=(5, 10), pady=(0, 10), sticky="nswe")
        self.columnconfigure(index=1, weight=1)

        self.rowconfigure(index=1, weight=1)

        # -------------------------------------
        # List Frame:
        self.listbox = tk.Listbox(
            self.f1, font=(LABEL_FONTNAME, 16), selectmode="SINGLE", activestyle=tk.NONE
        )
        self.listbox.bind("<<ListboxSelect>>", self._on_item_selected)
        self.listbox.bind("<Down>", self._on_arrow_down_click)
        self.listbox.bind("<Up>", self._on_arrow_up_click)
        self.listbox.bind("<Delete>", self._on_del_click)
        self.listbox.pack(fill="both", expand=True)

        self.leituras = None
        self.cur_index = None
        self.update_listbox_with_leituras()

        # -------------------------------------
        # Detail Frame:
        lf_canvas = ttk.Labelframe(self.f2, text="Imagem", bootstyle="primary")
        lf_canvas.grid(row=0, column=0, sticky="nsew", pady=(0, 5))

        self.canvas = ttk.Label(lf_canvas)
        self.canvas.pack(fill="both", expand="true", padx=10, pady=10)

        # Data:
        self.lbl_date = tk.StringVar()
        tk.Label(
            self.f2,
            textvariable=self.lbl_date,
            font=(LABEL_FONTNAME, 16),
        ).grid(row=1, column=0, sticky="nswe", pady=(5, 5))

        # Tipo:
        self.var_tipo = tk.StringVar()
        tk.Label(
            self.f2,
            textvariable=self.var_tipo,
            font=(LABEL_FONTNAME, 16),
        ).grid(row=2, column=0, sticky="nsew", pady=(5, 5))

        # Leitura:
        lf_leitura = ttk.Labelframe(self.f2, text="Leitura", bootstyle="primary")
        lf_leitura.grid(row=3, column=0, sticky="nsew", pady=(5, 5))

        self.var_leitura = tk.StringVar()

        self.entry_leitura = ttk.Entry(
            lf_leitura,
            font=(LABEL_FONTNAME, 16),
            state="readonly",
            textvariable=self.var_leitura,
        )
        self.entry_leitura.grid(row=0, column=0, sticky="we", pady=10, padx=(10, 5))

        self.btn_copiar_leitura = ttk.Button(
            lf_leitura, text="Copiar", command=self.on_copiar_leitura_click, width=7
        )
        self.btn_copiar_leitura.grid(
            row=0, column=1, sticky="ew", pady=10, padx=(5, 10)
        )

        lf_leitura.columnconfigure(0, weight=1)

        # Descrição:
        lf_descricao = ttk.Labelframe(self.f2, text="Descrição", bootstyle="primary")
        lf_descricao.grid(row=4, column=0, sticky="nsew", pady=(5, 0))

        self.var_descricao = tk.StringVar()

        self.entry_descricao = ttk.Entry(
            lf_descricao,
            font=(LABEL_FONTNAME, 16),
            state="readonly",
            textvariable=self.var_descricao,
        )
        self.entry_descricao.grid(row=0, column=0, sticky="we", pady=10, padx=(10, 5))
        self.entry_descricao.bind("<Return>", self.salvar_descricao)

        self.btn_descricao = ttk.Button(
            lf_descricao, text="Editar", command=self._on_btn_descricao_click, width=7
        )
        self.btn_descricao.grid(row=0, column=1, sticky="ew", pady=10, padx=(5, 10))

        lf_descricao.columnconfigure(0, weight=1)

        # Frame:
        self.f2.rowconfigure(index=0, weight=1)
        self.f2.columnconfigure(index=0, weight=1)

        # -------------------------------------
        self.bind("<Configure>", self._on_configure_callback)

        # -------------------------------------
        self.cur_img = None
        self.cur_img_resized = None
        self.photoimage = None

        # Leitura automática a cada X segundos:
        self.clipboard_thread_running = True
        self.task_queue = queue.Queue()

        self.clipboard_thread = threading.Thread(
            target=self.watch_clipboard,
            daemon=True,
        )
        self.clipboard_thread.start()

        self.after(100, self._process_queue)

        # -------------------------------------

    def change_theme(self, themename, *args, **kwargs):
        self.style.theme_use(themename)
        AppSettings.set_settings("themename", themename)

        self.style.configure(
            "TButton",
            font=(LABEL_FONTNAME, 12),
        )

        self.style.configure(
            "TLabelframe.Label",
            font=(LABEL_FONTNAME, 10),
        )

    def _on_sobre_click(self, *args, **kwargs):
        SobreToplevel(title="Sobre", resizable=(False, False), alpha=0.99, topmost=True)

    def _on_ajuda_click(self, *args, **kwargs):
        AjudaToplevel(title="Ajuda", minsize=(600, 600), alpha=0.99, topmost=True)

    def update_listbox_with_leituras(self, *args, **kwargs):
        """Método responsável por atualiza a lista com as leituras e atualiza o listbox."""

        # TODO: Pesado para fazer na thread principal ? Já receber a lista de leituras como argumento
        self.leituras = Leitura.get_leituras()

        self.listbox.delete(0, tk.END)

        for leitura in self.leituras:
            self.listbox.insert(tk.END, str(leitura))

    def update_listbox_and_selection(self, index: int):
        self.update_listbox_with_leituras()

        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(index)
        self.listbox.event_generate("<<ListboxSelect>>")

        # self.listbox.update()
        # self.update()
        # self.listbox.focus()

    def read_clipboard(self):
        """
        Função responsável por realizar a leitura de um código de barras.

        - Faz a leitura da imagem que estiver na Área de Transferência
        - Verifica se a leitura já existe no banco de dados
        - Caso não exista, salva a leitura no banco de dados
        - Desenha um retângulo em volta do código de barras
        - Atualiza a imagem no canvas
        - Atualiza os widgets com os dados da leitura
        """

        def capture_and_decode():
            """Faz a leitura da imagem que estiver na Área de Transferência.

            - Procura inicialmente por um Códigos de Barra
            - Caso não identifique nenhum código de barras, realiza OCR

            Raises:
                NoImageException: Caso não seja encontrado nenhuma imagem na Área de Transferência
                LeituraFalhaException: Caso qualquer problema ocorra ao realizar a leitura
            """

            # Imagem da Área de Transferência:
            img = ImageGrab.grabclipboard()

            # Código de Barras:
            try:
                results = decode(img)
            except (TypeError, Exception):
                raise NoImageException

            # Validando o número de códigos de barras encontrados:
            if len(results) == 0:
                texto = "Nenhum código de barras encontrado"
                logger.warning(texto)
                raise NoImageException(texto)

            # Validando o número de códigos de barras encontrados:
            if len(results) > 1:
                texto = "O seu print só deve conter apenas 1 código de barras"
                logger.warning(texto)
                raise LeituraFalhaException(texto)

            # Pegando o primeiro (único) resultado:
            decoded_data = results[0]

            # Result
            return img, decoded_data

        def create_leitura(decoded_data):
            # Texto:
            text = decoded_data.data.decode("utf-8")

            # Verificando o tipo do código de barras:
            match (decoded_data.type):
                case "I25":  # Boletos de Cobraça e Arrecadação
                    try:
                        boleto = new_boleto(cod_barras=text)
                        cod_conv = boleto.linha_digitavel
                        m_type = 1
                    except BoletoInvalidoException:
                        texto = f"Boleto Inválido: |{text}|"
                        logger.warning(texto)
                        raise LeituraFalhaException(texto)
                case "CODE128":  # Código de Nota Fiscal
                    cod_conv = text
                    m_type = 2
                case "QRCODE":  # QRCode
                    cod_conv = text
                    m_type = 3
                case _:  # Nenhum dos tipos anteriores
                    logger.warning(texto)
                    raise LeituraFalhaException(texto)

            # Criando a leitura:
            timens = time_ns()
            leitura = Leitura(
                mili=f"{timens}",
                data=timens_to_datetime(timens),
                type=m_type,
                cod_lido=text,
                cod_conv=cod_conv,
            )

            # Retornando a leitura:
            return leitura

        def highlight_rectangle(img: PngImageFile, decoded_data: Decoded):
            # Desenho do retângulo:
            x, y, wi, h = (
                decoded_data.rect.left,
                decoded_data.rect.top,
                decoded_data.rect.width,
                decoded_data.rect.height,
            )
            imgdraw = ImageDraw.Draw(img)
            imgdraw.rectangle(
                xy=(x, y, x + wi, y + h),
                outline="#FF0000",
                width=2,
            )
            logger.debug(f"Desenhando em ({x},{y}) -> ({x+wi},{y+h})")

            return img

        def store_image(leitura: Leitura, img: PngImageFile):
            """Salva a leitura no banco de dados juntamente com o print.

            Args:
                result (Leitura): Instância da classe Leitura com os dados da leitura
                img (PngImageFile): Print em si
            """

            # Salvando a imagem:
            img.save(os.path.join(HISTORY_PATH, f"{leitura.mili}.png"))
            logger.info(f"{leitura.mili}.png salvo com sucesso na pasta History")

            # Incluíndo a leitura no arquivo de resultados:
            Leitura.create_leitura(leitura)

        # Lendo a imagem da Área de Transferência:
        captured_image, decoded_data = capture_and_decode()

        # Criando a leitura:
        nova_leitura = create_leitura(decoded_data)

        # Desenhando o retângulo na imagem:
        highlighted_image = highlight_rectangle(captured_image, decoded_data)

        # Verificando se a leitura já existe:
        if old_leitura := Leitura.get_by_code(nova_leitura.cod_lido):
            raise DuplicatedLeituraException(
                message="Código de barras já lido anteriormente",
                leitura=old_leitura,
            )

        # Salvando a leitura:
        store_image(nova_leitura, highlighted_image)

        # Retornando a leitura:
        return nova_leitura

    def _on_ler_print_click(self, *args, **kwargs):
        """Método responsável por lidar com o evento do Botão "Ler Print" ao ser pressionado."""

        # TODO: O ideal seria fazer isso em uma thread separada para não travar a interface.

        try:
            self.read_clipboard()
            self.listbox.focus()
        except NoImageException as e:
            Messagebox.show_warning(title="Sem Imagem", message="Tire um print antes")
        except LeituraFalhaException as e:
            Messagebox.show_warning(title="Ops", message=e.message)
        except DuplicatedLeituraException as e:
            Messagebox.show_warning(
                title="Duplicado", message=f"Código de barras já lido."
            )

            # TODO: Algum lugar sobreescreveu o self.leituras por um objeto Leitura "ValueError: <Leitura: 3): Version 4 QR Code, up to 50 char> is not in list"
            index = self.leituras.index(e.leitura)
            self.update_listbox_and_selection(index)
        except Exception as e:
            logger.error(f"Erro ao ler a Área de Transferência: {e}")
            logger.exception(e)
            Messagebox.show_error(
                title="Erro", message=f"Erro ao ler a Área de Transferência"
            )

    def _on_item_selected(self, *args, **kwargs):
        """Método responsável por lidar com os eventos de um item selecionado na Listbox.

        Esse evento também é chamado caso o TkInter entenda que nenhum item foi selecionado.
        """

        cur_selection = self.listbox.curselection()
        if cur_selection:
            selected_index = cur_selection[0]
            self.cur_index = selected_index
            leitura = self.leituras[self.cur_index]

            self.update_frame_detail(leitura)

            self.btn_descricao.configure(text="Editar")
            self.entry_descricao.config(state="readonly")

    def _on_arrow_up_click(self, *args, **kwargs):
        """Método responsável por lidar com o evento do botão "Setinha Para Cima" pressionado no Lisbox"""
        cur_selection = self.listbox.curselection()

        if cur_selection:
            self.selected_index = cur_selection[0]

            if self.selected_index > 0:
                self.listbox.select_clear(self.selected_index)
                self.selected_index -= 1
                self.listbox.select_set(self.selected_index)
                self.listbox.event_generate(
                    "<<ListboxSelect>>"
                )  # Simulando um "item selecionado"

    def _on_arrow_down_click(self, *args, **kwargs):
        """Método responsável por lidar com o evento do botão "Setinha Para Baixo" pressionado no Lisbox"""
        cur_selection = self.listbox.curselection()

        if cur_selection:
            self.selected_index = cur_selection[0]

            if self.selected_index < self.listbox.size() - 1:
                self.listbox.select_clear(self.selected_index)
                self.selected_index += 1
                self.listbox.select_set(self.selected_index)
                self.listbox.event_generate(
                    "<<ListboxSelect>>"
                )  # Simulando um "item selecionado"

    def _on_del_click(self, *args, **kwargs):
        """Método responsável por lidar com o evento do botão "Delete" pressionado no Lisbox"""
        ans = Messagebox.yesno(title="Excluir", message="Excluir registro ?")

        if ans == MessageCatalog.translate("Yes"):
            cur_selection = self.listbox.curselection()

            if cur_selection:
                selected_index = cur_selection[0]
                leitura = self.leituras[selected_index]

                # TODO: Pathlib
                os.remove(os.path.join(HISTORY_PATH, f"{leitura.mili}.png"))
                Leitura.delete_leitura(leitura)

                self.update_listbox_with_leituras()
                self.reset_widgets()
            else:
                Messagebox.show_error(
                    title="Erro", message="Não foi possível excluir o registro"
                )

    def on_copiar_leitura_click(self, *args, **kwargs):
        """Método responsável por lidar com o evento do botão "Copiar" pressionado.
        No caso, envia para a Área de Transferência o que tiver no widget Leitura.
        """
        pyperclip.copy(self.var_leitura.get())
        self.btn_copiar_leitura.config(text="Copiado", bootstyle="success")
        self.after(
            1000,
            lambda: self.btn_copiar_leitura.config(text="Copiar", bootstyle="default"),
        )

    def _on_btn_descricao_click(self, *args, **kwargs):
        """
        Método responsável por lidar com o evento do botão "Editar/Salvar" pressionado.

        O mesmo botão tem 2 funções:
        1) Quando está com "Editar" e o usuário clicou, iremos habilitar os campos para que o usuário possa editar o EditText
        2) Quando está com "Salvar", iremos salvar as informações e desabilitar o EditText.
        """

        match (self.btn_descricao.cget("text")):
            case "Editar":
                self.btn_descricao.configure(text="Salvar", bootstyle="success")
                self.entry_descricao.config(state="normal")

            case "Salvar":
                self.salvar_descricao()

    def _on_configure_callback(self, event, *args, **kwargs):
        """Callback para qualquer evento de configuração da Janela.
        Utilizaremos para saber se usuário alterou o tamanho da janela e assim recalcularmos o tamanho da imagem dentro do canvas.

        Args:
            event ():
        """
        if event.widget == self.canvas:  # Houve uma alteração no Canvas:
            if (
                abs(event.width - self.last_width) > 50
                or abs(event.height - self.last_height) > 50
            ):  # Foi uma alteração de tamanho (usuário aumentou/diminui a janela ou simplesmente foi a inicialiação do GUI)
                if (
                    self.last_width != 0 and self.last_height != 0
                ):  # Ignorando a inicialização do GUI
                    try:
                        res_img = self.resize_image_to_canvas(self.cur_img)
                        self.update_canvas(img_resized=res_img)
                    except NoImageException:
                        pass
                self.last_width = event.width
                self.last_height = event.height

    def salvar_descricao(self, *args, **kwargs):
        self.btn_descricao.configure(text="Editar", bootstyle="default")
        self.entry_descricao.config(state="readonly")

        cur_selection = self.listbox.curselection()
        if cur_selection:
            self.cur_index = cur_selection[0]

        leitura = self.leituras[self.cur_index]

        Leitura.update_leitura(leitura, descricao=self.var_descricao.get())
        self.update_listbox_with_leituras()
        # TODO: Selecionar algum item da listbox (o anterior, o próximo, o primeiro...)

    def update_frame_detail(self, leitura: Leitura, *args, **kwargs):
        """Atualiza todos os widgets presentes no frame "Detail"

        Args:
            leitura(Leitura): Instância da class Leitura que contém todos os dados necessários para atualizar os widgets.
        """

        self.update_canvas(filename=os.path.join(HISTORY_PATH, f"{leitura.mili}.png"))
        self.update_widget_data(leitura.data)
        self.update_tipo(leitura.get_type_display())
        self.update_widget_leitura(leitura.cod_conv)
        self.update_widget_descricao(leitura.descricao)

    def update_tipo(self, tipo: str, *args, **kwargs):
        """Insere um valor no widget "Tipo".

        Args:
            tipo (str): Valor a ser inserido no widget
        """
        self.var_tipo.set(tipo)

    def update_widget_data(self, value: datetime.datetime = None, *args, **kwargs):
        """Insere um valor no widget "Date".

        Args:
            new_text (str): Valor a ser inserido no widget
        """
        if value:
            self.lbl_date.set(value.strftime("%d/%m/%Y %H:%M:%S"))
        else:
            self.lbl_date.set("")

    def update_widget_leitura(self, new_text: str, *args, **kwargs):
        """Insere um valor no widget "Leitura".

        Args:
            new_text (str): Valor a ser inserido no widget
        """
        self.var_leitura.set(new_text)

    def update_widget_descricao(self, new_text: str, *args, **kwargs):
        """Insere um valor no widget "Descrição".

        Args:
            new_text (str): Valor a ser inserido no widget
        """
        self.var_descricao.set(new_text if new_text else "")

    def resize_image_to_canvas(self, img: PngImageFile, *args, **kwargs) -> Image.Image:
        """Realiza o redimensionamento de uma imagem, mantendo as suas proporções, conforme o tamanho do Canvas.

        Args:
            img (PngImageFile): Imagem a ser redimensionada

        Raises:
            NoImageException: Caso não haja uma imagem

        Returns:
            Image.Image: Imagem redimensionada.
        """
        if img:
            cur_width, cur_height = img.size
            ratio = min(
                self.canvas.winfo_width() / cur_width,
                self.canvas.winfo_height() / cur_height,
            )
            new_width = int(cur_width * ratio)
            new_height = int(cur_height * ratio)

            return img.resize((new_width, new_height), Resampling.LANCZOS)
        else:
            raise NoImageException

    def update_canvas(
        self, filename: str = None, img_resized: Image.Image = None, *args, **kwargs
    ):
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
                self.cur_img = Image.open(filename)
                self.cur_img_resized = self.resize_image_to_canvas(
                    self.cur_img
                )  # Vamos redimensionar a imagem e deixar a função calcular automaticamente o tamanho
                self.photoimage = ImageTk.PhotoImage(self.cur_img_resized)
                self.canvas["image"] = self.photoimage
            except (FileNotFoundError, FileExistsError, NoImageException):
                logger.warning("Imagem não encontrada")
                Messagebox.show_error(title="Imagem", message="Imagem não encontrada")
            except ValueError:
                pass

        elif img_resized:
            self.cur_img_resized = img_resized
            self.photoimage = ImageTk.PhotoImage(self.cur_img_resized)
            self.canvas["image"] = self.photoimage

        else:
            self.canvas["image"] = ""

    def reset_widgets(self, *args, **kwargs):
        """Limpa todos os widgets."""
        self.listbox.selection_clear(0, tk.END)
        self.update_canvas()
        self.update_widget_data()
        self.update_tipo("")
        self.update_widget_leitura("")

    def _process_queue(self):
        """Processa a fila de tarefas.

        Essa função é chamada a cada 100ms e verifica se há tarefas na fila.
        Se houver, executa a tarefa e remove da fila.
        """

        while not self.task_queue.empty():
            task, args = self.task_queue.get()
            task(*args)

        # Schedule the next check
        # TODO: Usar uma variável para o tempo de espera
        self.after(500, self._process_queue)

    def watch_clipboard(self):
        """Método responsável por monitorar a Área de Transferência.

        Caso o usuário copie algo, iremos tentar fazer a leitura automaticamente.
        Caso não seja possível, iremos ignorar o erro e continuar monitorando a Área de Transferência.
        """

        # TODO: Fornecer a possibilidade de ativar/desativar essa função
        # TODO: No automático vai copiar o código de barras lido para a Área de Transferência e no manual não ?

        while self.clipboard_thread_running:
            leitura = None

            # Tenta ler a Área de Transferência:
            try:
                leitura = self.read_clipboard()
                index = 0
            except (NoImageException, LeituraFalhaException):
                logger.debug("Nenhum código de barras encontrado ou falha na leitura")
            except DuplicatedLeituraException as e:
                logger.debug("Leitura duplicada")
                leitura = e.leitura
                index = self.leituras.index(leitura)
            except Exception as e:
                logger.warning(f"Erro ao ler a Área de Transferência: {e}")

            # Schedule callbacks via the queue
            if leitura:
                self.task_queue.put((self.update_listbox_and_selection, (index,)))
                pyperclip.copy(leitura.cod_conv)

            # Reinicia o monitoramento da Área de Transferência:
            # TODO: Usar uma variável para o tempo de espera
            threading.Event().wait(1)

    def _on_close(self, *args, **kwargs):
        """Método responsável por lidar com o evento de fechamento da janela.

        Caso o usuário clique no botão de fechar a janela, iremos perguntar se ele realmente deseja sair.
        """

        ans = Messagebox.yesno(title="Sair", message="Deseja realmente sair ?")

        if ans == MessageCatalog.translate("Yes"):
            self.clipboard_thread_running = False
            self.clipboard_thread.join(timeout=0.5)
            self.destroy()
            self.quit()

    def run(self, *args, **kwargs):
        """Executa o loop principal da aplicação."""

        self.mainloop()


if __name__ == "__main__":
    initialize_system()  # TODO: Faz sentido fazer isso aqui?
    check_for_updates()  # TODO: Faz sentido fazer isso aqui?

    app = App(themename=AppSettings.get_settings("themename"))
    app.run()
