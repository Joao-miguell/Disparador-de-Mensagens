# app/core/updater.py
"""
updater.py
==========
Verifica em background se há uma versão nova no GitHub Releases.
Para publicar uma atualização, altere apenas VERSAO_ATUAL e crie uma nova
release no GitHub com a tag correspondente (ex: v1.1.0).
"""

import json
import threading
import tkinter
import tkinter.messagebox
import urllib.request
import webbrowser

VERSAO_ATUAL = "1.0.0"
GITHUB_USER  = "Joao-miguell"
GITHUB_REPO  = "Disparador-de-Mensagens"
API_URL      = f"https://api.github.com/repos/Joao-miguell/Disparador-de-Mensagens/releases/latest"
RELEASE_URL  = f"https://github.com/Joao-miguell/Disparador-de-Mensagens/releases/latest"


def verificar_atualizacao(root: tkinter.Tk) -> None:
    """Dispara a verificação em background — não bloqueia a UI."""
    threading.Thread(target=_checar, args=(root,), daemon=True).start()


def _checar(root: tkinter.Tk) -> None:
    try:
        req = urllib.request.Request(API_URL, headers={"User-Agent": "DisparadorAMTECH"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read())
        versao_nova = data["tag_name"].lstrip("v")
        if versao_nova != VERSAO_ATUAL:
            root.after(0, lambda: _mostrar_popup(versao_nova))
    except Exception:
        pass  # sem internet ou erro na API — silencioso


def _mostrar_popup(versao_nova: str) -> None:
    resposta = tkinter.messagebox.askyesno(
        "Atualização Disponível",
        f"Nova versão disponível: v{versao_nova}\n"
        f"Sua versão: v{VERSAO_ATUAL}\n\n"
        "Deseja ir para a página de download?",
    )
    if resposta:
        webbrowser.open(RELEASE_URL)
