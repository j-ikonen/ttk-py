"""
TODO
    Fix copy of product.
    Add search result limit and search result page browsing.
    Add search result count.

"""

import wx

import table as tb
from dbgrid import DbGrid


TITLE = "Hae tietokannasta"
BTN_SEARCH = "Etsi"
BTN_AC = "Lisää hakuehto"
BTN_DC = "Poista hakuehto"
SEARCH_COND = "Hakuehdot"
BORDER = 5


class SearchPanel(wx.Panel):
    def __init__(self, parent, db: tb.OfferTables, table: str="offers"):
        super().__init__(parent)

        self.db: tb.OfferTables = db
        self.table_labels = [
            "Tarjoukset",
            "Materiaalit",
            "Tuotteet",
            "Osat"
        ]
        self.tables = [
            "offers",
            "materials",
            "products",
            "parts"
        ]
        self.cond_labels = [[], [], [], []]
        self.col_widths = [[], [], [], []]
        self.cond_keys = [
            tb.offers_keys,
            tb.materials_keys,
            tb.products_keys,
            tb.parts_keys
        ]
        self.grids = []
        self.child_grids = {}
        self.columns = []
        self.copy = []
        for n in range(len(self.cond_keys)):
            columns = self.db.get_columns(self.tables[n])
            # print(columns)
            self.columns.append(columns)
            for key in self.cond_keys[n]:
                for col in columns:
                    if col[tb.KEY] == key:
                        self.cond_labels[n].append(col[tb.LABEL])
                        self.col_widths[n].append(col[tb.WIDTH])
                        break

        self.op_labels = ["like", "=", "!=", ">", "<", ">=", "<=", "!>", "!<"]
        self.cond_sizers = []

        title = wx.StaticText(self, label=TITLE)
        self.choice_table = wx.Choice(self, size=(85, -1), choices=self.table_labels)
        self.btn_add_condition = wx.Button(self, label=BTN_AC)
        self.btn_search = wx.Button(self, label=BTN_SEARCH)
        self.btn_show_cond = wx.Button(self, label=SEARCH_COND)
        product_grid = None
        for n, tablename in enumerate(self.tables):
            grid = DbGrid(self, self.db, tablename, 0)
            self.grids.append(grid)
            if tablename == "products":
                product_grid = grid
                child_grid = DbGrid(self, self.db, "products.parts", 0)
                self.child_grids[tablename] = child_grid
                child_grid.set_foreign_key(["product_code"])
                child_grid.Show(False)
            if tablename == "offers":
                grid.set_primary_key(["ID"])
            grid.Show(False)

        # self.lc_search = dv.DataViewListCtrl(self, style=dv.DV_ROW_LINES|dv.DV_MULTIPLE)

        self.Bind(wx.EVT_CHOICE, self.on_table_choice, self.choice_table)
        self.Bind(wx.EVT_BUTTON, self.on_add_condition, self.btn_add_condition)
        self.Bind(wx.EVT_BUTTON, self.on_search, self.btn_search)
        self.Bind(wx.EVT_BUTTON, self.on_show_conditions, self.btn_show_cond)
        self.Bind(wx.grid.EVT_GRID_SELECT_CELL, self.on_product_selection, product_grid)
        # self.Bind(dv.EVT_DATAVIEW_ITEM_CONTEXT_MENU, self.on_dv_menu, self.lc_search)

        sizer_top = wx.BoxSizer(wx.HORIZONTAL)
        # self.sizer_conditions = wx.StaticBoxSizer(wx.VERTICAL, self, SEARCH_COND)
        sizer = wx.BoxSizer(wx.VERTICAL)

        sizer_top.Add(title, 0, wx.RIGHT, BORDER)
        sizer_top.Add(self.choice_table, 0, wx.RIGHT, BORDER)
        sizer_top.Add(self.btn_search, 0, wx.RIGHT, BORDER)
        sizer_top.Add(self.btn_add_condition, 0, wx.RIGHT, BORDER)
        sizer_top.Add(self.btn_show_cond, 0, wx.RIGHT, BORDER)

        sizer.Add(sizer_top, 0, wx.ALL, BORDER)
        for n in range(len(self.table_labels)):
            box_sizer = wx.StaticBoxSizer(wx.VERTICAL, self, SEARCH_COND)
            box_sizer.AddSpacer(BORDER)
            self.cond_sizers.append(box_sizer)
            self.add_condition(n)
            sizer.Add(box_sizer, 0, wx.ALL, BORDER)
        # sizer.Add(self.sizer_conditions, 0, wx.ALL, BORDER)

        for grid in self.grids:
            sizer.Add(grid, 1, wx.EXPAND|wx.ALL, BORDER)

        for parent_key, grid in self.child_grids.items():
            sizer.Add(grid, 1, wx.EXPAND|wx.ALL, BORDER)

        self.SetSizer(sizer)
        self.set_table_choice(self.tables.index(table))
        self.Layout()

    def update_depended_grids(self, grid):
        """Update dependend grids."""
        table = self.get_table()
        sel = self.table_selection()
        if table == "products":
            self.child_grids["products"].GetTable().update_data_with_row_change(None)
        self.grids[sel].GetTable().update_data_with_row_change(None)

    def get_table(self):
        """Return the selected table name or None if nothing is selected."""
        sel = self.table_selection()
        if sel == None:
            return None
        return self.tables[sel]

    def add_condition(self, table: int):
        """Add a condition to search condition box in table index."""
        sizer_table = self.cond_sizers[table]
        box: wx.StaticBox = sizer_table.GetStaticBox()

        self.Freeze()   # Prevent flicker when creating the new windows.

        btn_del = wx.Button(box, label=BTN_DC)
        key_choice = wx.Choice(box, size=(120, -1), choices=self.cond_labels[table])
        op_choice = wx.Choice(box, size=(45, -1), choices=self.op_labels)
        text = wx.TextCtrl(box, size=(200, -1))

        sizer_con = wx.BoxSizer(wx.HORIZONTAL)
        sizer_con.Add(btn_del, 0, wx.RIGHT, BORDER)
        sizer_con.Add(key_choice, 0, wx.RIGHT, BORDER)
        sizer_con.Add(op_choice, 0, wx.RIGHT, BORDER)
        sizer_con.Add(text, 0, wx.RIGHT, BORDER)
        sizer_table.Add(sizer_con, 0, wx.LEFT|wx.BOTTOM|wx.RIGHT, BORDER)

        op_choice.SetSelection(0)
        key_choice.SetSelection(0)
        self.Thaw()

        self.Bind(wx.EVT_BUTTON, self.on_btn_del, btn_del)

    def on_btn_del(self, evt):
        """Delete the search condition row."""
        sel = self.table_selection()
        if sel is None:
            return

        sizer = evt.GetEventObject().GetContainingSizer()   # Get sizer that has button
        sizer.Clear(True)   # Destroy the windows in the sizer.
        self.cond_sizers[sel].Remove(sizer) # Destroy the now empty sizer.

        self.Layout()

    def on_product_selection(self, evt):
        """Update the parts grid with selected products parts."""
        sel = self.table_selection()
        if sel is None:
            return

        parent_table = self.get_table()
        parent_grid = self.grids[self.tables.index(parent_table)]
        part_grid: DbGrid = self.child_grids[parent_table]
        row = evt.GetRow()
        fk_val = parent_grid.GetCellValue(row, 0)

        part_grid.set_fk_value([fk_val])
        evt.Skip()

    def on_table_choice(self, evt):
        """Change the panel to search from chosen table."""
        sel = self.table_selection()
        if sel is not None:
            self.Freeze()
            for n, sizer in enumerate(self.cond_sizers):
                box: wx.StaticBox = sizer.GetStaticBox()
                if n != sel:
                    box.Show(False)
                else:
                    box.Show(True)

            for n, grid in enumerate(self.grids):
                if sel == n:
                    grid.Show(True)
                else:
                    grid.Show(False)
            
            for grid in self.child_grids.values():
                grid.Show(False)

            if self.tables[sel] in self.child_grids:
                self.child_grids[self.tables[sel]].Show(True)

            self.Layout()
            self.Thaw()

        self.on_search(None)

    def on_add_condition(self, evt):
        """Add a search condition line."""
        sel = self.table_selection()
        if sel is None:
            return
        self.add_condition(sel)
        self.Layout()

    def on_search(self, evt):
        """Search from database with conditions."""
        sel = self.table_selection()
        if sel is None:
            return

        conditions = {}
        sboxs = self.cond_sizers[sel]
        n = 1
        while n < sboxs.GetItemCount():
            sizer = sboxs.GetItem(n).GetSizer()
            n += 1

            choice_key: wx.Choice = sizer.GetItem(1).GetWindow()
            choice_op: wx.Choice = sizer.GetItem(2).GetWindow()
            text_ctrl: wx.TextCtrl = sizer.GetItem(3).GetWindow()

            key_idx = choice_key.GetSelection()
            if key_idx != wx.NOT_FOUND:
                key = self.cond_keys[sel][key_idx]
                op = choice_op.GetStringSelection()
                value = text_ctrl.GetValue()
                if op == 'like':
                    value = "%" + value + "%"
                if key not in conditions:
                    conditions[key] = [op, value]

        self.grids[sel].GetTable().update_data_with_row_change(conditions)

    def on_show_conditions(self, evt):
        """Show or hide search conditions."""
        sel = self.table_selection()
        if sel is None:
            return
        box: wx.StaticBox = self.cond_sizers[sel].GetStaticBox()
        box.Show(not box.IsShown())
        self.Layout()

    def table_selection(self):
        """Return the index of selected item in table choice window."""
        selection = self.choice_table.GetSelection()
        if selection == wx.NOT_FOUND:
            return None
        else:
            return selection

    def set_table_choice(self, table_idx):
        """Set the index of selected item in table choice window."""
        self.choice_table.SetSelection(table_idx)
        self.on_table_choice(None)


if __name__ == '__main__':
    app = wx.App()

    frame = wx.Frame(None, size=(1500, 800))
    db = tb.OfferTables()
    panel = SearchPanel(frame, db)
    frame.Show()

    app.MainLoop()