import logging
import subprocess
import urllib.request

import requests
from packaging import version
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.localization.msgcat import MessageCatalog

from clipbarcode.constants import CURRENT_VERSION

logger = logging.getLogger(__name__)


def check_for_updates(*args, **kwargs):
    try:
        response = requests.get(
            "https://api.github.com/repos/viniciusccosta/clipbarcode/releases",
            timeout=(1.0, 2.0),
        )

        match response.status_code:
            case 200:
                # Verifica se a resposta é válida
                json_data = response.json()
                if len(json_data) <= 0:
                    logger.warning("Nenhuma versão encontrada")
                    return

                # Verifica se a versão mais recente é maior que a versão atual
                release = json_data[0]
                latest_version = version.parse(release["tag_name"])
                assets = release["assets"]

                if latest_version <= CURRENT_VERSION:
                    logger.info("Versão instalada é a mais recente")
                    return

                if len(assets) < 0:
                    logger.warning("Nenhum asset encontrado")
                    return

                # Pergunta ao usuário se deseja atualizar:
                ans = Messagebox.yesno(
                    "Atualização",
                    "Uma nova versão está disponível, deseja baixá-la?",
                )

                if ans == MessageCatalog.translate("No"):
                    logger.info("Usuário decidiu não instalar a nova versão")
                    return

                # Baixa o arquivo executável
                for asset in assets:
                    url = asset["browser_download_url"]
                    filename = asset["name"]

                    if url.endswith(".exe"):
                        urllib.request.urlretrieve(url, filename)
                        subprocess.run([filename])
                        Messagebox.show_info(
                            title="Fim da Atualização",
                            message="Abra o programa novamente!",
                        )
                        exit(0)
            case _:
                pass
    except Exception:
        pass
