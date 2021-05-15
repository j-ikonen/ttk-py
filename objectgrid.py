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
    def __init__(self, parent, tables, gridname):
        super().__init__(parent)

        self.tables: db.OfferTables = tables
        self.gridname = gridname

        self.table_key = None
        self.table_label = None
        self.pk_key = None
        self.pk_val = None

        self.row_keys = []
        self.row_labels = []
        self.row_types = []
        self.n_rows = 0

        self.set_columns()

        self.n_rows = len(self.row_keys)

        self.CreateGrid(self.n_rows, 1)
        self.SetColLabelSize(1)

        for n, label in enumerate(self.row_labels):
            (editor, renderer) = get_editor_renderer(self.row_types[n])
            self.SetCellEditor(n, 0, editor)
            self.SetCellRenderer(n, 0, renderer)
            self.SetRowLabelValue(n, label)

        self.Bind(wxg.EVT_GRID_CELL_CHANGED, self.on_cell_changed)
        self.Bind(wxg.EVT_GRID_CELL_CHANGING, self.on_cell_changing)
        self.Bind(wxg.EVT_GRID_EDITOR_HIDDEN, self.on_editor_hidden)

        self.SetRowLabelSize(wxg.GRID_AUTOSIZE)

        # self.SetRowLabelAlignment(wx.ALIGN_RIGHT, wx.ALIGN_CENTER)

    def set_pk(self, pk: Iterable=None):
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
            self.pk_val = pk
            self.refresh_data()

    def refresh_data(self):
        """Get the data from table to grid."""
        obj = self.tables.get(
            self.table_key,
            self.row_keys,
            self.pk_key,
            self.pk_val
        )
        self.BeginBatch()
        for n in range(self.n_rows):
            self.SetCellValue(n, 0, db.type2str(obj[n]))
        self.EndBatch()

    def on_cell_changed(self, evt):
        """Handle cell changed event."""
        row = evt.GetRow()
        typestring = self.row_types[row]
        value = db.str2type(typestring, self.GetCellValue(row, 0))
        self.tables.update_one(
            self.table_key,
            self.row_keys[row],
            self.pk_key[0],
            [value] + self.pk_val
        )
        print([value] + self.pk_val)
        evt.Skip()

    def on_cell_changing(self, evt):
        if self.pk_val is None:
            evt.Veto()
        else:
            evt.Skip()

    def on_editor_hidden(self, evt):
        evt.Skip()

    def set_columns(self):
        """Set the setup values of this grid based on gridname."""
        display_setup = self.tables.get_display_setup(self.gridname)
        self.table_key = display_setup["table"]
        self.table_label = display_setup["label"]
        self.pk_key = display_setup["pk"]
        self.row_keys = display_setup["columns"]

        column_setup = self.tables.get_column_setup(self.table_key, self.row_keys)
        self.row_labels = [val["label"] for val in column_setup.values()]
        self.row_types = [val["type"] for val in column_setup.values()]


