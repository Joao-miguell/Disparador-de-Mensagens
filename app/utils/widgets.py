import tkinter as tk
from tkinter import ttk


def get_combobox_popdown_listbox_path(combobox: ttk.Combobox) -> str | None:
    """Caminho Tcl do Listbox da lista suspensa do Combobox."""
    try:
        popdown = combobox.tk.call("ttk::combobox::PopdownWindow", combobox._w)
        for child in combobox.tk.splitlist(combobox.tk.call("winfo", "children", f"{popdown}.f")):
            if str(child).endswith(".l"):
                return str(child)
    except tk.TclError:
        pass
    return None


def get_combobox_popdown_listbox(combobox: ttk.Combobox) -> tk.Listbox | None:
    """Referência Tkinter ao Listbox da lista suspensa (para bind de eventos)."""
    path = get_combobox_popdown_listbox_path(combobox)
    if path is None:
        return None
    return _tcl_path_to_listbox(combobox, path)


def _tcl_path_to_listbox(combobox: ttk.Combobox, path: str) -> tk.Listbox:
    """Referencia um Listbox Tcl que não está no mapa de filhos do Tkinter."""
    listbox = tk.Listbox.__new__(tk.Listbox)
    listbox.master = combobox
    listbox.tk = combobox.tk
    listbox._w = path
    listbox.children = {}
    return listbox


def combobox_dropdown_is_open(combobox: ttk.Combobox) -> bool:
    path = get_combobox_popdown_listbox_path(combobox)
    if path is None:
        return False
    try:
        return bool(combobox.tk.call("winfo", "ismapped", path))
    except tk.TclError:
        return False


def is_combobox_dropdown_listbox(widget: tk.Misc) -> bool:
    """True se o widget for o Listbox interno de um Combobox aberto."""
    if widget is None:
        return False
    try:
        if widget.winfo_class() != "Listbox":
            return False
    except tk.TclError:
        return False
    path = str(getattr(widget, "_w", widget)).lower()
    return "popdown" in path


def scroll_listbox_path(tk: tk.Misc, path: str, event) -> None:
    if getattr(event, "num", None) == 4:
        tk.call(path, "yview", "scroll", -1, "units")
    elif getattr(event, "num", None) == 5:
        tk.call(path, "yview", "scroll", 1, "units")
    else:
        tk.call(path, "yview", "scroll", int(-1 * (event.delta / 120)), "units")


def scroll_listbox(listbox: tk.Misc, event) -> None:
    scroll_listbox_path(listbox.tk, listbox._w, event)


def configure_combobox_dropdown_scroll(combobox: ttk.Combobox) -> None:
    """Com a lista aberta, a roda do mouse rola só as opções do Combobox."""

    def postcommand() -> None:
        path = get_combobox_popdown_listbox_path(combobox)
        if path is None:
            return

        listbox = _tcl_path_to_listbox(combobox, path)

        def on_wheel(event):
            scroll_listbox_path(combobox.tk, path, event)
            return "break"

        for sequence in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            listbox.bind(sequence, on_wheel)

    combobox.configure(postcommand=postcommand)


def block_combobox_mousewheel(root: tk.Misc, on_wheel=None) -> None:
    """Bloqueia mudança de valor no Combobox pela roda; opcionalmente repassa o scroll."""

    def _block(event):
        widget = event.widget
        if isinstance(widget, ttk.Combobox) and combobox_dropdown_is_open(widget):
            path = get_combobox_popdown_listbox_path(widget)
            if path is not None:
                scroll_listbox_path(widget.tk, path, event)
            return "break"
        if on_wheel is not None:
            on_wheel(event)
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
