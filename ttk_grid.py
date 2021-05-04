import wx.grid as wxg
import wx

from ttk_data import str2type, FIELD_KEY, FIELD_LABEL, FIELD_TYPE, FIELD_READONLY, type2str
from database import Database

COL_MIN_W = 250

GRIDMENU_DELSEL = "Poista"
GRIDMENU_DELSEL_HELP = "Poista valitut rivit."
GRIDMENU_COPY = "Kopioi"
GRIDMENU_COPY_HELP = "Kopioi valitut solut."
GRIDMENU_PASTE = "Liitä"
GRIDMENU_PASTE_HELP = "Liitä kopioidut valittuihin soluihin."
GRIDMENU_ITDB = "Syötä tietokantaan"
GRIDMENU_ITDB_HELP = "Syötä tietokantaan"
GRIDMENU_FFDB = "Etsi tietokannasta"
GRIDMENU_FFDB_HELP = "Etsi tietokannasta"
GRIDMENU_EDIT_OBJECT = "Muokkaa"
GRIDMENU_EDIT_OBJECT_HELP = "Muokkaa koodeja."

GIRD_ITDB_INS_IDS = "\tInserted ids: {}"
GRID_ITDB_NO_SELECTION = "Ei valintaa, jota syöttää tietokantaan."

CLR_CELL_EDITED_NO_MATCH = (255, 210, 210)
CLR_CELL_EDITED_DIFF_MATCH = (210, 210, 255)
CLR_CELL_EDITED_MATCH = (210, 255, 210)
CLR_WHITE = (255, 255, 255)

EDIT_CHAR = ['K', 'E', 'P']
EDITED_YES = 0
EDITED_NO = 1
EDITED_MISS = 2
EDIT_COLOUR = {
    'K': (255, 255, 180),
    'E': (180, 255, 180),
    'P': (255, 180, 180)
}
COLOUR_WHITE = (255, 255, 255)


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


class TtkGrid(wxg.Grid):
    def __init__(self, parent, name, setup):
        super().__init__(parent)

        self.data = None
        self.setup = setup
        self.name = name
        self.copied = []
        self.rclick_row = None

        fields = self.setup['fields']
        columns = self.setup['columns']
        self.CreateGrid(1, len(columns))
        self.SetRowLabelSize(30)

        for n, key in enumerate(columns):
            self.set_col_format(n, fields[key][FIELD_TYPE])
            self.SetColLabelValue(n, fields[key][FIELD_LABEL])
            self.AutoSizeColLabelSize(n)

        self.Bind(wxg.EVT_GRID_CELL_CHANGED, self.on_cell_changed)
        self.Bind(wxg.EVT_GRID_EDITOR_SHOWN, self.on_editor_shown)
        self.Bind(wxg.EVT_GRID_CELL_RIGHT_CLICK, self.on_cell_rclick)
        self.Bind(wxg.EVT_GRID_SELECT_CELL, self.on_cell_select)

    def change_data(self, data):
        """Change the data to given source."""
        print(f"TtkGrid.change_data - name: {self.name}")
        try:
            current_len = len(self.data)
        except TypeError:
            current_len = 0
        try:
            new_len = len(data)
        except TypeError:
            new_len = 0

        if data is None:
            print("\tclear grid")
            self.DeleteRows(0, current_len)
            self.data = data
        else:
            print("\trefresh to new size")
            sz_change = new_len - current_len
            self.data = data

            self.BeginBatch()
            self.changed_rows(sz_change)
            for row, item in enumerate(self.data):
                for col, key in enumerate(self.setup['columns']):
                    self.SetCellValue(row, col, type2str(item[key]))
            self.EndBatch()

    def changed_rows(self, n_change):
        """Update the grid with a size change.
        
        Positive n_change for added rows. Negative for deleted.
        """
        print(f"TtkGrid.changed_rows - name: {self.name} rows changed: {n_change}")
        if n_change > 0:
            self.AppendRows(n_change)
        elif n_change < 0:
            self.DeleteRows(self.GetNumberRows() - 1 + n_change, 0 - n_change)

    def init_row(self):
        """Initialize a new row."""
        new_row = {}
        new_row_idx = len(self.data)

        for key, value in self.setup['fields'].items():
            new_row[key] = value[FIELD_KEY]
        self.data.append(new_row)

        self.BeginBatch()
        for n, k in enumerate(self.setup['columns']):
            self.SetCellValue(new_row_idx, n, type2str(self.data[new_row_idx][k]))
        self.EndBatch()

    def on_cell_changed(self, evt):
        """Save changed value to data and append a row if edit is at last row."""
        row = evt.GetRow()
        col = evt.GetCol()
        key = self.setup['columns'][col]
        typestring = self.setup['fields'][key][FIELD_TYPE]
        value = str2type(typestring, self.GetCellValue(row, col))

        if ("prevent_new_row" not in self.setup and row >= len(self.data)):
            self.changed_rows(1)
        try:
            self.data[row][key] = value
        except IndexError:
            self.init_row()
            self.data[row][key] = value
            self.SetCellValue(row, col, type2str(value))

        evt.Skip()
        # print(f"TtkGrid.on_cell_changed - name: {self.name}\n\tNew value in self.data: {self.data[row][key]}")

    def on_cell_select(self, evt):
        """Handle select event."""
        evt.Skip()

    def on_cell_rclick(self, evt):
        """Open menu on right click."""
        selected = self.GetSelectedRows()
        self.rclick_row = self.evt.GetRow()

        if not hasattr(self, 'id_copy'):
            self.id_copy = wx.NewIdRef()
            self.id_paste = wx.NewIdRef()
            self.id_edit_object = wx.NewIdRef()
            self.id_del_sel = wx.NewIdRef()
            self.id_itdb = wx.NewIdRef()        # Insert To DataBase
            self.id_ffdb = wx.NewIdRef()        # Find from DataBase

            self.Bind(wx.EVT_MENU, self.on_copy, id=self.id_copy)
            self.Bind(wx.EVT_MENU, self.on_paste, id=self.id_paste)
            self.Bind(wx.EVT_MENU, self.on_edit_object, id=self.id_edit_object)
            self.Bind(wx.EVT_MENU, self.on_delete_selected, id=self.id_del_sel)
            self.Bind(wx.EVT_MENU, self.on_insert_to_db, id=self.id_itdb)
            self.Bind(wx.EVT_MENU, self.on_find_from_db, id=self.id_ffdb)

        menu = wx.Menu()
        menu.Append(self.id_copy, GRIDMENU_COPY, GRIDMENU_COPY_HELP)
        menu.Append(self.id_paste, GRIDMENU_PASTE, GRIDMENU_PASTE_HELP)
        menu.AppendSeparator()
        menu.Append(self.id_edit_object, GRIDMENU_EDIT_OBJECT, GRIDMENU_EDIT_OBJECT_HELP)
        menu.Append(self.id_del_sel, GRIDMENU_DELSEL, GRIDMENU_DELSEL_HELP)

        # Gray out menuitems that require row selections.
        if not selected:
            menu.Enable(self.copy_id, False)
            menu.Enable(self.del_sel_id, False)

        # Gray out paste if nothing is copied or cut.
        if not self.copied:
            menu.Enable(self.paste_id, False)

        # Append database menuitems if grid has database items.
        if 'db' in self.setup:
            menu.AppendSeparator()
            menu.Append(self.id_itdb, GRIDMENU_ITDB, GRIDMENU_ITDB_HELP)
            menu.Append(self.id_ffdb, GRIDMENU_FFDB, GRIDMENU_FFDB_HELP)

            if not selected:
                menu.Enable(self.id_itdb, False)

        self.PopupMenu(menu)
        menu.Destroy()
        self.rclick_row = None

    def on_copy(self, evt):
        """Copy the selected cells."""
        print("\TtkGrid.on_copy")
        selection = self.GetSelectedRows()
        selection.sort(reverse=True)
        self.copied = []

        for n in selection:
            obj = self.data[n]
            self.copied.append(obj)

    def on_paste(self, evt):
        """Paste the copied selection to new selection."""
        print("\nCustomGrid.on_paste")
        try:
            oldlen = len(self.data)
        except TypeError:
            oldlen = 0

        for obj in self.copied:
            self.data.append(obj)

        try:
            newlen = len(self.data)
        except TypeError:
            newlen = 0
        self.changed_rows(newlen - oldlen)

    def on_editor_shown(self, evt):
        """Veto event if cell is readonly."""
        col = evt.GetCol()
        key = self.setup['columns'][col]
        if self.setup['fields'][key][FIELD_READONLY]:
            print(f"TtkGrid.on_editor_shown - Key '{key}' is read only.")
            evt.Veto()
        evt.Skip()

    def on_edit_object(self, evt):
        """Edit all objects fields."""
        pass

    def on_delete_selected(self, evt):
        """Delete the selected rows from grid and data."""
        print("\nTtkGrid.on_delete_selected")
        selected = self.GetSelectedRows()
        selected.sort(reverse=True)
        print(f"\tDelete rows: {selected}")
        for index in selected:
            self.DeleteRows(index)
            try:
                del self.data[index]
            except IndexError:
                pass

    def on_insert_to_db(self, evt):
        """Insert selected rows to database."""
        print("\nTtkGrid.on_insert_to_db")
        selected = self.GetSelectedRows()
        to_db = []
        for row in selected:
            to_db.append(self.data[row])
        
        if len(to_db) > 0:
            ids = Database(self.name).insert(to_db)
            print(GIRD_ITDB_INS_IDS.format(ids))
        else:
            print(GRID_ITDB_NO_SELECTION)

    def on_find_from_db(self, evt):
        """Open database dialog with current grid selected."""
        print("TtkGrid.on_find_from_db TO BE IMPLEMENTED")

    def refresh_attr(self):
        """Refresh the cell attributes where required."""
        print("TtkGrid.refresh_attr")
        try:
            col = self.setup['columns'].index('edited')
        except ValueError:
            pass
        else:
            for row, item in enumerate(self.data):
                # value = self.GetCellValue(row, col)
                value = item['edited']
                try:
                    colour = EDIT_COLOUR[value]
                except KeyError:
                    colour = COLOUR_WHITE
                self.SetCellBackgroundColour(row, col, colour)
        self.change_data(self.data)
        self.Refresh()

    def set_col_format(self, col, typestring):
        """Set column format."""
        split = typestring.split(':')
        if len(split) > 1:
            args = split[1].split(',')
        else:
            args = []

        if split[0] == "long":
            self.SetColFormatNumber(col)
        elif split[0] == "double":
            if len(args) == 2:
                self.SetColFormatFloat(col, int(args[0]), int(args[1]))
            else:
                self.SetColFormatFloat(col)
        elif split[0] == "bool":
            self.SetColFormatBool(col)
        elif split[0] == "date":
            self.SetColFormatDate(col)


class SetupGrid(wxg.Grid):
    def __init__(self, parent, setup):
        super().__init__(parent)

        self.data = None
        self.setup = setup

        fields = self.setup['fields']
        self.CreateGrid(len(fields), 1)
        self.SetColLabelSize(1)
        # self.SetColSize(0, 200)

        for n, field in enumerate(fields):
            (editor, renderer) = get_editor_renderer(field[FIELD_TYPE])
            self.SetCellEditor(n, 0, editor)
            self.SetCellRenderer(n, 0, renderer)
            self.SetRowLabelValue(n, field[FIELD_LABEL])
        self.Bind(wxg.EVT_GRID_CELL_CHANGED, self.on_cell_changed)
        self.Bind(wxg.EVT_GRID_EDITOR_HIDDEN, self.on_editor_hidden)

        self.SetColMinimalAcceptableWidth(COL_MIN_W)
        self.SetColSize(0, COL_MIN_W)

    def change_data(self, data):
        """Change the data to given source."""
        print("SetupGrid.change_data")
        self.data = data
        if data is None:
            print("\tClear data from grid.")
            self.ClearGrid()
        else:
            print("\tRefresh with new data.")
            for n, value in enumerate(data.values()):
                self.SetCellValue(n, 0, type2str(value))
        self.AutoSizeColumn(0)

    def on_cell_changed(self, evt):
        """Handle cell changed event."""
        row = evt.GetRow()
        key = self.setup['fields'][row][FIELD_KEY]
        typestring = self.setup['fields'][row][FIELD_TYPE]
        value = str2type(typestring, self.GetCellValue(row, 0))
        self.data[key] = value
        print(f"SetupGrid.on_cell_changed\n\tNew value in self.data: {self.data[key]}" +
              f"\n\tat row, key: {row}, {key}")
        evt.Skip()

    def on_editor_hidden(self, evt):
        print("editor hidden")
        # self.AutoSizeColumn(0)
        evt.Skip()