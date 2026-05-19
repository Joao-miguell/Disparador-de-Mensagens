"""Utilitários: persistência em disco e widgets reutilizáveis."""

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
    save_last_line,
    save_settings,
)
from app.utils.widgets import (
    ToolTip,
    add_placeholder,
    block_combobox_mousewheel,
    create_tooltip,
    is_combobox,
)

__all__ = [
    "carregar_cursos",
    "salvar_cursos_json",
    "carregar_templates_mensagens",
    "salvar_templates_mensagens",
    "carregar_mensagem_padrao",
    "salvar_mensagem_padrao",
    "load_last_line",
    "save_last_line",
    "load_settings",
    "save_settings",
    "carregar_numeros_enviados",
    "salvar_numeros_enviados",
    "add_placeholder",
    "block_combobox_mousewheel",
    "create_tooltip",
    "is_combobox",
    "ToolTip",
]
