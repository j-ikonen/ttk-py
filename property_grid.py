from decimal import Decimal

import wx
import wx.grid as wxg

import db
from grid_decimal_editor import GridDecimalEditor
from sizes import Sizes


class PropertyGridBase(wxg.GridTableBase):
    def __init__(self, db: db.SQLTableBase, fk: int=None):
        super().__init__()

        self.db = db
        self.fk = None
        self.data = None

        self.set_fk(fk)

    def GetNumberRows(self):
        """Return the number of rows on display.
        
        Uses database columns as rows.
        """
        return self.db.get_num_columns()

    def GetNumberCols(self):
        """Return 1."""
        return 1

    def IsEmptyCell(self, row, col):
        """Return true if given cell is empty.
        
        Used to determine if previous rows content can overflow to this cell."""
        if self.GetValue(row, col) == "":
            return True
        return False

    def GetValue(self, row, col):
        """Return value in cell."""
        try:
            return self.data[row]
        except IndexError as e:
            return None

    def GetColLabelValue(self, col):
        """Return the column label."""
        return ""
    
    def GetRowLabelValue(self, row):
        """Return the database column label as row label."""
        return self.db.get_column_label(row)

    def GetTypeName(self, row, col):
        """Return the type name."""
        return self.db.get_column_type(row)

    def CanGetValueAs(self, row, col, type_name):
        """Test if value can be received as type."""
        col_type = self.GetTypeName(row, col).split(":")[0]
        if type_name == col_type:
            return True
        else:
            return False

    def CanSetValueAs(self, row, col, type_name):
        """Test if value can be set as type."""
        return self.CanGetValueAs(row, col, type_name)

    def SetValue(self, row, col, value):
        """Update the database with a new value."""
        # Interpret an empty value as None.
        if value == "":
            value = None

        rowid = self.get_rowid(row)

        # Set value to a valid row with Primary Key.
        if rowid is not None:
            if isinstance(value, float):
                value = Decimal(value)
            success = self.db.update(rowid, row, value)

            if success:
                self.update_data()

    def GetValueAsDouble(self, row, col):
        """Return value as double."""
        try:
            return super().GetValueAsDouble(row, col)
        except TypeError:
            return 0.0

    def GetValueAsLong(self, row, col):
        """Return value as long."""
        try:
            return super().GetValueAsLong(row, col)
        except TypeError:
            return 0

    def GetValueAsBool(self, row, col):
        """Return value as boolean."""
        try:
            return super().GetValueAsBool(row, col)
        except TypeError:
            return False

    def set_fk(self, fk: int, pk: int=None):
        """Set the foreign key value and update the grid."""
        self.fk = fk
        self.pk = pk
        self.update_data()

    def get_fk(self) -> int:
        """Return the foreign key value."""
        return self.fk

    def new_row(self) -> int:
        """Initialize a new row to database and return it's pk."""
        self.pk = self.db.insert_empty(self.fk)
        self.update_data()
        return self.pk
    
    def set_pk(self, pk: int):
        """Set the primary key and update the grid."""
        self.pk = pk
        self.update_data()

    def get_pk(self) -> int:
        """Return the primary key value."""
        return self.pk

    def update_data(self):
        """Update the displayed data from database."""
        pk_filter = {0: ["=", self.pk]}
        try:
            self.data = list(self.db.select(self.fk, pk_filter)[0])
            # for n, value in enumerate(self.data):
            #     if isinstance(value, Decimal):
            #         self.data[n] = value.quantize(Decimal('.01'))
        except IndexError:
            self.data = [None] * self.GetNumberRows()

    def get_rowid(self, row):
        """Return the rowid of given row."""
        try:
            return self.data[0]
        except IndexError:
            return None

    def is_init(self):
        """Return True if this grid table is connected to a source."""
        return self.fk is not None


class PropertyGrid(wxg.Grid):
    def __init__(self, parent, db: db.SQLTableBase, fk: int=None):
        super().__init__(parent, style=wx.WANTS_CHARS)
        self.db = db
        self.copied_rows = []
        self.read_only = self.db.get_column_read_only()
        
        table = PropertyGridBase(db, fk)
        self.SetTable(table, True)
        
        font = wx.Font()
        dc = wx.ScreenDC()
        dc.SetFont(font)
        widest = 0
        for row in range(table.GetNumberRows()):
            w, _ = dc.GetTextExtent(self.GetRowLabelValue(row))
            if w > widest:
                widest = w

        self.SetRowLabelSize(widest)
        self.SetColLabelSize(0)
        self.SetColSize(0, Sizes.search)

        self.RegisterDataType("decimal", None, GridDecimalEditor())

        # Set row attributes.
        for row, ro in enumerate(self.db.get_column_read_only()):
            if ro == 1:
                attr = wxg.GridCellAttr()
                attr.SetReadOnly(True)
                self.SetRowAttr(row, attr)

        self.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        self.Bind(wxg.EVT_GRID_CELL_RIGHT_CLICK, self.on_context_menu)
        self.Bind(wxg.EVT_GRID_LABEL_LEFT_CLICK, self.on_label_lclick)  # Set Focus
        self.Bind(wxg.EVT_GRID_CELL_CHANGED, self.on_cell_changed) # Refresh
        # Event that can be used to veto edit before showing editor.
        self.Bind(wxg.EVT_GRID_EDITOR_SHOWN, self.on_show_editor)

    def on_show_editor(self, evt):
        """Veto show editor event when foreign key is not defined."""
        if self.get_fk() is None:
            evt.Veto()
        else:
            evt.Skip()

    def undo_barrier(self):
        """Set an undo barrier."""
        self.db.undo_barrier(self.get_fk())

    def can_undo(self):
        """Return True if action can be undone."""
        return self.db.can_undo(self.get_fk())

    def on_undo(self, evt):
        """Handle the menu event."""
        self.undo()

    def undo(self):
        """Undo an action until previous undo barrier."""
        if not self.can_undo():
            return

        self.db.undo(self.get_fk())
        self.update_content()
        self.ForceRefresh()

    def can_redo(self):
        """Return True if action can be redone."""
        return self.db.can_redo(self.get_fk())

    def on_redo(self, evt):
        """Handle the menu event."""
        self.redo()
    
    def redo(self):
        """Redo an undone action."""
        if not self.can_redo():
            return
        
        self.db.redo(self.get_fk())
        self.update_content()
        self.ForceRefresh()

    def on_cut(self, evt):
        """Handle the menu event."""
        self.cut()

    def cut(self):
        """Copy and delete the selected rows."""
        self.copy()
        self.delete()
        self.ClearSelection()

    def on_copy(self, evt):
        """Handle the menu event."""
        self.copy()

    def copy(self):
        """Save the current values in selected rows to 'copied_rows'."""
        selected: list = self.GetSelectedRows()
        selected.sort()
        self.copied_rows = {}
        for row in selected:
            self.copied_rows[row] = self.GetTable().GetValue(row, 0)

    def can_paste(self):
        """Return True if copied values can be pasted."""
        return len(self.copied_rows) > 0

    def on_paste(self, evt):
        """Handle the menu event."""
        self.paste()

    def paste(self):
        """Insert copied or cut rows to the grid."""
        for n, (row, col) in enumerate(self.GetSelectedCells()):
            self.GetTable().SetValue(row, col, self.copied_rows[n % len(self.copied_rows)])
        self.copied_rows = []
        self.undo_barrier()
        self.update_content()

    def on_delete(self, evt):
        """Handle the menu event."""
        self.delete()

    def delete(self):
        """Delete selected rows."""
        for (row, col) in self.GetSelectedCells():
            self.GetTable().SetValue(row, col, None)

        self.undo_barrier()
        self.update_content()
        self.ClearSelection()

    def on_context_menu(self, evt):
        """Open the cell context menu."""
        self.SetFocus()     # Set focus on this grid.
        menu = wx.Menu()
        row = evt.GetRow()
        col = evt.GetCol()
        no_row_selected = len(self.GetSelectedRows()) == 0

        # Clear selection and set grid cursor to clicked cell if
        # right click was not in a selected cell.
        if not self.IsInSelection(row, col):
            self.ClearSelection()
            self.SetGridCursor(row, col)

        # Init event bindings on first open of menu.
        if not hasattr(self, "id_save"):
            self.id_save = wx.NewIdRef()
            self.Bind(wx.EVT_MENU, self.on_undo, id=wx.ID_UNDO)
            self.Bind(wx.EVT_MENU, self.on_cut, id=wx.ID_CUT)
            self.Bind(wx.EVT_MENU, self.on_copy, id=wx.ID_COPY)
            self.Bind(wx.EVT_MENU, self.on_paste, id=wx.ID_PASTE)
            self.Bind(wx.EVT_MENU, self.on_delete, id=wx.ID_DELETE)
            self.Bind(wx.EVT_MENU, self.on_undo, id=wx.ID_UNDO)
            self.Bind(wx.EVT_MENU, self.on_redo, id=wx.ID_REDO)

        mi_undo: wx.MenuItem = menu.Append(wx.ID_UNDO)
        mi_redo: wx.MenuItem = menu.Append(wx.ID_REDO)
        menu.Append(wx.ID_CUT)
        menu.Append(wx.ID_COPY)
        mi_paste = menu.Append(wx.ID_PASTE)
        menu.AppendSeparator()
        mi_delete = menu.Append(wx.ID_DELETE, "Poista\tDelete")

        # Disable menu items that cannot be done.
        if not self.can_undo():
            mi_undo.Enable(False)

        if not self.can_redo():
            mi_redo.Enable(False)

        if not self.can_paste():
            mi_paste.Enable(False)

        if no_row_selected:
            mi_delete.Enable(False)

        self.PopupMenu(menu)
        menu.Destroy()
        evt.Skip()

    def on_key_down(self, evt):
        """Handle key events."""
        keycode = evt.GetUnicodeKey()
        if keycode == wx.WXK_NONE:
            keycode = evt.GetKeyCode()

        mod = evt.GetModifiers()
        if mod == wx.MOD_CONTROL:
            if mod == wx.MOD_SHIFT:
                pass

            # CTRL+A
            if keycode == 65:
                self.SelectAll()

            # CTRL+C
            elif keycode == 67:
                self.copy()

            # CTRL+V
            elif keycode == 86:
                self.paste()

            # CTRL+X
            elif keycode == 88:
                self.cut()

            # CTRL+Z
            elif keycode == 90:
                self.undo()

        elif mod == wx.MOD_SHIFT:
            pass

        elif mod == wx.MOD_ALT:
            pass

        elif mod == wx.MOD_NONE:
            # Delete
            if keycode == wx.WXK_DELETE:
                self.delete()
        
        elif mod == wx.MOD_CONTROL | wx.MOD_SHIFT:
            
            # CTRL + SHIFT + Z
            if keycode == 90:
                self.redo()

        evt.Skip()

    def on_label_lclick(self, evt):
        """Set focus on this grid."""
        self.SetFocus()
        evt.Skip()

    def set_fk(self, value: int):
        """Set the foreign key for the grid."""
        self.GetTable().set_fk(value)
        self.ForceRefresh()
    
    def set_keys(self, fk: int, pk: int):
        """Set the foreign and primary key."""
        self.GetTable().set_fk(fk, pk)
        self.ForceRefresh()

    def get_fk(self) -> int:
        """Return the value of foreign key."""
        return self.GetTable().get_fk()

    def get_rowid(self, row: int) -> int:
        """Return the primary key from the given row."""
        return self.GetTable().get_rowid(row)

    # def on_cell_changing(self, evt):
    #     """Veto cell change event if change is not allowed."""
    #     # A required foreign key is not set.
    #     if not self.GetTable().is_init():
    #         print(f"\nError: Can not change value in grid for {type(self.db)}.")
    #         print("\tForeign key or filter needs to be set.")
    #         evt.Veto()

    #     evt.Skip()

    def on_cell_changed(self, evt):
        """Refresh the grid on changed cell."""
        self.undo_barrier()
        self.ForceRefresh()
        evt.Skip()

    def update_content(self):
        """Update the contents of this grid."""
        self.GetTable().update_data()


if __name__ == '__main__':
    con = db.connect(":memory:", False, True, True)
    table = db.GroupMaterialsTable(con)
    table.create()

    app = wx.App()

    frame = wx.Frame(None, size=(400, 600), title="PropertyGridTest")
    grid = PropertyGrid(frame, table, 1)
    grid.GetTable().new_row()

    frame.Show()
    app.MainLoop()
