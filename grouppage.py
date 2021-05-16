import wx

from table import OfferTables
from grid import BaseGrid, TableGrid


BORDER = 5
TXT_NAME_NO_SEL = "Ryhmää ei ole valittu"
BTN_EDIT_NAME = "Muokkaa nimeä"


class GroupPage(wx.Panel):
    def __init__(self, parent, tables):
        super().__init__(parent)

        self.tables: OfferTables = tables
        self.SetBackgroundColour((255, 200, 255))

        self.pk_val = None

        self.txt_name = wx.StaticText(self, label=TXT_NAME_NO_SEL, size=(180, -1))
        self.btn_edit_name = wx.Button(self, label=BTN_EDIT_NAME)

        self.ids_predefs = []
        self.ids_materials = []
        self.ids_products = []
        self.ids_parts = []

        self.grid_predefs = TableGrid(self, tables, "predefs", self.ids_predefs)
        self.grid_materials = TableGrid(self, tables, "materials", self.ids_materials)
        self.grid_products = TableGrid(self, tables, "products", self.ids_products)
        self.grid_parts = TableGrid(self, tables, "parts", self.ids_parts)
        
        self.Bind(wx.EVT_BUTTON, self.on_btn_name, self.btn_edit_name)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer_label = wx.BoxSizer(wx.HORIZONTAL)
        sizer_grids = wx.BoxSizer(wx.HORIZONTAL)

        sizer_label.Add(self.txt_name, 0, wx.RIGHT, BORDER)
        sizer_label.Add(self.btn_edit_name, 0, wx.RIGHT, BORDER)

        sizer_grids.Add(self.grid_predefs, 1, wx.EXPAND|wx.RIGHT, BORDER)
        sizer_grids.Add(self.grid_materials, 1, wx.EXPAND)

        sizer.Add(sizer_label, 0, wx.ALL, BORDER)
        sizer.Add(sizer_grids, 1, wx.EXPAND|wx.ALL, BORDER)
        sizer.Add(self.grid_products, 1, wx.EXPAND|wx.ALL, BORDER)
        sizer.Add(self.grid_parts, 1, wx.EXPAND|wx.ALL, BORDER)

        self.SetSizer(sizer)


    def set_pk(self, pk):
        """Set the private key string for table offers. Refresh with new values."""
        self.pk_val = pk
        self.grid_predefs.set_parent_id(self.pk_val)
        self.grid_materials.set_parent_id(self.pk_val)
        self.grid_products.set_parent_id(self.pk_val)
        self.grid_parts.set_parent_id(None)

        # self.grid_client.set_pk([pk])   # Grid refreshes on new pk.
        self.refresh()
        self.Layout()
    
    def refresh(self):
        """Refresh the page with new values from tables."""
        if self.pk_val is None:
            self.txt_name.SetLabel(TXT_NAME_NO_SEL)
        else:
            name = self.tables.get(
                "offer_groups",
                ["name"],
                ["id"],
                [self.pk_val]
            )
            self.txt_name.SetLabel(name[0])


    def on_btn_name(self, evt):
        """Update the name of the offer with new value from dialog."""
        if self.pk_val is None:
            return

        self.change_name()

    def change_name(self):
        """Open TextEntryDialog and edit name of the group."""
        with wx.TextEntryDialog(self, "Ryhmän uusi nimi", "Muuta nimeä") as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                name = dlg.GetValue()
                self.tables.update_one(
                    "offer_groups",
                    "name",
                    "id",
                    [name, self.pk_val]
                )
                self.GetGrandParent().GetParent().refresh_tree()
                self.refresh()