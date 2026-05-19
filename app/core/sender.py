"""
sender.py
=========
Contém toda a lógica de envio de mensagens via WhatsApp Web.
É completamente desacoplado da interface gráfica — recebe callbacks
para atualizar o progresso e para verificar cancelamento.
"""

import logging
import os
import re
import subprocess
from time import sleep
from typing import Callable
from urllib.parse import quote

import pandas as pd
import pyautogui
import webbrowser

from app.core.models import SendConfig
from app.utils.file_manager import (
    carregar_mensagem_padrao,
    save_last_line,
    salvar_numeros_enviados,
)

logging.basicConfig(
    filename="mesagens_enviadas.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
)


# ──────────────────────── HELPERS ────────────────────────

def limpar_telefone(valor) -> int | None:
    """
    Remove formatação, valida e normaliza para o padrão internacional brasileiro.
    Retorna int com DDI 55 incluso, ou None se inválido.
    """
    if not valor:
        return None

    # Pandas lê colunas com células vazias como float (ex: 44998618601.0)
    # Converte para int antes de transformar em string para eliminar o ".0"
    try:
        valor = int(float(str(valor)))
    except (ValueError, OverflowError):
        pass  # se não conseguir converter, segue com o valor original

    apenas_numeros = re.sub(r"\D", "", str(valor))

    if not apenas_numeros:
        return None

    # Já tem DDI 55 → valida tamanho (12 = fixo, 13 = celular)
    if apenas_numeros.startswith("55") and len(apenas_numeros) in (12, 13):
        pass

    # Tem DDD + número, sem DDI (10 ou 11 dígitos) → adiciona 55
    elif len(apenas_numeros) in (10, 11):
        apenas_numeros = "55" + apenas_numeros

    # Qualquer outro tamanho → inválido
    else:
        logging.warning("Número ignorado por formato inválido: %s", valor)
        return None

    # Valida DDD brasileiro (11–99)
    ddd = int(apenas_numeros[2:4])
    if not (11 <= ddd <= 99):
        logging.warning("DDD inválido no número: %s", valor)
        return None

    try:
        return int(apenas_numeros)
    except ValueError:
        return None



# ──────────────────────── CLASSE PRINCIPAL ────────────────────────

class MessageSender:
    """
    Executa o ciclo de envio de mensagens WhatsApp.

    Parâmetros de callbacks:
      on_progress(value)         — chamado a cada linha para atualizar a barra
      is_running()               — retorna False quando o usuário cancela
      on_status(linha, total, n) — chamado com status de linha atual (opcional)
      on_invalid(valor)          — chamado quando um número é inválido (opcional)
      root                       — acesso à janela raiz para clipboard (opcional)
    """

    def __init__(
        self,
        config: SendConfig,
        numeros_enviados: set[int],
        on_progress: Callable[[int], None],
        is_running: Callable[[], bool],
        root=None,
        on_status: Callable[[int, int, str], None] | None = None,
        on_invalid: Callable[[str], None] | None = None,
    ) -> None:
        self.config = config
        self.numeros_enviados = numeros_enviados
        self.on_progress = on_progress
        self.is_running = is_running
        self.root = root
        self.on_status = on_status
        self.on_invalid = on_invalid

        self.linhas_processadas = 0
        self.linhas_puladas_historico = 0
        self.invalidos: list[str] = []

    # ── Ponto de entrada ──

    def run(self) -> tuple[int, int, list[str]]:
        """
        Executa o envio. Retorna (linhas_processadas, linhas_puladas_historico, invalidos).
        """
        cfg = self.config
        alunos = self._carregar_planilha(cfg.caminho_planilha)
        modelo = carregar_mensagem_padrao()
        total = cfg.linha_max - cfg.linha_min

        for x in range(cfg.linha_min, cfg.linha_max):
            if not self.is_running():
                logging.info("Envio interrompido pelo usuário na linha %d.", x)
                break

            self.on_progress(x - cfg.linha_min + 1)

            # Emite status com número do contato (se disponível)
            if self.on_status:
                try:
                    numero_raw = alunos.loc[x, "Whatsapp com DDD (somente números - sem espaço)"]
                    self.on_status(x - cfg.linha_min + 1, total, str(numero_raw))
                except Exception:
                    self.on_status(x - cfg.linha_min + 1, total, "")

            try:
                self._processar_linha(x, alunos, modelo)
            except Exception as exc:
                logging.warning("Erro ao processar linha %d: %s", x, exc)

        return self.linhas_processadas, self.linhas_puladas_historico, self.invalidos

    # ── Processamento por linha ──

    def _processar_linha(self, x: int, alunos: pd.DataFrame, modelo: str) -> None:
        cfg = self.config
        linha_log = x + 2   # índice pandas → número real na planilha

        if cfg.simple_mode:
            self._enviar_simples(x, alunos, modelo, linha_log)
        elif cfg.por_grupo:
            self._enviar_por_grupo(x, alunos, modelo, linha_log)
        else:
            self._enviar_por_curso(x, alunos, modelo, linha_log)

    def _enviar_simples(self, x: int, alunos: pd.DataFrame, modelo: str, linha_log: int) -> None:
        nome, telefone = self._extrair_contato(x, alunos)
        if telefone is None or self._ja_enviado(telefone):
            return

        self._disparar(telefone, modelo)
        self._registrar(telefone, nome, "", linha_log)

    def _enviar_por_grupo(self, x: int, alunos: pd.DataFrame, modelo: str, linha_log: int) -> None:
        cfg = self.config
        cursos_aluno = self._cursos_do_aluno(x, alunos)
        categoria = self._encontra_categoria(cfg.curso)

        for curso in cursos_aluno:
            if curso in categoria:
                nome, telefone = self._extrair_contato(x, alunos)
                if telefone is None or self._ja_enviado(telefone):
                    return
                mensagem = self._formatar_mensagem(modelo, nome)
                self._disparar(telefone, mensagem)
                self._registrar(telefone, nome, cfg.curso, linha_log)
                return   # uma mensagem por aluno, mesmo que ele tenha vários cursos da categoria

    def _enviar_por_curso(self, x: int, alunos: pd.DataFrame, modelo: str, linha_log: int) -> None:
        cfg = self.config
        cursos_aluno = self._cursos_do_aluno(x, alunos)

        for curso in cursos_aluno:
            if curso.upper() == cfg.curso.upper():
                nome, telefone = self._extrair_contato(x, alunos)
                if telefone is None or self._ja_enviado(telefone):
                    return
                mensagem = self._formatar_mensagem(modelo, nome)
                self._disparar(telefone, mensagem)
                self._registrar(telefone, nome, cfg.curso, linha_log)
                return

    # ── Helpers internos ──

    def _carregar_planilha(self, caminho: str) -> pd.DataFrame:
        return pd.read_excel(caminho)

    def _extrair_contato(self, x: int, alunos: pd.DataFrame) -> tuple[str, int | None]:
        nome = alunos.loc[x, "Nome Completo"]
        valor_raw = alunos.loc[x, "Whatsapp com DDD (somente números - sem espaço)"]
        telefone = limpar_telefone(valor_raw)
        if telefone is None and valor_raw:
            self.invalidos.append(str(valor_raw))
            if self.on_invalid:
                self.on_invalid(str(valor_raw))
        return nome, telefone

    def _cursos_do_aluno(self, x: int, alunos: pd.DataFrame) -> list[str]:
        val = alunos.loc[x, "Dentre as opções qual curso gostaria de fazer?"]
        if pd.isna(val):
            return []
        return str(val).split(sep=", ")

    def _ja_enviado(self, telefone: int) -> bool:
        if telefone in self.numeros_enviados:
            self.linhas_puladas_historico += 1
            return True
        return False

    def _formatar_mensagem(self, modelo: str, nome: str) -> str:
        cfg = self.config
        return modelo.format(
            nome=nome,
            parceiro=cfg.parceiro,
            curso=cfg.curso,
            idade_minima=cfg.idade_minima,
            duracao=cfg.duracao,
            horario=cfg.horario,
        )

    def _registrar(self, telefone: int, nome: str, curso: str, linha: int) -> None:
        self.numeros_enviados.add(telefone)
        salvar_numeros_enviados(self.numeros_enviados)
        self.linhas_processadas += 1
        save_last_line(linha)
        logging.info(
            "Mensagem enviada para: %s | Tel: %s | Curso: %s | Linha: %d",
            nome, telefone, curso or "GENÉRICA", linha,
        )

    def _encontra_categoria(self, curso: str) -> list[str]:
        for _cat, lista in self.config.config_cursos.items():
            if curso in lista:
                return lista
        return []

    def _disparar(self, telefone: int, mensagem: str) -> None:
        img = self.config.caminho_imagem
        if img and os.path.exists(img):
            self._disparar_com_imagem(telefone, mensagem, img)
        else:
            self._disparar_sem_imagem(telefone, mensagem)

    def _disparar_com_imagem(self, telefone: int, mensagem: str, img_path: str) -> None:
        link = f"https://web.whatsapp.com/send/?phone={telefone}"
        webbrowser.open(link)
        sleep(20)  # margem maior para carregamento

        caminho_win = os.path.normpath(img_path).replace("'", "''")
        subprocess.run(
            f"powershell -command \"Set-Clipboard -Path '{caminho_win}'\"",
            shell=True,
        )
        sleep(2)          # aguarda clipboard de imagem estar pronto
        pyautogui.hotkey("ctrl", "v")
        sleep(4)          # aguarda preview da imagem aparecer no campo

        if self.root:
            self.root.clipboard_clear()
            self.root.clipboard_append(mensagem)
            self.root.update()
        sleep(2)          # aguarda clipboard de texto estar pronto
        pyautogui.hotkey("ctrl", "v")
        sleep(3)          # aguarda texto aparecer no campo antes de enviar  ← era 1s
        pyautogui.press("enter")
        sleep(9)          # aguarda envio completar antes de fechar
        pyautogui.hotkey("ctrl", "w")

    def _disparar_sem_imagem(self, telefone: int, mensagem: str) -> None:
        link = f"https://web.whatsapp.com/send/?phone={telefone}&text={quote(mensagem)}"
        webbrowser.open(link)
        sleep(20)         # margem maior para carregamento  ← era 17s
        pyautogui.press("enter")
        sleep(8)          # aguarda envio completar  ← era 6s
        pyautogui.hotkey("ctrl", "w")
