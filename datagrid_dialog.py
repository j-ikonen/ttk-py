from ttk_grid import TtkGrid
import wx

# NoteBookDialog
NBD_TITLE = ""
BORDER = 5
NBD_SIZE = (250, 250)


class NotebookDialog(wx.Dialog):
    def __init__(self, parent, title, pages):
        super().__init__(
            parent,
            title=title,
            size=NBD_SIZE,
            style=wx.RESIZE_BORDER|wx.DEFAULT_DIALOG_STYLE)
        self.CenterOnParent()

        self.pagedata = pages
        self.book = wx.Notebook(self)
        
        btn_ok = wx.Button(self, wx.ID_OK)
        btn_ok.SetDefault()

        for obj in self.pagedata:
            panel = wx.Panel(self.book)
            if obj['setup']['type'] == "DataGrid":
                sizer_grid = wx.BoxSizer(wx.VERTICAL)
                grid = TtkGrid(panel, obj['name'], obj['setup'])
                grid.change_data(obj['data'])
                sizer_grid.Add(grid, 1, wx.EXPAND)
                panel.SetSizer(sizer_grid)
                self.book.AddPage(panel, obj['label'])

                self.Bind(wx.grid.EVT_GRID_CELL_CHANGED, self.on_cell_change, grid)
            else:
                print(f"NotebookDialog - Page for type '{obj['type']}' is not defined.")

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer_btn = wx.StdDialogButtonSizer()

        sizer_btn.AddButton(btn_ok)
        sizer_btn.Realize()

        sizer.Add(self.book, 1, wx.EXPAND)
        sizer.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.LEFT|wx.RIGHT, BORDER)
        sizer.Add(sizer_btn, 0, wx.EXPAND|wx.ALL, BORDER)

        self.SetSizer(sizer)
        sizer.Fit(self)

    def on_cell_change(self, evt):
        """Refit the dialog on grid change."""
        size = self.GetParent().GetTopLevelParent().GetSize()
        # size = self.GetTopLevelParent().GetSize()
        print(f"\nsize: {size.GetWidth()}, {size.GetHeight()}")
        if (self.GetSize().GetHeight() < size.GetHeight() - 50 and
            self.GetSize().GetWidth() < size.GetWidth() - 50):
            self.GetSizer().Fit(self)
        evt.Skip()
