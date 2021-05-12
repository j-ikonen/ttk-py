from typing import Iterable

import wx
import wx.dataview as dv
import wx.grid as wxg
from bson.objectid import ObjectId

import grid
import table as db


CHOICE_DB_SIZE = (120, -1)
BORDER = 5
BTN_ADD = "Lisää valitut tarjoukseen"
BTN_DEL = "Poista valitut"
BTN_ADD_TO_DB = "Lisää/Muokkaa"
BTN_DEL_FROM_DB = "Poista tietokannasta"
ADD_TO_TABLE_TITLE = "Lisää tietokantaan"


def get_editor_renderer(typestring):
    """Return the cell editor matching the given type string."""
    split = typestring.split(':')
    if len(split) > 1:
        args = split[1].split(',')
    else:
        args = []

    editor = None
    renderer = None

    if split[0] == "string":
        renderer = wxg.GridCellStringRenderer()
        if len(args) == 1:
            editor = wxg.GridCellTextEditor(int(args[0]))
    elif split[0] == "long":
        renderer = wxg.GridCellNumberRenderer()
        if len(args) == 2:
            editor = wxg.GridCellNumberEditor(int(args[0]), int(args[1]))
        elif len(args) == 1:
            editor = wxg.GridCellNumberEditor(int(args[0]))
        else:
            editor = wxg.GridCellNumberEditor()
    elif split[0] == "double":
        if len(args) == 2:
            editor = wxg.GridCellFloatEditor(int(args[0]), int(args[1]))
            renderer = wxg.GridCellFloatRenderer(int(args[0]), int(args[1]))
        else:
            editor = wxg.GridCellFloatRenderer()
            renderer = wxg.GridCellFloatRenderer()

    if editor is None:
        editor = wxg.GridCellTextEditor()
    if renderer is None:
        renderer = wxg.GridCellStringRenderer()
    return (editor, renderer)


class ObjectGrid(wxg.Grid):
    def __init__(self, parent, tables, tablename):
        super().__init__(parent)

        self.tables: db.OfferTables = tables

        self.panel_key = "objectgrid"
        self.tablename = tablename
        self.setup_key = self.panel_key + "." + tablename

        self.table_label = ""
        self.pk_key = None
        self.pk = None

        self.row_keys = []
        self.row_labels = []
        self.row_types = []

        self.get_setup()
        self.rows = len(self.row_keys)

        self.CreateGrid(self.rows, 1)
        self.SetColLabelSize(1)

        for n, label in enumerate(self.row_labels):
            (editor, renderer) = get_editor_renderer(self.row_types[n])
            self.SetCellEditor(n, 0, editor)
            self.SetCellRenderer(n, 0, renderer)
            self.SetRowLabelValue(n, label)

        self.Bind(wxg.EVT_GRID_CELL_CHANGED, self.on_cell_changed)
        self.Bind(wxg.EVT_GRID_EDITOR_HIDDEN, self.on_editor_hidden)

        self.SetRowLabelSize(wxg.GRID_AUTOSIZE)
        # self.SetRowLabelAlignment(wx.ALIGN_RIGHT, wx.ALIGN_CENTER)

    def change_data(self, pk: Iterable=None):
        """Change the data to row at new private key.

        Parameters
        ----------
        pk : Iterable, optional
            Private key to the new row, must be iterable, by default None.
        """
        if pk is None:
            self.ClearGrid()
            self.pk = None
        else:
            self.pk = pk
            self.refresh_data()

    def refresh_data(self):
        obj = self.tables.get(
            self.tablename,
            self.row_keys,
            self.pk_key,
            self.pk
        )
        self.BeginBatch()
        print(f"\nSetupGrid.refresh_data - self.data: {self.data}\n")
        for n in range(self.rows):
            self.SetCellValue(n, 0, db.type2str(obj[n]))
        self.EndBatch()

    def on_cell_changed(self, evt):
        """Handle cell changed event."""
        row = evt.GetRow()
        typestring = self.types[row]
        value = db.str2type(typestring, self.GetCellValue(row, 0))
        self.tables.update_one(
            self.tablename,
            self.row_keys[row],
            self.pk_key,
            (value, self.pk)
        )
        evt.Skip()

    def on_editor_hidden(self, evt):
        evt.Skip()

    def get_setup(self):
        col_setup = self.tables.get_column_setup(self.setup_key)
        panel_setup = self.tables.get_panel_setup(self.panel_key)[self.tablename]

        self.row_keys = [key for key in col_setup.keys()]
        self.row_labels = [val["label"] for val in col_setup.values()]
        self.row_types = [val["type"] for val in col_setup.values()]

        self.table_label = panel_setup["label"]
        self.pk_key = panel_setup["pk"]
        if isinstance(self.pk_key, str):
            self.pk_key = [self.pk_key]


class AddToDatabaseDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title=ADD_TO_TABLE_TITLE)



class DatabasePanel(wx.Panel):
    def __init__(self, parent, tables):
        super().__init__(parent)

        self.tables: db.OfferTables = tables

        self.panel_key = "dbpanel"
        self.table_setup = tables.get_panel_setup(self.panel_key)
        self.table_keys = [key for key in self.table_setup.keys()]

        self.db_labels = [val["label"] for val in self.table_setup.values()]
        self.db_pk = [val["pk"] for val in self.table_setup.values()]

        self.to_offer = {k: [] for k in self.table_keys}

        self.column_keys = []
        self.column_labels = []
        self.column_widths = []
        self.column_setup(0)

        self.choice_db = wx.Choice(self, size=CHOICE_DB_SIZE, choices=self.db_labels)
        self.choice_col = wx.Choice(self, size=CHOICE_DB_SIZE, choices=self.column_labels)
        self.search = wx.SearchCtrl(self)
        self.btn_add = wx.Button(self, label=BTN_ADD)
        self.btn_del = wx.Button(self, label=BTN_DEL)
        self.btn_add_to_db = wx.Button(self, label=BTN_ADD_TO_DB)
        self.btn_del_from_db = wx.Button(self, label=BTN_DEL_FROM_DB)
        self.list_search = dv.DataViewListCtrl(self, style=dv.DV_ROW_LINES|dv.DV_MULTIPLE)
        self.list_2offer = dv.DataViewListCtrl(self, style=dv.DV_ROW_LINES|dv.DV_MULTIPLE)

        self.Bind(wx.EVT_CHOICE, self.on_choice_db, self.choice_db)
        self.Bind(wx.EVT_CHOICE, self.on_choice_col, self.choice_col)
        self.Bind(wx.EVT_SEARCH, self.on_search, self.search)
        self.Bind(wx.EVT_BUTTON, self.on_btn_add, self.btn_add)
        self.Bind(wx.EVT_BUTTON, self.on_btn_del, self.btn_del)
        self.Bind(wx.EVT_BUTTON, self.on_btn_add_to_db, self.btn_add_to_db)
        self.Bind(wx.EVT_BUTTON, self.on_btn_del_from_db, self.btn_del_from_db)

        self.choice_db.SetSelection(0)
        self.reset_setup()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer_choices = wx.BoxSizer(wx.HORIZONTAL)
        sizer_2db = wx.BoxSizer(wx.HORIZONTAL)

        sizer_choices.Add(self.choice_db, 0, wx.EXPAND|wx.RIGHT, BORDER)
        sizer_choices.Add(self.choice_col, 0, wx.EXPAND|wx.RIGHT, BORDER)
        sizer_choices.Add(self.search, 0, wx.EXPAND|wx.RIGHT, BORDER)
        sizer_choices.Add(self.btn_add_to_db, 0, wx.EXPAND|wx.RIGHT, BORDER)
        sizer_choices.Add(self.btn_del_from_db, 0, wx.EXPAND|wx.RIGHT, BORDER)

        sizer.Add(sizer_choices, 0, wx.EXPAND|wx.ALL, BORDER)
        sizer.Add(self.list_search, 1, wx.EXPAND)

        sizer_2db.Add(self.btn_add, 0, wx.EXPAND|wx.RIGHT, BORDER)
        sizer_2db.Add(self.btn_del, 0, wx.EXPAND|wx.RIGHT, BORDER)

        sizer.Add(sizer_2db, 0, wx.EXPAND|wx.ALL, BORDER)
        sizer.Add(self.list_2offer, 1, wx.EXPAND)

        self.SetSizer(sizer)

    def column_setup(self, sel):
        column_setup = tables.get_column_setup(
            self.panel_key + '.' + self.table_keys[sel])
        self.column_keys = [key for key in column_setup.keys()]
        self.column_labels = [value["label"] for value in column_setup.values()]
        self.column_widths = [value["width"] for value in column_setup.values()]

    def on_btn_add(self, evt):
        sel_items = self.list_search.GetSelections()
        sel_rows = [self.list_search.ItemToRow(item) for item in sel_items]
        pk_key = self.db_pk[self.choice_db.GetSelection()]
        pk_idx = self.column_keys.index(pk_key)
        table_key = self.table_keys[self.choice_db.GetSelection()]
        for n in sel_rows:
            row_data = self.tables.get(
                table_key,
                self.column_keys,
                [pk_key],
                [self.list_search.GetValue(n, pk_idx)],
            )
            self.to_offer[table_key].append(row_data)
            self.list_2offer.AppendItem([db.type2str(val) for val in row_data])

    def on_btn_del(self, evt):
        table_key = self.table_keys[self.choice_db.GetSelection()]
        sel_items = self.list_2offer.GetSelections()
        sel_rows = [self.list_2offer.ItemToRow(item) for item in sel_items]
        sel_rows.sort(reverse=True)
        for row in sel_rows:
            del self.to_offer[table_key][row]
            self.list_2offer.DeleteItem(row)

    def on_btn_add_to_db(self, evt):
        pass

    def on_btn_del_from_db(self, evt):
        pass


    def on_choice_db(self, evt):
        """."""
        selection = self.choice_db.GetSelection()
        self.column_setup(selection)
        self.reset_setup()

    def on_choice_col(self, evt):
        """."""
        pass

    def on_search(self, evt):
        """."""
        column_idx = self.choice_col.GetSelection()
        table_idx = self.choice_db.GetSelection()
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
        print(data)
        self.reset_list(data)

    def reset_list(self, data):
        self.list_search.DeleteAllItems()
        for row_data in data:
            row_str = [db.type2str(value) for value in row_data]
            self.list_search.AppendItem(row_str)

    def reset_list_2offer(self):
        self.list_2offer.DeleteAllItems()
        for item in self.to_offer[self.table_keys[self.choice_db.GetSelection()]]:
            self.list_2offer.AppendItem([db.type2str(val) for val in item])

    def reset_setup(self):
        self.search.SetValue("")
        self.list_search.DeleteAllItems()
        self.list_2offer.DeleteAllItems()
        self.choice_col.Clear()
        self.choice_col.AppendItems(self.column_labels)
        self.choice_col.Select(0)
        self.list_search.ClearColumns()
        self.list_2offer.ClearColumns()
        for n, label in enumerate(self.column_labels):
            self.list_search.AppendTextColumn(
                label,
                width=self.column_widths[n]
            )
            self.list_2offer.AppendTextColumn(
                label,
                width=self.column_widths[n]
            )
        self.reset_list_2offer()



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

    frame.Show()
    frame.Layout()

    app.MainLoop()
