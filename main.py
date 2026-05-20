import os
import sys
import tkinter as tk

from app.gui.main_window import CourseOfferGUI
from app.core.updater import verificar_atualizacao


def resource_path(relative: str) -> str:
    """Retorna o caminho absoluto do recurso, compatível com PyInstaller."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)


def main():
    root = tk.Tk()
    try:
        root.iconbitmap(resource_path("icone.ico"))
    except Exception:
        pass  # ícone opcional — não impede a execução se o arquivo não existir
    CourseOfferGUI(root)
    verificar_atualizacao(root)
    root.mainloop()


if __name__ == "__main__":
    main()