import wx.grid as wxg


class TtkGrid(wxg.Grid):
    def __init__(self, parent, setup):
        super().__init__(parent)

        self.data = None
        self.setup = setup

    def change_data(self, data):
        """Change the data to given source."""
        print("TtkGrid.change_data")
        self.data = data
        if data is None:
            print("\tclear grid")
        else:
            print("\trefresh to new size")

    def changed_rows(self, n_change):
        """Update the grid with a size change.
        
        Positive n_change for added rows. Negative for deleted.
        """
        print(f"TtkGrid.changed_rows - rows changed: {n_change}")
    
    def refresh_attr(self):
        """Refresh the cell attributes where required."""
        print("TtkGrid.refresh_attr")
        self.Refresh()


class SetupGrid(wxg.Grid):
    def __init__(self, parent, setup):
        super().__init__(parent)

        self.data = None
        self.setup = setup

    def change_data(self, data):
        """Change the data to given source."""
        print("SetupGrid.change_data")
        self.data = data
        if data is None:
            print("\tclear grid")
        else:
            print("\trefresh to new size")