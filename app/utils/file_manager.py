import json
import os
import sys
from typing import Any


def _get_base_dir() -> str:
    """Retorna a pasta onde os arquivos de dados devem ser salvos.

    - Executável compilado (PyInstaller): mesma pasta do .exe
    - Script Python (desenvolvimento): raiz do projeto
    """
    if getattr(sys, "frozen", False):
        # Rodando como .exe — salva na mesma pasta do executável
        return os.path.dirname(sys.executable)
    # Rodando como script — sobe 2 níveis a partir de app/utils/
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Variável mutável: testes podem substituir fm.BASE_DIR = tmp_dir para isolar operações
BASE_DIR: str = _get_base_dir()


def _path(filename: str) -> str:
    """Retorna o caminho completo de um arquivo de dados dentro de BASE_DIR."""
    return os.path.join(BASE_DIR, filename)


# ──────────────────────────── CURSOS ────────────────────────────

def carregar_cursos() -> dict[str, list[str]]:
    caminho = _path("config_cursos.json")
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)

    modelo_padrao: dict[str, list[str]] = {"Geral": ["Exemplo Curso 1", "Exemplo Curso 2"]}
    salvar_cursos_json(modelo_padrao)
    return modelo_padrao


def salvar_cursos_json(dados: dict[str, list[str]]) -> None:
    with open(_path("config_cursos.json"), "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)


# ──────────────────────── TEMPLATES DE MENSAGENS ────────────────────────

def carregar_templates_mensagens() -> dict[str, str]:
    caminho = _path("templates_mensagens.json")
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def salvar_templates_mensagens(dados: dict[str, str]) -> None:
    with open(_path("templates_mensagens.json"), "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)


# ──────────────────────── MENSAGEM PADRÃO ATIVA ────────────────────────

_MENSAGEM_MODELO_PADRAO = (
    "Olá *{nome}.* Nós somos da AMTECH - Agência Maringá de Tecnologia e Inovação. "
    "entramos em contato porque você demonstrou interesse em cursos de tecnologia preenchendo um formulário.📋\n\n"
    "Nós iremos iniciar em parceria com o *{parceiro}*, o curso:\n\n"
    "🌟*{curso}*.🌟\n\n"
    "Todos podem participar desde que sejam maior de *{idade_minima}* anos e tenham a escolaridade mínima do Ensino Fundamental Completo.🎓\n\n"
    "🎯 Duração do curso: *{duracao}*\n\n"
    "🕒 Horário: *{horario}*\n\n"
    "⚠️ Atenção: As vagas são limitadas! Responda o mais rápido possível! 🏃‍♂️💨 📢*\n\n"
    "*📍Local: Acesso 1 | Piso Superior Terminal Urbano - Av. Tamandaré, 600 - Zona 01, Maringá🗺️ -*\n\n"
    "*🏫 MODALIDADE: curso é PRESENCIAL E 100% GRATUITO! 🎉*\n\n"
    "Qualquer dúvida, estamos à disposição! Esperamos você! 😉"
)


def carregar_mensagem_padrao() -> str:
    caminho = _path("mensagem_padrao.txt")
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            return f.read()

    salvar_mensagem_padrao(_MENSAGEM_MODELO_PADRAO)
    return _MENSAGEM_MODELO_PADRAO


def salvar_mensagem_padrao(texto: str) -> None:
    with open(_path("mensagem_padrao.txt"), "w", encoding="utf-8") as f:
        f.write(texto)


# ──────────────────────── ÚLTIMA LINHA ────────────────────────

def load_last_line() -> int:
    caminho = _path("last_line.json")
    if os.path.exists(caminho):
        with open(caminho, "r") as f:
            data: dict[str, Any] = json.load(f)
            return data.get("Ultima_linha_enviada", 0)
    return 0


def save_last_line(last_line: int) -> None:
    with open(_path("last_line.json"), "w") as f:
        json.dump({"Ultima_linha_enviada": last_line}, f)


# ──────────────────────── SETTINGS (TEMA) ────────────────────────

def load_settings() -> dict[str, Any]:
    caminho = _path("settings.json")
    if os.path.exists(caminho):
        with open(caminho, "r") as f:
            return json.load(f)
    return {"theme": "journal"}


def save_settings(settings: dict[str, Any]) -> None:
    with open(_path("settings.json"), "w") as f:
        json.dump(settings, f)


# ──────────────────────── NÚMEROS ENVIADOS ────────────────────────

def carregar_numeros_enviados() -> set[int]:
    caminho = _path("numeros_enviados.json")
    if os.path.exists(caminho):
        with open(caminho, "r") as f:
            return set(json.load(f))
    return set()


def salvar_numeros_enviados(numeros: set[int]) -> None:
    with open(_path("numeros_enviados.json"), "w") as f:
        json.dump(list(numeros), f)