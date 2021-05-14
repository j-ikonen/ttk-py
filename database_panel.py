"""
TODO
    Add label for to_offer list and move it together with the list to a panel.
    Add SearchPanel for search stuff
    Move product and part buttons to top row when their grids are hitten.
    Remove add to db buttons from all but first row.
    Add functionality to RCLICK menu items.    
    
"""
import wx
import wx.dataview as dv
from bson.objectid import ObjectId

import grid
import table as db


CHOICE_DB_SIZE = (120, -1)
BORDER = 5
BTN_CHOSEN = "Valitut"
BTN_CHOSEN_TT = "Näytä/Piilota Tarjoukseen siirrettävien lista."
# BTN_ADD = "Tarjoukseen"
# BTN_DEL = "Poista tarjouksesta"
BTN_EDIT = "Muokattavaksi"
# BTN_ADD_TO_DB = "Näytä"
# BTN_DEL_FROM_DB = "Poista tietokannasta"
ADD_TO_TABLE_TITLE = "Lisää tietokantaan"

BTN_ADD_TO_DB_TT = "Näytä Lisää tietokantaan taulukot."

MENU_TO_OFFER = "Lisää tarjoukseen"
MENU_TO_OFFER_HELP = "Lisää valitut hakutulokset tarjoukseen siirrettäviin."
MENU_TO_ADD = "Lisää muokattavaksi"
MENU_TO_ADD_HELP = "Lisää valitut hakutulokset muokattavaksi."
MENU_DEL_OFFER = "Tyhjennä tarjoukseen lista"
MENU_DEL_OFFER_HELP = "Tyhjennä tarjoukseen siirrettyjen lista."
MENU_DEL_DB = "Poista tietokannasta"
MENU_DEL_DB_HELP = "Poista valitut hakutulokset tietokannasta."
MENU_DEL_ADD = "Poista lisättävistä"
MENU_DEL_ADD_HELP = "Poista valitut tietokantaan lisättävistä."
MENU_SHOW_TO_OFFER = "Näytä tarjoukseen"
MENU_SHOW_TO_OFFER_HELP = "Näytä tarjoukseen siirrettävien lista."
MENU_SHOW_SEARCH = "Näytä haku"
MENU_SHOW_SEARCH_HELP = "Näytä tietokanta haku."
MENU_SHOW_ADD = "Näytä lisäys"
MENU_SHOW_ADD_HELP = "Näytä tietokantaan lisättävien taulukot."

TO_OFFER_TITLE = "Tarjoukseen siirrettävät {}"


class AddToDatabasePanel(wx.Panel):
    def __init__(self, parent, table_keys, table_labels, column_setup):
        super().__init__(parent)

        self.table_keys = table_keys
        self.table_labels = table_labels
        self.column_setup = column_setup
        self.grids = {}
        # self.btns = {}
        self.top_btns = {}
        # self.labels = {}

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer_top = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(sizer)

        self.addbtn = wx.Button(self, label=ADD_TO_TABLE_TITLE)
        sizer.Add(sizer_top, 0, wx.EXPAND)

        # first = True
        for n, tablekey in enumerate(self.table_keys):
            grid_2db = grid.BaseGrid(self, self.column_setup[n])
            # label = wx.StaticText(self, label=self.table_labels[n])
            topbtn = wx.Button(self, label=self.table_labels[n])
            # labelbtn = wx.Button(self, label=self.table_labels[n])

            # self.Bind(wx.EVT_BUTTON, self.on_hide_btn, labelbtn)
            self.Bind(wx.EVT_BUTTON, self.on_show_btn, topbtn)

            # self.btns[tablekey] = labelbtn
            self.top_btns[tablekey] = topbtn
            self.grids[tablekey] = grid_2db

            self.sizer_label = wx.BoxSizer(wx.HORIZONTAL)

            self.sizer_label.Add(topbtn, 0, wx.TOP|wx.LEFT, BORDER)
            # self.sizer_label.Add(label, 0, wx.TOP|wx.BOTTOM|wx.LEFT, BORDER)

            sizer.Add(wx.StaticLine(self, size=(20, -1)), 0, wx.EXPAND|wx.LEFT|wx.TOP|wx.RIGHT, BORDER)
            sizer.Add(self.sizer_label, 0, wx.EXPAND)
            sizer.Add(grid_2db, 1, wx.EXPAND|wx.LEFT|wx.TOP|wx.RIGHT, BORDER)

        sizer_top.Add(self.addbtn, 0, wx.LEFT|wx.RIGHT|wx.TOP, BORDER)

    def on_show_btn(self, evt):
        eobj = evt.GetEventObject()
        for k, btn in self.top_btns.items():
            if eobj == btn:
                gr = self.grids[k]
                gr.Show(not gr.IsShown())
                self.Layout()
                evt.Skip()
    
    def get_content(self, table):
        return self.grids[table].get_content()
    
    def get_to_db_button(self):
        return self.addbtn

    def clear_content(self, table):
        self.grids[table].clear_content()


class ToOfferPanel(wx.Panel):
    def __init__(self, parent, title, column_setup):
        super().__init__(parent)

        self.column_setup = column_setup
        self.title = wx.StaticText(self, label=TO_OFFER_TITLE.format(title))
        self.listctrl = dv.DataViewListCtrl(self, style=dv.DV_ROW_LINES|dv.DV_MULTIPLE)

        self.set_columns(title, column_setup)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer_label = wx.BoxSizer(wx.HORIZONTAL)

        sizer_label.Add(self.title, 0, wx.EXPAND)

        sizer.Add(sizer_label, 0, wx.EXPAND|wx.ALL, BORDER)
        sizer.Add(self.listctrl, 1, wx.EXPAND)

        self.SetSizer(sizer)
    
    def set_columns(self, title, column_setup):
        self.column_setup = column_setup
        self.title.SetLabel(TO_OFFER_TITLE.format(title))
        self.listctrl.DeleteAllItems()
        self.listctrl.ClearColumns()
        for value in column_setup.values():
            self.listctrl.AppendTextColumn(value["label"], width=value["width"])

    def delete_selected(self):
        """Delete selected rows and return list of deleted row indexes."""
        del_rows = []
        for item in self.listctrl.GetSelections():
            del_rows.append(self.listctrl.ItemToRow(item))
            self.listctrl.DeleteItem(item)
        del_rows.sort(reverse=True)
        return del_rows

    def append_content(self, data):
        for item in data:
            self.append_row(item)

    def append_row(self, rowdata):
        rowstrings = [db.type2str(value) for value in rowdata]
        self.listctrl.AppendItem(rowstrings)

    def clear(self):
        self.listctrl.DeleteAllItems()


class DatabasePanel(wx.Panel):
    def __init__(self, parent, tables, selection=0):
        super().__init__(parent)

        self.tables: db.OfferTables = tables

        self.display_key = "database"

        display_setup = self.tables.get_display_setup(self.display_key)
        dsp_label = display_setup["label"]
        self.table_keys = display_setup["table"]
        self.table_labels = display_setup["table_label"]
        self.table_pk = display_setup["pk"]
        self.table_columns = display_setup["columns"]

        self.move_to_table = display_setup["move_to_table"]
        self.move_to_columns = display_setup["move_to_columns"]
        self.move_to_ids = [None] * len(self.table_keys)

        self.column_setup = []
        for n, table_key in enumerate(self.table_keys):
            st = tables.get_column_setup(table_key, self.table_columns[n])
            self.column_setup.append(st)

        self.column_keys = []
        self.column_labels = []
        self.column_widths = []

        self.show_search = True
        self.show_to_offer = True
        self.show_add = True

        self.to_offer = {k: [] for k in self.table_keys}
        self.GetParent().SetLabel(dsp_label)
        self.set_column_setup(selection)

        self.choice_dbs = wx.Choice(self, size=CHOICE_DB_SIZE, choices=self.table_labels)
        self.choice_col = wx.Choice(self, size=CHOICE_DB_SIZE, choices=self.column_labels)
        self.search = wx.SearchCtrl(self)
        self.list_search = dv.DataViewListCtrl(self, style=dv.DV_ROW_LINES|dv.DV_MULTIPLE)
        
        self.to_offer_panel = ToOfferPanel(
            self,
            self.table_labels[selection],
            self.column_setup[selection]
        )
        self.add_to_db_panel = AddToDatabasePanel(
            self,
            self.table_keys,
            self.table_labels,
            self.column_setup)

        self.Bind(wx.EVT_CHOICE, self.on_choice_db, self.choice_dbs)
        self.Bind(wx.EVT_CHOICE, self.on_choice_col, self.choice_col)
        self.Bind(wx.EVT_SEARCH, self.on_search, self.search)
        self.Bind(wx.EVT_BUTTON, self.on_add_to_db, self.add_to_db_panel.get_to_db_button())
        # self.Bind(wx.EVT_BUTTON, self.on_btn_add, self.btn_add)
        # self.Bind(wx.EVT_BUTTON, self.on_btn_del, self.btn_del)
        # self.Bind(wx.EVT_BUTTON, self.on_btn_add_to_db, self.btn_add_to_db)
        # self.Bind(wx.EVT_BUTTON, self.on_btn_del_from_db, self.btn_del_from_db)
        self.Bind(dv.EVT_DATAVIEW_ITEM_CONTEXT_MENU, self.on_context_menu)
        self.Bind(wx.EVT_CONTEXT_MENU, self.on_context_menu)

        self.choice_dbs.SetSelection(selection)
        self.reset_setup()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer_choices = wx.BoxSizer(wx.HORIZONTAL)
        # sizer_2db = wx.BoxSizer(wx.HORIZONTAL)
        sizer_div = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_right = wx.BoxSizer(wx.VERTICAL)
        self.sizer_left = wx.BoxSizer(wx.VERTICAL)

        sizer_choices.Add(self.choice_dbs, 0, wx.EXPAND|wx.RIGHT, BORDER)
        sizer_choices.Add(self.choice_col, 0, wx.EXPAND|wx.RIGHT, BORDER)
        sizer_choices.Add(self.search, 0, wx.EXPAND|wx.RIGHT, BORDER)
        # sizer_choices.Add(self.btn_del_from_db, 0, wx.EXPAND|wx.RIGHT, BORDER)
        # sizer_choices.Add(self.btn_add_to_db, 0, wx.EXPAND|wx.RIGHT, BORDER)

        self.sizer_left.Add(sizer_choices, 0, wx.EXPAND|wx.ALL, BORDER)
        self.sizer_left.Add(self.list_search, 1, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, BORDER)

        # sizer_2db.Add(self.btn_add, 0, wx.EXPAND|wx.RIGHT, BORDER)
        # sizer_2db.Add(self.btn_del, 0, wx.EXPAND|wx.RIGHT, BORDER)

        # sizer_left.Add(sizer_2db, 0, wx.EXPAND|wx.ALL, BORDER)
        self.sizer_left.Add(self.to_offer_panel, 1, wx.BOTTOM|wx.LEFT|wx.RIGHT|wx.EXPAND, BORDER)

        self.sizer_right.Add(self.add_to_db_panel, 1, wx.BOTTOM|wx.EXPAND, BORDER)

        sizer_div.Add(self.sizer_left, 1, wx.EXPAND)
        sizer_div.Add(self.sizer_right, 1, wx.EXPAND|wx.LEFT, BORDER)
        sizer.Add(sizer_div, 1, wx.EXPAND)

        self.SetSizer(sizer)

    def set_column_setup(self, sel):
        self.column_keys = [key for key in self.column_setup[sel].keys()]
        self.column_labels = [value["label"] for value in self.column_setup[sel].values()]
        self.column_widths = [value["width"] for value in self.column_setup[sel].values()]

    def on_context_menu(self, evt):
        if not hasattr(self, "id_to_offer"):
            self.id_to_offer = wx.NewIdRef()
            self.id_to_add = wx.NewIdRef()

            self.id_del_offer = wx.NewIdRef()
            self.id_del_db = wx.NewIdRef()
            self.id_del_add = wx.NewIdRef()

            self.id_show_to_offer = wx.NewIdRef()
            self.id_show_search = wx.NewIdRef()
            self.id_show_add = wx.NewIdRef()

            self.Bind(wx.EVT_MENU, self.on_to_offer, id=self.id_to_offer)
            self.Bind(wx.EVT_MENU, self.on_to_add, id=self.id_to_add)
            self.Bind(wx.EVT_MENU, self.on_del_offer, id=self.id_del_offer)
            self.Bind(wx.EVT_MENU, self.on_del_db, id=self.id_del_db)
            self.Bind(wx.EVT_MENU, self.on_del_add, id=self.id_del_add)
            self.Bind(wx.EVT_MENU, self.on_show_to_offer, id=self.id_show_to_offer)
            self.Bind(wx.EVT_MENU, self.on_show_search, id=self.id_show_search)
            self.Bind(wx.EVT_MENU, self.on_show_add, id=self.id_show_add)

        menu = wx.Menu()
        menu.Append(self.id_to_offer, MENU_TO_OFFER, MENU_TO_OFFER_HELP)
        menu.Append(self.id_to_add, MENU_TO_ADD, MENU_TO_ADD_HELP)
        menu.AppendSeparator()
        menu.Append(self.id_del_offer, MENU_DEL_OFFER, MENU_DEL_OFFER_HELP)
        menu.Append(self.id_del_db, MENU_DEL_DB, MENU_DEL_DB_HELP)
        menu.Append(self.id_del_add, MENU_DEL_ADD, MENU_DEL_ADD_HELP)
        menu.AppendSeparator()
        menu.AppendCheckItem(self.id_show_to_offer, MENU_SHOW_TO_OFFER, MENU_SHOW_TO_OFFER_HELP)
        menu.AppendCheckItem(self.id_show_search, MENU_SHOW_SEARCH, MENU_SHOW_SEARCH_HELP)
        menu.AppendCheckItem(self.id_show_add, MENU_SHOW_ADD, MENU_SHOW_ADD_HELP)

        if self.show_search:
            menu.Check(self.id_show_search, True)
        if self.show_to_offer:
            menu.Check(self.id_show_to_offer, True)
        if self.show_add:
            menu.Check(self.id_show_add, True)

        self.PopupMenu(menu)
        # menu.Destroy()
        # evt.Skip()

    def set_move_to_id(self, table_key, move_to):
        """Set the id of parents where search results can be added to from each table."""
        self.move_to_ids[self.table_keys.index(table_key)] = move_to

    def on_to_offer(self, evt):
        print("Menu - on_to_offer")

        if self.move_to_ids is None:
            print("No target selected where selected items can be moved.")
            return

        search_table = self.table_keys[self.choice_dbs.GetSelection()]
        selection = self.choice_dbs.GetSelection()
        table = self.move_to_table[selection]
        columns = self.move_to_columns[selection]
        parent_id = self.move_to_ids[selection]
        delcol = []
        # print(self.column_keys)
        for n, key in enumerate(self.column_keys):
            if key not in columns:
                delcol.append(n)
                print(key)
        delcol.sort(reverse=True)
        data = self.get_search_selections()

        for datarow in data:
            oid = str(ObjectId())
            datarow = list(datarow)
            for col in delcol:
                del datarow[col]
            if self.tables.insert(
                table,
                columns,
                [oid, parent_id] + datarow
            ):
                self.to_offer_panel.append_row(datarow)
                self.to_offer[search_table].append(datarow)

    def on_add_to_db(self, evt):
        for n, table in enumerate(self.table_keys):
            content = self.add_to_db_panel.get_content(table)
            print(content)

            self.tables.insert(
                table,
                self.table_columns[n],
                content,
                True
            )

            self.add_to_db_panel.clear_content(table)


    def on_to_add(self, evt):
        print("Menu - ")

    def on_del_offer(self, evt):
        print("Menu - ")
        self.del_to_offer()

    def on_del_db(self, evt):
        print("Menu - ")

    def on_del_add(self, evt):
        print("Menu - ")

    def on_show_to_offer(self, evt):
        if evt.IsChecked():
            self.show_to_offer = True
        else:
            self.show_to_offer = False
        self.to_offer_panel.Show(self.show_to_offer)
        self.Layout()

    def on_show_search(self, evt):
        if evt.IsChecked():
            self.show_search = True
        else:
            self.show_search = False
        self.sizer_left.ShowItems(self.show_search)
        self.to_offer_panel.Show(self.show_to_offer)
        self.Layout()

    def on_show_add(self, evt):
        if evt.IsChecked():
            self.show_add = True
        else:
            self.show_add = False
        self.add_to_db_panel.Show(self.show_add)
        self.Layout()

    def get_search_selections(self):
        """Return list of rows found from database with keys of selected search results."""
        sel_items = self.list_search.GetSelections()
        sel_rows = [self.list_search.ItemToRow(item) for item in sel_items]

        pk_key = self.table_pk[self.choice_dbs.GetSelection()]
        pk_idx = [self.column_keys.index(key) for key in pk_key]

        table_key = self.table_keys[self.choice_dbs.GetSelection()]

        data = []

        for n in sel_rows:
            pk_value = []

            # Form the private key values.
            for col in pk_idx:
                pk_value.append(self.list_search.GetValue(n, col))
            
            # Get the row data with the private key.
            row_data = self.tables.get(
                table_key,
                self.column_keys,
                pk_key,
                pk_value,
            )
            data.append(row_data)
        return data


    # def add_to_offer(self):
    #     sel_items = self.list_search.GetSelections()
    #     sel_rows = [self.list_search.ItemToRow(item) for item in sel_items]
    #     # for parts pk_key = ["code", "product_code"]
    #     pk_key = self.table_pk[self.choice_dbs.GetSelection()]
    #     pk_idx = [self.column_keys.index(key) for key in pk_key]
    #     table_key = self.table_keys[self.choice_dbs.GetSelection()]
    #     for n in sel_rows:
    #         pk_value = []
    #         for col in pk_idx:
    #             pk_value.append(self.list_search.GetValue(n, col))
    #         row_data = self.tables.get(
    #             table_key,
    #             self.column_keys,
    #             pk_key,
    #             pk_value,
    #         )
    #         self.to_offer[table_key].append(row_data)
    #         self.to_offer_panel.append_row(row_data)

    def del_to_offer(self):
        """Clear the to offer list."""
        table_key = self.table_keys[self.choice_dbs.GetSelection()]
        # del_rows = self.add_to_db_panel.delete_selected()
        # for row in del_rows:
        #     del self.to_offer[table_key][row]
        self.to_offer_panel.listctrl.DeleteAllItems()
        self.to_offer[table_key] = []

    def on_choice_db(self, evt):
        """Change the column setups on database table choice."""
        selection = self.choice_dbs.GetSelection()
        self.set_column_setup(selection)
        self.reset_setup()

    def on_choice_col(self, evt):
        """."""
        pass

    def on_search(self, evt):
        """."""
        column_idx = self.choice_col.GetSelection()
        table_idx = self.choice_dbs.GetSelection()
        column_key = self.column_keys[column_idx]
        value = evt.GetString()
        data = self.tables.get(
            self.table_keys[table_idx],
            self.column_keys,
            [column_key],
            ['%'+value+'%'],
            True,
            " like "
        )
        # print(data)
        self.reset_list(data)

    def reset_list(self, data):
        self.list_search.DeleteAllItems()
        for row_data in data:
            row_str = [db.type2str(value) for value in row_data]
            self.list_search.AppendItem(row_str)

    def reset_setup(self):
        self.search.SetValue("")

        self.choice_col.Clear()
        self.choice_col.AppendItems(self.column_labels)
        self.choice_col.Select(0)

        self.list_search.DeleteAllItems()
        self.list_search.ClearColumns()

        for n, label in enumerate(self.column_labels):
            self.list_search.AppendTextColumn(
                label,
                width=self.column_widths[n]
            )
        selection = self.choice_dbs.GetSelection()
        setup = self.column_setup[selection]

        self.to_offer_panel.set_columns(self.table_labels[selection], setup)
        self.to_offer_panel.append_content(self.to_offer[self.table_keys[selection]])



if __name__ == '__main__':
    app = wx.App(useBestVisual=True)

    offer_keys = ["id", "name"]
    offer_data = [
        (str(ObjectId()), "Tarjous 1"),
        (str(ObjectId()), "Tarjous 2"),
        (str(ObjectId()), "Testi tarjous"),
        (str(ObjectId()), "Uusi tarjous")
    ]
    group_keys = ["id", "offer_id", "name"]
    group_data = [
        (str(ObjectId()), offer_data[0][0], "Keittiö"),
        (str(ObjectId()), offer_data[0][0], "Kylpyhuone"),
        (str(ObjectId()), offer_data[1][0], "Keittiö"),
        (str(ObjectId()), offer_data[2][0], "Keittiö"),
        (str(ObjectId()), offer_data[3][0], "Keittiö"),
        (str(ObjectId()), offer_data[3][0], "...")
    ]
    opredef_keys = ["id", "group_id"]
    opredef_data = (str(ObjectId()), group_data[0][0])

    omaterial_keys = ["id", "group_id"]
    omaterial_data = (str(ObjectId()), group_data[0][0])

    oproduct_keys = ["id", "group_id", "width", "height", "depth"]
    oproduct_data = (str(ObjectId()), group_data[0][0], 1200, 2300, 620)

    opart_keys = ["id", "product_id"]
    opart_data = (str(ObjectId()), oproduct_data[0][0])

    material_keys = ["code"]
    material_data = ("MAT16",)

    product_keys = ["code", "width", "height", "depth"]
    product_data = ("kaappi", 1200, 2300, 620)
    product_data2 = ("tuote", 650, 300, 420)
    product_data3 = [("tuote1", 650, 300, 420), ("tuote2", 640, 310, 410)]

    part_keys = ["code", "product_code"]
    part_data = [
        ("hylly", "kaappi"),
        ("tausta", "kaappi"),
        ("ovi", "kaappi")
    ]
    tables = db.OfferTables()

    tables.insert("offers", offer_keys, offer_data[0])
    tables.insert("offers", offer_keys, offer_data[1:], True)
    tables.insert("offer_groups", group_keys,  group_data, True)
    tables.insert("offer_predefs", opredef_keys, opredef_data)

    tables.insert("offer_materials", omaterial_keys, omaterial_data)
    tables.insert("offer_products", oproduct_keys, oproduct_data)
    tables.insert("offer_parts", opart_keys, opart_data)
    tables.insert("materials", material_keys, material_data)
    tables.insert("products", product_keys, product_data)
    tables.insert("parts", part_keys, part_data, True)
    tables.insert("products", product_keys, product_data2)
    tables.insert("products", product_keys, product_data3, True)

    frame = wx.Frame(None, size=(1200, 500))
    panel = DatabasePanel(frame, tables)
    panel.set_move_to_id("materials", group_data[0][0])

    frame.Show()
    frame.Layout()

    app.MainLoop()
