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

        # ── Gerenciador de páginas ──
        self._pages: dict[str, ttk.Frame] = {}
        self._current_page: ttk.Frame | None = None

        # main_container é criado antes das páginas (é o pai de todas elas)
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

        # Os combos existem após _build_main_page — só então registrar scroll
        block_combobox_mousewheel(self.root, on_wheel=self._scroll_canvas)
        self._configure_combobox_scroll()

        self._show_page("main")

    # ══════════════════════════════════════════════
    # GERENCIADOR DE PÁGINAS
    # ══════════════════════════════════════════════

    def _show_page(self, name: str) -> None:
        """Esconde a página atual e exibe a solicitada, recarregando dados lazy."""
        # Recarrega dados dinâmicos antes de exibir a página
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
        """Constrói o scroll container e todos os blocos da tela principal."""
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

        ttkb.Button(frame, text="⚙️ Gerenciar Cursos",  command=lambda: self._show_page("cursos"),  bootstyle="secondary-outline").pack(side="left", padx=(0, 5))  # type: ignore
        ttkb.Button(frame, text="📝 Editar Mensagem",   command=lambda: self._show_page("editor"),  bootstyle="secondary-outline").pack(side="left", padx=5)  # type: ignore

        frame_tema = ttk.Frame(frame)
        frame_tema.pack(side="right")
        ttk.Label(frame_tema, text="🎨 Tema:", font=("Arial", 9)).pack(side="left", padx=(0, 5))

        temas_cap = [t.capitalize() for t in self._THEMES]
        tema_atual = self.settings.get("theme", "journal").capitalize()
        self.theme_selected = tkinter.StringVar(value=tema_atual)

        self.combo_theme = ttkb.Combobox(  # type: ignore
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
        ttk.Label(  # type: ignore
            self.scrollable_frame,
            text="Disparador de Mensagens",
            font=("Arial", 22, "bold"),
            bootstyle="primary", # type: ignore
        ).pack(pady=(5, 15))

    def _build_arquivo_block(self) -> None:
        frame = ttk.LabelFrame(self.scrollable_frame, text=" Base de Dados ", padding=15, bootstyle="info")  # type: ignore
        frame.pack(fill="x", pady=(0, 15))

        self.caminho_arquivo = tkinter.StringVar()
        ttkb.Button(frame, text="📁 Selecionar Planilha de Alunos", command=self._selecionar_arquivo, bootstyle="info-outline").pack(pady=(0, 5))  # type: ignore
        ttk.Label(frame, textvariable=self.caminho_arquivo, font=("Arial", 8, "italic"), foreground="gray").pack(pady=(0, 2))
        self.lbl_planilha_info = ttk.Label(frame, text="", font=("Arial", 8, "bold"))
        self.lbl_planilha_info.pack(pady=(0, 8))

        # Imagem
        self.caminho_imagem = tkinter.StringVar()
        frame_img = ttk.Frame(frame)
        frame_img.pack(pady=(0, 10))
        ttkb.Button(frame_img, text="🖼️ Selecionar Imagem (Opcional)", command=self._selecionar_imagem, bootstyle="primary-outline").pack(side="left", padx=5)  # type: ignore
        ttkb.Button(frame_img, text="❌", command=lambda: self.caminho_imagem.set(""), bootstyle="danger-outline").pack(side="left", padx=5)  # type: ignore
        ttk.Label(frame, textvariable=self.caminho_imagem, font=("Arial", 8, "italic"), foreground="gray").pack(pady=(0, 10))

        # Modo simples
        self.simple_mode_var = tkinter.BooleanVar(value=False)
        ttkb.Checkbutton(  # type: ignore
            frame,
            text="Enviar Apenas Mensagem Personalizada (Ignorar Variáveis e Cursos)",
            variable=self.simple_mode_var,
            command=self._toggle_inputs,
            bootstyle="info-round-toggle",
        ).pack(pady=(5, 0))

    def _build_filtros_block(self) -> None:
        frame = ttk.LabelFrame(self.scrollable_frame, text=" Seleção de Curso e Instituição ", padding=15, bootstyle="primary")  # type: ignore
        frame.pack(fill="x", pady=(0, 15))

        self.course_selected = tkinter.StringVar(value="Selecione um Curso")
        self.combo_course = ttkb.Combobox(frame, textvariable=self.course_selected, state="readonly", bootstyle="primary")  # type: ignore
        self._refresh_curso_combo()
        self.combo_course.pack(pady=(0, 10), fill="x", padx=40)

        self.partner_selected = tkinter.StringVar(value="Instituição Parceira")
        self.combo_partner = ttkb.Combobox(  # type: ignore
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
        self.combo_group = ttkb.Combobox(  # type: ignore
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
        frame = ttk.LabelFrame(self.scrollable_frame, text=" Variáveis da Mensagem ", padding=15, bootstyle="secondary")  # type: ignore
        frame.pack(fill="x", pady=(0, 15))

        self.lbl_horario  = ttk.Label(frame, text="Horário:")
        self.lbl_horario.pack()
        self.schedule_entry = ttk.Entry(frame, width=35, bootstyle="info")  # type: ignore
        self.schedule_entry.pack(pady=(0, 5))
        add_placeholder(self.schedule_entry, "Ex: 19:00 às 22:00")

        self.lbl_minage = ttk.Label(frame, text="Idade mínima:")
        self.lbl_minage.pack()
        self.minage_entry = ttk.Entry(frame, width=35, bootstyle="info")  # type: ignore
        self.minage_entry.pack(pady=(0, 5))

        self.lbl_duration = ttk.Label(frame, text="Data de Início e Fim:")
        self.lbl_duration.pack()
        self.duration_entry = ttk.Entry(frame, width=35, bootstyle="info")  # type: ignore
        self.duration_entry.pack(pady=(0, 5))
        add_placeholder(self.duration_entry, "Ex: 10/02 a 15/02")

    def _build_linhas_block(self) -> None:
        frame = ttk.LabelFrame(self.scrollable_frame, text=" Intervalo da Planilha ", padding=15, bootstyle="warning")  # type: ignore
        frame.pack(fill="x", pady=(0, 15))

        inner = ttk.Frame(frame)
        inner.pack()

        frame_min = ttk.Frame(inner)
        frame_min.pack(side="left", padx=10)
        ttk.Label(frame_min, text="Da linha:").pack(anchor="w")
        self.minrange_entry = ttk.Entry(frame_min, width=22, bootstyle="warning") # type: ignore
        self.minrange_entry.pack()
        add_placeholder(self.minrange_entry, f"Última: {self.last_line}")

        frame_max = ttk.Frame(inner)
        frame_max.pack(side="left", padx=10)
        ttk.Label(frame_max, text="Até a linha:").pack(anchor="w")
        self.maxrange_entry = ttk.Entry(frame_max, width=22, bootstyle="warning") # type: ignore
        self.maxrange_entry.pack()

    def _build_acoes_block(self) -> None:
        frame = ttk.Frame(self.scrollable_frame)
        frame.pack(fill="x", pady=(5, 0))

        frame_top_btns = ttk.Frame(frame)
        frame_top_btns.pack(pady=(0, 10))
        ttkb.Button(frame_top_btns, text="🚀 ENVIAR MENSAGENS", command=self._start_sending, bootstyle="success", width=28).pack(side="left", padx=(0, 8))  # type: ignore
        ttkb.Button(frame_top_btns, text="👁️ Preview", command=self._abrir_preview, bootstyle="info-outline", width=12).pack(side="left")  # type: ignore

        self.progress = ttkb.Progressbar(frame, orient="horizontal", length=400, mode="determinate", bootstyle="success-striped")  # type: ignore
        self.progress.pack(pady=(0, 5))

        self.lbl_status = ttk.Label(frame, text="", font=("Arial", 8), foreground="gray")
        self.lbl_status.pack(pady=(0, 2))

        self.lbl_invalidos = ttk.Label(frame, text="", font=("Arial", 8), foreground="#e67e22")
        self.lbl_invalidos.pack(pady=(0, 8))

        frame_btns = ttk.Frame(frame)
        frame_btns.pack()

        ttkb.Button(frame_btns, text="🛑 Interromper",    command=self._interromper,             bootstyle="danger").pack(side="left", padx=5)  # type: ignore
        ttkb.Button(frame_btns, text="🗑️ Limpar Histórico", command=self._limpar_historico,       bootstyle="warning-outline").pack(side="left", padx=5)  # type: ignore

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
        """Replica a UI do MessageEditor como página embutida."""
        # ── Barra superior: Voltar ──
        top_bar = ttk.Frame(container, padding=(10, 8))
        top_bar.pack(fill="x")
        ttkb.Button(top_bar, text="← Voltar", command=lambda: self._show_page("main"), bootstyle="secondary-outline").pack(side="left")  # type: ignore

        # ── Header informativo ──
        ttkb.Label(  # type: ignore
            container,
            text="Edite o modelo da mensagem abaixo.",
            font=("Arial", 12, "bold"),
        ).pack(pady=(5, 3))
        ttkb.Label(  # type: ignore
            container,
            text="Use as variáveis entre chaves { } para que o robô substitua pelos dados reais.",
            font=("Arial", 9),
        ).pack()
        info_vars = (
            "{nome} - Nome do Aluno  |  {parceiro} - Instituição (SENAI/SENAC)  |  {curso} - Nome do Curso\n"
            "{idade_minima} - Idade Mínima  |  {duracao} - Data de Início/Fim  |  {horario} - Horário do Curso"
        )
        ttkb.Label(container, text=info_vars, bootstyle="info", justify="center").pack(pady=8)  # type: ignore

        # ── Biblioteca de templates ──
        # lib_frame usa grid: linha 0 = combobox (fill), linha 1 = botões centralizados
        lib_frame = ttk.LabelFrame(container, text=" 📚 Biblioteca de Modelos Salvos ", padding=10, bootstyle="primary")  # type: ignore
        lib_frame.pack(fill="x", padx=15, pady=5)
        lib_frame.columnconfigure(0, weight=1)

        # Linha 0: combobox ocupa toda a largura
        self.combo_templates = ttkb.Combobox(lib_frame, state="readonly")  # type: ignore
        self.combo_templates.grid(row=0, column=0, sticky="ew", padx=5, pady=(0, 6))
        configure_combobox_dropdown_scroll(self.combo_templates)

        # Linha 1: 4 botões centralizados — nunca ficam cortados independente da escala
        btn_row = ttk.Frame(lib_frame)
        btn_row.grid(row=1, column=0)
        template_buttons = [
            ("📂 Carregar",   "info",    self._editor_load_template),
            ("➕ Salvar Novo", "success", self._editor_save_new_template),
            ("🔄 Atualizar",  "warning", self._editor_update_template),
            ("🗑️ Excluir",    "danger",  self._editor_delete_template),
        ]
        for text, style, cmd in template_buttons:
            ttkb.Button(btn_row, text=text, bootstyle=style, command=cmd).pack(side="left", padx=4)  # type: ignore

        # ── Área de texto (atributo público — usado pelos testes) ──
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

        # ── Botão aplicar ──
        ttkb.Button(  # type: ignore
            container,
            text="✅ APLICAR ESTA MENSAGEM NO ROBÔ",
            command=self._salvar_mensagem_ativa,
            bootstyle="success",
            width=40,
        ).pack(pady=10)

        # Carrega templates no combo
        self._editor_templates = carregar_templates_mensagens()
        self._editor_refresh_combo()

    def _reload_editor_text(self) -> None:
        """Recarrega texto e templates do disco ao entrar na página do editor."""
        # Recarrega templates do disco para refletir alterações externas
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

    def _editor_refresh_combo(self) -> None:
        self.combo_templates["values"] = list(self._editor_templates.keys())

    def _editor_load_template(self) -> None:
        nome = self.combo_templates.get()
        if nome in self._editor_templates:
            self.txt_mensagem.delete("1.0", tkinter.END)
            self.txt_mensagem.insert("1.0", self._editor_templates[nome])
        else:
            tkinter.messagebox.showwarning("Aviso", "Selecione um modelo válido para carregar.", parent=self.root)

    def _editor_save_new_template(self) -> None:
        nome = simpledialog.askstring(
            "Salvar Novo Modelo",
            "Digite um nome para este modelo (ex: Aviso de Vagas):",
            parent=self.root,
        )
        if not nome:
            return
        if nome in self._editor_templates:
            tkinter.messagebox.showwarning(
                "Aviso",
                "Já existe um modelo com esse nome. Use o botão 'Atualizar'.",
                parent=self.root,
            )
            return
        self._editor_templates[nome] = self._editor_get_text()
        salvar_templates_mensagens(self._editor_templates)
        self._editor_refresh_combo()
        self.combo_templates.set(nome)
        tkinter.messagebox.showinfo("Sucesso", f"Modelo '{nome}' salvo na biblioteca!", parent=self.root)

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
            self.combo_templates.set("")
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
        """Replica a UI do CourseEditor como página embutida."""
        # O container usa .grid() para as duas colunas principais.
        # Os frames internos de botões (frame_cat_btns, frame_cur_btns) usam .pack() — correto.
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)
        container.grid_rowconfigure(2, weight=1)

        # ── Barra superior: Voltar ──
        top_bar = ttk.Frame(container, padding=(10, 8))
        top_bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        ttkb.Button(top_bar, text="← Voltar", command=lambda: self._show_page("main"), bootstyle="secondary-outline").pack(side="left")  # type: ignore
        ttk.Label(top_bar, text="Gerenciador de Cursos e Categorias", font=("Arial", 12, "bold")).pack(side="left", padx=15)

        # ── Cabeçalhos das colunas ──
        ttkb.Label(container, text="1. Categorias (Grupos)", font=("Arial", 10, "bold")).grid(  # type: ignore
            row=1, column=0, pady=10
        )
        ttkb.Label(container, text="2. Cursos da Categoria", font=("Arial", 10, "bold")).grid(  # type: ignore
            row=1, column=1, pady=10
        )

        # ── Listbox categorias ──
        self.listbox_categorias = tkinter.Listbox(container, exportselection=False)
        self.listbox_categorias.grid(row=2, column=0, sticky="nsew", padx=10)
        self.listbox_categorias.bind("<<ListboxSelect>>", self._cursos_ao_selecionar_categoria)

        frame_cat_btns = ttkb.Frame(container)  # type: ignore
        frame_cat_btns.grid(row=3, column=0, pady=5)
        ttkb.Button(frame_cat_btns, text="+ Add Categoria", command=self._cursos_add_categoria, bootstyle="success-outline", width=15).pack(pady=2)  # type: ignore
        ttkb.Button(frame_cat_btns, text="- Remover",       command=self._cursos_del_categoria, bootstyle="danger-outline",  width=15).pack(pady=2)  # type: ignore

        # ── Listbox cursos ──
        self.listbox_cursos = tkinter.Listbox(container, exportselection=False)
        self.listbox_cursos.grid(row=2, column=1, sticky="nsew", padx=10)

        frame_cur_btns = ttkb.Frame(container)  # type: ignore
        frame_cur_btns.grid(row=3, column=1, pady=5)
        ttkb.Button(frame_cur_btns, text="+ Add Curso", command=self._cursos_add_curso, bootstyle="info-outline",   width=15).pack(pady=2)  # type: ignore
        ttkb.Button(frame_cur_btns, text="- Remover",   command=self._cursos_del_curso, bootstyle="danger-outline", width=15).pack(pady=2)  # type: ignore

        # ── Rodapé: Salvar ──
        ttkb.Button(  # type: ignore
            container,
            text="💾 SALVAR ALTERAÇÕES",
            command=self._salvar_cursos_editor,
            bootstyle="success",
        ).grid(row=4, column=0, columnspan=2, pady=15, sticky="ew", padx=20)

    def _reload_curso_dados(self) -> None:
        """Reinicia _editor_dados como cópia fresca de config_cursos e atualiza as listboxes."""
        self._editor_dados = {k: list(v) for k, v in self.config_cursos.items()}
        self._cursos_refresh_categorias()
        # Limpa seleção e conteúdo para evitar estado visual inconsistente
        self.listbox_categorias.selection_clear(0, tkinter.END)
        self.listbox_cursos.delete(0, tkinter.END)

    def _cursos_refresh_categorias(self) -> None:
        self.listbox_categorias.delete(0, tkinter.END)
        for cat in self._editor_dados:
            self.listbox_categorias.insert(tkinter.END, cat)

    def _cursos_refresh_cursos(self, categoria: str) -> None:
        self.listbox_cursos.delete(0, tkinter.END)
        for curso in self._editor_dados.get(categoria, []):
            self.listbox_cursos.insert(tkinter.END, curso)

    def _cursos_ao_selecionar_categoria(self, _event) -> None:
        sel = self.listbox_categorias.curselection()
        if sel:
            self._cursos_refresh_cursos(self.listbox_categorias.get(sel[0]))

    def _cursos_categoria_selecionada(self) -> str | None:
        sel = self.listbox_categorias.curselection()
        return self.listbox_categorias.get(sel[0]) if sel else None

    def _cursos_add_categoria(self) -> None:
        nova = simpledialog.askstring("Nova Categoria", "Nome da nova categoria:", parent=self.root)
        if nova and nova not in self._editor_dados:
            self._editor_dados[nova] = []
            self._cursos_refresh_categorias()

    def _cursos_del_categoria(self) -> None:
        cat = self._cursos_categoria_selecionada()
        if cat and tkinter.messagebox.askyesno(
            "Confirmar", f"Apagar a categoria '{cat}' e todos os seus cursos?", parent=self.root
        ):
            del self._editor_dados[cat]
            self._cursos_refresh_categorias()
            self.listbox_cursos.delete(0, tkinter.END)

    def _cursos_add_curso(self) -> None:
        cat = self._cursos_categoria_selecionada()
        if not cat:
            tkinter.messagebox.showwarning("Aviso", "Selecione uma categoria primeiro!", parent=self.root)
            return
        novo = simpledialog.askstring("Novo Curso", f"Nome do curso para '{cat}':", parent=self.root)
        if novo:
            self._editor_dados[cat].append(novo)
            self._cursos_refresh_cursos(cat)

    def _cursos_del_curso(self) -> None:
        cat = self._cursos_categoria_selecionada()
        sel_cur = self.listbox_cursos.curselection()
        if cat and sel_cur:
            curso = self.listbox_cursos.get(sel_cur[0])
            self._editor_dados[cat].remove(curso)
            self._cursos_refresh_cursos(cat)

    def _salvar_cursos_editor(self) -> None:
        self._salvar_cursos(self._editor_dados)
        # Navega primeiro, depois exibe o popup — feedback aparece sobre a tela principal
        self._show_page("main")
        tkinter.messagebox.showinfo("Sucesso", "Lista de cursos atualizada com sucesso!", parent=self.root)

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
            self.combo_templates,  # página editor
        ):
            configure_combobox_dropdown_scroll(combo)

    def _scroll_canvas(self, event) -> None:
        # Só rola o canvas da página main quando ela está ativa
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
            return widget._w  # type: ignore

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

    def _on_mousewheel(self, event) -> str | None:
        # Ignora eventos de Toplevels externos (ex: janela de Preview)
        if event.widget.winfo_toplevel() is not self.root:
            return None
        path = self._popdown_listbox_path_at_pointer(event)
        if path is not None:
            scroll_listbox_path(self.root.tk, path, event)
            return "break"
        if is_combobox_dropdown_listbox(event.widget):
            scroll_listbox(event.widget, event)
            return "break"
        self._scroll_canvas(event)
        return None

    def _on_mousewheel_linux(self, event) -> str | None:
        # Ignora eventos de Toplevels externos (ex: janela de Preview)
        if event.widget.winfo_toplevel() is not self.root:
            return None
        path = self._popdown_listbox_path_at_pointer(event)
        if path is not None:
            scroll_listbox_path(self.root.tk, path, event)
            return "break"
        if is_combobox_dropdown_listbox(event.widget):
            scroll_listbox(event.widget, event)
            return "break"
        self._scroll_canvas(event)
        return None

    # ══════════════════════════════════════════════
    # AÇÕES
    # ══════════════════════════════════════════════

    def _selecionar_arquivo(self) -> None:
        path = filedialog.askopenfilename(title="Selecione a planilha", filetypes=[("Excel", "*.xlsx *.xls")])
        if path:
            self.caminho_arquivo.set(path)
            self._validar_planilha(path)

    def _validar_planilha(self, path: str) -> None:
        """Verifica colunas obrigatórias e exibe contagem de contatos."""
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
        path = filedialog.askopenfilename(title="Selecione a imagem", filetypes=[("Imagens", "*.png *.jpg *.jpeg")])
        if path:
            self.caminho_imagem.set(path)

    @staticmethod
    def _get_field(entry: ttk.Entry, placeholder_prefix: str = "Ex:") -> str:
        """Retorna o valor do campo, ou string vazia se ainda exibe o placeholder."""
        val = entry.get()
        return "" if placeholder_prefix in val else val

    def _abrir_preview(self) -> None:
        """Abre janela de preview com a mensagem formatada com os valores atuais."""
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

        ttkb.Button(win, text="Fechar", command=win.destroy, bootstyle="secondary").pack(pady=10)  # type: ignore

    def _salvar_cursos(self, novos_dados: dict) -> None:
        """Persiste os dados de cursos e atualiza o combo da tela principal.
        O feedback ao usuário fica a cargo do chamador."""
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
            return   # validação falhou

        self.running = True
        self._invalidos_count = 0
        self.lbl_status.config(text="Iniciando...")
        self.lbl_invalidos.config(text="")
        self.root.attributes("-topmost", True)
        self.progress["maximum"] = config.linha_max - config.linha_min
        self.progress["value"] = 0

        threading.Thread(target=self._run_sender, args=(config,), daemon=True).start()

    def _coletar_config(self) -> SendConfig | None:
        """Lê os campos da UI e retorna um SendConfig validado, ou None em erro."""
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

        # Linhas
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
        """Atualiza o label de status de forma thread-safe."""
        def _do():
            self.lbl_status.config(text=f"Enviando linha {linha}/{total} — {numero}")
        self.root.after(0, _do)

    def _on_invalid(self, valor: str) -> None:
        """Incrementa o contador de inválidos de forma thread-safe."""
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