import toml
from packaging import version

from clipbarcode.utils import resource_path

HISTORY_PATH = resource_path("./history")
CURRENT_VERSION = version.parse(
    toml.load(resource_path("pyproject.toml"))["tool"]["poetry"]["version"]
)

LABEL_FONTNAME = "Arial"
TESSERACT_DEFAULT_PATHS = {
    "posix": "/usr/bin/tesseract",
    "nt": "C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
}
