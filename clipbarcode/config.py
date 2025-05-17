import logging
import os
import shutil
import sys
from tkinter import messagebox

import pytesseract

from clipbarcode.constants import HISTORY_PATH, LABEL_FONTNAME, TESSERACT_DEFAULT_PATHS
from clipbarcode.database import db
from clipbarcode.models import Leitura, Preferencia
from clipbarcode.utils import resource_path


def create_tables():
    # TODO: with db...

    db.connect()
    db.create_tables(
        [
            Leitura,
            Preferencia,
        ],
        safe=True,
    )
    Preferencia.get_or_create(id=0)
    db.close()


def config_logger():
    logging.basicConfig(
        stream=open(resource_path(f".log"), "a", encoding="utf-8"),
        level=logging.INFO,
        datefmt="%Y-%m-%d %H:%M:%S",
        format="%(asctime)s %(levelname)-8s %(message)s",
    )


def create_database():
    json_path = os.path.join(HISTORY_PATH, "results.json")

    create_tables()
    if os.path.exists(json_path):
        try:
            Leitura.from_json_to_sqlite(json_path)
            os.remove(json_path)  # Excluindo json após transferir as leituras para DB
        except Exception as e:
            print(e)
            logging.error(e)


def create_images_directory():
    # TODO: Use pathlib

    if not os.path.exists(HISTORY_PATH):
        os.mkdir(HISTORY_PATH)
        logging.info("Pasta HISTORY criada com sucesso")


def set_tess_path():
    def find_tesseract():
        """Search for the Tesseract executable in multiple locations."""
        # Check for bundled Tesseract when running as a PyInstaller app
        if getattr(sys, "frozen", False):
            bundle_tesseract = os.path.join(
                os.path.dirname(sys.executable), "tesseract"
            )
            if os.path.exists(bundle_tesseract):
                return bundle_tesseract

        # Check environment variable
        tesseract_cmd = os.environ.get("TESSERACT_CMD")
        if tesseract_cmd and os.path.exists(tesseract_cmd):
            return tesseract_cmd

        # Check default path
        default_path = TESSERACT_DEFAULT_PATHS.get(os.name)
        if default_path and os.path.exists(default_path):
            return default_path

        # Check common locations for macOS
        if os.name == "posix":  # Use posix for macOS
            common_locations = [
                "/opt/homebrew/bin/tesseract",
                "/usr/local/bin/tesseract",
            ]
            for location in common_locations:
                if os.path.exists(location):
                    return location

        # Try searching in the system's PATH
        tesseract_path = shutil.which("tesseract")
        if tesseract_path:
            return tesseract_path

        return None

    tesseract_path = find_tesseract()

    if tesseract_path:
        pytesseract.pytesseract.tesseract_cmd = tesseract_path

        try:
            pytesseract.get_tesseract_version()
            logging.info("Tesseract encontrado com sucesso")
        except Exception as e:
            logging.error(f"Erro ao executar Tesseract: {e}")
            messagebox.showerror("Erro", f"Erro ao executar Tesseract: {e}")
            tesseract_path = None
    else:
        logging.error("Tesseract não encontrado")
        messagebox.showerror("Erro", "Tesseract não encontrado!")


def initialize():
    """Initialize the application by creating necessary directories and setting up the database."""
    config_logger()
    create_images_directory()
    set_tess_path()
    create_database()
