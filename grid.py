import wx
import wx.grid as wxg
from bson.objectid import ObjectId


from table import OfferTables, str2type, type2str


class GridPanel(wx.Panel):
    BORDER = 5
    BTN_DEL = "Poista valitut"

    def __init__(self, parent, tables: OfferTables, key):
        super().__init__(parent)

        # self.SetBackgroundColour((255, 150, 100))
        self.SetBackgroundColour((255, 200, 120))

        label = wx.StaticText(self, label=key)
        btn_del = wx.Button(self, label=self.BTN_DEL)
        # self.grid = TheGrid(self, tables, key)
        # dsp = tables.get_display_setup("products")
        # setup = tables.get_column_setup(dsp.get("table"), dsp.get("columns"))
        self.ids = []
        self.grid = TableGrid(self, tables, "products", self.ids)
        pk = tables.group_data[0][0]
        self.grid.set_parent_id(pk)

        self.Bind(wx.EVT_BUTTON, self.on_btn_del, btn_del)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer_label = wx.BoxSizer(wx.HORIZONTAL)

        sizer_label.Add(label, 0, wx.EXPAND)
        sizer_label.Add(btn_del, 0, wx.EXPAND|wx.LEFT, 55)

        sizer.Add(sizer_label, 0, wx.EXPAND|wx.TOP|wx.LEFT, self.BORDER)
        sizer.Add(self.grid, 1, wx.EXPAND)
        self.SetSizer(sizer)

    def on_btn_del(self, evt):
        self.grid.delete_selected()


class BaseGrid(wxg.Grid):
    def __init__(self, parent, setup, n_rows=None):
        super().__init__(parent)

        self.setup = {}
        self.keys = []
        self.read_only = []
        self.unique = []

        self.set_setup(setup)
        self.n_columns = len(self.keys)
        self.static_rows = True

        if n_rows is None:
            self.static_rows = False
            self.CreateGrid(1, self.n_columns)
        else:
            self.CreateGrid(n_rows, self.n_columns)

        self.SetRowLabelSize(35)

        for col in range(self.n_columns):
            self.SetColLabelValue(col, self.get_label(col))
            self.SetColSize(col, self.get_width(col))
            self.set_col_format(col)
            
        self.Bind(wxg.EVT_GRID_EDITOR_SHOWN, self.on_show_editor)
        self.Bind(wxg.EVT_GRID_CELL_CHANGING, self.on_cell_changing)
        self.Bind(wx.EVT_KEY_DOWN, self.on_key_down)

    def on_key_down(self, evt):
        """Handle key events for this grid."""
        keycode = evt.GetKeyCode()
        # alt = evt.AltDown()
        # shift = evt.ShiftDown()

        if keycode == wx.WXK_RETURN:
            if evt.ControlDown():
                self.moveto_first()

        elif keycode == wx.WXK_TAB:
            print("TAB")

        elif keycode == wx.WXK_DELETE:
            self.delete_selected()

        evt.Skip()

    def moveto_first(self):
        """Moves cursor to the first columns of the next row."""
        row = self.GetGridCursorRow()
        col = self.GetGridCursorCol()
        if row >= self.GetNumberRows() - 1:
            newrow = row
        else:
            newrow = row + 1

        self.SetGridCursor(newrow, 0)

    def on_show_editor(self, evt):
        """Veto showing of editor on read only columns."""
        if evt.GetCol() in self.read_only:
            print("BaseGrid.on_show_editor - " +
                  f"Column '{evt.GetCol()}' is read only.")
            evt.Veto()

    def on_cell_changing(self, evt):
        """Veto change on unique columns and init when edit in last row."""
        value = evt.GetString()
        col = evt.GetCol()
        row = evt.GetRow()

        # Veto if the value exists in unique column.
        if col in self.unique and self.value_exists(col, value):
            evt.Veto()

        # Init uninitiated row.
        if not self.static_rows and row >= self.GetNumberRows() - 1:
            if not self.edit_in_last_row(row, col, value):
                evt.Veto()
        else:
            if not self.edit_value(row, col, value):
                evt.Veto()

        evt.Skip()

    def value_exists(self, col, value):
        """Return True if the value already exists in the column."""
        for test_row in range(self.GetNumberRows()):
            if value == self.GetCellValue(test_row, col):
                print("TheGrid.on_cell_changing - " +
                    f"Column '{self.get_label(col)}' is unique. " +
                    f"Value '{value}' already exists.")
                return True
        return False

    def edit_value(self, row, col, value) -> bool:
        """Overload this for saving the edited values where required.

        Returns
        -------
        True. Return False from overload to Veto cell change.
        """
        return True

    def edit_in_last_row(self, row, col, value) -> bool:
        """Overload this for handling first edit on a new row.
        
        Call this through super for appending an empty row.

        Returns
        -------
        True. Return False from overload to Veto cell change.
        """
        self.AppendRows(1)
        return True

    def set_content(self, data):
        """Set the content of the grid."""
        nrows = self.GetNumberRows()
        if nrows > 0:
            self.DeleteRows(0, nrows)
        self.AppendRows(len(data))
        if not self.static_rows:
            self.AppendRows(1)

        self.BeginBatch()
        for row, row_data in enumerate(data):
            for col, value in enumerate(row_data):
                if value is not None:
                    self.SetCellValue(row, col, type2str(value))
        self.EndBatch()

    def get_content(self):
        """Return a list of lists formed from content of the grid."""
        content = []
        for row in range(self.GetNumberRows()-1):
            row_data = []
            for col in range(self.GetNumberCols()):
                value = str2type(self.get_type(col), self.GetCellValue(row, col))
                row_data.append(value)
            content.append(row_data)
        return content

    def clear_content(self):
        rows = self.GetNumberRows()
        if rows > 0:
            self.DeleteRows(0, rows)
            self.AppendRows(1)

    def delete_selected(self):
        selected = self.GetSelectedRows()
        selected.sort(reverse=True)
        for row in selected:
            self.delete_row(row)

    def delete_row(self, row):
        self.DeleteRows(row)

    def set_setup(self, setup):
        self.keys = [k for k in setup.keys()]
        self.setup = setup
        for col, v in enumerate(self.setup.values()):
            if v["ro"]:
                self.read_only.append(col)
            
            if v["unique"]:
                self.unique.append(col)

    def get_label(self, col):
        """Return the label of column."""
        return self.setup[self.keys[col]]["label"]

    def get_type(self, col):
        """Return the type of column."""
        return self.setup[self.keys[col]]["type"]

    def get_width(self, col):
        """Return the width of column."""
        return self.setup[self.keys[col]]["width"]

    def get_read_only(self, col):
        """Return the read_only of column."""
        return self.setup[self.keys[col]]["read_only"]

    def get_unique(self, col):
        """Return the unique of column."""
        return self.setup[self.keys[col]]["unique"]

    def set_width(self, col, width):
        """Set the width of a column setup."""
        self.setup[self.keys[col]]["width"] = width

    def set_col_format(self, col):
        """Set the column format by typestring."""
        typestring = self.get_type(col)
        typesplit = typestring.split(':')
        t = typesplit[0]
        if len(typesplit) == 2:
            args = typesplit[1].split(',')
        else:
            args = None
        if t == "double":
            if args is None:
                self.SetColFormatFloat(col)
            else:
                self.SetColFormatFloat(col, int(args[0]), int(args[1]))
        elif t == "long":
            self.SetColFormatNumber(col)
        elif t == "choice":
            self.SetColFormatCustom(col, typestring)
        elif t == "bool":
            self.SetColFormatBool(col)


class FieldCountGrid(BaseGrid):
    def __init__(self, parent, tables: OfferTables):

        setup = {
            "unit": {
                "label": "Asennusyksikkö",
                "type": "string",
                "width": 100,
                "ro": True,
                "unique": True
            },
            "mult": {
                "label": "Kerroin",
                "type": "double:6,2",
                "width": 55,
                "ro": True,
                "unique": False
            },
            "count": {
                "label": "Määrä",
                "type": "double:6,2",
                "width": 45,
                "ro": True,
                "unique": False
            },
            "cost": {
                "label": "Hinta",
                "type": "double:6,2",
                "width": 45,
                "ro": True,
                "unique": False
            }
        }
        super().__init__(parent, setup, 0)
        self.tables = tables


class TableGrid(BaseGrid):
    
    def __init__(self, parent, tables: OfferTables, name, ids):
        self.tables = tables

        display_setup = self.tables.get_display_setup(name)
        self.label = display_setup["label"]
        self.tablename = display_setup["table"]
        self.pk_key = display_setup["pk"]
        self.fk_key = display_setup["fk"]
        self.column_keys = display_setup["columns"]

        column_setup = self.tables.get_column_setup(self.tablename, self.column_keys)
        self.types = [val["type"] for val in column_setup.values()]

        self.parent_id = None
        self.ids = ids

        super().__init__(parent, column_setup)

        self.Bind(wxg.EVT_GRID_CELL_CHANGING, self.on_cell_changing)
        self.Bind(wxg.EVT_GRID_EDITOR_SHOWN, self.on_show_editor)

    def set_parent_id(self, parent_id):
        self.parent_id = parent_id
        self.refresh()

    def refresh(self):
        if self.parent_id is None:
            self.clear_content()
        else:
            if self.tablename == "offer_products":
                data = self.tables.get_offer_products(self.parent_id)
            else:
                data = self.tables.get(
                    self.tablename,
                    ["id"] + self.column_keys,
                    self.fk_key,
                    [self.parent_id],
                    True
            )
            content = []
            for datarow in data:
                self.ids.append(datarow[0])
                content.append(datarow[1:])
                print(datarow)
            self.set_content(content)


    def get_id(self, row):
        return self.ids[row]

    def on_cell_changing(self, evt):
        super().on_cell_changing(evt)

        # value = evt.GetString()
        # row = evt.GetRow()
        # col = evt.GetCol()


    def on_show_editor(self, evt):
        """Veto edit if not data source is defined."""
        if self.parent_id is None:
            print("Grid '{}' has no defined data source".format(self) +
                  " to table '{}'. Vetoing show editor.\n".format(self.tablename))
            evt.Veto()

        super().on_show_editor(evt)

    def delete_row(self, row):
        rowid = self.ids[row]
        return super().delete_row(row)

    def edit_value(self, row, col, value):
        key = self.column_keys[col]

        table = self.tablename
        pk = self.pk_key[0]
        values = [str2type(self.get_type(col), value), self.ids[row]]

        success = self.tables.update_one(table, key, pk, values)
        # print(f"{table}, {key}, {pk}, {values}")
        if success:
            return super().edit_value(row, col, value)
        else:
            return False

    def edit_in_last_row(self, row, col, value):
        """Insert a new unique item to table on editing the last row."""
        key = self.column_keys[col]
        oid = str(ObjectId())

        # Append an empty row on successful insert.
        # print(self.pk_key)
        columns = self.pk_key + self.fk_key + [key]
        values = (oid, self.parent_id, value)
        if self.tables.insert(self.tablename, columns, values):
            self.ids.append(oid)
            return super().edit_in_last_row(row, col, value)
        else:
            return False


if __name__ == '__main__':
    app = wx.App(useBestVisual=True)
    tables = OfferTables()

    # offer_keys = ["id", "name"]
    # offer_data = [
    #     (str(ObjectId()), "Tarjous 1"),
    #     (str(ObjectId()), "Tarjous 2"),
    #     (str(ObjectId()), "Testi tarjous"),
    #     (str(ObjectId()), "Uusi tarjous")
    # ]
    # group_keys = ["id", "offer_id", "name"]
    # group_data = [
    #     (str(ObjectId()), offer_data[0][0], "Keittiö"),
    #     (str(ObjectId()), offer_data[0][0], "Kylpyhuone"),
    #     (str(ObjectId()), offer_data[1][0], "Keittiö"),
    #     (str(ObjectId()), offer_data[2][0], "Keittiö"),
    #     (str(ObjectId()), offer_data[3][0], "Keittiö"),
    #     (str(ObjectId()), offer_data[3][0], "...")
    # ]

    # tables.insert("offers", offer_keys, offer_data[0])
    # tables.insert("offers", offer_keys, offer_data[1:], True)

    # tables.insert("offer_materials", )

    frame = wx.Frame(None, size=(1200, 500))
    panel = GridPanel(frame, tables, "database_add_materials")
    # panel.grid.set_parent_id(group_data[0][0])

    frame.Show()
    frame.Layout()

    app.MainLoop()