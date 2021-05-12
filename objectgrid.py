from typing import Iterable

import wx.grid as wxg

import table as db


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

