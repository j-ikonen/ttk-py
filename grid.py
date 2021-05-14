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
        dsp = tables.get_display_setup("database_add_products")
        setup = tables.get_column_setup(dsp.get("table"), dsp.get("columns"))
        self.grid = BaseGrid(self, setup)

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

    def on_show_editor(self, evt):
        """Veto showing of editor on read only columns."""
        if evt.GetCol() in self.read_only:
            print("BaseGrid.on_show_editor - " +
                  f"Column '{self.labels[evt.GetCol()]}' is read only.")
            evt.Veto()

    def on_cell_changing(self, evt):
        """."""
        value = evt.GetString()
        col = evt.GetCol()
        row = evt.GetRow()

        # Veto if the value exists in unique column.
        if col in self.unique and self.value_exists(col, value):
            evt.Veto()

        # Init uninitiated row.
        if not self.static_rows and row >= self.GetNumberRows() - 1:
            self.edit_in_last_row()

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

    def edit_in_last_row(self):
        self.AppendRows(1)

    def get_content(self):
        content = []
        for row in range(self.GetNumberRows()-1):
            row_data = []
            for col in range(self.GetNumberCols()):
                value = str2type(self.get_type(col), self.GetCellValue(row, col))
                row_data.append(value)
            content.append(row_data)
        return content

    def clear_content(self):
        self.DeleteRows(0, self.GetNumberRows())
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


class TheGrid(wxg.Grid):

    def __init__(self, parent, tables, key):
        super().__init__(parent)

        self.tables: OfferTables = tables

        self.key = key
        self.label = ""
        self.table_name = ""
        self.keys = []
        self.labels = []
        self.widths = []

        self.read_only = []
        self.types = []
        self.unique = []
        self.pk = []
        self.ids = []
        self.parent_key_values = None
        self.parent_keys = None

        self.column_setup()

        self.n_columns = len(self.labels)

        self.CreateGrid(1, self.n_columns)
        self.SetRowLabelSize(35)

        for n in range(self.n_columns):
            self.SetColLabelValue(n, self.labels[n])
            self.SetColSize(n, self.widths[n])
            self.set_col_format(n)

        self.Bind(wxg.EVT_GRID_EDITOR_SHOWN, self.on_show_editor)
        self.Bind(wxg.EVT_GRID_CELL_CHANGING, self.on_cell_changing)

    def column_setup(self):
        display = self.tables.get_display_setup(self.key)
        self.keys = display["columns"]
        self.table_name = display["table"]
        self.pk = display["pk"]
        self.label = display["label"]
        if "parent_keys" in display:
            self.parent_keys = display["parent_keys"]
            self.parent_key_values = []

        setup = self.tables.get_column_setup(self.table_name, self.keys)
        for col, value in enumerate(setup.values()):
            self.labels.append(value["label"])
            self.widths.append(value["width"])
            self.types.append(value["type"])
            if value["ro"]:
                self.read_only.append(col)
            if value["unique"]:
                self.unique.append(col)

    def on_cell_changing(self, evt):
        """Save changed value to table.

        Veto changing of the cell if:
            Column is unique.
            Parent ID is None.
            Insert or Update to database failed and returned False.
        """
        value = evt.GetString()
        col = evt.GetCol()
        row = evt.GetRow()
        print(value)

        # Veto if no parent id is not defined.
        if self.parent_keys is None:
            print("TheGrid.on_cell_changing - " +
                f"No parent ID defined.")
            evt.Veto()

        # Veto if the value exists in unique column.
        if col in self.unique:
            for test_row in range(self.GetNumberRows()):
                if value == self.GetCellValue(test_row, col):
                    print("TheGrid.on_cell_changing - " +
                        f"Column '{self.labels[col]}' is unique. " +
                        f"Value '{value}' already exists.")
                    evt.Veto()

        # Init uninitiated row.
        if row >= len(self.ids):
            pk_values = []
            for k in self.pk:
                if k in self.keys:
                    pk_values.append(value) # Unique test done already
                elif k in self.parent_keys:
                    pk_values.append(self.parent_keys[self.parent_key_values.index(k)])
                else:
                    oid = str(ObjectId())
                    pk_values.append(oid)

            self.ids.append(pk_values)
            self.AppendRows()
            if not self.tables.insert(self.table_name, self.pk, pk_values):
                evt.Veto()

        if not self.tables.update_one(
            self.table_name,
            self.keys[col],
            self.pk,
            [str2type(self.types[col], value)] + self.ids[col]
        ):
            evt.Veto()

        self.update_data()
        evt.Skip()

    def on_show_editor(self, evt):
        """Veto showing of editor on read only columns."""
        if evt.GetCol() in self.read_only:
            print("TheGrid.on_show_editor - " +
                  f"Column '{self.labels[evt.GetCol()]}' is read only.")
            evt.Veto()

    # def set_new_rows(self, key, data):
    #     # data = self.tables.get_by_ids(key, ids)
    #     self.tables.insert()
    #     row = self.GetNumberRows()
    #     self.BeginBatch()
    #     self.AppendRows(len(data))
    #     for item in data:
    #         for col, value in enumerate(item):
    #             self.SetCellValue(row, col, type2str(value))
    #         row += 1
    #     self.EndBatch()

    def set_parent_id(self, parent):
        if self.parent_key_values != parent:
            self.parent_key_values = parent
            self.update_data()

    def update_data(self):
        self.ids.clear()
        data = self.tables.get(
            self.table_name,
            self.keys,

        )
        self.BeginBatch()
        self.DeleteRows(0, self.GetNumberRows())
        self.AppendRows(len(data) + 1)
        for row, row_data in enumerate(data):
            self.ids.append(row_data[0])
            for col, value in enumerate(row_data[1:]):
                if value is None:
                    value = ""
                self.SetCellValue(row, col, type2str(value))
        self.EndBatch()

    def delete_selected(self):
        selected_rows = self.GetSelectedRows()
        selected_rows.sort(reverse=True)
        for row in selected_rows:
            try:
                row_id = self.ids.pop(row)
            except IndexError:
                pass
            self.tables.delete(self.key, row_id)
            self.DeleteRows(row)


if __name__ == '__main__':
    app = wx.App(useBestVisual=True)
    tables = OfferTables()

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

    tables.insert("offers", offer_keys, offer_data[0])
    tables.insert("offers", offer_keys, offer_data[1:], True)

    # tables.insert("offer_materials", )

    frame = wx.Frame(None, size=(1200, 500))
    panel = GridPanel(frame, tables, "database_add_materials")
    # panel.grid.set_parent_id(group_data[0][0])

    frame.Show()
    frame.Layout()

    app.MainLoop()