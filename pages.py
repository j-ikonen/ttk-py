import wx

from dialog import DbDialog
from datagrid_dialog import NotebookDialog
from setup_grid import SetupGrid
from ttk_grid import TtkGrid
from ttk_data import DataChild, DataItem, DataRoot
from setup import Setup


BORDER = 5
BTN_REFRESH = "Päivitä"
BTN_DB = "Tietokanta"
BTN_NEW_CHILD = "Lisää ryhmä"
BTN_DEL_CHILD = "Poista ryhmä"
BTN_CLOSE_ITEM = "Sulje tarjous"
BTN_MULT = "Kertoimet"
CHK_FC_LABEL = "Käytä yleisiä kertoimia"
TEDLG_MSG = "Uuden ryhmän nimi"
MCDLG_MSG = "Valitse poistettavat ryhmät"
MCDLG_CAP = "Poista ryhmiä"
TXTC_NAME_SIZE = (120, -1)


class Page(wx.Panel):
    def __init__(self, parent, setup):
        super().__init__(parent)
        self.SetBackgroundColour((255, 200, 255))

        self.setup: Setup = setup

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)


class RootPage(wx.Panel):
    def __init__(self, parent, setup, refresh_tree):
        super().__init__(parent)
        self.SetBackgroundColour((200, 255, 255))

        self.setup: Setup = setup
        self.data = None
        self.refresh_tree = refresh_tree

        txt_name = wx.StaticText(self, label=self.setup["static"]["label"]["value"])
        # self.txtc_name = wx.TextCtrl(self, value="", size=TXTC_NAME_SIZE)

        # self.Bind(wx.EVT_TEXT, self.on_text, self.txtc_name)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer_name = wx.BoxSizer(wx.HORIZONTAL)

        sizer_name.Add(txt_name, 0, wx.EXPAND|wx.RIGHT, BORDER)
        # sizer_name.Add(self.txtc_name, 0, wx.EXPAND|wx.RIGHT, BORDER)

        sizer.Add(sizer_name, 0, wx.EXPAND|wx.ALL, BORDER)

        self.SetSizer(sizer)

    def change_data(self, data: DataRoot):
        """Change the data to a new DataRoot."""
        self.data = data
        print(f"RootPage.change_data - name: {self.data.get_data('name')}")
        # self.txtc_name.SetValue(data.get_name())
        # self.grid_info.change_data(data.get_data('info'))

    # def on_text(self, evt):
    #     """Update the DataRoot name."""
    #     print("RootPage.on_text")
    #     if self.data is not None:
    #         txtc: wx.TextCtrl = evt.GetEventObject()
    #         self.data.set_name(txtc.GetValue())
    #         print(f"\t{txtc.GetValue()}")
    #         self.refresh_tree()


class ItemPage(wx.Panel):
    def __init__(self, parent, setup: Setup, fc_mult, refresh_tree):
        super().__init__(parent)
        self.SetBackgroundColour((255, 255, 200))

        self.setup_child: Setup = setup.get_parent().get_child("child")
        self.setup: Setup = setup
        self.data: DataItem = None
        self.refresh_tree = refresh_tree
        self.use_global = False
        self.global_mult = fc_mult

        txt_name = wx.StaticText(self, label=self.setup["static"]["label"]["value"])
        self.txtc_name = wx.TextCtrl(self, value="", size=TXTC_NAME_SIZE)

        self.btn_add_child = wx.Button(self, label=BTN_NEW_CHILD)
        btn_del_child = wx.Button(self, label=BTN_DEL_CHILD)
        btn_mult = wx.Button(self, label=BTN_MULT)

        self.chk_labels = self.setup['data']["use_global"]["label"]
        self.chk_fc = wx.CheckBox(
            self, label=self.chk_labels[0],
            style=wx.CHK_3STATE|wx.CHK_ALLOW_3RD_STATE_FOR_USER
        )
        self.chk_fc.Set3StateValue(self.setup['data']["use_global"]["value"])

        self.grid_client = SetupGrid(self, self.setup.get_grandchild("data", "client"))
        self.grid_file = SetupGrid(self, self.setup.get_grandchild("data", "save_file"))
        self.grid_fc = TtkGrid(self, 'fieldcount', self.setup.get_grandchild("data", "fieldcount"))

        grid_file_size = len(self.grid_file.setup['fields'])
        grid_info_size = len(self.grid_client.setup['fields'])

        # Set row labels to match the bigger grid labels.
        info_size = self.grid_client.GetRowLabelSize()
        file_size = self.grid_file.GetRowLabelSize()
        label_size = info_size if info_size > file_size else file_size
        self.grid_client.SetRowLabelSize(label_size)
        self.grid_file.SetRowLabelSize(label_size)

        self.Bind(wx.EVT_TEXT, self.on_text, self.txtc_name)
        self.Bind(wx.EVT_BUTTON, self.on_add_child, self.btn_add_child)
        self.Bind(wx.EVT_BUTTON, self.on_del_child, btn_del_child)
        self.Bind(wx.EVT_BUTTON, self.on_mult_edit, btn_mult)
        self.Bind(wx.EVT_CHECKBOX, self.on_check, self.chk_fc)

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
        sizer_name.Add(btn_mult, 0, wx.EXPAND|wx.RIGHT, BORDER)
        sizer_name.Add(self.chk_fc, 0, wx.EXPAND|wx.RIGHT, BORDER)

        sizer_info.Add(self.grid_file, grid_file_size, wx.EXPAND)
        sizer_info.Add(self.grid_client, grid_info_size, wx.EXPAND)

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
            self.txtc_name.SetValue(self.data.get_data("name"))
        if fc:
            use_global = self.data.get_data('use_global')
            if self.chk_fc.Get3StateValue() != use_global:
                self.chk_fc.Set3StateValue(use_global)
                self.chk_fc.SetLabel(self.chk_labels[use_global])

            self.update_fieldcount()
        if info:
            self.grid_client.change_data(self.data.get_data('client'))
        if file:
            self.grid_file.change_data(self.data.get_data('save_file'))

    def change_data(self, data: DataItem):
        """Change the data to a new DataItem."""
        # self.global_mult = fc_mult
        self.data = data
        self.refresh(True, True, True, True)
        print(f"ItemPage.change_data - name: {self.data.get_data('name')}")

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
        value = self.chk_fc.Get3StateValue()
        self.data.set_data('use_global', value)
        self.chk_fc.SetLabel(self.chk_labels[value])
        fc = self.data.get_data('fieldcount')
        self.update_multipliers(fc)

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

    def on_mult_edit(self, evt):
        """Open dialog for editing the multipliers."""
        MULT_DLG_TITLE = "Muokkaa kertoimia"
        LM_LABEL = "Tarjous"
        GM_LABEL = "Jaettu"
        lm = self.data.get_data('fieldcount_multiplier')
        gm = self.global_mult
        st = self.setup.get("data", "fieldcount_multiplier")
        pages = [
            {'label': LM_LABEL, 'data': lm, 'setup': st, 'name': 'fc_mult'},
            {'label': GM_LABEL, 'data': gm, 'setup': st, 'name': 'fc_mult'}
        ]

        with NotebookDialog(self, MULT_DLG_TITLE, pages) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                fc = self.data.get_data('fieldcount')
                self.update_multipliers(fc)

    def on_text(self, evt):
        """Update the DataItem name."""
        if self.data is not None:
            txtc: wx.TextCtrl = evt.GetEventObject()
            self.data.set_name(txtc.GetValue())
            self.refresh_tree()

    def update_fieldcount(self):
        """Update the fieldcount data and display."""
        new_count = {}
        # Iterate over all DataChild objects.
        for child in self.data.get_children():
            # Iterate over all rows in products grid.
            for obj in child.get_data('products'):
                unit = obj['inst_unit']
                try:
                    new_count[unit]['count'] += obj['count']
                # Init the unit on first count
                except KeyError:
                    new_count[unit] = {'mult': 0.0, 'count': obj['count'], 'cost': 0.0}
        
        new_list = [
            {
                'unit': unit,
                'mult': v['mult'],
                'count': v['count'],
                'cost': v['cost']
            } for unit, v in new_count.items()]

        self.update_multipliers(new_list)

    def update_multipliers(self, datalist):
        """Update the multipliers in fieldcount data and grid."""
        local_mult: list = self.data.get_data('fieldcount_multiplier')
        use_global: int = self.data.get_data('use_global')
        new_fc = []
        total = 0.0
        total_count = 0
        weighted_mult_total = 0.0
        # Form a list of dictionaries
        for item in datalist:
            unit = item['unit']
            if unit == 'TOTAL':
                continue
            count = item['count']

            # Get the local or global mult.
            mult = 0.0
            if use_global == 0 or unit in local_mult:
                source = local_mult
            else:
                source = self.global_mult

            for mult_obj in source:
                if mult_obj['unit'] == unit:
                    mult = mult_obj['mult']

            # print(f"update_multipliers: unit: {unit}, mult: {mult}")
            new_obj = {
                'unit': unit,
                'mult': mult,
                'count': count,
                'cost': mult * count,
            }
            new_fc.append(new_obj)
            total += (mult * count)
            total_count += count
            weighted_mult_total += mult * count

        # Insert total as first row.
        try:
            wmult = weighted_mult_total / total_count
        except ZeroDivisionError:
            wmult = 0.0

        new_obj = {
            'unit': "TOTAL",
            'mult': wmult,
            'count': total_count,
            'cost': total,
        }
        new_fc.insert(0, new_obj)
        self.data.set_data('fieldcount', new_fc)
        self.grid_fc.change_data(new_fc)


class ChildPage(wx.Panel):
    def __init__(self, parent, setup, refresh_tree):
        super().__init__(parent)
        self.SetBackgroundColour((255, 220, 220))

        self.setup: Setup = setup
        self.data: DataChild = None
        self.refresh_tree = refresh_tree

        self.setup_predef = self.setup.get_grandchild("data", "predefs")
        self.setup_materials = self.setup.get_grandchild("data", "materials")
        self.setup_products = self.setup.get_grandchild("data", "products")
        self.setup_parts = self.setup_products.get_grandchild("child_data", "parts")

        btn_refresh = wx.Button(self, label=BTN_REFRESH)
        btn_db = wx.Button(self, label=BTN_DB)

        self.txtc_name = wx.TextCtrl(self, value="", size=TXTC_NAME_SIZE)

        txt_name = wx.StaticText(self, label=self.setup["static"]["label"]["value"])
        txt_predefs = wx.StaticText(self, label=self.setup_predef['label'])
        txt_materials = wx.StaticText(self, label=self.setup_materials['label'])
        txt_products = wx.StaticText(self, label=self.setup_products['label'])
        self.txt_parts = wx.StaticText(self, label=self.setup_parts['label'])

        self.grid_predefs = TtkGrid(self, 'predefs', self.setup_predef)
        self.grid_materials = TtkGrid(self, 'materials', self.setup_materials)
        self.grid_products = TtkGrid(self, 'products', self.setup_products)
        self.grid_parts = TtkGrid(self, 'parts', self.setup_parts)

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
        self.collections = {}
        for key in self.setup["database"]:
            self.collections[key] = self.setup["database"][key]

    def append_data(self, data: dict):
        """Append new data to existing DataChild object.
        
        Args:
        - data (dict): {Grid Key: List of objects}
        """
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
        name = data.get_data("name")
        print("ChildPage.change_data")
        print(f"\tname: {name}")
        self.data = data

        self.txtc_name.SetValue(name)
        self.txt_parts.SetLabel(self.setup_parts['label_wo_parent'])

        self.grid_predefs.change_data(data.get_data('predefs'))
        self.grid_materials.change_data(data.get_data('materials'))
        self.grid_products.change_data(data.get_data('products'))
        self.grid_parts.change_data(None)

    def on_btn_db(self, evt):
        """Open the database dialog."""
        child_setups = {'products.parts': self.setup_parts}
        with DbDialog(self, self.collections, child_setups) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                for key, objlist in dlg.to_offer.items():
                    for obj in objlist:
                        self.grids[key].push(obj)

    def on_btn_refresh(self, evt):
        """Do evals on coded cells."""
        print("ChildPage.on_btn_refresh - Implement refresh of coded values here.")
        refresh_n = self.data.get_data('n_process_codes')
        def inner_refresh(n):
            self.data.process_codes()

            if n == refresh_n - 1:
                self.grid_predefs.refresh_attr()
                self.grid_materials.refresh_attr()
                self.grid_products.refresh_attr()
                self.grid_parts.refresh_attr()

        if self.data is not None:
            for n in range(refresh_n):
                inner_refresh(n)

    def on_select_product(self, evt):
        """Change the parts grid content to new product selection."""
        row = evt.GetRow()
        product_name_key = self.setup_parts['key_parent_label_field']

        # Prevent raised error if self.data is None
        try:
            products = self.data.get_data('products')
        except AttributeError:
            products = []

        # Row that is not initialized in data selected.
        if row >= len(products):
            label = self.setup_parts['label_wo_parent']

        # Update the parts label and grid.
        else:
            product_name = products[row][product_name_key]
            label = self.setup_parts['label_w_parent'].format(product_name)

        self.txt_parts.SetLabel(label)

    def on_text(self, evt):
        """Update the ChildData name."""
        if self.data is not None:
            txtc: wx.TextCtrl = evt.GetEventObject()
            self.data.set_data("name", txtc.GetValue())
            self.refresh_tree()
