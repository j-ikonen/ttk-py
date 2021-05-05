import wx

from setup_grid import SetupGrid
from ttk_grid import TtkGrid
from ttk_data import DataChild, DataItem, DataRoot, Data, str2type, type2str


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
    def __init__(self, parent, setup, refresh_tree):
        super().__init__(parent)
        self.SetBackgroundColour((200, 255, 255))

        self.setup = setup[str(DataRoot)]
        self.data = None
        self.refresh_tree = refresh_tree

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
        print(f"RootPage.change_data - name: {self.data.get_name()}")
        self.txtc_name.SetValue(data.get_name())
        # self.grid_info.change_data(data.get_data('info'))

    def on_text(self, evt):
        """Update the DataItem name."""
        print("RootPage.on_text")
        if self.data is not None:
            txtc: wx.TextCtrl = evt.GetEventObject()
            self.data.set_name(txtc.GetValue())
            print(f"\t{txtc.GetValue()}")
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
        self.global_mult = fc_mult

        txt_name = wx.StaticText(self, label=self.setup['__name'])
        self.txtc_name = wx.TextCtrl(self, value="", size=TXTC_NAME_SIZE)

        self.btn_add_child = wx.Button(self, label=BTN_NEW_CHILD)
        btn_del_child = wx.Button(self, label=BTN_DEL_CHILD)

        chk_fc = wx.CheckBox(self, label=CHK_FC_LABEL)

        self.grid_info = SetupGrid(self, self.setup['info'])
        self.grid_file = SetupGrid(self, self.setup['file'])
        self.grid_fc = TtkGrid(self, 'fieldcount', self.setup['fieldcount'])
        grid_file_size = len(self.setup['file']['fields'])
        grid_info_size = len(self.setup['info']['fields'])

        # Set row labels to match the bigger grid labels.
        info_size = self.grid_info.GetRowLabelSize()
        file_size = self.grid_file.GetRowLabelSize()
        label_size = info_size if info_size > file_size else file_size
        self.grid_info.SetRowLabelSize(label_size)
        self.grid_file.SetRowLabelSize(label_size)

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
        sizer_name.Add(chk_fc, 0, wx.EXPAND|wx.RIGHT, BORDER)

        sizer_info.Add(self.grid_file, grid_file_size, wx.EXPAND)
        sizer_info.Add(self.grid_info, grid_info_size, wx.EXPAND)

        # sizer_fc.Add(chk_fc, 0, wx.EXPAND|wx.ALL, BORDER)
        sizer_fc.Add(self.grid_fc, 1, wx.EXPAND)

        sizer_grids.Add(sizer_info, 1, wx.EXPAND)
        sizer_grids.Add(sizer_fc, 1, wx.EXPAND)
        sizer.Add(sizer_name, 0, wx.EXPAND|wx.ALL, BORDER)
        sizer.Add(sizer_grids, 1, wx.EXPAND)

        self.SetSizer(sizer)

    def refresh(self, name=False, fc=False, info=False, file=False):
        """Refresh the content of the page with self.data."""
        if name:
            self.txtc_name.SetValue(self.data.get_name())
        if fc:
            self.update_fieldcount()
        if info:
            self.grid_info.change_data(self.data.get_data('info'))
        if file:
            self.grid_file.change_data(self.data.get_data('file'))

    def change_data(self, data: DataItem, fc_mult: list):
        """Change the data to a new DataItem."""
        self.global_mult = fc_mult
        self.data = data
        self.refresh(True, True, True, True)
        print(f"ItemPage.change_data - name: {self.data.get_name()}")

    def on_add_child(self, evt):
        """Add a child data object to current DataItem."""
        if self.data is not None:
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
        if self.data is not None:
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
        if self.data is not None:
            txtc: wx.TextCtrl = evt.GetEventObject()
            self.data.set_name(txtc.GetValue())
            self.refresh_tree()

    def update_fieldcount(self):
        """Update the fieldcount data and display."""
        new_count = {}
        local_mult = self.data.get_data('fc_mult')
        # Iterate over all DataChild objects.
        for child in self.data.get_children():
            # Iterate over all rows in products grid.
            for obj in child.get_data('products'):
                unit = obj['inst_unit']
                try:
                    new_count[unit]['count'] += 1
                # Init the unit on first count
                except KeyError:
                    mult = self.global_mult[unit] if self.use_global else local_mult[unit]
                    new_count[unit] = {'mult': mult, 'count': 0, 'cost': 0.0}

        # Form a list of dictionaries
        new_fc = []
        for unit, value in new_count.items():
            new_obj = {
                'unit': unit,
                'mult': value['mult'],
                'count': value['count'],
                'cost': value['mult'] * value['count'],
            }
            new_fc.append(new_obj)

        self.data.set_data('fieldcount', new_fc)
        self.grid_fc.change_data(new_fc)


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

        self.grid_predefs = TtkGrid(self, 'predefs', self.setup['predefs'])
        self.grid_materials = TtkGrid(self, 'materials', self.setup['materials'])
        self.grid_products = TtkGrid(self, 'products', self.setup['products'])
        self.grid_parts = TtkGrid(self, 'parts', self.setup['parts'])

        self.grid_products.set_child_grid(self.grid_parts)

        self.Bind(wx.EVT_TEXT, self.on_text, self.txtc_name)
        self.Bind(wx.EVT_BUTTON, self.on_btn_refresh, btn_refresh)
        self.Bind(wx.EVT_BUTTON, self.on_btn_db, btn_db)
        self.Bind(wx.grid.EVT_GRID_SELECT_CELL, self.on_select_product, self.grid_products)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer_label = wx.BoxSizer(wx.HORIZONTAL)
        sizer_twogrids = wx.BoxSizer(wx.HORIZONTAL)
        sizer_predefs = wx.BoxSizer(wx.VERTICAL)
        sizer_materials = wx.BoxSizer(wx.VERTICAL)
        sizer_products = wx.BoxSizer(wx.VERTICAL)
        sizer_parts = wx.BoxSizer(wx.VERTICAL)

        sizer_label.Add(txt_name, 0, wx.EXPAND|wx.RIGHT, BORDER)
        sizer_label.Add(self.txtc_name, 0, wx.EXPAND|wx.RIGHT, BORDER)
        sizer_label.Add((80, 5))
        sizer_label.Add(btn_refresh, 0, wx.EXPAND|wx.RIGHT, BORDER)
        sizer_label.Add(btn_db, 0, wx.EXPAND|wx.RIGHT, BORDER)

        sizer_predefs.Add(txt_predefs, 0, wx.EXPAND|wx.TOP|wx.BOTTOM, BORDER)
        sizer_predefs.Add(self.grid_predefs, 1, wx.EXPAND)

        sizer_materials.Add(txt_materials, 0, wx.EXPAND|wx.TOP|wx.BOTTOM, BORDER)
        sizer_materials.Add(self.grid_materials, 1, wx.EXPAND)

        sizer_products.Add(txt_products, 0, wx.EXPAND|wx.TOP|wx.BOTTOM, BORDER)
        sizer_products.Add(self.grid_products, 1, wx.EXPAND)

        sizer_parts.Add(self.txt_parts, 0, wx.EXPAND|wx.TOP|wx.BOTTOM, BORDER)
        sizer_parts.Add(self.grid_parts, 1, wx.EXPAND)

        sizer_twogrids.Add(sizer_predefs, 0, wx.EXPAND|wx.ALL, BORDER)
        sizer_twogrids.Add(sizer_materials, 0, wx.EXPAND|wx.ALL, BORDER)

        sizer.Add(sizer_label, 0, wx.EXPAND|wx.ALL, BORDER)
        sizer.Add(sizer_twogrids, 1, wx.EXPAND|wx.ALL, BORDER)
        sizer.Add(sizer_products, 1, wx.EXPAND|wx.ALL, BORDER)
        sizer.Add(sizer_parts, 1, wx.EXPAND|wx.ALL, BORDER)

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
        print("ChildPage.change_data")
        print(f"\tname: {data.get_name()}")
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

        if self.data is not None:
            for n in range(self.setup['__refresh_n']):
                inner_refresh(n)

    def on_select_product(self, evt):
        """Change the parts grid content to new product selection."""
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
            # parts = None

        # Update the parts label and grid.
        else:
            # parts = products[row]['parts']
            # if parts is None:
                # products[row]['parts'] = []
                # parts = products[row]['parts']

            product_name = products[row][product_name_key]
            label = self.setup['parts']['name_on_parent_selection'].format(product_name)

        # self.grid_parts.change_data(parts)
        self.txt_parts.SetLabel(label)

    def on_text(self, evt):
        """Update the ChildData name."""
        if self.data is not None:
            txtc: wx.TextCtrl = evt.GetEventObject()
            self.data.set_name(txtc.GetValue())
            self.refresh_tree()
