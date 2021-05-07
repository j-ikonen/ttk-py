import wx
import wx.grid as wxg

from setup import Setup, str2type, type2str


COL_MIN_W = 250
ROW_LABEL_SIZE = 120

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


class SetupGrid(wxg.Grid):
    def __init__(self, parent, setup):
        super().__init__(parent)

        self.data = None
        self.setup: Setup = setup

        fields: dict = self.setup['fields']
        self.CreateGrid(len(fields), 1)
        self.SetColLabelSize(1)

        for n, field in enumerate(fields.values()):
            (editor, renderer) = get_editor_renderer(field["type"])
            self.SetCellEditor(n, 0, editor)
            self.SetCellRenderer(n, 0, renderer)
            self.SetRowLabelValue(n, field["label"])

        self.Bind(wxg.EVT_GRID_CELL_CHANGED, self.on_cell_changed)
        self.Bind(wxg.EVT_GRID_EDITOR_HIDDEN, self.on_editor_hidden)

        self.SetColMinimalAcceptableWidth(COL_MIN_W)
        self.SetColSize(0, COL_MIN_W)
        self.SetRowLabelSize(wxg.GRID_AUTOSIZE)
        self.SetRowLabelAlignment(wx.ALIGN_RIGHT, wx.ALIGN_CENTER)

    def change_data(self, data: dict):
        """Change the data to given source."""
        print("SetupGrid.change_data")
        self.data = data
        if data is None:
            print("\tClear data from grid.")
            self.ClearGrid()
        else:
            print("\tRefresh with new data.")
            self.refresh_data()
        self.AutoSizeColumn(0)

    def refresh_data(self):
        self.BeginBatch()
        # print(f"\nSetupGrid.refresh_data - self.data: {self.data}\n")
        for n, k in enumerate(self.setup['fields'].keys()):
            self.SetCellValue(n, 0, type2str(self.data[k]))
        self.EndBatch()

    def on_cell_changed(self, evt):
        """Handle cell changed event."""
        row = evt.GetRow()
        key = list(self.setup['fields'].keys())[row]
        typestring = self.setup['fields'][key]["type"]
        value = str2type(typestring, self.GetCellValue(row, 0))
        self.data[key] = value
        print(f"SetupGrid.on_cell_changed\n\tNew value in self.data: {self.data[key]}" +
              f"\n\tat row, key: {row}, {key}")
        evt.Skip()

    def on_editor_hidden(self, evt):
        print("editor hidden")
        # self.AutoSizeColumn(0)
        evt.Skip()