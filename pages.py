import wx

from ttk_grid import TtkGrid
from ttk_data import DataChild


BORDER = 5
BTN_REFRESH = "Päivitä"
BTN_DB = "Tietokanta"
TXTC_NAME_SIZE = (120, -1)

class Page(wx.Panel):
    def __init__(self, parent, setup):
        super().__init__(parent)
        self.SetBackgroundColour((255, 200, 255))

        self.setup = setup


class RootPage(wx.Panel):
    def __init__(self, parent, setup):
        super().__init__(parent)
        self.SetBackgroundColour((200, 255, 255))

        self.setup = setup


class ItemPage(wx.Panel):
    def __init__(self, parent, setup):
        super().__init__(parent)
        self.SetBackgroundColour((255, 255, 200))

        self.setup = setup


class ChildPage(wx.Panel):
    def __init__(self, parent, setup):
        super().__init__(parent)
        self.SetBackgroundColour((255, 220, 220))

        self.setup = setup
        self.data: DataChild = None

        btn_refresh = wx.Button(self, label=BTN_REFRESH)
        btn_db = wx.Button(self, label=BTN_DB)

        self.txtc_name = wx.TextCtrl(self, value="", size=TXTC_NAME_SIZE)

        txt_name = wx.StaticText(self, label=setup['__name'])
        txt_predefs = wx.StaticText(self, label=setup['predefs']['name'])
        txt_materials = wx.StaticText(self, label=setup['materials']['name'])
        txt_products = wx.StaticText(self, label=setup['products']['name'])
        self.txt_parts = wx.StaticText(self, label=setup['parts']['name'])

        self.grid_predefs = TtkGrid(self, setup['predefs'])
        self.grid_materials = TtkGrid(self, setup['materials'])
        self.grid_products = TtkGrid(self, setup['products'])
        self.grid_parts = TtkGrid(self, setup['parts'])

        self.Bind(wx.EVT_TEXT, self.on_text, self.txtc_name)
        self.Bind(wx.EVT_BUTTON, self.on_btn_refresh, btn_refresh)
        self.Bind(wx.EVT_BUTTON, self.on_btn_db, btn_db)
        self.Bind(wx.grid.EVT_GRID_SELECT_CELL, self.on_select_product, self.grid_products)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer_label = wx.BoxSizer(wx.HORIZONTAL)
        sizer_predefs = wx.BoxSizer(wx.HORIZONTAL)
        sizer_materials = wx.BoxSizer(wx.HORIZONTAL)
        sizer_products = wx.BoxSizer(wx.HORIZONTAL)
        sizer_parts = wx.BoxSizer(wx.HORIZONTAL)

        sizer_label.Add(txt_name, 0, wx.EXPAND|wx.RIGHT, BORDER)
        sizer_label.Add(self.txtc_name, 0, wx.EXPAND|wx.RIGHT, BORDER)
        sizer_label.Add((80, 5))
        sizer_label.Add(btn_refresh, 0, wx.EXPAND|wx.RIGHT, BORDER)
        sizer_label.Add(btn_db, 0, wx.EXPAND|wx.RIGHT, BORDER)

        sizer_predefs.Add(txt_predefs, 0, wx.EXPAND|wx.RIGHT, BORDER)
        sizer_materials.Add(txt_materials, 0, wx.EXPAND|wx.RIGHT, BORDER)
        sizer_products.Add(txt_products, 0, wx.EXPAND|wx.RIGHT, BORDER)
        sizer_parts.Add(self.txt_parts, 0, wx.EXPAND|wx.RIGHT, BORDER)

        sizer.Add(sizer_label, 0, wx.EXPAND|wx.ALL, BORDER)
        sizer.Add(sizer_predefs, 0, wx.EXPAND|wx.ALL, BORDER)
        sizer.Add(self.grid_predefs, 1, wx.EXPAND)
        sizer.Add(sizer_materials, 0, wx.EXPAND|wx.ALL, BORDER)
        sizer.Add(self.grid_materials, 1, wx.EXPAND)
        sizer.Add(sizer_products, 0, wx.EXPAND|wx.ALL, BORDER)
        sizer.Add(self.grid_products, 1, wx.EXPAND)
        sizer.Add(sizer_parts, 0, wx.EXPAND|wx.ALL, BORDER)
        sizer.Add(self.grid_parts, 1, wx.EXPAND)

        self.SetSizer(sizer)
        
        self.grids = {
            'predefs': self.grid_predefs,
            'materials': self.grid_materials,
            'products': self.grid_products,
            'parts': self.grid_parts,
        }

    def append_data(self, data: dict):
        """Append new data to existing DataChild object."""
        for k, v in data.items():
            try:
                obj = self.data.get_data(k)
            except KeyError:
                continue
            for item in v:
                obj.append(item)
            self.grids[k].changed_rows(len(v))

    def change_data(self, data: DataChild):
        """Change page contents to a new DataChild object."""
        print("ChildPage.change_data - Implement chaning contents here.")

        self.grid_predefs.change_data(data.get_data('predefs'))
        self.grid_materials.change_data(data.get_data('materials'))
        self.grid_products.change_data(data.get_data('products'))
        self.grid_parts.change_data(None)

    def on_btn_db(self, evt):
        """."""
        print("ChildPage.on_btn_db - Implement open db dialog here.")

    def on_btn_refresh(self, evt):
        """Do evals on coded cells."""
        print("ChildPage.on_btn_refresh - Implement refresh of coded values here.")
        def inner_refresh(n):
            self.data.process_codes()

            if n == self.setup['__refresh_n'] - 1:
                self.grid_predefs.refresh_attr()
                self.grid_materials.refresh_attr()
                self.grid_products.refresh_attr()
                self.grid_parts.refresh_attr()

        for n in range(self.setup['__refresh_n']):
            inner_refresh(n)

    def on_select_product(self, evt):
        """Change the parts grid content to new product selection."""
        print("ChildPage.on_select_product - Implement changing parts grid to new data here.")
        row = evt.GetRow()
        product_name_key = self.setup['parts']['parent_name_key']
        products = self.data.get_data('products')

        if row >= len(products):
            label = self.setup['parts']['name']
            parts = None

        else:
            parts = products[row]['parts']
            product_name = products[row][product_name_key]
            label = self.setup['parts']['name_on_parent_selection'].format(product_name)

        self.grid_parts.change_data(parts)
        self.txt_parts.SetLabel(label)

    def on_text(self, evt):
        """Update the ChildData name."""
        print("ChildPage.on_text - Implement changing DataChild name here.")
        txtc: wx.TextCtrl = evt.GetEventObject()
        self.data.set_name(txtc.GetValue())
        evt.Skip()
    