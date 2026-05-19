import tkinter as tk
from app.gui.main_window import CourseOfferGUI


def main():
    root = tk.Tk()
    CourseOfferGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()