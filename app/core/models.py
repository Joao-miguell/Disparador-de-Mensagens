"""
models.py
=========
Tipos de dados usados em toda a aplicação.
Centralizar aqui evita passar dezenas de parâmetros avulsos entre classes.
"""

from dataclasses import dataclass, field


@dataclass
class SendConfig:
    """Parâmetros coletados da UI antes de um ciclo de envio."""

    # Planilha
    caminho_planilha: str
    linha_min: int
    linha_max: int

    # Modo
    simple_mode: bool = False

    # Campos do modo completo
    curso: str = ""
    parceiro: str = ""
    horario: str = ""
    duracao: str = ""
    idade_minima: int = 0
    por_grupo: bool = False   # True = "SIM", False = "NÃO"

    # Imagem opcional
    caminho_imagem: str = ""

    # Configuração de cursos (para busca de categoria)
    config_cursos: dict = field(default_factory=dict)