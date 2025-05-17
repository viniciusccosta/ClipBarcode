import logging
import os
import subprocess
import sys
import urllib.request
from tkinter import messagebox

import requests
from packaging import version

from clipbarcode.constants import CUR_VERSION


def verificar_versao(*args, **kwargs):
    try:
        response = requests.get(
            "https://api.github.com/repos/viniciusccosta/clipbarcode/releases",
            timeout=(1.0, 2.0),
        )

        match response.status_code:
            case 200:
                json_data = response.json()

                if len(json_data) > 0:
                    release = json_data[0]
                    latest_version = version.parse(release["tag_name"])
                    assets = release["assets"]

                    logging.info(f"Versão mais recente: {latest_version}")

                    if latest_version > CUR_VERSION and len(assets) > 0:
                        logging.warning("Versão instalada não é a mais recente")

                        atualizar = messagebox.askyesno(
                            "Atualização",
                            "Uma nova versão está disponível, deseja baixá-la?",
                        )
                        if atualizar:
                            logging.info("Usuário decidiu instalar a nova versão")

                            for asset in assets:
                                url = asset["browser_download_url"]
                                filename = asset["name"]

                                if url.endswith(".exe"):
                                    urllib.request.urlretrieve(url, filename)
                                    subprocess.run([filename])
                                    messagebox.showinfo(
                                        "Fim da Atualização",
                                        "Abra o programa novamente!",
                                    )
                                    exit(0)
            case _:
                pass
    except Exception:
        pass
