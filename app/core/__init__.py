"""Lógica de negócio: modelos de dados e envio de mensagens."""

from app.core.models import SendConfig
from app.core.sender import MessageSender

__all__ = ["SendConfig", "MessageSender"]
