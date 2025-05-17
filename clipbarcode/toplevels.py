import os
import tkinter as tk

import markdown
import ttkbootstrap as ttk
from tkhtmlview import HTMLScrolledText

from clipbarcode.constants import CUR_VERSION, LABEL_FONTNAME
from clipbarcode.utils import resource_path


class BaseToplevel(ttk.Toplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.iconbitmap(resource_path("icon.ico"))
        self.grab_set()
        self.position_center()
        self.place_window_center()


class SobreToplevel(BaseToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        f = tk.Frame(self)
        f.pack(expand=True, fill="both", pady=10, padx=10)

        tk.Label(f, text="ClipBarcode", font=(LABEL_FONTNAME, 16)).pack(
            expand=False, fill="both"
        )
        tk.Label(f, text=f"Versão {CUR_VERSION}").pack(expand=False, fill="both")
        tk.Label(f, text="Vinícius Costa").pack(expand=False, fill="both")
        tk.Label(f, text="https://github.com/viniciusccosta/ClipBarcode").pack(
            expand=False, fill="both"
        )


class AjudaToplevel(BaseToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        html_content = self._get_html_content()

        self.html_label = HTMLScrolledText(self)
        self.html_label.pack(expand=True, fill="both")
        self.html_label.set_html(html_content)

    def _get_html_content(self):
        with open(resource_path("README.md"), "r", encoding="utf8") as file:
            markdown_content = file.read()

        return markdown.markdown(markdown_content)
