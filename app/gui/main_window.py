"""
main_window.py
==============
Janela principal do Disparador de Mensagens AMTECH.
Orquestra a UI e delega o envio para MessageSender.

Sistema de páginas:
  - "main"   → tela principal com scroll
  - "editor" → editor de mensagem embutido (sem Toplevel)
  - "cursos" → gerenciador de cursos embutido (sem Toplevel)
"""

import threading
import tkinter
import tkinter.messagebox
from tkinter import filedialog, scrolledtext, simpledialog, ttk

import pandas as pd

import ttkbootstrap as ttkb
from ttkbootstrap.style import Style

from app.core.models import SendConfig
from app.core.sender import MessageSender
from app.utils.file_manager import (
    carregar_cursos,
    carregar_mensagem_padrao,
    carregar_numeros_enviados,
    carregar_templates_mensagens,
    load_last_line,
    load_settings,
    salvar_cursos_json,
    salvar_mensagem_padrao,
    salvar_numeros_enviados,
    salvar_templates_mensagens,
    save_settings,
)
from app.utils.widgets import (
    add_placeholder,
    block_combobox_mousewheel,
    configure_combobox_dropdown_scroll,
    create_tooltip,
    is_combobox_dropdown_listbox,
    scroll_listbox,
    scroll_listbox_path,
)


class CourseOfferGUI:
    """Janela principal do aplicativo."""

    _THEMES = [
        "superhero", "flatly", "darkly", "journal", "cyborg", "lumen",
        "minty", "pulse", "sandstone", "solar", "united", "yeti",
        "cerulean", "cosmo", "litera", "morph", "simplex", "vapor",
    ]

    def __init__(self, root: tkinter.Tk) -> None:
        self.root = root
        self.root.title("Disparador de Mensagens - AMTECH")
        self.root.geometry("580x750")
        self.root.minsize(580, 500)

        self.settings = load_settings()
        self.style = Style(theme=self.settings.get("theme", "journal"))
        self.last_line = load_last_line()
        self.numeros_enviados = carregar_numeros_enviados()
        self.config_cursos = carregar_cursos()
        self.running = False
        self._invalidos_count = 0

        # ── Estado das páginas auxiliares ──
        self._editor_templates: dict[str, str] = {}
        self._editor_dados: dict[str, list[str]] = {}
        self._editor_novo_mode: bool = False
        self._editor_texto_anterior: str = ""
        self._editor_titulo_anterior: str = ""

        # ── Estado do gerenciador de cursos ──
        self._cat_selecionada: str | None = None
        self._cat_buttons: dict[str, object] = {}

        # ── Gerenciador de páginas ──
        self._pages: dict[str, ttk.Frame] = {}
        self._current_page: ttk.Frame | None = None

        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill="both", expand=True)

        page_main   = ttk.Frame(self.main_container)
        page_editor = ttk.Frame(self.main_container)
        page_cursos = ttk.Frame(self.main_container)

        self._pages["main"]   = page_main
        self._pages["editor"] = page_editor
        self._pages["cursos"] = page_cursos

        self._build_main_page(page_main)
        self._build_message_editor_page(page_editor)
        self._build_course_editor_page(page_cursos)

        block_combobox_mousewheel(self.root, on_wheel=self._scroll_canvas)
        self._configure_combobox_scroll()

        self._show_page("main")

    # ══════════════════════════════════════════════
    # GERENCIADOR DE PÁGINAS
    # ══════════════════════════════════════════════

    def _show_page(self, name: str) -> None:
        if name == "editor":
            self._reload_editor_text()
        elif name == "cursos":
            self._reload_curso_dados()

        if self._current_page is not None:
            self._current_page.pack_forget()

        page = self._pages[name]
        page.pack(fill="both", expand=True)
        self._current_page = page

    # ══════════════════════════════════════════════
    # PÁGINA PRINCIPAL (main)
    # ══════════════════════════════════════════════

    def _build_main_page(self, container: ttk.Frame) -> None:
        bg = self.style.colors.bg
        self.canvas = tkinter.Canvas(container, bg=bg, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)

        self.scrollable_frame = ttk.Frame(self.canvas, padding=15)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(
            self.canvas_window, width=e.width))
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.root.bind_all("<MouseWheel>", self._on_mousewheel)
        self.root.bind_all("<Button-4>", self._on_mousewheel_linux)
        self.root.bind_all("<Button-5>", self._on_mousewheel_linux)

        self._build_header()
        self._build_title()
        self._build_arquivo_block()
        self._build_filtros_block()
        self._build_variaveis_block()
        self._build_linhas_block()
        self._build_acoes_block()
        self._build_credits()

    def _build_header(self) -> None:
        frame = ttk.Frame(self.scrollable_frame)
        frame.pack(fill="x", pady=(0, 15))

        ttkb.Button(frame, text="⚙️ Gerenciar Cursos",  command=lambda: self._show_page("cursos"),  bootstyle="secondary-outline").pack(side="left", padx=(0, 5))
        ttkb.Button(frame, text="📝 Editar Mensagem",   command=lambda: self._show_page("editor"),  bootstyle="secondary-outline").pack(side="left", padx=5)

        frame_tema = ttk.Frame(frame)
        frame_tema.pack(side="right")
        ttk.Label(frame_tema, text="🎨 Tema:", font=("Arial", 9)).pack(side="left", padx=(0, 5))

        temas_cap = [t.capitalize() for t in self._THEMES]
        tema_atual = self.settings.get("theme", "journal").capitalize()
        self.theme_selected = tkinter.StringVar(value=tema_atual)

        self.combo_theme = ttkb.Combobox(
            frame_tema,
            textvariable=self.theme_selected,
            values=temas_cap,
            state="readonly",
            bootstyle="info",
            width=12,
        )
        self.combo_theme.pack(side="left")
        self.combo_theme.bind("<<ComboboxSelected>>", lambda _e: self._change_theme(self.theme_selected.get().lower()))

    def _build_title(self) -> None:
        ttk.Label(
            self.scrollable_frame,
            text="Disparador de Mensagens",
            font=("Arial", 22, "bold"),
            bootstyle="primary",
        ).pack(pady=(5, 15))

    def _build_arquivo_block(self) -> None:
        frame = ttk.LabelFrame(self.scrollable_frame, text=" Base de Dados ", padding=15, bootstyle="info")
        frame.pack(fill="x", pady=(0, 15))

        self.caminho_arquivo = tkinter.StringVar()
        ttkb.Button(frame, text="📁 Selecionar Planilha de Alunos", command=self._selecionar_arquivo, bootstyle="info-outline").pack(pady=(0, 5))
        ttk.Label(frame, textvariable=self.caminho_arquivo, font=("Arial", 8, "italic"), foreground="gray").pack(pady=(0, 2))
        self.lbl_planilha_info = ttk.Label(frame, text="", font=("Arial", 8, "bold"))
        self.lbl_planilha_info.pack(pady=(0, 8))

        self.caminho_imagem = tkinter.StringVar()
        frame_img = ttk.Frame(frame)
        frame_img.pack(pady=(0, 10))
        ttkb.Button(frame_img, text="🖼️ Selecionar Imagem (Opcional)", command=self._selecionar_imagem, bootstyle="primary-outline").pack(side="left", padx=5)
        ttkb.Button(frame_img, text="❌", command=lambda: self.caminho_imagem.set(""), bootstyle="danger-outline").pack(side="left", padx=5)
        ttk.Label(frame, textvariable=self.caminho_imagem, font=("Arial", 8, "italic"), foreground="gray").pack(pady=(0, 10))

        self.simple_mode_var = tkinter.BooleanVar(value=False)
        ttkb.Checkbutton(
            frame,
            text="Enviar Apenas Mensagem Personalizada (Ignorar Variáveis e Cursos)",
            variable=self.simple_mode_var,
            command=self._toggle_inputs,
            bootstyle="info-round-toggle",
        ).pack(pady=(5, 0))

    def _build_filtros_block(self) -> None:
        frame = ttk.LabelFrame(self.scrollable_frame, text=" Seleção de Curso e Instituição ", padding=15, bootstyle="primary")
        frame.pack(fill="x", pady=(0, 15))

        self.course_selected = tkinter.StringVar(value="Selecione um Curso")
        self.combo_course = ttkb.Combobox(frame, textvariable=self.course_selected, state="readonly", bootstyle="primary")
        self._refresh_curso_combo()
        self.combo_course.pack(pady=(0, 10), fill="x", padx=40)

        self.partner_selected = tkinter.StringVar(value="Instituição Parceira")
        self.combo_partner = ttkb.Combobox(
            frame,
            textvariable=self.partner_selected,
            values=["SENAC", "SENAI"],
            state="readonly",
            bootstyle="primary",
        )
        self.combo_partner.pack(pady=(0, 10), fill="x", padx=40)

        frame_g = ttk.Frame(frame)
        frame_g.pack(pady=(0, 5))
        ttk.Label(frame_g, text="Deseja enviar mensagem por grupos?", font=("Arial", 9)).pack(side="left", padx=(0, 5))

        self.group_selected = tkinter.StringVar(value="NÃO")
        self.combo_group = ttkb.Combobox(
            frame_g,
            textvariable=self.group_selected,
            values=["SIM", "NÃO"],
            state="readonly",
            bootstyle="primary",
            width=8,
        )
        self.combo_group.pack(side="left")

        lbl_help = ttk.Label(frame_g, text="(?)", font=("Arial", 9, "bold"), foreground="#17a2b8", cursor="hand2")
        lbl_help.pack(side="left", padx=(5, 0))
        create_tooltip(lbl_help, (
            "COMO FUNCIONA O ENVIO POR GRUPOS:\n\n"
            "• SIM: O robô enviará mensagem para todos os alunos que escolheram cursos\n"
            "da mesma CATEGORIA do curso selecionado.\n\n"
            "• NÃO: O robô enviará mensagem APENAS para quem escolheu EXATAMENTE\n"
            "o nome do curso selecionado."
        ))

    def _build_variaveis_block(self) -> None:
        frame = ttk.LabelFrame(self.scrollable_frame, text=" Variáveis da Mensagem ", padding=15, bootstyle="secondary")
        frame.pack(fill="x", pady=(0, 15))

        self.lbl_horario  = ttk.Label(frame, text="Horário:")
        self.lbl_horario.pack()
        self.schedule_entry = ttk.Entry(frame, width=35, bootstyle="info")
        self.schedule_entry.pack(pady=(0, 5))
        add_placeholder(self.schedule_entry, "Ex: 19:00 às 22:00")

        self.lbl_minage = ttk.Label(frame, text="Idade mínima:")
        self.lbl_minage.pack()
        self.minage_entry = ttk.Entry(frame, width=35, bootstyle="info")
        self.minage_entry.pack(pady=(0, 5))

        self.lbl_duration = ttk.Label(frame, text="Data de Início e Fim:")
        self.lbl_duration.pack()
        self.duration_entry = ttk.Entry(frame, width=35, bootstyle="info")
        self.duration_entry.pack(pady=(0, 5))
        add_placeholder(self.duration_entry, "Ex: 10/02 a 15/02")

    def _build_linhas_block(self) -> None:
        frame = ttk.LabelFrame(self.scrollable_frame, text=" Intervalo da Planilha ", padding=15, bootstyle="warning")
        frame.pack(fill="x", pady=(0, 15))

        inner = ttk.Frame(frame)
        inner.pack()

        frame_min = ttk.Frame(inner)
        frame_min.pack(side="left", padx=10)
        ttk.Label(frame_min, text="Da linha:").pack(anchor="w")
        self.minrange_entry = ttk.Entry(frame_min, width=22, bootstyle="warning")
        self.minrange_entry.pack()
        add_placeholder(self.minrange_entry, f"Última: {self.last_line}")

        frame_max = ttk.Frame(inner)
        frame_max.pack(side="left", padx=10)
        ttk.Label(frame_max, text="Até a linha:").pack(anchor="w")
        self.maxrange_entry = ttk.Entry(frame_max, width=22, bootstyle="warning")
        self.maxrange_entry.pack()

    def _build_acoes_block(self) -> None:
        frame = ttk.Frame(self.scrollable_frame)
        frame.pack(fill="x", pady=(5, 0))

        frame_top_btns = ttk.Frame(frame)
        frame_top_btns.pack(pady=(0, 10))
        ttkb.Button(frame_top_btns, text="🚀 ENVIAR MENSAGENS", command=self._start_sending, bootstyle="success", width=28).pack(side="left", padx=(0, 8))
        ttkb.Button(frame_top_btns, text="👁️ Preview", command=self._abrir_preview, bootstyle="info-outline", width=12).pack(side="left")

        self.progress = ttkb.Progressbar(frame, orient="horizontal", length=400, mode="determinate", bootstyle="success-striped")
        self.progress.pack(pady=(0, 5))

        self.lbl_status = ttk.Label(frame, text="", font=("Arial", 8), foreground="gray")
        self.lbl_status.pack(pady=(0, 2))

        self.lbl_invalidos = ttk.Label(frame, text="", font=("Arial", 8), foreground="#e67e22")
        self.lbl_invalidos.pack(pady=(0, 8))

        frame_btns = ttk.Frame(frame)
        frame_btns.pack()

        ttkb.Button(frame_btns, text="🛑 Interromper",    command=self._interromper,             bootstyle="danger").pack(side="left", padx=5)
        ttkb.Button(frame_btns, text="🗑️ Limpar Histórico", command=self._limpar_historico,       bootstyle="warning-outline").pack(side="left", padx=5)

        lbl_help = ttk.Label(frame_btns, text="(?)", font=("Arial", 9, "bold"), foreground="#ffc107", cursor="hand2")
        lbl_help.pack(side="left", padx=(0, 5))
        create_tooltip(lbl_help, (
            "CUIDADO: ESTA AÇÃO É IRREVERSÍVEL!\n\n"
            "O robô salva uma lista de telefones que já receberam mensagens.\n"
            "Use este botão APENAS ao iniciar uma NOVA campanha."
        ))

    def _build_credits(self) -> None:
        ttkb.Label(
            self.scrollable_frame,
            text="Desenvolvido por: Lucas Ferrari, Eduardo Zanin & João Miguel",
            font=("Arial", 8, "italic"),
            foreground="gray",
        ).pack(side="bottom", pady=(15, 0))

    # ══════════════════════════════════════════════
    # PÁGINA EDITOR DE MENSAGEM (editor)
    # ══════════════════════════════════════════════

    def _build_message_editor_page(self, container: ttk.Frame) -> None:
        top_bar = ttk.Frame(container, padding=(10, 8))
        top_bar.pack(fill="x")
        ttkb.Button(top_bar, text="← Voltar", command=lambda: self._show_page("main"), bootstyle="secondary-outline").pack(side="left")

        ttkb.Label(
            container,
            text="Edite o modelo da mensagem abaixo.",
            font=("Arial", 12, "bold"),
        ).pack(pady=(5, 3))
        ttkb.Label(
            container,
            text="Use as variáveis entre chaves { } para que o robô substitua pelos dados reais.",
            font=("Arial", 9),
        ).pack()
        info_vars = (
            "{nome} - Nome do Aluno  |  {parceiro} - Instituição (SENAI/SENAC)  |  {curso} - Nome do Curso\n"
            "{idade_minima} - Idade Mínima  |  {duracao} - Data de Início/Fim  |  {horario} - Horário do Curso"
        )
        ttkb.Label(container, text=info_vars, bootstyle="info", justify="center", wraplength=540).pack(pady=8)

        lib_frame = ttk.LabelFrame(container, text=" 📚 Biblioteca de Modelos Salvos ", padding=10, bootstyle="primary")
        lib_frame.pack(fill="x", padx=15, pady=5)
        lib_frame.columnconfigure(0, weight=1)

        self.combo_templates = ttkb.Combobox(lib_frame, state="readonly")
        self.combo_templates.grid(row=0, column=0, sticky="ew", padx=5, pady=(0, 6))
        configure_combobox_dropdown_scroll(self.combo_templates)
        self.combo_templates.bind("<<ComboboxSelected>>", self._editor_on_select_template)

        self._entry_titulo_novo = ttk.Entry(lib_frame, font=("Arial", 10))

        self._btn_row = ttk.Frame(lib_frame)
        self._btn_row.grid(row=1, column=0)

        self._btn_salvar_novo = ttkb.Button(
            self._btn_row, text="➕ Salvar Novo", bootstyle="success",
            command=self._editor_iniciar_novo_template,
        )
        self._btn_atualizar = ttkb.Button(
            self._btn_row, text="🔄 Atualizar", bootstyle="warning",
            command=self._editor_update_template,
        )
        self._btn_excluir = ttkb.Button(
            self._btn_row, text="🗑️ Excluir", bootstyle="danger",
            command=self._editor_delete_template,
        )

        self._btn_confirmar = ttkb.Button(
            self._btn_row, text="💾 Confirmar Salvamento", bootstyle="success",
            command=self._editor_confirmar_novo_template,
        )
        self._btn_cancelar_novo = ttkb.Button(
            self._btn_row, text="✖ Cancelar", bootstyle="secondary-outline",
            command=self._editor_cancelar_novo_template,
        )

        self.txt_mensagem = scrolledtext.ScrolledText(
            container,
            width=80,
            height=15,
            font=("Arial", 10),
            bg=self.style.colors.bg,
            fg=self.style.colors.fg,
            insertbackground=self.style.colors.fg,
        )
        self.txt_mensagem.pack(padx=15, pady=10, expand=True, fill="both")

        self._btn_aplicar = ttkb.Button(
            container,
            text="✅ APLICAR ESTA MENSAGEM NO ROBÔ",
            command=self._salvar_mensagem_ativa,
            bootstyle="success",
            width=40,
        )
        self._btn_aplicar.pack(pady=10)

        self._editor_set_novo_mode_buttons(False)

        self._editor_templates = carregar_templates_mensagens()
        self._editor_refresh_combo()

    def _reload_editor_text(self) -> None:
        self._editor_novo_mode = False
        self._editor_templates = carregar_templates_mensagens()
        self._editor_refresh_combo()

        try:
            texto = carregar_mensagem_padrao()
        except Exception as exc:
            tkinter.messagebox.showwarning(
                "Aviso",
                f"Não foi possível carregar a mensagem padrão:\n{exc}",
                parent=self.root,
            )
            texto = ""
        self.txt_mensagem.delete("1.0", tkinter.END)
        self.txt_mensagem.insert("1.0", texto)

        match = next(
            (nome for nome, t in self._editor_templates.items() if t.strip() == texto.strip()),
            "",
        )
        self._editor_sair_modo_novo(match)

    def _editor_refresh_combo(self) -> None:
        self.combo_templates["values"] = list(self._editor_templates.keys())

    def _editor_on_select_template(self, _event) -> None:
        if self._editor_novo_mode:
            return
        nome = self.combo_templates.get()
        if nome in self._editor_templates:
            self.txt_mensagem.delete("1.0", tkinter.END)
            self.txt_mensagem.insert("1.0", self._editor_templates[nome])

    def _editor_iniciar_novo_template(self) -> None:
        self._editor_texto_anterior  = self._editor_get_text()
        self._editor_titulo_anterior = self.combo_templates.get()
        self._editor_novo_mode = True
        self.combo_templates.grid_remove()
        self._entry_titulo_novo.delete(0, tkinter.END)
        self._entry_titulo_novo.grid(row=0, column=0, sticky="ew", padx=5, pady=(0, 6))
        self._entry_titulo_novo.focus_set()
        self.txt_mensagem.delete("1.0", tkinter.END)
        self._editor_set_novo_mode_buttons(True)

    def _editor_confirmar_novo_template(self) -> None:
        titulo = self._entry_titulo_novo.get().strip()
        texto  = self._editor_get_text()
        if not titulo:
            tkinter.messagebox.showwarning("Aviso", "Preencha o título do modelo no campo acima.", parent=self.root)
            self._entry_titulo_novo.focus_set()
            return
        if not texto:
            tkinter.messagebox.showwarning("Aviso", "Escreva o texto da mensagem antes de salvar.", parent=self.root)
            self.txt_mensagem.focus_set()
            return
        if titulo in self._editor_templates:
            tkinter.messagebox.showwarning(
                "Aviso",
                f"Já existe um modelo chamado '{titulo}'.\nEscolha outro nome ou use 'Atualizar'.",
                parent=self.root,
            )
            return
        self._editor_templates[titulo] = texto
        salvar_templates_mensagens(self._editor_templates)
        self._editor_refresh_combo()
        self._editor_sair_modo_novo(titulo)
        tkinter.messagebox.showinfo("Sucesso", f"Modelo '{titulo}' salvo na biblioteca!", parent=self.root)

    def _editor_cancelar_novo_template(self) -> None:
        self._editor_sair_modo_novo(self._editor_titulo_anterior)
        self.txt_mensagem.delete("1.0", tkinter.END)
        self.txt_mensagem.insert("1.0", self._editor_texto_anterior)

    def _editor_sair_modo_novo(self, nome: str) -> None:
        self._editor_novo_mode = False
        self._entry_titulo_novo.grid_remove()
        self._editor_refresh_combo()
        self.combo_templates.grid(row=0, column=0, sticky="ew", padx=5, pady=(0, 6))
        self.combo_templates.set(nome)
        self._editor_set_novo_mode_buttons(False)

    def _editor_set_novo_mode_buttons(self, novo_mode: bool) -> None:
        if novo_mode:
            self._btn_salvar_novo.pack_forget()
            self._btn_atualizar.pack_forget()
            self._btn_excluir.pack_forget()
            self._btn_confirmar.pack(side="left", padx=4)
            self._btn_cancelar_novo.pack(side="left", padx=4)
            self._btn_aplicar.config(state="disabled")
        else:
            self._btn_confirmar.pack_forget()
            self._btn_cancelar_novo.pack_forget()
            self._btn_salvar_novo.pack(side="left", padx=4)
            self._btn_atualizar.pack(side="left", padx=4)
            self._btn_excluir.pack(side="left", padx=4)
            self._btn_aplicar.config(state="normal")

    def _editor_update_template(self) -> None:
        nome = self.combo_templates.get()
        if not nome:
            tkinter.messagebox.showwarning("Aviso", "Selecione um modelo na lista para atualizar.", parent=self.root)
            return
        if tkinter.messagebox.askyesno(
            "Confirmar",
            f"Deseja sobrescrever o modelo '{nome}' com o texto atual?",
            parent=self.root,
        ):
            self._editor_templates[nome] = self._editor_get_text()
            salvar_templates_mensagens(self._editor_templates)
            tkinter.messagebox.showinfo("Sucesso", f"Modelo '{nome}' atualizado!", parent=self.root)

    def _editor_delete_template(self) -> None:
        nome = self.combo_templates.get()
        if not nome:
            tkinter.messagebox.showwarning("Aviso", "Selecione um modelo na lista para excluir.", parent=self.root)
            return
        if tkinter.messagebox.askyesno(
            "Confirmar",
            f"Tem certeza que deseja apagar o modelo '{nome}'?",
            parent=self.root,
        ):
            del self._editor_templates[nome]
            salvar_templates_mensagens(self._editor_templates)
            self._editor_refresh_combo()
            try:
                texto_ativo = carregar_mensagem_padrao()
            except Exception:
                texto_ativo = ""
            self.txt_mensagem.delete("1.0", tkinter.END)
            self.txt_mensagem.insert("1.0", texto_ativo)
            match = next(
                (n for n, t in self._editor_templates.items() if t.strip() == texto_ativo.strip()),
                "",
            )
            self.combo_templates.set(match)
            tkinter.messagebox.showinfo("Sucesso", "Modelo excluído.", parent=self.root)

    def _salvar_mensagem_ativa(self) -> None:
        texto = self._editor_get_text()
        if not texto:
            tkinter.messagebox.showwarning("Aviso", "A mensagem não pode estar vazia.", parent=self.root)
            return
        salvar_mensagem_padrao(texto)
        tkinter.messagebox.showinfo(
            "Sucesso",
            "Mensagem aplicada! O robô usará este texto no próximo envio.",
            parent=self.root,
        )
        self._show_page("main")

    def _editor_get_text(self) -> str:
        return self.txt_mensagem.get("1.0", tkinter.END).strip()

    # ══════════════════════════════════════════════
    # PÁGINA GERENCIADOR DE CURSOS (cursos)
    # ══════════════════════════════════════════════

    def _build_course_editor_page(self, container: ttk.Frame) -> None:
        """
        Gerenciador de cursos redesenhado:
        - Esquerda: cards de categoria em grid 2 colunas com scroll
        - Direita: listbox estilizado com fonte maior e scroll
        """
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)
        container.grid_rowconfigure(1, weight=1)

        # ── Barra superior: Voltar ──
        top_bar = ttk.Frame(container, padding=(10, 8))
        top_bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        ttkb.Button(
            top_bar, text="← Voltar",
            command=lambda: self._show_page("main"),
            bootstyle="secondary-outline",
        ).pack(side="left")
        ttk.Label(
            top_bar,
            text="Gerenciador de Cursos e Categorias",
            font=("Arial", 12, "bold"),
        ).pack(side="left", padx=15)

        # ════════════════════════════════
        # COLUNA ESQUERDA — Categorias (cards 2×N com scroll)
        # ════════════════════════════════
        cat_lf = ttk.LabelFrame(
            container, text=" 📂 Categorias ", padding=8, bootstyle="primary"
        )
        cat_lf.grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=(5, 0))
        cat_lf.grid_rowconfigure(0, weight=1)
        cat_lf.grid_columnconfigure(0, weight=1)

        # Canvas scrollável para os cards — width=1 deixa o grid decidir o tamanho igualmente
        self._cat_canvas = tkinter.Canvas(cat_lf, highlightthickness=0, width=1)
        cat_vsb = ttk.Scrollbar(cat_lf, orient="vertical", command=self._cat_canvas.yview)
        self._cat_canvas.configure(yscrollcommand=cat_vsb.set)
        self._cat_canvas.grid(row=0, column=0, sticky="nsew")
        cat_vsb.grid(row=0, column=1, sticky="ns")

        # Frame interno 1 coluna para os cards (um abaixo do outro)
        self._cat_inner = ttk.Frame(self._cat_canvas)
        self._cat_inner.columnconfigure(0, weight=1)
        self._cat_inner.bind(
            "<Configure>",
            lambda e: self._cat_canvas.configure(
                scrollregion=self._cat_canvas.bbox("all")
            ),
        )
        self._cat_canvas_window = self._cat_canvas.create_window(
            (0, 0), window=self._cat_inner, anchor="nw"
        )
        self._cat_canvas.bind(
            "<Configure>",
            lambda e: self._cat_canvas.itemconfig(
                self._cat_canvas_window, width=e.width
            ),
        )
        # Scroll do canvas de categorias é tratado pelo handler central _on_mousewheel

        # Botões de ação das categorias
        frame_cat_btns = ttk.Frame(cat_lf)
        frame_cat_btns.grid(row=1, column=0, columnspan=2, pady=(8, 0))
        ttkb.Button(
            frame_cat_btns, text="+ Categoria",
            command=self._cursos_add_categoria,
            bootstyle="success-outline", width=13,
        ).pack(side="left", padx=4)
        ttkb.Button(
            frame_cat_btns, text="− Remover",
            command=self._cursos_del_categoria,
            bootstyle="danger-outline", width=13,
        ).pack(side="left", padx=4)

        # ════════════════════════════════
        # COLUNA DIREITA — Cursos (listbox maior + scroll)
        # ════════════════════════════════
        cur_lf = ttk.LabelFrame(
            container, text=" 📚 Cursos da Categoria ", padding=8, bootstyle="info"
        )
        cur_lf.grid(row=1, column=1, sticky="nsew", padx=(5, 10), pady=(5, 0))
        cur_lf.grid_rowconfigure(0, weight=1)
        cur_lf.grid_columnconfigure(0, weight=1)

        # Listbox com fonte maior e zebra striping
        self.listbox_cursos = tkinter.Listbox(
            cur_lf,
            exportselection=False,
            font=("Arial", 12),          # fonte maior que o original (era 11)
            activestyle="none",
            bd=0,
            relief="flat",
            selectmode=tkinter.SINGLE,
            selectbackground="#4a9fd4",
            selectforeground="white",
        )
        cur_vsb = ttk.Scrollbar(
            cur_lf, orient="vertical", command=self.listbox_cursos.yview
        )
        self.listbox_cursos.configure(yscrollcommand=cur_vsb.set)
        self.listbox_cursos.grid(row=0, column=0, sticky="nsew")
        cur_vsb.grid(row=0, column=1, sticky="ns")

        # Scroll do listbox de cursos é tratado pelo handler central _on_mousewheel

        # Botões de ação dos cursos
        frame_cur_btns = ttk.Frame(cur_lf)
        frame_cur_btns.grid(row=1, column=0, columnspan=2, pady=(8, 0))
        ttkb.Button(
            frame_cur_btns, text="+ Curso",
            command=self._cursos_add_curso,
            bootstyle="info-outline", width=13,
        ).pack(side="left", padx=4)
        ttkb.Button(
            frame_cur_btns, text="− Remover",
            command=self._cursos_del_curso,
            bootstyle="danger-outline", width=13,
        ).pack(side="left", padx=4)

        # ── Rodapé: Salvar ──
        ttkb.Button(
            container,
            text="💾 SALVAR ALTERAÇÕES",
            command=self._salvar_cursos_editor,
            bootstyle="success",
        ).grid(row=2, column=0, columnspan=2, pady=12, sticky="ew", padx=20)

    # ── Scroll interno do canvas de categorias ──

    def _cat_scroll(self, event) -> None:
        self._cat_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ── Reload e refresh ──

    def _reload_curso_dados(self) -> None:
        """Reinicia _editor_dados como cópia fresca de config_cursos e atualiza os paineis."""
        self._editor_dados = {k: list(v) for k, v in self.config_cursos.items()}
        self._cat_selecionada = None
        self._cursos_refresh_categorias()
        self.listbox_cursos.delete(0, tkinter.END)

    def _cursos_refresh_categorias(self) -> None:
        """Reconstrói os cards de categoria no painel da esquerda (2 por linha)."""
        for w in self._cat_inner.winfo_children():
            w.destroy()
        self._cat_buttons.clear()

        for i, cat in enumerate(self._editor_dados):
            selecionado = (cat == self._cat_selecionada)
            style = "primary" if selecionado else "primary-outline"
            btn = ttkb.Button(
                self._cat_inner,
                text=cat,
                bootstyle=style,
                command=lambda c=cat: self._cursos_selecionar_categoria(c),
            )
            btn.grid(row=i, column=0, padx=6, pady=4, sticky="ew")
            self._cat_buttons[cat] = btn

        self._cat_inner.update_idletasks()
        self._cat_canvas.configure(scrollregion=self._cat_canvas.bbox("all"))

    def _cursos_selecionar_categoria(self, nome: str) -> None:
        self._cat_selecionada = nome
        for cat, btn in self._cat_buttons.items():
            estilo = "primary" if cat == nome else "primary-outline"
            btn.config(bootstyle=estilo)
        self._cursos_refresh_cursos(nome)

    def _cursos_refresh_cursos(self, categoria: str) -> None:
        """Popula o listbox de cursos — SEM prefixo de espaços para evitar bugs no remove."""
        self.listbox_cursos.delete(0, tkinter.END)
        for i, curso in enumerate(self._editor_dados.get(categoria, [])):
            # ─── CORREÇÃO: inserir SEM espaços extras para que o remove() funcione ───
            self.listbox_cursos.insert(tkinter.END, curso)
            # Padding visual via itemconfig (não via texto)
            self.listbox_cursos.itemconfig(
                i,
                background="#f0f4ff" if i % 2 == 0 else "",
                selectbackground="#4a9fd4",
            )

    def _cursos_categoria_selecionada(self) -> str | None:
        return self._cat_selecionada

    # ── Ações de categorias ──

    def _cursos_add_categoria(self) -> None:
        nova = simpledialog.askstring(
            "Nova Categoria", "Nome da nova categoria:", parent=self.root
        )
        if nova and nova.strip() and nova.strip() not in self._editor_dados:
            self._editor_dados[nova.strip()] = []
            self._cursos_refresh_categorias()

    def _cursos_del_categoria(self) -> None:
        cat = self._cursos_categoria_selecionada()
        if not cat:
            tkinter.messagebox.showwarning(
                "Aviso", "Selecione uma categoria primeiro!", parent=self.root
            )
            return
        if tkinter.messagebox.askyesno(
            "Confirmar",
            f"Apagar a categoria '{cat}' e todos os seus cursos?",
            parent=self.root,
        ):
            del self._editor_dados[cat]
            self._cat_selecionada = None
            self._cursos_refresh_categorias()
            self.listbox_cursos.delete(0, tkinter.END)

    # ── Ações de cursos ──

    def _cursos_add_curso(self) -> None:
        cat = self._cursos_categoria_selecionada()
        if not cat:
            tkinter.messagebox.showwarning(
                "Aviso", "Selecione uma categoria primeiro!", parent=self.root
            )
            return
        novo = simpledialog.askstring(
            "Novo Curso", f"Nome do curso para '{cat}':", parent=self.root
        )
        if novo and novo.strip():
            self._editor_dados[cat].append(novo.strip())
            self._cursos_refresh_cursos(cat)

    def _cursos_del_curso(self) -> None:
        cat = self._cursos_categoria_selecionada()
        sel_cur = self.listbox_cursos.curselection()
        if not cat:
            tkinter.messagebox.showwarning(
                "Aviso", "Selecione uma categoria primeiro!", parent=self.root
            )
            return
        if not sel_cur:
            tkinter.messagebox.showwarning(
                "Aviso", "Selecione um curso para remover.", parent=self.root
            )
            return
        # ─── CORREÇÃO: o texto do listbox é exatamente o nome do curso (sem espaços) ───
        curso = self.listbox_cursos.get(sel_cur[0])
        if curso in self._editor_dados[cat]:
            self._editor_dados[cat].remove(curso)
            self._cursos_refresh_cursos(cat)

    def _salvar_cursos_editor(self) -> None:
        self._salvar_cursos(self._editor_dados)
        self._show_page("main")
        tkinter.messagebox.showinfo(
            "Sucesso", "Lista de cursos atualizada com sucesso!", parent=self.root
        )

    # ══════════════════════════════════════════════
    # HELPERS DE UI
    # ══════════════════════════════════════════════

    def _refresh_curso_combo(self) -> None:
        cursos = [c for lista in self.config_cursos.values() for c in lista]
        if hasattr(self, "combo_course"):
            self.combo_course["values"] = cursos

    def _toggle_inputs(self) -> None:
        disabled = self.simple_mode_var.get()
        entry_state = "disabled" if disabled else "normal"
        combo_state = "disabled" if disabled else "readonly"
        lbl_color = "gray" if disabled else ""

        for w in (self.schedule_entry, self.minage_entry, self.duration_entry):
            w.config(state=entry_state)
        for lbl in (self.lbl_horario, self.lbl_minage, self.lbl_duration):
            lbl.config(foreground=lbl_color)
        for combo in (self.combo_course, self.combo_partner, self.combo_group):
            combo.config(state=combo_state)

    def _configure_combobox_scroll(self) -> None:
        for combo in (
            self.combo_theme,
            self.combo_course,
            self.combo_partner,
            self.combo_group,
            self.combo_templates,
        ):
            configure_combobox_dropdown_scroll(combo)

    def _scroll_canvas(self, event) -> None:
        if self._current_page is not self._pages.get("main"):
            return
        if getattr(event, "num", None) == 4:
            self.canvas.yview_scroll(-1, "units")
        elif getattr(event, "num", None) == 5:
            self.canvas.yview_scroll(1, "units")
        else:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _popdown_listbox_path_at_pointer(self, event) -> str | None:
        widget = event.widget
        if is_combobox_dropdown_listbox(widget):
            return widget._w

        try:
            path = self.root.tk.call("winfo", "containing", event.x_root, event.y_root)
        except tkinter.TclError:
            return None

        if not path:
            return None

        path_str = str(path)
        if "popdown" in path_str.lower() and path_str.lower().endswith(".l"):
            return path_str

        return None

    def _widget_under_pointer(self, event) -> tkinter.Misc | None:
        """Retorna o widget Tkinter sob o ponteiro do mouse (mais confiável que event.widget)."""
        try:
            path = self.root.tk.call("winfo", "containing", event.x_root, event.y_root)
            if path:
                return self.root.nametowidget(str(path))
        except (tkinter.TclError, KeyError):
            pass
        return event.widget

    def _on_mousewheel(self, event) -> str | None:
        if event.widget.winfo_toplevel() is not self.root:
            return None

        # 1. Dropdown de Combobox aberto — rola as opções
        path = self._popdown_listbox_path_at_pointer(event)
        if path is not None:
            scroll_listbox_path(self.root.tk, path, event)
            return "break"
        if is_combobox_dropdown_listbox(event.widget):
            scroll_listbox(event.widget, event)
            return "break"

        # 2. Identifica o widget real sob o ponteiro
        target = self._widget_under_pointer(event)

        # 3. Mouse sobre o canvas de categorias ou seus filhos → rola categorias
        #    mas só se o conteúdo for maior que a área visível
        if target is not None:
            w = target
            while w is not None:
                if w is self._cat_canvas or w is self._cat_inner:
                    # Só rola se houver conteúdo além da área visível
                    top, bottom = self._cat_canvas.yview()
                    if top > 0 or bottom < 1:
                        self._cat_scroll(event)
                    return "break"
                try:
                    w = w.master
                except AttributeError:
                    break

        # 4. Mouse sobre o listbox de cursos → rola cursos
        if target is self.listbox_cursos:
            delta = int(-1 * (event.delta / 120))
            self.listbox_cursos.yview_scroll(delta, "units")
            return "break"

        # 5. Fallback → rola o canvas da tela principal
        self._scroll_canvas(event)
        return None

    def _on_mousewheel_linux(self, event) -> str | None:
        if event.widget.winfo_toplevel() is not self.root:
            return None

        path = self._popdown_listbox_path_at_pointer(event)
        if path is not None:
            scroll_listbox_path(self.root.tk, path, event)
            return "break"
        if is_combobox_dropdown_listbox(event.widget):
            scroll_listbox(event.widget, event)
            return "break"

        target = self._widget_under_pointer(event)

        if target is not None:
            w = target
            while w is not None:
                if w is self._cat_canvas or w is self._cat_inner:
                    top, bottom = self._cat_canvas.yview()
                    if top > 0 or bottom < 1:
                        self._cat_scroll(event)
                    return "break"
                try:
                    w = w.master
                except AttributeError:
                    break

        if target is self.listbox_cursos:
            num = getattr(event, "num", None)
            delta = -1 if num == 4 else 1
            self.listbox_cursos.yview_scroll(delta, "units")
            return "break"

        self._scroll_canvas(event)
        return None

    # ══════════════════════════════════════════════
    # AÇÕES
    # ══════════════════════════════════════════════

    def _selecionar_arquivo(self) -> None:
        path = filedialog.askopenfilename(
            title="Selecione a planilha", filetypes=[("Excel", "*.xlsx *.xls")]
        )
        if path:
            self.caminho_arquivo.set(path)
            self._validar_planilha(path)

    def _validar_planilha(self, path: str) -> None:
        COLUNAS = [
            "Nome Completo",
            "Whatsapp com DDD (somente números - sem espaço)",
            "Dentre as opções qual curso gostaria de fazer?",
        ]
        try:
            df = pd.read_excel(path)
            faltando = [c for c in COLUNAS if c not in df.columns]
            if faltando:
                self.lbl_planilha_info.config(
                    text=f"❌ Coluna(s) não encontrada(s): {', '.join(faltando)}",
                    foreground="#e74c3c",
                )
            else:
                total = len(df)
                self.lbl_planilha_info.config(
                    text=f"✅ Planilha válida — {total} contatos encontrados",
                    foreground="#27ae60",
                )
        except Exception as exc:
            self.lbl_planilha_info.config(
                text=f"❌ Erro ao ler planilha: {exc}",
                foreground="#e74c3c",
            )

    def _selecionar_imagem(self) -> None:
        path = filedialog.askopenfilename(
            title="Selecione a imagem",
            filetypes=[("Imagens", "*.png *.jpg *.jpeg")],
        )
        if path:
            self.caminho_imagem.set(path)

    @staticmethod
    def _get_field(entry: ttk.Entry, placeholder_prefix: str = "Ex:") -> str:
        val = entry.get()
        return "" if placeholder_prefix in val else val

    def _abrir_preview(self) -> None:
        modelo = carregar_mensagem_padrao()
        simple = self.simple_mode_var.get()

        horario  = self._get_field(self.schedule_entry) if not simple else ""
        duracao  = self._get_field(self.duration_entry)  if not simple else ""
        minage   = self.minage_entry.get()               if not simple else ""
        curso    = self.course_selected.get()            if not simple else ""
        parceiro = self.partner_selected.get()           if not simple else ""
        idade    = int(minage) if minage.strip().isdigit() else 0

        try:
            preview_text = modelo.format(
                nome="[Nome do Aluno]",
                parceiro=parceiro or "[Parceiro]",
                curso=curso or "[Curso]",
                idade_minima=idade,
                duracao=duracao or "[Duração]",
                horario=horario or "[Horário]",
            )
        except KeyError as e:
            preview_text = f"Erro ao formatar mensagem — variável desconhecida: {e}"

        win = tkinter.Toplevel(self.root)
        win.title("👁️ Preview da Mensagem")
        win.geometry("520x460")
        win.resizable(True, True)

        ttk.Label(win, text="Preview da Mensagem", font=("Arial", 13, "bold")).pack(pady=(12, 6))
        ttk.Label(win, text="(Exemplo com dados fictícios)", font=("Arial", 8, "italic"), foreground="gray").pack(pady=(0, 8))

        frame_txt = ttk.Frame(win, padding=10)
        frame_txt.pack(fill="both", expand=True)

        txt = tkinter.Text(frame_txt, wrap="word", font=("Arial", 10), relief="flat", padx=8, pady=8)
        sb  = ttk.Scrollbar(frame_txt, orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        txt.pack(fill="both", expand=True)

        txt.insert("1.0", preview_text)
        txt.config(state="disabled")

        ttkb.Button(win, text="Fechar", command=win.destroy, bootstyle="secondary").pack(pady=10)

    def _salvar_cursos(self, novos_dados: dict) -> None:
        """Persiste os dados de cursos e atualiza o combo da tela principal."""
        self.config_cursos = novos_dados
        salvar_cursos_json(self.config_cursos)
        self._refresh_curso_combo()

    def _change_theme(self, theme: str) -> None:
        self.style.theme_use(theme)
        self.settings["theme"] = theme
        save_settings(self.settings)
        self.canvas.configure(bg=self.style.colors.bg)

    def _interromper(self) -> None:
        self.running = False
        self.root.attributes("-topmost", False)
        tkinter.messagebox.showwarning("Cancelado", "Envio de mensagens cancelado.")

    def _limpar_historico(self) -> None:
        if self.running:
            tkinter.messagebox.showwarning("Aviso", "Pare o envio antes de limpar o histórico.")
            return
        if tkinter.messagebox.askyesno("Confirmar", "Isso apagará todos os números já enviados. Continuar?"):
            self.numeros_enviados = set()
            salvar_numeros_enviados(self.numeros_enviados)
            tkinter.messagebox.showinfo("Sucesso", "Histórico limpo com sucesso!")

    # ══════════════════════════════════════════════
    # LÓGICA DE ENVIO
    # ══════════════════════════════════════════════

    def _start_sending(self) -> None:
        if self.running:
            return

        if not self.caminho_arquivo.get():
            tkinter.messagebox.showwarning("Aviso", "Selecione a planilha primeiro.")
            return

        config = self._coletar_config()
        if config is None:
            return

        self.running = True
        self._invalidos_count = 0
        self.lbl_status.config(text="Iniciando...")
        self.lbl_invalidos.config(text="")
        self.root.attributes("-topmost", True)
        self.progress["maximum"] = config.linha_max - config.linha_min
        self.progress["value"] = 0

        threading.Thread(target=self._run_sender, args=(config,), daemon=True).start()

    def _coletar_config(self) -> SendConfig | None:
        simple = self.simple_mode_var.get()

        if not simple:
            if self.course_selected.get() in ("Selecione um Curso", ""):
                tkinter.messagebox.showwarning("Atenção", "Selecione um Curso válido.")
                return None
            if self.partner_selected.get() in ("Instituição Parceira", ""):
                tkinter.messagebox.showwarning("Atenção", "Selecione uma Instituição Parceira.")
                return None

            horario = self.schedule_entry.get()
            duracao = self.duration_entry.get()
            if "Ex:" in horario or not horario.strip():
                tkinter.messagebox.showwarning("Atenção", "Preencha o campo HORÁRIO.")
                return None
            if "Ex:" in duracao or not duracao.strip():
                tkinter.messagebox.showwarning("Atenção", "Preencha o campo DATA DE INÍCIO E FIM.")
                return None

        linhamin = self._parse_linhamin()
        linhamax = self._parse_linhamax()
        if linhamin is None or linhamax is None:
            return None
        if linhamin >= linhamax:
            tkinter.messagebox.showwarning("Atenção", "A linha final deve ser MAIOR que a inicial.")
            return None

        entrada_idade = self.minage_entry.get()
        idademin = int(entrada_idade) if entrada_idade.strip().isdigit() else 0

        return SendConfig(
            caminho_planilha=self.caminho_arquivo.get(),
            linha_min=linhamin,
            linha_max=linhamax,
            simple_mode=simple,
            curso=self.course_selected.get() if not simple else "",
            parceiro=self.partner_selected.get() if not simple else "",
            horario=self._get_field(self.schedule_entry) if not simple else "",
            duracao=self._get_field(self.duration_entry)  if not simple else "",
            idade_minima=idademin,
            por_grupo=(self.group_selected.get() == "SIM"),
            caminho_imagem=self.caminho_imagem.get(),
            config_cursos=self.config_cursos,
        )

    def _parse_linhamin(self) -> int | None:
        val = self.minrange_entry.get()
        if "Última:" in val:
            try:
                return int(val.split(": ")[1])
            except (IndexError, ValueError):
                return self.last_line
        if val.strip() == "":
            return self.last_line
        try:
            return int(val)
        except ValueError:
            tkinter.messagebox.showwarning("Atenção", "O campo 'Da linha' precisa ser um número.")
            return None

    def _parse_linhamax(self) -> int | None:
        val = self.maxrange_entry.get().strip()
        if not val:
            tkinter.messagebox.showwarning("Atenção", "Preencha o campo 'Até a linha'.")
            return None
        try:
            return int(val)
        except ValueError:
            tkinter.messagebox.showwarning("Atenção", "O campo 'Até a linha' precisa ser um número.")
            return None

    def _run_sender(self, config: SendConfig) -> None:
        processadas, puladas, invalidos = 0, 0, []
        cancelado = False
        try:
            sender = MessageSender(
                config=config,
                numeros_enviados=self.numeros_enviados,
                on_progress=self._update_progress,
                is_running=lambda: self.running,
                root=self.root,
                on_status=self._update_status,
                on_invalid=self._on_invalid,
            )
            processadas, puladas, invalidos = sender.run()
            cancelado = not self.running
            self.numeros_enviados = sender.numeros_enviados

        except PermissionError:
            tkinter.messagebox.showerror("Erro", "Feche o arquivo Excel e tente novamente.")
        except Exception as exc:
            tkinter.messagebox.showerror("Erro Grave", f"O programa encontrou um erro:\n{exc}")
        finally:
            if not cancelado:
                self._finalizar_envio(processadas, puladas, invalidos)
            else:
                self.running = False
                self.progress["value"] = 0
                self.lbl_status.config(text="")
                self.lbl_invalidos.config(text="")
                self.root.attributes("-topmost", False)

    def _update_progress(self, value: int) -> None:
        self.progress["value"] = value
        self.root.update_idletasks()

    def _update_status(self, linha: int, total: int, numero: str) -> None:
        def _do():
            self.lbl_status.config(text=f"Enviando linha {linha}/{total} — {numero}")
        self.root.after(0, _do)

    def _on_invalid(self, valor: str) -> None:
        def _do():
            self._invalidos_count += 1
            self.lbl_invalidos.config(text=f"⚠️ Números inválidos/pulados: {self._invalidos_count}")
        self.root.after(0, _do)

    def _finalizar_envio(self, processadas: int, puladas: int, invalidos: list[str]) -> None:
        self.running = False
        self.progress["value"] = 0
        self.lbl_status.config(text="")
        self.root.attributes("-topmost", False)

        resumo_invalidos = ""
        if invalidos:
            resumo_invalidos = f"\n\n⚠️ {len(invalidos)} número(s) ignorado(s) por formato inválido:"
            for n in invalidos[:10]:
                resumo_invalidos += f"\n  • {n}"
            if len(invalidos) > 10:
                resumo_invalidos += f"\n  ... e mais {len(invalidos) - 10}"

        if processadas == 0 and puladas > 0:
            tkinter.messagebox.showwarning(
                "Atenção",
                f"Encontrei {puladas} números já no histórico. Nenhuma mensagem nova foi enviada.\n\n"
                f"Use 'Limpar Histórico' se quiser forçar o reenvio.{resumo_invalidos}",
            )
        elif processadas > 0:
            tkinter.messagebox.showinfo(
                "Concluído",
                f"Envio concluído!\n{processadas} mensagens enviadas.{resumo_invalidos}",
            )
        elif invalidos:
            tkinter.messagebox.showwarning(
                "Atenção",
                f"Nenhuma mensagem enviada.{resumo_invalidos}",
            )