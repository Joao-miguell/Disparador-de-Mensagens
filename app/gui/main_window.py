"""
main_window.py
==============
Janela principal do Disparador de Mensagens AMTECH.
Orquestra a UI e delega o envio para MessageSender.
"""

import threading
import tkinter
import tkinter.messagebox
from tkinter import filedialog, ttk

import ttkbootstrap as ttkb
from ttkbootstrap.style import Style

from app.core.models import SendConfig
from app.core.sender import MessageSender
from app.gui.course_editor import CourseEditor
from app.gui.message_editor import MessageEditor
from app.utils.file_manager import (
    carregar_cursos,
    carregar_numeros_enviados,
    load_last_line,
    load_settings,
    salvar_cursos_json,
    salvar_numeros_enviados,
    save_settings,
)
from app.utils.widgets import add_placeholder, block_combobox_mousewheel, create_tooltip, is_combobox


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

        block_combobox_mousewheel(self.root)

        self._build_scroll_container()
        self._build_header()
        self._build_title()
        self._build_arquivo_block()
        self._build_filtros_block()
        self._build_variaveis_block()
        self._build_linhas_block()
        self._build_acoes_block()
        self._build_credits()

    # ══════════════════════════════════════════════
    # CONSTRUÇÃO DA UI
    # ══════════════════════════════════════════════

    def _build_scroll_container(self) -> None:
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill="both", expand=True)

        bg = self.style.colors.bg
        self.canvas = tkinter.Canvas(self.main_container, bg=bg, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.main_container, orient="vertical", command=self.canvas.yview)

        self.scrollable_frame = ttk.Frame(self.canvas, padding=15)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.root.bind_all("<MouseWheel>", self._on_mousewheel)
        self.root.bind_all("<Button-4>", self._on_mousewheel_linux)
        self.root.bind_all("<Button-5>", self._on_mousewheel_linux)

    def _build_header(self) -> None:
        frame = ttk.Frame(self.scrollable_frame)
        frame.pack(fill="x", pady=(0, 15))

        ttkb.Button(frame, text="⚙️ Gerenciar Cursos",  command=self._abrir_editor_cursos,   bootstyle="secondary-outline").pack(side="left", padx=(0, 5))
        ttkb.Button(frame, text="📝 Editar Mensagem",   command=self._abrir_editor_mensagem, bootstyle="secondary-outline").pack(side="left", padx=5)

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
        ttk.Label(frame, textvariable=self.caminho_arquivo, font=("Arial", 8, "italic"), foreground="gray").pack(pady=(0, 10))

        # Imagem
        self.caminho_imagem = tkinter.StringVar()
        frame_img = ttk.Frame(frame)
        frame_img.pack(pady=(0, 10))
        ttkb.Button(frame_img, text="🖼️ Selecionar Imagem (Opcional)", command=self._selecionar_imagem, bootstyle="primary-outline").pack(side="left", padx=5)
        ttkb.Button(frame_img, text="❌", command=lambda: self.caminho_imagem.set(""), bootstyle="danger-outline").pack(side="left", padx=5)
        ttk.Label(frame, textvariable=self.caminho_imagem, font=("Arial", 8, "italic"), foreground="gray").pack(pady=(0, 10))

        # Modo simples
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

        self.schedule_entry  = self._labeled_entry(frame, "Horário:",             "Ex: 19:00 às 22:00")
        self.minage_entry    = self._labeled_entry(frame, "Idade mínima:")
        self.duration_entry  = self._labeled_entry(frame, "Data de Início e Fim:", "Ex: 10/02 a 15/02")

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

        ttkb.Button(frame, text="🚀 ENVIAR MENSAGENS", command=self._start_sending, bootstyle="success", width=30).pack(pady=(0, 10))

        self.progress = ttkb.Progressbar(frame, orient="horizontal", length=400, mode="determinate", bootstyle="success-striped")
        self.progress.pack(pady=(0, 10))

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
    # HELPERS DE UI
    # ══════════════════════════════════════════════

    def _labeled_entry(self, parent, label_text: str, placeholder: str = "") -> ttk.Entry:
        ttk.Label(parent, text=label_text).pack()
        entry = ttk.Entry(parent, width=35, bootstyle="info")
        entry.pack(pady=(0, 5))
        if placeholder:
            add_placeholder(entry, placeholder)
        return entry

    def _refresh_curso_combo(self) -> None:
        cursos = [c for lista in self.config_cursos.values() for c in lista]
        if hasattr(self, "combo_course"):
            self.combo_course["values"] = cursos

    def _toggle_inputs(self) -> None:
        disabled = self.simple_mode_var.get()
        entry_state = "disabled" if disabled else "normal"
        combo_state = "disabled" if disabled else "readonly"

        for w in (self.schedule_entry, self.minage_entry, self.duration_entry):
            w.config(state=entry_state)
        for combo in (self.combo_course, self.combo_partner, self.combo_group):
            combo.config(state=combo_state)

    def _on_mousewheel(self, event) -> str | None:
        if self._mousewheel_over_combobox(event.widget):
            return "break"
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return None

    def _on_mousewheel_linux(self, event) -> str | None:
        if self._mousewheel_over_combobox(event.widget):
            return "break"
        self.canvas.yview_scroll(-1 if event.num == 4 else 1, "units")
        return None

    @staticmethod
    def _mousewheel_over_combobox(widget) -> bool:
        while widget:
            if is_combobox(widget):
                return True
            widget = widget.master
        return False

    # ══════════════════════════════════════════════
    # AÇÕES
    # ══════════════════════════════════════════════

    def _selecionar_arquivo(self) -> None:
        path = filedialog.askopenfilename(title="Selecione a planilha", filetypes=[("Excel", "*.xlsx *.xls")])
        if path:
            self.caminho_arquivo.set(path)

    def _selecionar_imagem(self) -> None:
        path = filedialog.askopenfilename(title="Selecione a imagem", filetypes=[("Imagens", "*.png *.jpg *.jpeg")])
        if path:
            self.caminho_imagem.set(path)

    def _abrir_editor_cursos(self) -> None:
        CourseEditor(self.root, self.config_cursos, self._salvar_cursos)

    def _abrir_editor_mensagem(self) -> None:
        MessageEditor(self.root)

    def _salvar_cursos(self, novos_dados: dict) -> None:
        self.config_cursos = novos_dados
        salvar_cursos_json(self.config_cursos)
        self._refresh_curso_combo()
        tkinter.messagebox.showinfo("Sucesso", "Lista de cursos atualizada com sucesso!")

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
            horario=self.schedule_entry.get() if not simple else "",
            duracao=self.duration_entry.get() if not simple else "",
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
        try:
            sender = MessageSender(
                config=config,
                numeros_enviados=self.numeros_enviados,
                on_progress=self._update_progress,
                is_running=lambda: self.running,
                root=self.root,
            )
            processadas, puladas = sender.run()

            self.numeros_enviados = sender.numeros_enviados

        except PermissionError:
            tkinter.messagebox.showerror("Erro", "Feche o arquivo Excel e tente novamente.")
        except Exception as exc:
            tkinter.messagebox.showerror("Erro Grave", f"O programa encontrou um erro:\n{exc}")
        finally:
            self._finalizar_envio(
                processadas if self.running else 0,
                puladas if self.running else 0,
            )

    def _update_progress(self, value: int) -> None:
        self.progress["value"] = value
        self.root.update_idletasks()

    def _finalizar_envio(self, processadas: int, puladas: int) -> None:
        self.running = False
        self.progress["value"] = 0
        self.root.attributes("-topmost", False)

        if processadas == 0 and puladas > 0:
            tkinter.messagebox.showwarning(
                "Atenção",
                f"Encontrei {puladas} números já no histórico. Nenhuma mensagem nova foi enviada.\n\n"
                "Use 'Limpar Histórico' se quiser forçar o reenvio.",
            )
        elif processadas > 0:
            tkinter.messagebox.showinfo("Concluído", f"Envio concluído!\n{processadas} mensagens enviadas.")