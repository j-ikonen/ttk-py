import wx

from table import OfferTables
from grid import BaseGrid, GroupGrid


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

        # self.setup_predefs = {}
        # self.setup_materials = {}
        # self.setup_products = {}
        # self.setup_parts = {}

        # self.columns_predefs = []
        # self.columns_materials = []
        # self.columns_products = []
        # self.columns_parts = []

        # self.types_predefs = []
        # self.types_materials = []
        # self.types_products = []
        # self.types_parts = []

        # self.set_setup()

        self.grid_predefs = GroupGrid(self, tables, "predefs")
        self.grid_materials = GroupGrid(self, tables, "materials")
        self.grid_products = GroupGrid(self, tables, "products")
        self.grid_parts = GroupGrid(self, tables, "parts")

        self.ids_predefs = []
        self.ids_materials = []
        self.ids_products = []
        self.ids_parts = []
        
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

    # def set_setup(self):
    #     disp_predefs = self.tables.get_display_setup("predefs")
    #     disp_materials = self.tables.get_display_setup("materials")
    #     disp_products = self.tables.get_display_setup("products")
    #     disp_parts = self.tables.get_display_setup("parts")

    #     self.columns_predefs = disp_predefs["columns"]
    #     self.columns_materials = disp_materials["columns"]
    #     self.columns_products = disp_products["columns"]
    #     self.columns_parts = disp_parts["columns"]

    #     self.setup_predefs = self.tables.get_column_setup("offer_predefs", self.columns_predefs)
    #     self.setup_materials = self.tables.get_column_setup("offer_predefs", self.columns_predefs)
    #     self.setup_products = self.tables.get_column_setup("offer_materials", self.columns_materials)
    #     self.setup_parts = self.tables.get_column_setup("offer_products", self.columns_products)

    #     self.types_predefs = [val["type"] for val in self.setup_predefs.values()]
    #     self.types_materials = [val["type"] for val in self.setup_materials.values()]
    #     self.types_products = [val["type"] for val in self.setup_products.values()]
    #     self.types_parts = [val["type"] for val in self.setup_parts.values()]

    def set_pk(self, pk):
        """Set the private key string for table offers. Refresh with new values."""
        self.pk_val = pk
        self.grid_predefs.set_pk(self.pk_val)
        self.grid_materials.set_pk(self.pk_val)
        self.grid_products.set_pk(self.pk_val)
        self.grid_parts.set_pk(None)

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