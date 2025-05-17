try:
    import os

    os.environ["LC_ALL"] = "en_US.UTF-8"
except Exception:
    print("Failed to set environment variable LC_ALL. ")

try:
    import locale

    locale.setlocale(locale.LC_ALL, "")
except locale.Error:
    print("Failed to set locale to environment's LC_ALL")
except Exception as e:
    print(f"Failed to set locale: {e}")

try:
    import sys

    if getattr(sys, "frozen", False):
        tessdata_path = os.path.join(sys._MEIPASS, "tessdata")
        os.environ["TESSDATA_PREFIX"] = tessdata_path
except Exception as e:
    print(f"Failed to set TESSDATA_PREFIX: {e}")


import datetime
import logging
import tkinter as tk
from time import time_ns
from tkinter import messagebox

import pyperclip
import pytesseract
import ttkbootstrap as ttk
from PIL import Image, ImageDraw, ImageGrab, ImageTk
from PIL.Image import Resampling
from PIL.PngImagePlugin import PngImageFile
from pyzbar.pyzbar import decode

from clipbarcode.boleto import BoletoInvalidoException, new_boleto
from clipbarcode.config import initialize
from clipbarcode.constants import CUR_VERSION, HISTORY_PATH, LABEL_FONTNAME
from clipbarcode.datetime_tools import timens_to_datetime
from clipbarcode.exceptions import LeituraFalhaException, NoImageException
from clipbarcode.models import Leitura, Preferencia
from clipbarcode.toplevels import AjudaToplevel, SobreToplevel
from clipbarcode.update import verificar_versao
from clipbarcode.utils import resource_path


class App(ttk.Window):
    def __init__(self, themename="darkly", alpha=0.99, iconphoto=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title(f"Clip Barcode {CUR_VERSION}")
        self.geometry("1280x720")
        self.iconbitmap(resource_path("assets/icon.png"))
        self.place_window_center()
        self.position_center()

        self.last_width = 0
        self.last_height = 0

        self._change_theme(themename)

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
                command=lambda t=theme_name: self._change_theme(t),
            )

        menubar.add_cascade(
            label="Temas",
            menu=theme_menu,
        )

        # Ajuda:
        help_menu = ttk.Menu()

        help_menu.add_command(
            label="Ajuda",
            command=self._on_ajuda_click,
        )

        help_menu.add_separator()

        help_menu.add_command(
            label="Sobre",
            command=self._on_sobre_click,
        )

        menubar.add_cascade(
            label="Ajuda",
            menu=help_menu,
        )

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
        self._fill_list()

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
        self.entry_descricao.bind("<Return>", self._salvar_descricao)

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

        self._hot_read()
        # -------------------------------------

    def _change_theme(self, themename, *args, **kwargs):
        self.style.theme_use(themename)
        Preferencia.update_preferencia(themename=themename)

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

    def _fill_list(self, *args, **kwargs):
        """Método responsável por atualiza a lista com as leituras e atualiza o listbox."""
        self.leituras = Leitura.get_leituras()

        self.listbox.delete(0, tk.END)

        for leitura in self.leituras:
            self.listbox.insert(tk.END, str(leitura))

    def _ler_print(self):
        """Método responsáel por realizar a leitura do print, verificar se é duplicado, e etc."""

        def salvar_leitura(leitura: Leitura, img: PngImageFile, *args, **kwargs):
            """Salva a leitura no banco de dados juntamente com o print.

            Args:
                result (Leitura): Instância da classe Leitura com os dados da leitura
                img (PngImageFile): Print em si
            """

            # Salvando a imagem:
            img.save(os.path.join(HISTORY_PATH, f"{leitura.mili}.png"))
            logging.info(f"{leitura.mili}.png salvo com sucesso na pasta History")

            # Incluíndo a leitura no arquivo de resultados:
            Leitura.create_leitura(leitura)

        def realizar_leitura(*args, **kwargs):
            """Faz a leitura da imagem que estiver na Área de Transferência.

            - Procura inicialmente por um Códigos de Barra
            - Caso não identifique nenhum código de barras, realiza OCR

            Raises:
                NoImageException: Caso não seja encontrado nenhuma imagem na Área de Transferência
                LeituraFalhaException: Caso qualquer problema ocorra ao realizar a leitura
            """

            # -----------------------------------------------------------
            timens = time_ns()
            agora = timens_to_datetime(timens)

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

                match (d.type):
                    case "I25":  # Boletos de Cobraça e Arrecadação
                        logging.debug(
                            "Código de barrras do tipo I25 (boletos de cobrança e arrecadação)"
                        )
                        try:
                            boleto = new_boleto(cod_barras=text)
                            cod_conv = boleto.linha_digitavel
                            m_type = 1
                        except BoletoInvalidoException:
                            texto = f"Boleto Inválido: |{text}|"
                            logging.error(texto)
                            raise LeituraFalhaException(texto)
                    case "CODE128":  # Código de Nota Fiscal
                        logging.debug(
                            "Código de barras do tipo CODE128 (notas fiscais)"
                        )
                        cod_conv = text
                        m_type = 2
                    case "QRCODE":  # QRCode
                        logging.debug("Código de barras do tipo QRCODE")
                        cod_conv = text
                        m_type = 3
                    case _:  # Nenhum dos tipos anteriores
                        texto = f"O código de barras do tipo {d.type} não é suportado"
                        logging.warning(texto)
                        raise LeituraFalhaException(texto)

                x, y, wi, h = d.rect.left, d.rect.top, d.rect.width, d.rect.height
                imgdraw = ImageDraw.Draw(img)
                imgdraw.rectangle(
                    xy=(x, y, x + wi, y + h),
                    outline="#FF0000",
                    width=2,
                )
                logging.debug(f"Imagem encontrada em ({x},{y}) -> ({x+wi},{y+h})")

                leitura = Leitura(
                    mili=f"{timens}",
                    data=agora,
                    type=m_type,
                    cod_lido=text,
                    cod_conv=cod_conv,
                )

                return (leitura, img)

            # -----------------------------------------------------------
            # OCR:
            else:
                logging.info(
                    "Nenhum código de barras encontrado, programa tentará fazer OCR."
                )

                try:
                    text = pytesseract.image_to_string(
                        img,
                        lang="por",
                    ).strip(
                        "\n"
                    )  # TODO: Tesseract está tendo dificuldades em ler números com mais de dois 0 seguidos
                except TypeError:
                    raise NoImageException

                if len(text) <= 0:
                    texto = "OCR não encontrou nada"
                    logging.warning(texto)
                    raise LeituraFalhaException(texto)

                logging.debug(f"OCR realizado com sucesso |{text}|")

                boleto = new_boleto(linha_digitavel=text)

                leitura = Leitura(
                    mili=f"{timens}",
                    data=agora,
                    type=0,
                    cod_lido=text,
                    cod_conv=boleto.linha_digitavel if boleto else text,
                )

                return (leitura, img)

        def verifica_se_duplicado(leitura: Leitura, *args, **kwargs):
            """Verifica se a linha digitável já foi inserida no banco de dados"""
            leitura = Leitura.get_leitura_por_cod_lido(leitura.cod_lido)

            if leitura:
                return True, leitura

            return False, None

        nova_leitura, img = realizar_leitura()
        duplicado, leitura = verifica_se_duplicado(nova_leitura)

        index = 0
        if duplicado:
            salvar = messagebox.askyesno(
                title="Duplicado",
                message=f"Código de barras já lido.\nDeseja salvar mesmo assim ?",
            )
            if salvar:
                salvar_leitura(nova_leitura, img)
            else:
                index = self.leituras.index(leitura)
        else:
            salvar_leitura(nova_leitura, img)

        self._fill_list()
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(index)
        self.listbox.event_generate(
            "<<ListboxSelect>>"
        )  # Simulando um "item selecionado"

    def _hot_read(self):
        """Método responsável por tentar realizar uma leitura logo na inicialização da aplicação."""
        try:
            self._ler_print()
        except Exception:
            pass

        self.listbox.focus()

    def _on_ler_print_click(self, *args, **kwargs):
        """Método responsável por lidar com o evento do Botão "Ler Print" ao ser pressionado."""
        try:
            self._ler_print()
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
        ans = messagebox.askyesno(title="Excluir", message="Excluir registro ?")

        if ans:
            cur_selection = self.listbox.curselection()

            if cur_selection:
                selected_index = cur_selection[0]
                leitura = self.leituras[selected_index]

                # TODO: Pathlib
                os.remove(os.path.join(HISTORY_PATH, f"{leitura.mili}.png"))
                Leitura.delete_leitura(leitura)

                self._fill_list()
                self.clear()
            else:
                messagebox.showerror("Erro", "Não foi possível excluir o registro")

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
                self._salvar_descricao()

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

    def _salvar_descricao(self, *args, **kwargs):
        self.btn_descricao.configure(text="Editar", bootstyle="default")
        self.entry_descricao.config(state="readonly")

        cur_selection = self.listbox.curselection()
        if cur_selection:
            self.cur_index = cur_selection[0]

        leitura = self.leituras[self.cur_index]

        Leitura.update_leitura(leitura, descricao=self.var_descricao.get())
        self._fill_list()
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
                logging.error("Imagem não encontrada")
                messagebox.showerror("Imagem", "Imagem não encontrada")
            except ValueError:
                pass

        elif img_resized:
            self.cur_img_resized = img_resized
            self.photoimage = ImageTk.PhotoImage(self.cur_img_resized)
            self.canvas["image"] = self.photoimage

        else:
            self.canvas["image"] = ""

    def clear(self, *args, **kwargs):
        """Limpa todos os widgets."""
        self.listbox.selection_clear(0, tk.END)
        self.update_canvas()
        self.update_widget_data()
        self.update_tipo("")
        self.update_widget_leitura("")

    def run(self, *args, **kwargs):
        """Executa o loop principal da aplicação."""
        self.mainloop()


if __name__ == "__main__":
    try:
        initialize()
        verificar_versao()
        preferences = Preferencia.get_preferencia()

        app = App(themename=preferences.themename)
        app.run()
    except Exception as e:
        logging.error(e)
        messagebox.showerror("Erro", f"Erro: {e}")
