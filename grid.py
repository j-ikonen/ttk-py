import wx
import wx.grid as wxg
from bson.objectid import ObjectId


from table import OfferTables, str2type, type2str


class GridPanel(wx.Panel):
    BORDER = 5

    def __init__(self, parent, tables, key):
        super().__init__(parent)

        # self.SetBackgroundColour((255, 150, 100))
        self.SetBackgroundColour((255, 200, 120))

        label = wx.StaticText(self, label=key)
        btn_del = wx.Button(self, label="-")
        self.grid = TheGrid(self, tables, key)

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


class TheGrid(wxg.Grid):

    def __init__(self, parent, tables, key):
        super().__init__(parent)

        self.tables: OfferTables = tables

        self.key = key
        self.keys = OfferTables.keys[key]
        self.labels = OfferTables.labels[key]
        self.label_sizes = OfferTables.label_sizes[key]
        self.read_only = OfferTables.read_only[key]
        self.types = OfferTables.types[key]
        self.unique = OfferTables.unique[key]

        self.n_columns = len(self.labels)
        self.ids = []
        self.parent_id = None

        self.CreateGrid(1, self.n_columns)
        self.SetRowLabelSize(35)

        for n in range(self.n_columns):
            self.SetColLabelValue(n, self.labels[n])
            self.SetColSize(n, self.label_sizes[n])
            self.set_col_format(n)

        self.Bind(wxg.EVT_GRID_EDITOR_SHOWN, self.on_show_editor)
        self.Bind(wxg.EVT_GRID_CELL_CHANGING, self.on_cell_changing)

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
        if self.parent_id is None:
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
            oid = str(ObjectId())
            self.ids.append(oid)
            self.AppendRows()

        values = (self.ids[row], self.parent_id, str2type(self.types[col], value))
        if not self.tables.upsert(self.key, self.keys[col], values):
            evt.Veto()

        self.update_data()
        evt.Skip()

    def on_show_editor(self, evt):
        """Veto showing of editor on read only columns."""
        if evt.GetCol() in self.read_only:
            print("TheGrid.on_show_editor - " +
                  f"Column '{self.labels[evt.GetCol()]}' is read only.")
            evt.Veto()

    def set_col_format(self, col):
        """Set the column format by typestring."""
        typestring = self.types[col]
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

    def set_parent_id(self, id: str):
        if self.parent_id != id:
            self.parent_id = id
            self.update_data()

    def update_data(self):
        self.ids.clear()
        data = self.tables.get_grid(self.key, self.parent_id)
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
    panel = GridPanel(frame, tables, "offer_materials")
    panel.grid.set_parent_id(group_data[0][0])

    frame.Show()
    frame.Layout()

    app.MainLoop()