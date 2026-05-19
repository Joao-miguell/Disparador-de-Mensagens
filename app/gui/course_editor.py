"""
course_editor.py
================
Janela para gerenciar as categorias e os cursos dentro de cada categoria.
"""

import tkinter
import tkinter.messagebox
from tkinter import simpledialog
from typing import Callable

import ttkbootstrap as ttkb
from tkinter import ttk


class CourseEditor(ttkb.Toplevel):
    """Permite adicionar/remover categorias e cursos por categoria."""

    def __init__(
        self,
        parent,
        dados_atuais: dict[str, list[str]],
        callback_salvar: Callable[[dict[str, list[str]]], None],
    ) -> None:
        super().__init__(parent)
        self.title("Gerenciador de Cursos e Categorias")
        self.geometry("600x450")

        # Trabalha sobre uma cópia para não mutar o original antes de salvar
        self.dados: dict[str, list[str]] = {k: list(v) for k, v in dados_atuais.items()}
        self.callback_salvar = callback_salvar

        self._configure_grid()
        self._build_categorias()
        self._build_cursos()
        self._build_footer()

        self._refresh_categorias()

    # ── Layout ──

    def _configure_grid(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

    def _build_categorias(self) -> None:
        ttkb.Label(self, text="1. Categorias (Grupos)", font=("Arial", 10, "bold")).grid(
            row=0, column=0, pady=10
        )

        self.listbox_categorias = tkinter.Listbox(self, exportselection=False)
        self.listbox_categorias.grid(row=1, column=0, sticky="nsew", padx=10)
        self.listbox_categorias.bind("<<ListboxSelect>>", self._ao_selecionar_categoria)

        frame = ttkb.Frame(self)
        frame.grid(row=2, column=0, pady=5)
        ttkb.Button(frame, text="+ Add Categoria", command=self._add_categoria, bootstyle="success-outline", width=15).pack(pady=2)
        ttkb.Button(frame, text="- Remover",       command=self._del_categoria, bootstyle="danger-outline",  width=15).pack(pady=2)

    def _build_cursos(self) -> None:
        ttkb.Label(self, text="2. Cursos da Categoria", font=("Arial", 10, "bold")).grid(
            row=0, column=1, pady=10
        )

        self.listbox_cursos = tkinter.Listbox(self, exportselection=False)
        self.listbox_cursos.grid(row=1, column=1, sticky="nsew", padx=10)

        frame = ttkb.Frame(self)
        frame.grid(row=2, column=1, pady=5)
        ttkb.Button(frame, text="+ Add Curso", command=self._add_curso, bootstyle="info-outline",   width=15).pack(pady=2)
        ttkb.Button(frame, text="- Remover",   command=self._del_curso, bootstyle="danger-outline", width=15).pack(pady=2)

    def _build_footer(self) -> None:
        ttkb.Button(
            self,
            text="💾 SALVAR ALTERAÇÕES",
            command=self._salvar_e_fechar,
            bootstyle="success",
        ).grid(row=3, column=0, columnspan=2, pady=15, sticky="ew", padx=20)

    # ── Atualização das listas ──

    def _refresh_categorias(self) -> None:
        self.listbox_categorias.delete(0, tkinter.END)
        for cat in self.dados:
            self.listbox_categorias.insert(tkinter.END, cat)

    def _refresh_cursos(self, categoria: str) -> None:
        self.listbox_cursos.delete(0, tkinter.END)
        for curso in self.dados.get(categoria, []):
            self.listbox_cursos.insert(tkinter.END, curso)

    def _ao_selecionar_categoria(self, _event) -> None:
        sel = self.listbox_categorias.curselection()
        if sel:
            self._refresh_cursos(self.listbox_categorias.get(sel[0]))

    def _categoria_selecionada(self) -> str | None:
        sel = self.listbox_categorias.curselection()
        return self.listbox_categorias.get(sel[0]) if sel else None

    # ── Ações de categorias ──

    def _add_categoria(self) -> None:
        nova = simpledialog.askstring("Nova Categoria", "Nome da nova categoria:", parent=self)
        if nova and nova not in self.dados:
            self.dados[nova] = []
            self._refresh_categorias()

    def _del_categoria(self) -> None:
        cat = self._categoria_selecionada()
        if cat and tkinter.messagebox.askyesno(
            "Confirmar", f"Apagar a categoria '{cat}' e todos os seus cursos?"
        ):
            del self.dados[cat]
            self._refresh_categorias()
            self.listbox_cursos.delete(0, tkinter.END)

    # ── Ações de cursos ──

    def _add_curso(self) -> None:
        cat = self._categoria_selecionada()
        if not cat:
            tkinter.messagebox.showwarning("Aviso", "Selecione uma categoria primeiro!")
            return
        novo = simpledialog.askstring("Novo Curso", f"Nome do curso para '{cat}':", parent=self)
        if novo:
            self.dados[cat].append(novo)
            self._refresh_cursos(cat)

    def _del_curso(self) -> None:
        cat = self._categoria_selecionada()
        sel_cur = self.listbox_cursos.curselection()
        if cat and sel_cur:
            curso = self.listbox_cursos.get(sel_cur[0])
            self.dados[cat].remove(curso)
            self._refresh_cursos(cat)

    # ── Salvar ──

    def _salvar_e_fechar(self) -> None:
        self.callback_salvar(self.dados)
        self.destroy()