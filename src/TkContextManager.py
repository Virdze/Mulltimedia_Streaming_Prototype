from ClientGUI import ClientGUI
from LockedString import LockedString


class TkContextManager:

    root : Tk
    gui_app : ClientGUI

    def __init__(self, addr : str, port : int, ls : LockedString):
        import sys
        if sys.version_info[0] == 3:
            import tkinter as Tk
        else:
            import Tkinter as Tk

        self.root = Tk.Tk()
        self.gui_app = ClientGUI(self.root, 'Cliente Exemplo', addr, port, ls)

    def run(self):
        self.root.mainloop()
