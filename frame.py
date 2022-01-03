"""Main Frame of the application."""
import wx


class Frame(wx.Frame):
    """Main frame of the application. Handle menu operations."""
    def __init__(self):
        super().__init__(None, title="TTK-PY", size=(800,600))

        menu_bar = wx.MenuBar()

        # File menu
        file_menu = wx.Menu()
        file_menu.Append(101, "Uusi Tarjous", "Luo uusi tarjous")
        file_menu.Append(102, "Avaa Tarjous", "Avaa tallennettu tarjous")
        file_menu.Append(103, "Poista Tarjous", "Poista tarjous")

        menu_bar.Append(file_menu, "Tiedosto")

        self.SetMenuBar(menu_bar)

        self.Bind(wx.EVT_MENU, self.new_quote, id=101)
        self.Bind(wx.EVT_MENU, self.open_quote, id=102)
        self.Bind(wx.EVT_MENU, self.delete_quote, id=103)

    def new_quote(self, _evt):
        """Handle new quote menu event"""
        print("New quote")

    def open_quote(self, _evt):
        """Handle open quote menu event"""
        print("Open quote")

    def delete_quote(self, _evt):
        """Handle delete quote menu event"""
        print("Delete quote")
