import tkinter as tk
from tkinter import scrolledtext

import ttkbootstrap as ttk

from clipbarcode.constants import CURRENT_VERSION, LABEL_FONTNAME
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

        tk.Label(f, text="ClipBarcode", font=(LABEL_FONTNAME, 16)).pack(expand=False, fill="both")
        tk.Label(f, text=f"Versão {CURRENT_VERSION}").pack(expand=False, fill="both")
        tk.Label(f, text="Vinícius Costa").pack(expand=False, fill="both")
        tk.Label(f, text="https://github.com/viniciusccosta/ClipBarcode").pack(expand=False, fill="both")


class AjudaToplevel(BaseToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        help_content = self._get_help_content()

        self.help_text = scrolledtext.ScrolledText(self, wrap="word")
        self.help_text.pack(expand=True, fill="both")
        self.help_text.insert("1.0", help_content)
        self.help_text.configure(state="disabled")

    def _get_help_content(self):
        with open(resource_path("README.md"), "r", encoding="utf8") as file:
            return file.read()
