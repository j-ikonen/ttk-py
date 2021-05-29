
import wx
import wx.grid as wxg

import table as tb


class DatabaseGridTable(wxg.GridTableBase):
    def __init__(self, db, table):
        """Custom grid table for displaying data from a database.

        Parameters
        ----------
        db : table.OfferTables
            Database control class.
        table : str
            Name of the database table this class displays.
        """
        super().__init__()

        # Class for database funcitons.
        self.db: tb.OfferTables = db

        # Name of database table.
        self.table = table

        # Data used for display. Update after any change in database.
        self.data = []

        # Values used to limit data displayed.
        self.fk_value = None
        self.condition = None

        # Boolean for locking update until it is unlocked.
        self.is_update_locked = False

    def GetNumberRows(self):
        """Return the number of rows on display.
        
        N rows of data + 1 uninitalized for inserting a new row.
        """
        return len(self.data) + 1

    def GetNumberCols(self):
        """Return the number of columns."""
        return self.db.column_count(self.table)

    def IsEmptyCell(self, row, col):
        """Return true if given cell is empty.
        
        Used to determine if previous rows content can overflow to this cell."""
        return False

    def GetValue(self, row, col):
        """Return value in cell."""
        try:
            return self.data[row][col]
        except IndexError as e:
            # print(f"IndexError: {e} in DbGridTable.GetValue")
            return None

    def GetColLabelValue(self, col):
        """Return the column label."""
        return self.db.get_column_value(self.table, "label", col)

    def GetTypeName(self, row, col):
        """Return the type name."""
        return self.db.get_column_value(self.table, "type", col)

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
        if row >= self.GetNumberRows() - 1:
            pk_value = self.db.insert_with_fk(self.table, self.fk_value)

        # Cell in initialized row.
        else:
            pk_value = self.get_pk_value(row)

        # Set value to a valid row with Primary Key.
        if pk_value is not None:
            success = self.db.update_cell(self.table, col, pk_value, value)

            if success:
                self.update_data()
            else:
                print("\nDbGridTable.SetValue update value failed.")
                print(f"\ttable: {self.table}")
                print(f"\t(row, col): ({row}, {col})")
                print(f"\tpk_value: {pk_value}")
                print(f"\tvalue: {value}")

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
        self.fk_value = value
        self.update_data()

    def get_fk(self) -> int:
        """Return the foreign key value."""
        return self.fk_value

    def set_condition(self, condition):
        """Set the conditions for search and update the grid."""
        self.condition = condition
        self.update_data()

    def update_data(self):
        """Update the displayed data from database."""
        if not self.update_locked():
            oldn = len(self.data)
            self.data = self.db.select_with(self.table, self.fk_value, self.condition)
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

    def update_locked(self):
        """Return True if update is not allowed."""
        return self.is_update_locked

    def lock_update(self, is_locked: bool):
        """Set the value of update lock."""
        self.is_update_locked = is_locked

        # Refresh data on unlock.
        if is_locked is False:
            self.update_data()

    def get_pk_value(self, row: int) -> int:
        """Return the primary key value."""
        pk_column = tb.get_pk_column(self.table)
        return self.GetValue(row, pk_column)

    def delete_row(self, row: int):
        pkval = self.get_pk_value(row)
    # def GetValueFromDb(self, row, col):
    #     """Return value from database."""


SHOW_COL_HELP = "Muuta sarakkeen näkyvyyttä"


class DatabaseGrid(wxg.Grid):
    def __init__(self, parent, db, dbtable):
        """Grid to display data from a database table.

        Either by search conditions, foreign key or neither.

        Parameters
        ----------
        parent : wx.Window
            The parent wx.Window.
        db : table.OfferTables
            The database control class.
        dbtable : str
            Name of the database table.
        """
        super().__init__(parent, style=wx.WANTS_CHARS|wx.HD_ALLOW_REORDER)

        self.table_name = dbtable
        self.db: tb.OfferTables = db

        table = DatabaseGridTable(db, dbtable)
        self.SetTable(table, True, self.GridSelectRows)
        self.set_widths()
        self.set_order()

        # Set Read Only Columns.
        for col in self.db.get_read_only(self.table_name):
            attr = wxg.GridCellAttr()
            attr.SetReadOnly(True)
            self.SetColAttr(col, attr)

        # List of functions that are used to update an objects foreign key
        # with the primary key of this grid.
        self.child_set_fks = []

        self.copied_rows = []
        self.history = {}
        self.can_save_history = True

        self.SetRowLabelSize(35)
        self.EnableDragColMove(True)
        # self.UseNativeColHeader(True)

        self.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        self.Bind(wxg.EVT_GRID_CELL_RIGHT_CLICK, self.on_context_menu)

        self.Bind(wxg.EVT_GRID_LABEL_RIGHT_CLICK, self.on_label_menu) # Hide Columns
        self.Bind(wxg.EVT_GRID_LABEL_LEFT_CLICK, self.on_label_lclick)  # Set Focus

        self.Bind(wxg.EVT_GRID_CELL_CHANGED, self.on_cell_changed) # Refresh
        self.Bind(wxg.EVT_GRID_CELL_CHANGING, self.on_cell_changing) # Check if has fk

        # Event that can be used to veto edit before showing editor.
        # self.Bind(wxg.EVT_GRID_EDITOR_SHOWN, self.on_show_editor)

        self.Bind(wxg.EVT_GRID_SELECT_CELL, self.on_select_cell) # Run child set fk
        self.Bind(wxg.EVT_GRID_COL_SIZE, self.on_col_size) # Save size
        self.Bind(wxg.EVT_GRID_COL_MOVE, self.on_col_move) # Save order

    def can_undo(self):
        """Return True if action can be undone."""
        if self.get_fk() in self.history and len(self.history[self.get_fk()]) > 0:
            return True
        return False

    def on_undo(self, evt):
        """Handle the menu event."""
        self.undo()

    def undo(self):
        """."""
        pass
    
    def on_cut(self, evt):
        """Handle the menu event."""
        pass

    def cut(self):
        """."""
        pass
    
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
        pass
    
    def on_delete(self, evt):
        """Handle the menu event."""
        pass

    def delete(self):
        """."""
        pass
    
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
                pass

        elif mod == wx.MOD_SHIFT:
            pass

        elif mod == wx.MOD_ALT:
            pass

        else:
            # Delete
            if keycode == wx.WXK_DELETE:
                pass

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

        for (col, label, is_shown) in positions:
            menu.AppendCheckItem(self.id_columns[col], label, SHOW_COL_HELP)
            menu.Check(self.id_columns[col], is_shown)

        self.PopupMenu(menu)
        menu.Destroy()
        evt.Skip()

    def on_show_column(self, evt):
        """Show or hide the column."""
        is_checked = evt.IsChecked()
        col = self.id_columns.index(evt.GetId())

        if is_checked:
            width = self.db.get_column_value(self.table_name, "width", col)
            self.db.set_visible(self.table_name, col, True)
            self.SetColSize(col, width)
        else:
            self.HideCol(col)
            self.db.set_visible(self.table_name, col, False)
        evt.Skip()

    def on_label_lclick(self, evt):
        """Set focus on this grid."""
        self.SetFocus()
        evt.Skip()

    def set_fk(self, value: int):
        """Set the foreign key for the grid."""
        self.GetTable().set_fk(value)

    def get_fk(self) -> int:
        """Return the value of foreign key."""
        return self.GetTable().get_fk()

    def get_pk(self, row: int) -> int:
        """Return the primary key from the given row."""
        return self.GetTable().get_pk_value(row)

    def on_cell_changing(self, evt):
        """Veto cell change event if change is not allowed."""
        # A required foreign key is not set.
        if tb.has_fk(self.table_name) and self.get_fk() is None:
            print(f"\nError: Can not change value in grid for table '{self.table_name}'.")
            print("\tForeign key needs to be set.")
            evt.Veto()

        self.db.save_temp(self.table_name, self.get_fk())
        evt.Skip()

    def on_cell_changed(self, evt):
        """Refresh the grid on changed cell."""
        self.ForceRefresh()
        evt.Skip()

    def on_col_size(self, evt):
        """Update the columns table with new column width."""
        col = evt.GetRowOrCol()
        width = self.GetColSize(col)
        if width != 0:
            self.save_width(col, width)
        self.PostSizeEventToParent()
        evt.Skip()

    def on_col_move(self, evt):
        """Veto moves of hidden columns and do CallAfter to save new positions."""
        col = evt.GetCol()
        if self.GetColSize(col) == 0:
            evt.Veto()
        pos = self.GetColPos(col)
        wx.CallAfter(self.col_moved, col, pos)
        evt.Skip()

    def col_moved(self, col_id, old_pos):
        positions = []
        for col in range(self.GetNumberCols()):
            colpos = self.GetColPos(col)
            positions.append((colpos, col, self.table_name))
        self.db.set_column_values("col_order", positions)

    def on_select_cell(self, evt):
        """Set the primary key of selected row as foreign key of any child grids."""
        # self.ClearSelection()
        rowid = self.get_pk(evt.GetRow())
        for fn in self.child_set_fks:
            fn(rowid)
        evt.Skip()

    # def on_show_editor(self, evt):
    #     """Veto cell editing for read only columns."""
    #     col = evt.GetCol()
    #     if col in self.read_only:
    #         print(f"Column {col} is read only. Value can not be changed.")
    #         evt.Veto()

    def save_width(self, col, width):
        """Set the width of the column in columns table."""
        self.db.set_column_value(self.table_name, "width", col, width)

    def set_widths(self):
        """Set the columns to widths from columns table."""
        is_visible = self.db.get_visible(self.table_name)
        for col in range(self.GetNumberCols()):
            if is_visible[col]:
                width = self.db.get_column_value(self.table_name, "width", col)
                self.SetColSize(col, width)
            else:
                self.HideCol(col)

    def set_order(self):
        """Set the order of the columns."""
        order = self.db.get_col_order(self.table_name)
        self.SetColumnsOrder(order)
        self.Layout()

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


class GridPanel(wx.Panel):
    def __init__(self, parent, db):
        super().__init__(parent)

        self.copied_cells = []

        self.grid_mats = DatabaseGrid(self, db, "group_materials")

        sizer = wx.BoxSizer(wx.VERTICAL)

        sizer.Add(self.grid_mats, 1, wx.EXPAND)
        self.SetSizer(sizer)
    
    def set_fk(self, value):
        """Set the foreign key for the grids."""
        self.grid_mats.set_fk(value)


if __name__ == '__main__':
    app = wx.App()

    frame = wx.Frame(None, size=(1200, 600))
    db = tb.OfferTables()
    panel = GridPanel(frame, db)

    # rowid = db.insert_with_fk("offers", None)
    # group_row_id = db.insert_with_fk("groups", rowid)

    panel.set_fk(1)
    frame.Show()

    app.MainLoop()