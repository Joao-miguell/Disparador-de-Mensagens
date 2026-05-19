"""
file_manager.py
===============
Responsável por toda a persistência em disco:
  - Configurações de cursos      (config_cursos.json)
  - Templates de mensagens       (templates_mensagens.json)
  - Mensagem padrão ativa        (mensagem_padrao.txt)
  - Última linha processada      (last_line.json)
  - Configurações de tema        (settings.json)
  - Histórico de números enviados (numeros_enviados.json)
"""

import json
import os
from typing import Any


# ──────────────────────────── CURSOS ────────────────────────────

CURSOS_FILE = "config_cursos.json"

def carregar_cursos() -> dict[str, list[str]]:
    if os.path.exists(CURSOS_FILE):
        with open(CURSOS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    modelo_padrao: dict[str, list[str]] = {"Geral": ["Exemplo Curso 1", "Exemplo Curso 2"]}
    salvar_cursos_json(modelo_padrao)
    return modelo_padrao


def salvar_cursos_json(dados: dict[str, list[str]]) -> None:
    with open(CURSOS_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)


# ──────────────────────── TEMPLATES DE MENSAGENS ────────────────────────

TEMPLATES_FILE = "templates_mensagens.json"

def carregar_templates_mensagens() -> dict[str, str]:
    if os.path.exists(TEMPLATES_FILE):
        with open(TEMPLATES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def salvar_templates_mensagens(dados: dict[str, str]) -> None:
    with open(TEMPLATES_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)


# ──────────────────────── MENSAGEM PADRÃO ATIVA ────────────────────────

MENSAGEM_FILE = "mensagem_padrao.txt"

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
    if os.path.exists(MENSAGEM_FILE):
        with open(MENSAGEM_FILE, "r", encoding="utf-8") as f:
            return f.read()

    salvar_mensagem_padrao(_MENSAGEM_MODELO_PADRAO)
    return _MENSAGEM_MODELO_PADRAO


def salvar_mensagem_padrao(texto: str) -> None:
    with open(MENSAGEM_FILE, "w", encoding="utf-8") as f:
        f.write(texto)


# ──────────────────────── ÚLTIMA LINHA ────────────────────────

LAST_LINE_FILE = "last_line.json"

def load_last_line() -> int:
    if os.path.exists(LAST_LINE_FILE):
        with open(LAST_LINE_FILE, "r") as f:
            data: dict[str, Any] = json.load(f)
            return data.get("Ultima_linha_enviada", 0)
    return 0


def save_last_line(last_line: int) -> None:
    with open(LAST_LINE_FILE, "w") as f:
        json.dump({"Ultima_linha_enviada": last_line}, f)


# ──────────────────────── SETTINGS (TEMA) ────────────────────────

SETTINGS_FILE = "settings.json"

def load_settings() -> dict[str, Any]:
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return {"theme": "journal"}


def save_settings(settings: dict[str, Any]) -> None:
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f)


# ──────────────────────── NÚMEROS ENVIADOS ────────────────────────

ENVIADOS_FILE = "numeros_enviados.json"

def carregar_numeros_enviados() -> set[int]:
    if os.path.exists(ENVIADOS_FILE):
        with open(ENVIADOS_FILE, "r") as f:
            return set(json.load(f))
    return set()


def salvar_numeros_enviados(numeros: set[int]) -> None:
    with open(ENVIADOS_FILE, "w") as f:
        json.dump(list(numeros), f)