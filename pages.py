import wx

from ttk_grid import TtkGrid, SetupGrid
from ttk_data import DataChild, DataItem, DataRoot, Data


BORDER = 5
BTN_REFRESH = "Päivitä"
BTN_DB = "Tietokanta"
BTN_NEW_CHILD = "Lisää ryhmä"
BTN_DEL_CHILD = "Poista ryhmä"
BTN_CLOSE_ITEM = "Sulje tarjous"
CHK_FC_LABEL = "Käytä yleisiä kertoimia"
TEDLG_MSG = "Uuden ryhmän nimi"
MCDLG_MSG = "Valitse poistettavat ryhmät"
MCDLG_CAP = "Poista ryhmiä"
TXTC_NAME_SIZE = (120, -1)


class Page(wx.Panel):
    def __init__(self, parent, setup):
        super().__init__(parent)
        self.SetBackgroundColour((255, 200, 255))

        self.setup = setup[str(Data)]

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)

class RootPage(wx.Panel):
    def __init__(self, parent, setup):
        super().__init__(parent)
        self.SetBackgroundColour((200, 255, 255))

        self.setup = setup[str(DataRoot)]
        self.data = None

        txt_name = wx.StaticText(self, label=self.setup['__name'])
        self.txtc_name = wx.TextCtrl(self, value="", size=TXTC_NAME_SIZE)
        # GLOBAL FC MULT EDITS HERE

        self.Bind(wx.EVT_TEXT, self.on_text, self.txtc_name)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer_name = wx.BoxSizer(wx.HORIZONTAL)

        sizer_name.Add(txt_name, 0, wx.EXPAND|wx.RIGHT, BORDER)
        sizer_name.Add(self.txtc_name, 0, wx.EXPAND|wx.RIGHT, BORDER)

        sizer.Add(sizer_name, 0, wx.EXPAND|wx.ALL, BORDER)

        self.SetSizer(sizer)

    def change_data(self, data: DataRoot):
        """Change the data to a new DataItem."""
        self.data = data
        self.txtc_name.SetValue(data.get_name())
        # self.grid_info.change_data(data.get_data('info'))

    def on_text(self, evt):
        """Update the DataItem name."""
        print("ItemPage.on_text - Implement changing DataItem name here.")
        if self.data:
            txtc: wx.TextCtrl = evt.GetEventObject()
            self.data.set_name(txtc.GetValue())
            self.refresh_tree()


class ItemPage(wx.Panel):
    def __init__(self, parent, setup, fc_mult, refresh_tree):
        super().__init__(parent)
        self.SetBackgroundColour((255, 255, 200))

        self.setup_child = setup[str(DataChild)]
        self.setup = setup[str(DataItem)]
        self.data: DataItem = None
        self.refresh_tree = refresh_tree
        self.use_global = False
        self.gfc_mult = fc_mult
        self.fc = []

        txt_name = wx.StaticText(self, label=self.setup['__name'])
        self.txtc_name = wx.TextCtrl(self, value="", size=TXTC_NAME_SIZE)

        self.btn_add_child = wx.Button(self, label=BTN_NEW_CHILD)
        btn_del_child = wx.Button(self, label=BTN_DEL_CHILD)

        chk_fc = wx.CheckBox(self, label=CHK_FC_LABEL)

        self.grid_info = SetupGrid(self, self.setup['info'])
        self.grid_fc = TtkGrid(self, self.setup['fieldcount'])

        self.Bind(wx.EVT_TEXT, self.on_text, self.txtc_name)
        self.Bind(wx.EVT_BUTTON, self.on_add_child, self.btn_add_child)
        self.Bind(wx.EVT_BUTTON, self.on_del_child, btn_del_child)
        self.Bind(wx.EVT_CHECKBOX, self.on_check, chk_fc)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer_name = wx.BoxSizer(wx.HORIZONTAL)
        sizer_info = wx.BoxSizer(wx.VERTICAL)
        sizer_fc = wx.BoxSizer(wx.VERTICAL)
        sizer_grids = wx.BoxSizer(wx.HORIZONTAL)

        sizer_name.Add(txt_name, 0, wx.EXPAND|wx.RIGHT, BORDER)
        sizer_name.Add(self.txtc_name, 0, wx.EXPAND|wx.RIGHT, BORDER)
        sizer_name.Add((80, 5), 0, wx.EXPAND|wx.RIGHT, BORDER)
        sizer_name.Add(self.btn_add_child, 0, wx.EXPAND|wx.RIGHT, BORDER)
        sizer_name.Add(btn_del_child, 0, wx.EXPAND|wx.RIGHT, BORDER)

        sizer_info.Add(self.grid_info, 0, wx.EXPAND)

        sizer_fc.Add(chk_fc, 0, wx.EXPAND|wx.ALL, BORDER)
        sizer_fc.Add(self.grid_fc, 0, wx.EXPAND)

        sizer_grids.Add(sizer_info, 1, wx.EXPAND)
        sizer_grids.Add(sizer_fc, 1, wx.EXPAND)

        sizer.Add(sizer_name, 0, wx.EXPAND|wx.ALL, BORDER)
        sizer.Add(sizer_grids, 1, wx.EXPAND)

        self.SetSizer(sizer)


    def change_data(self, data: DataItem):
        """Change the data to a new DataItem."""
        # self.fc = self.data.get_data('fieldcount')
        self.data = data
        self.txtc_name.SetValue(data.get_name())
        self.update_fieldcount()
        self.grid_info.change_data(data.get_data('info'))

    def on_add_child(self, evt):
        """Add a child data object to current DataItem."""
        if self.data:
            with wx.TextEntryDialog(self, TEDLG_MSG) as dlg:
                if dlg.ShowModal() == wx.ID_OK:
                    name = dlg.GetValue()
                    self.data.push(name, self.setup_child)
                    self.refresh_tree()

    def on_check(self, evt):
        """Get global fieldcount multipliers if box is checked."""
        if evt.IsChecked():
            self.use_global = True
        else:
            self.use_global = False
        self.update_fieldcount()

    def on_del_child(self, evt):
        """Delete a child from DataItem."""
        if self.data:
            child_list = [child.get_name() for child in self.data.get_children()]
            with wx.MultiChoiceDialog(
                self, MCDLG_MSG, MCDLG_CAP,
                len(child_list), child_list
            ) as dlg:

                if dlg.ShowModal() == wx.ID_OK:
                    selections: list = dlg.GetSelections()
                    selections.sort(reverse=True)
                    for n in selections:
                        self.data.delete_child(n)
                    self.refresh_tree()

    def on_text(self, evt):
        """Update the DataItem name."""
        print("ItemPage.on_text - Implement changing DataItem name here.")
        if self.data:
            txtc: wx.TextCtrl = evt.GetEventObject()
            self.data.set_name(txtc.GetValue())
            self.refresh_tree()

    def update_fieldcount(self):
        self.fc.clear()
        for item in self.data.get_data('fieldcount'):
            mult = self.gfc_mult[item['unit']] if self.use_global else item['mult']
            self.fc.append({
                'unit': item['unit'],
                'mult': mult,
                'count': item['count'],
                'cost': mult * item['count']
            })
        self.grid_fc.change_data(self.fc)


class ChildPage(wx.Panel):
    def __init__(self, parent, setup, refresh_tree):
        super().__init__(parent)
        self.SetBackgroundColour((255, 220, 220))

        self.setup = setup[str(DataChild)]
        self.data: DataChild = None
        self.refresh_tree = refresh_tree

        btn_refresh = wx.Button(self, label=BTN_REFRESH)
        btn_db = wx.Button(self, label=BTN_DB)

        self.txtc_name = wx.TextCtrl(self, value="", size=TXTC_NAME_SIZE)

        txt_name = wx.StaticText(self, label=self.setup['__name'])
        txt_predefs = wx.StaticText(self, label=self.setup['predefs']['name'])
        txt_materials = wx.StaticText(self, label=self.setup['materials']['name'])
        txt_products = wx.StaticText(self, label=self.setup['products']['name'])
        self.txt_parts = wx.StaticText(self, label=self.setup['parts']['name'])

        self.grid_predefs = TtkGrid(self, self.setup['predefs'])
        self.grid_materials = TtkGrid(self, self.setup['materials'])
        self.grid_products = TtkGrid(self, self.setup['products'])
        self.grid_parts = TtkGrid(self, self.setup['parts'])

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
        self.data = data

        self.txtc_name.SetValue(data.get_name())

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

        if self.data:
            for n in range(self.setup['__refresh_n']):
                inner_refresh(n)

    def on_select_product(self, evt):
        """Change the parts grid content to new product selection."""
        print("ChildPage.on_select_product - Implement changing parts grid to new data here.")
        row = evt.GetRow()
        product_name_key = self.setup['parts']['parent_name_key']

        # Prevent raised error if self.data is None
        try:
            products = self.data.get_data('products')
        except AttributeError:
            products = []

        # Row that is not initialized in data selected.
        if row >= len(products):
            label = self.setup['parts']['name']
            parts = None

        # Update the parts label and grid.
        else:
            parts = products[row]['parts']
            product_name = products[row][product_name_key]
            label = self.setup['parts']['name_on_parent_selection'].format(product_name)

        self.grid_parts.change_data(parts)
        self.txt_parts.SetLabel(label)

    def on_text(self, evt):
        """Update the ChildData name."""
        print("ChildPage.on_text - Implement changing DataChild name here.")
        if self.data:
            txtc: wx.TextCtrl = evt.GetEventObject()
            self.data.set_name(txtc.GetValue())
            self.refresh_tree()
