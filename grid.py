"""Classes for handling grids."""

from old.newgrid import SHOW_COL_HELP
import wx
import wx.grid as wxg

import db


class GridBase(wxg.GridTableBase):
    def __init__(self, db: db.SQLTableBase, fk: int=None):
        """Custom GridTableBase for grids using database as data source.

        Setting self.data as None will show an empty noneditable grid.
        Either filter or foreign key must not be None.
        To find everything in table with no foreign key set filter as 
        an empty dictionary.

        Parameters
        ----------
        db : db.SQLTableBase
            The class for handling database operations.
        fk : int, optional
            Foreign key to the data this grid represents, by default None
        """
        super().__init__()

        self.db = db
        self.fk = fk
        self.filter = None
        self.data = None

    def GetNumberRows(self):
        """Return the number of rows on display.

        Display one extra row for inserting a new row to the grid.
        Grid with no defined source will have 0 rows.
        """
        try:
            return len(self.data) + 1
        except TypeError:
            return 0

    def GetNumberCols(self):
        """Return the number of columns."""
        return self.db.get_num_columns()

    def IsEmptyCell(self, row, col):
        """Return true if given cell is empty.
        
        Used to determine if previous rows content can overflow to this cell."""
        if self.GetValue(row, col) == "":
            return True
        return False

    def GetValue(self, row, col):
        """Return value in cell."""
        try:
            return self.data[row][col]
        except IndexError as e:
            return None

    def GetColLabelValue(self, col):
        """Return the column label."""
        return self.db.get_column_label(col)

    def GetTypeName(self, row, col):
        """Return the type name."""
        return self.db.get_column_type(col)

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

        # Cell in unitialized row.
        is_last_row = row >= (self.GetNumberRows() - 1)
        if is_last_row:
            rowid = self.db.insert_empty(self.fk)

            # Debug to make sure database receives correct type.
            print("Updating value: '{}' of type: {} at col: {}".format(
                value, type(value), col
            ))

        # Cell in initialized row.
        else:
            rowid = self.get_rowid(row)

        # Set value to a valid row with Primary Key.
        if rowid is not None:
            success = self.db.update(rowid, col, value)

            if success:
                self.update_data()
                return

            elif is_last_row:
                self.db.delete_row(self.table, rowid)
            print("\nGridBase.SetValue update value failed.")
                # print(f"\ttable: {self.table}")
                # print(f"\t(row, col): ({row}, {col})")
                # print(f"\tpk_value: {pk_value}")
                # print(f"\tvalue: {value}")

    def AppendRows(self, numRows):
        """Append rows to the grid."""
        msg = wxg.GridTableMessage(self, wxg.GRIDTABLE_NOTIFY_ROWS_APPENDED, numRows)
        self.GetView().ProcessTableMessage(msg)
        # self.GetView().PostSizeEventToParent()

    def DeleteRows(self, pos, numRows):
        """Delete rows from the grid at pos."""
        msg = wxg.GridTableMessage(self, wxg.GRIDTABLE_NOTIFY_ROWS_DELETED, pos, numRows)
        self.GetView().ProcessTableMessage(msg)
        # self.GetView().PostSizeEventToParent()

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
    
    def CanMeasureColUsingSameAttr(self, col):
        """Use same attributes for all rows of a column."""
        return True

    def set_fk(self, value: int):
        """Set the foreign key value and update the grid."""
        self.fk = value
        self.update_data()

    def get_fk(self) -> int:
        """Return the foreign key value."""
        return self.fk

    def set_filter(self, flt: dict):
        """Set the conditions for search and update the grid."""
        self.filter = flt
        self.update_data()

    def update_data(self):
        """Update the displayed data from database."""
        # if not self.update_locked():
        oldn = len(self.data)
        self.data = self.db.select(self.fk, self.filter)
        newn = len(self.data)
        self.update_rows(oldn, newn)

    def update_rows(self, old_row_count, new_row_count):
        """Update the number of rows in grid."""
        diff = new_row_count - old_row_count

        # Positive difference adds rows.
        if diff > 0:
            self.AppendRows(diff)
        elif diff < 0:
            self.DeleteRows(0, abs(diff))

        # Alternate by deleting all rows and reinserting new amount.
        # self.DeleteRows(0, self.GetNumberRows()-1)
        # self.AppendRows(new_row_count)

    def get_rowid(self, row):
        """Return the rowid of given row."""
        return self.data[row][0]

    def delete_row_data(self, row: int):
        """Delete the data at given row."""
        self.db.delete(self.get_rowid(row))


class DbGrid(wxg.Grid):
    def __init__(self, parent, db: db.SQLTableBase, fk: int=None):
        super().__init__(
            parent,
            style=wx.WANTS_CHARS|
                  wx.HD_ALLOW_REORDER
        )
        # List of different objects member functions that are used to
        # update their foreign keys with the primary key of this grid.
        self.child_set_fks = []
        self.db = db
        self.copied_rows = []

        table = GridBase(db, fk)
        self.SetTable(table, True, self.GridSelectRows)
        self.SetRowLabelSize(35)
        self.EnableDragColMove(True)

        self.set_widths()
        self.set_order()

        # Set column attributes.
        for col in self.db.get_column_read_only():
            attr = wxg.GridCellAttr()
            attr.SetReadOnly(True)
            self.SetColAttr(col, attr)

        self.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        self.Bind(wxg.EVT_GRID_CELL_RIGHT_CLICK, self.on_context_menu)

        self.Bind(wxg.EVT_GRID_LABEL_RIGHT_CLICK, self.on_label_menu) # Hide Columns
        self.Bind(wxg.EVT_GRID_LABEL_LEFT_CLICK, self.on_label_lclick)  # Set Focus

        self.Bind(wxg.EVT_GRID_CELL_CHANGED, self.on_cell_changed) # Refresh
        self.Bind(wxg.EVT_GRID_CELL_CHANGING, self.on_cell_changing) # Check if has fk

        self.Bind(wxg.EVT_GRID_SELECT_CELL, self.on_select_cell) # Run child set fk
        self.Bind(wxg.EVT_GRID_COL_SIZE, self.on_col_size) # Save size
        self.Bind(wxg.EVT_GRID_COL_MOVE, self.on_col_move) # Save order
        
        # Event that can be used to veto edit before showing editor.
        # self.Bind(wxg.EVT_GRID_EDITOR_SHOWN, self.on_show_editor)

    def undo_barrier(self):
        """Set an undo barrier."""
        self.db.undo_barrier(self.get_fk())

    def delete_row(self, row):
        """Delete a row and it's data from grid."""
        self.GetTable().delete_row_data(row)
        self.undo_barrier()

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

    def on_cut(self, evt):
        """Handle the menu event."""
        self.cut()

    def cut(self):
        """."""
        self.undo_barrier()

    def on_copy(self, evt):
        """Handle the menu event."""
        pass

    def copy(self):
        """."""
        pass

    def can_paste(self):
        """Return True if copied values can be pasted."""
        pass

    def on_paste(self, evt):
        """Handle the menu event."""
        pass

    def paste(self):
        """."""
        self.undo_barrier()
    
    def on_delete(self, evt):
        """Handle the menu event."""
        self.delete()

    def delete(self):
        """Delete selected rows."""
        selected_rows = self.GetSelectedRows()
        selected_rows.sort(reverse=True)
        for row in selected_rows:
            self.delete_row(row)
        
        self.undo_barrier()
        # self.ForceRefresh()
    
    def on_save(self, evt):
        """Handle the menu event."""
        pass

    def save(self):
        """."""
        pass

    def on_context_menu(self, evt):
        """Open the cell context menu."""
        self.SetFocus()
        menu = wx.Menu()
        row = evt.GetRow()
        col = evt.GetCol()
        no_row_selected = len(self.GetSelectedRows()) == 0

        # Clear selection and set grid cursor to clicked cell if
        # right click was not in a selected cell.
        if not self.IsInSelection(row, col):
            self.ClearSelection()
            self.SetGridCursor(row, col)

        if not hasattr(self, "id_save"):
            self.id_save = wx.NewIdRef()
            self.Bind(wx.EVT_MENU, self.on_undo, id=wx.ID_UNDO)
            self.Bind(wx.EVT_MENU, self.on_cut, id=wx.ID_CUT)
            self.Bind(wx.EVT_MENU, self.on_copy, id=wx.ID_COPY)
            self.Bind(wx.EVT_MENU, self.on_paste, id=wx.ID_PASTE)
            self.Bind(wx.EVT_MENU, self.on_delete, id=wx.ID_DELETE)
            self.Bind(wx.EVT_MENU, self.on_save, id=self.id_save)
        
        mi_undo: wx.MenuItem = menu.Append(wx.ID_UNDO)
        menu.Append(wx.ID_CUT)
        menu.Append(wx.ID_COPY)
        mi_paste = menu.Append(wx.ID_PASTE)
        menu.AppendSeparator()
        mi_delete = menu.Append(wx.ID_DELETE, "Poista\tDelete")

        # Only add db items if the grid table has database table.
        if self.db.has_database_table(self.table_name):
            menu.AppendSeparator()
            mi_save = menu.Append(self.id_save, "Tallenna", "Tallenna valinta tietokantaan")

            if no_row_selected:
                mi_save.Enable(False)

        if not self.can_undo():
            mi_undo.Enable(False)

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

            # CTRL+A
            if keycode == 65:
                pass

            # CTRL+C
            elif keycode == 67:
                pass

            # CTRL+V
            elif keycode == 86:
                pass

            # CTRL+Z
            elif keycode == 90:
                self.undo()

        elif mod == wx.MOD_SHIFT:
            pass

        elif mod == wx.MOD_ALT:
            pass

        else:
            # Delete
            if keycode == wx.WXK_DELETE:
                self.delete()

        evt.Skip()

    def on_label_menu(self, evt):
        """Open menu to hide or show columns."""
        self.SetFocus()

        # Do not show label menu on row label click.
        if evt.GetCol() == -1:
            return

        menu = wx.Menu()

        if not hasattr(self, "id_columns"):
            self.id_columns = wx.NewIdRef(self.GetNumberCols())
            self.Bind(
                wx.EVT_MENU,
                self.on_show_column,
                id=self.id_columns[0],
                id2=self.id_columns[-1]
            )

        positions = [None] * self.GetNumberCols()
        for col in range(self.GetNumberCols()):
            pos = self.GetColPos(col)
            is_shown = False if self.GetColSize(col) == 0 else True
            label = self.GetColLabelValue(col)
            positions[pos] = (col, label, is_shown)
        SHOW_COL_HELP = "Muuta sarakkeen näkyvyyttä"
        for (col, label, is_shown) in positions:
            menu.AppendCheckItem(self.id_columns[col], label, SHOW_COL_HELP)
            menu.Check(self.id_columns[col], is_shown)

        self.PopupMenu(menu)
        menu.Destroy()
        evt.Skip()

    def set_widths(self):
        """Sets the widths of columns from database values."""
        for col in range(self.GetNumberCols()):
            self.set_width(col)

    def set_width(self, col):
        """Sets the width of a column from database value."""
        # if self.db.get_column_visible(col):
        # Width of 0 should be equal as a hidden column.
        self.SetColSize(col, self.get_column_width(col))
        # else:
        #     self.HideCol(col)

    def set_order(self):
        """Set the order of the columns."""
        self.SetColumnsOrder(self.db.get_column_order())
        self.Layout()

    def update_content(self):
        """Update the contents of this grid."""
        self.GetTable().update_data()

    def register_child(self, obj) -> bool:
        """Register a child obj for setting it's foreign key by this grids selection.

        Parameters
        ----------
        obj : Object
            Any object that has set_fk function.

        Returns
        -------
        bool
            False if object has no set_fk function.
        """
        try:
            self.child_set_fks.append(obj.set_fk)
        except AttributeError as e:
            print(f"AttributeError: {e} in DatabaseGrid.register_child")
            print(f"\tGiven object does not have obj.set_fk(value: int) function.")
            return False
        return True


if __name__ == '__main__':
    app = wx.App()

    frame = wx.Frame(None, size=(1200, 600), title="GridTest")
    grid = DbGrid(frame)

    frame.Show()
    app.MainLoop()