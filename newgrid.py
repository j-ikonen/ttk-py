
import wx
import wx.grid as wxg

import table as tb


class DatabaseGridTable(wxg.GridTableBase):
    def __init__(self, db, table):
        super().__init__()

        # Class for database funcitons.
        self.db: tb.OfferTables = db

        # Name of database table.
        self.table = table

        # Data used for display. Update after any change in database.
        self.data = []

        # Values used to limit data displayed.
        self.fk_value = None
        self.condition = {}

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
        return self.db.get_column_setup(self.table, "label", col)

    def GetTypeName(self, row, col):
        """Return the type name."""
        return self.db.get_column_setup(self.table, "type", col)

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

    def set_fk(self, value):
        """Set the foreign key value and update the grid."""
        self.fk_value = value
        self.update_data()

    def get_fk(self):
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

    def get_pk_value(self, row) -> int:
        """Return the primary key value."""
        pk_column = tb.get_pk_column(self.table)
        return self.GetValue(row, pk_column)

    # def GetValueFromDb(self, row, col):
    #     """Return value from database."""

class DatabaseGrid(wxg.Grid):
    def __init__(self, parent, db, dbtable):
        super().__init__(parent, style=wx.WANTS_CHARS|wx.HD_ALLOW_REORDER)

        table = DatabaseGridTable(db, dbtable)
        self.SetTable(table, True)

        self.db: tb.OfferTables = db
        self.table_name = dbtable

        self.copied_rows = []
        self.history = {}
        self.can_save_history = True

        # List of read only columns.
        self.read_only = self.db.get_read_only(self.table_name)

        self.SetRowLabelSize(35)
        self.EnableDragColMove(True)

        self.Bind(wxg.EVT_GRID_CELL_CHANGED, self.on_cell_changed)
        self.Bind(wxg.EVT_GRID_CELL_CHANGING, self.on_cell_changing)
        self.Bind(wxg.EVT_GRID_EDITOR_SHOWN, self.on_show_editor)

    def set_fk(self, value):
        """Set the foreign key for the grid."""
        self.GetTable().set_fk(value)
    
    def get_fk(self):
        """Return the value of foreign key."""
        return self.GetTable().get_fk()

    def on_cell_changing(self, evt):
        """Veto cell change event if change is not allowed."""
        # A required foreign key is not set.
        if tb.has_fk(self.table_name) and self.get_fk() is None:
            print(f"\nError: Can not change value in grid for table '{self.table_name}'.")
            print("\tForeign key needs to be set.")
            evt.Veto()

        evt.Skip()

    def on_cell_changed(self, evt):
        """Refresh the grid on changed cell."""
        self.ForceRefresh()
        evt.Skip()

    def on_show_editor(self, evt):
        """Veto cell editing for read only columns."""
        col = evt.GetCol()
        if col in self.read_only:
            print(f"Column {col} is read only. Value can not be changed.")
            evt.Veto()

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