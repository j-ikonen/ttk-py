"""Classes for handling grids."""

import wx
import wx.grid as wxg

import db


class GridBase(wxg.GridTableBase):
    def __init__(self, db: db.SQLTableBase, fk: int=None):
        super().__init__()

        self.db = db
        self.fk = fk
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
            self.db.update(rowid, col, value)

            # Debug to make sure database receives correct type.
            print("Updating value: '{}' of type: {} at col: {}".format(
                value, type(value), col
            ))

        # Cell in initialized row.
        else:
            rowid = self.data[0]

        # Set value to a valid row with Primary Key.
        if rowid is not None:
            success = self.db.update(self.table, col, rowid, value)

            if not success and is_last_row:
                self.db.delete_row(self.table, rowid)
            elif success:
                self.update_data()
            else:
                print("\nDbGridTable.SetValue update value failed.")
                # print(f"\ttable: {self.table}")
                # print(f"\t(row, col): ({row}, {col})")
                # print(f"\tpk_value: {pk_value}")
                # print(f"\tvalue: {value}")


class DbGrid(wxg.Grid):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


if __name__ == '__main__':
    app = wx.App()

    frame = wx.Frame(None, size=(1200, 600), title="GridTest")
    grid = DbGrid(frame)

    frame.Show()
    app.MainLoop()