import tkinter as tk
from tkinter import ttk


def block_combobox_mousewheel(root: tk.Misc) -> None:
    """Impede que a roda do mouse altere Comboboxes; seleção apenas por clique."""

    def _block(_event):
        return "break"

    for sequence in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
        root.bind_class("TCombobox", sequence, _block)


def is_combobox(widget: tk.Misc) -> bool:
    return isinstance(widget, ttk.Combobox)


def add_placeholder(entry, placeholder_text: str, color: str = "grey") -> None:
    """Adiciona texto de placeholder a um Entry que some ao focar."""
    entry.insert(0, placeholder_text)
    entry.configure(foreground=color)

    def on_focus_in(event):
        if entry.get() == placeholder_text:
            entry.delete(0, "end")
            entry.configure(foreground="")

    def on_focus_out(event):
        if entry.get() == "":
            entry.insert(0, placeholder_text)
            entry.configure(foreground=color)

    entry.bind("<FocusIn>", on_focus_in)
    entry.bind("<FocusOut>", on_focus_out)


class ToolTip:
    """Tooltip flutuante que aparece ao passar o mouse sobre um widget."""

    def __init__(self, widget: tk.Widget, text: str) -> None:
        self.widget = widget
        self.text = text
        self.tipwindow: tk.Toplevel | None = None

    def show(self) -> None:
        if self.tipwindow or not self.text:
            return
        x, y, _cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += cy + self.widget.winfo_rooty() + 25

        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            tw,
            text=self.text,
            justify=tk.LEFT,
            background="#ffffe0",
            relief=tk.SOLID,
            borderwidth=1,
            font=("tahoma", "8", "normal"),
        )
        label.pack(ipadx=1)

    def hide(self) -> None:
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None


def create_tooltip(widget: tk.Widget, text: str) -> ToolTip:
    """Cria e vincula um ToolTip a um widget. Retorna a instância criada."""
    tip = ToolTip(widget, text)
    widget.bind("<Enter>", lambda _e: tip.show())
    widget.bind("<Leave>", lambda _e: tip.hide())
    return tip