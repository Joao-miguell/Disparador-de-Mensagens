import tkinter as tk
from app.gui.main_window import CourseOfferGUI
from app.core.updater import verificar_atualizacao


def main():
    root = tk.Tk()
    root.iconbitmap("icone.ico")
    CourseOfferGUI(root)
    verificar_atualizacao(root)
    root.mainloop()


if __name__ == "__main__":
    main()