import wx

from table import OfferTables
from objectgrid import ObjectGrid
from grid import BaseGrid


TXT_NAME = "Tarjous: {}"
TXT_NAME_NO_SEL = "Tarjousta ei ole valittu"
BTN_EDIT_NAME = "Muuta nimeä"
BORDER = 5


class OfferPage(wx.Panel):
    def __init__(self, parent, tables):
        super().__init__(parent)

        self.tables: OfferTables = tables
        self.SetBackgroundColour((220, 255, 220))

        self.pk_val = None

        self.txt_name = wx.StaticText(self, label=TXT_NAME_NO_SEL, size=(180, -1))
        self.btn_edit_name = wx.Button(self, label=BTN_EDIT_NAME)
        self.grid_client = ObjectGrid(self, tables, "client")
        # self.grid_fc = BaseGrid(self)

        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_BUTTON, self.on_btn_name, self.btn_edit_name)


        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer_label = wx.BoxSizer(wx.HORIZONTAL)
        sizer_client = wx.BoxSizer(wx.HORIZONTAL)
        sizer_fc = wx.BoxSizer(wx.VERTICAL)
        # sizer_grids = wx.BoxSizer(wx.HORIZONTAL)

        sizer_label.Add(self.txt_name, 0, wx.RIGHT, BORDER)
        sizer_label.Add(self.btn_edit_name, 0, wx.RIGHT, BORDER)

        sizer_client.Add(self.grid_client, 1, wx.EXPAND|wx.RIGHT, BORDER)

        sizer.Add(sizer_label, 0, wx.ALL, BORDER)
        sizer.Add(sizer_client, 1, wx.ALL|wx.EXPAND, BORDER)
        self.SetSizer(sizer)
        self.set_client_grid_size()
    
    def set_pk(self, pk):
        """Set the private key string for table offers. Refresh with new values."""
        self.pk_val = pk
        self.grid_client.set_pk([pk])   # Grid refreshes on new pk.
        self.refresh()
        self.Layout()
    
    def refresh(self):
        """Refresh the page with new values from tables."""
        name = self.tables.get(
            "offers",
            ["name"],
            ["id"],
            [self.pk_val]
        )
        self.txt_name.SetLabel(name[0])

    def refresh_client(self):
        """Refresh the data in client grid."""
        self.grid_client.refresh_data()

    def set_client_grid_size(self):
        size = self.grid_client.GetSize()
        label_size = self.grid_client.GetRowLabelSize()
        newsize = size.GetWidth() - label_size - 50
        try:
            self.grid_client.SetColSize(0, newsize)
        except:
            self.grid_client.SetColSize(0, 350)

    def on_size(self, evt):
        # self.set_client_grid_size()
        evt.Skip()

    def on_btn_name(self, evt):
        """Update the name of the offer with new value from dialog."""
        if self.pk_val is None:
            return

        with wx.TextEntryDialog(self, "Tarjouksen uusi nimi", "Muuta nimeä") as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                name = dlg.GetValue()
                self.tables.update_one(
                    "offers",
                    "name",
                    "id",
                    [name, self.pk_val]
                )
                self.GetGrandParent().GetParent().refresh_tree()
                self.refresh()