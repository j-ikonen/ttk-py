import wx.grid as wxg
import wx

from dataobj_dialog import DataObjectDialog
from ttk_data import str2type, FIELD_KEY, FIELD_LABEL, FIELD_TYPE, FIELD_READONLY, type2str
from database import Database


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

EDIT_CHAR = ['K', 'E', 'P']
EDITED_YES = 0
EDITED_NO = 1
EDITED_MISS = 2
COLOUR_EDITED = {           # Is edited?
    'K': (255, 255, 180),   # Yes
    'E': (180, 255, 180),   # No
    'P': (255, 180, 180)    # No db entry to compare to
}
COLOUR_WHITE = (255, 255, 255)


class TtkGrid(wxg.Grid):
    def __init__(self, parent, name, setup):
        """### Grid window for a list of objects.
        
        ### Args:
        - parent: Parent wx.Window.
        - name (str): Key for this grids setup information.
        - setup (dict): Setup information. Must contain keys 'fields' and 'columns'."""
        super().__init__(parent)

        self.data = None
        self.setup = setup
        self.child_grid = None
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

    def set_child_grid(self, grid):
        self.child_grid = grid

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

            self.changed_rows(sz_change)
            self.refresh_data()

    def refresh_data(self):
        """Refresh the data."""
        self.BeginBatch()
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
        child = self.setup.get('child', None)

        for key, value in self.setup['fields'].items():
            if child is not None and key == child:
                new_row[key] = []
            else:
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

        # if self.data is None:
        #     self.data = []

        if ("prevent_new_row" not in self.setup and row >= len(self.data)):
            self.changed_rows(1)

        try:
            self.data[row][key] = value
        except IndexError:
            self.init_row()
            self.data[row][key] = value
            self.SetCellValue(row, col, type2str(value))
        
        self.SetGridCursor(row, col)
        evt.Skip()
        # print(f"TtkGrid.on_cell_changed - name: {self.name}\n\tNew value in self.data: {self.data[row][key]}")

    def on_cell_select(self, evt):
        """Handle select event."""
        row = evt.GetRow()
        child = self.setup.get('child', None)
        self.update_child_grid(row, child)
        evt.Skip()

    def update_child_grid(self, row, child_key):
        """Update the data in child grid."""
        if child_key is not None and self.data is not None:
            if row >= len(self.data):
                child_data = None
            else:
                if self.data[row][child_key] is None:
                    self.data[row][child_key] = []
                child_data = self.data[row][child_key]
            self.child_grid.change_data(child_data)

    def on_cell_rclick(self, evt):
        """Open menu on right click."""
        selected = self.GetSelectedRows()
        self.rclick_row = evt.GetRow()

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
            menu.Enable(self.id_copy, False)
            menu.Enable(self.id_del_sel, False)

        # Gray out paste if nothing is copied or cut.
        if not self.copied:
            menu.Enable(self.id_paste, False)

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
        try:
            obj = self.data[self.rclick_row]
        except IndexError:
            self.init_row()
            self.changed_rows(1)
            obj = self.data[self.rclick_row]
        except TypeError:
            print("Chosen row has can not be initialized. " +
                  "Try initializing a parent object first.")
            return

        with DataObjectDialog(self, obj, self.setup) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self.refresh_attr()

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
                    colour = COLOUR_EDITED[value]
                except KeyError:
                    colour = COLOUR_WHITE
                self.SetCellBackgroundColour(row, col, colour)
        self.refresh_data()
        # self.Refresh()

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
