"""
message_editor.py
=================
Janela de edição e biblioteca de modelos de mensagem.
"""

import tkinter
import tkinter.messagebox
from tkinter import scrolledtext, simpledialog, ttk

import ttkbootstrap as ttkb

from app.utils.file_manager import (
    carregar_mensagem_padrao,
    carregar_templates_mensagens,
    salvar_mensagem_padrao,
    salvar_templates_mensagens,
)
from app.utils.widgets import configure_combobox_dropdown_scroll


class MessageEditor(ttkb.Toplevel):
    """Permite editar a mensagem ativa e gerenciar uma biblioteca de modelos."""

    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.title("Editor de Mensagem Padrão")
        self.geometry("800x700")
        self.minsize(800, 650)
        self.transient(parent)
        self.lift()
        self.focus_force()

        self.templates: dict[str, str] = carregar_templates_mensagens()

        self._build_header()
        self._build_template_library()
        self._build_footer()
        self._build_text_area()

    # ── Construção da UI ──

    def _build_header(self) -> None:
        ttkb.Label(
            self,
            text="Edite o modelo da mensagem abaixo.",
            font=("Arial", 12, "bold"),
        ).pack(pady=(10, 5))

        ttkb.Label(
            self,
            text="Use as variáveis entre chaves { } para que o robô substitua pelos dados reais.",
            font=("Arial", 9),
        ).pack(pady=0)

        info_vars = (
            "{nome} - Nome do Aluno  |  {parceiro} - Instituição (SENAI/SENAC)  |  {curso} - Nome do Curso\n"
            "{idade_minima} - Idade Mínima  |  {duracao} - Data de Início/Fim  |  {horario} - Horário do Curso"
        )
        ttkb.Label(self, text=info_vars, bootstyle="info", justify="center").pack(pady=10)

    def _build_template_library(self) -> None:
        frame = ttk.Labelframe(
            self,
            text=" 📚 Biblioteca de Modelos Salvos ",
            padding=10,
            bootstyle="primary",
        )
        frame.pack(fill="x", padx=15, pady=5)

        self.combo_templates = ttkb.Combobox(frame, state="readonly", width=30)
        self.combo_templates.pack(side="left", padx=5)
        configure_combobox_dropdown_scroll(self.combo_templates)

        buttons = [
            ("📂 Carregar", "info", self.load_template),
            ("➕ Salvar Novo", "success", self.save_new_template),
            ("🔄 Atualizar", "warning", self.update_template),
            ("🗑️ Excluir", "danger", self.delete_template),
        ]
        for text, style, cmd in buttons:
            ttkb.Button(frame, text=text, bootstyle=style, command=cmd).pack(side="left", padx=5)

        self._refresh_combo()

    def _build_text_area(self) -> None:
        style = ttkb.Style()
        self.txt_mensagem = scrolledtext.ScrolledText(
            self,
            width=80,
            height=15,
            font=("Arial", 10),
            bg=style.colors.bg,
            fg=style.colors.fg,
            insertbackground=style.colors.fg,
        )
        self.txt_mensagem.pack(padx=15, pady=10, expand=True, fill="both")
        self.txt_mensagem.insert("1.0", carregar_mensagem_padrao())

    def _build_footer(self) -> None:
        ttkb.Button(
            self,
            text="✅ APLICAR ESTA MENSAGEM NO ROBÔ",
            command=self._salvar_ativa,
            bootstyle="success",
            width=40,
        ).pack(side="bottom", pady=15)

    # ── Gerenciamento de templates ──

    def _refresh_combo(self) -> None:
        self.combo_templates["values"] = list(self.templates.keys())

    def load_template(self) -> None:
        nome = self.combo_templates.get()
        if nome in self.templates:
            self.txt_mensagem.delete("1.0", tkinter.END)
            self.txt_mensagem.insert("1.0", self.templates[nome])
        else:
            tkinter.messagebox.showwarning("Aviso", "Selecione um modelo válido para carregar.", parent=self)

    def save_new_template(self) -> None:
        nome = simpledialog.askstring(
            "Salvar Novo Modelo",
            "Digite um nome para este modelo (ex: Aviso de Vagas):",
            parent=self,
        )
        if not nome:
            return
        if nome in self.templates:
            tkinter.messagebox.showwarning(
                "Aviso",
                "Já existe um modelo com esse nome. Use o botão 'Atualizar'.",
                parent=self,
            )
            return
        self.templates[nome] = self._get_text()
        salvar_templates_mensagens(self.templates)
        self._refresh_combo()
        self.combo_templates.set(nome)
        tkinter.messagebox.showinfo("Sucesso", f"Modelo '{nome}' salvo na biblioteca!", parent=self)

    def update_template(self) -> None:
        nome = self.combo_templates.get()
        if not nome:
            tkinter.messagebox.showwarning("Aviso", "Selecione um modelo na lista para atualizar.", parent=self)
            return
        if tkinter.messagebox.askyesno(
            "Confirmar",
            f"Deseja sobrescrever o modelo '{nome}' com o texto atual?",
            parent=self,
        ):
            self.templates[nome] = self._get_text()
            salvar_templates_mensagens(self.templates)
            tkinter.messagebox.showinfo("Sucesso", f"Modelo '{nome}' atualizado!", parent=self)

    def delete_template(self) -> None:
        nome = self.combo_templates.get()
        if not nome:
            tkinter.messagebox.showwarning("Aviso", "Selecione um modelo na lista para excluir.", parent=self)
            return
        if tkinter.messagebox.askyesno(
            "Confirmar",
            f"Tem certeza que deseja apagar o modelo '{nome}'?",
            parent=self,
        ):
            del self.templates[nome]
            salvar_templates_mensagens(self.templates)
            self._refresh_combo()
            self.combo_templates.set("")
            tkinter.messagebox.showinfo("Sucesso", "Modelo excluído.", parent=self)

    def _salvar_ativa(self) -> None:
        texto = self._get_text()
        if not texto:
            tkinter.messagebox.showwarning("Aviso", "A mensagem não pode estar vazia.", parent=self)
            return
        salvar_mensagem_padrao(texto)
        tkinter.messagebox.showinfo(
            "Sucesso",
            "Mensagem aplicada! O robô usará este texto no próximo envio.",
            parent=self,
        )
        self.destroy()

    def _get_text(self) -> str:
        return self.txt_mensagem.get("1.0", tkinter.END).strip()
