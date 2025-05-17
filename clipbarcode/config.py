import logging
import os
import shutil
import sys
from pathlib import Path

import pytesseract
from decouple import config
from rich.logging import RichHandler
from ttkbootstrap.dialogs import Messagebox

from clipbarcode.constants import HISTORY_PATH, TESSERACT_DEFAULT_PATHS
from clipbarcode.database import db
from clipbarcode.models import AppSettings, Leitura
from clipbarcode.utils import resource_path

logger = logging.getLogger(__name__)


def configure_logger():
    """
    Configure the logger for the application.
    """

    log_level = config("LOGGING_LEVEL", default=logging.INFO)

    # Handlers:
    file_handler = logging.FileHandler(resource_path("clipbarcode.log"))
    file_handler.setLevel(log_level)
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s"
        )
    )

    console_handler = RichHandler(rich_tracebacks=True)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(funcName)s - %(message)s")
    )

    # Logger:
    logging.basicConfig(
        level=log_level,
        handlers=[console_handler, file_handler],
    )


def create_database():
    """
    Create the database and tables if they do not exist.
    This function connects to the database, creates the necessary tables,
    and populates the Preferencia table with a default entry.
    It also checks for the existence of a JSON file containing results,
    and if it exists, it transfers the data to the SQLite database.

    Returns:
        None
    """

    def _create_tables():
        # TODO: with db...

        db.connect()
        db.create_tables([Leitura, AppSettings], safe=True)
        db.close()

    json_path = os.path.join(HISTORY_PATH, "results.json")

    _create_tables()
    if os.path.exists(json_path):
        try:
            Leitura.from_json_to_sqlite(json_path)
            os.remove(json_path)  # Excluindo json após transferir as leituras para DB
        except Exception as e:
            print(e)
            logger.error(e)


def create_images_directory():
    """
    Create the images directory if it does not exist.

    Returns:
        None
    """

    Path(HISTORY_PATH).mkdir(parents=True, exist_ok=True)


def initialize_tesseract_path():
    """
    Initialize the Tesseract OCR path by searching for the executable
    in various locations. It checks for the Tesseract executable in the
    following order:

        1. Bundled Tesseract when running as a PyInstaller app.
        2. Environment variable TESSERACT_CMD.
        3. Default path based on the operating system.
        4. Common locations for macOS.
        5. System's PATH.

    If Tesseract is found, it sets the tesseract_cmd attribute of
    pytesseract.pytesseract to the found path. If Tesseract is not found,
    it shows an error message and logs the error.

    Returns:
        None
    """

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
            logger.info("Tesseract encontrado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao executar Tesseract: {e}")
            Messagebox.show_error("Erro", f"Erro ao executar Tesseract: {e}")
            tesseract_path = None
    else:
        logger.error("Tesseract não encontrado")
        Messagebox.show_error(title="Erro", message="Tesseract não encontrado!")


def initialize_system():
    """Initialize the application by creating necessary directories and setting up the database."""

    configure_logger()
    create_images_directory()
    initialize_tesseract_path()
    create_database()
