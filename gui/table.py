"""Grid classes for showing the data inside groups."""
#pylint: disable=invalid-name

from decimal import Decimal

#import wx
import wx.grid as wxg

from quote import Quote
from gui.grid_decimal_editor import GridDecimalEditor


class TableBase(wxg.GridTableBase):
    """."""
    def __init__(self, quote):
        super().__init__()
        self.quote: Quote = quote
        self.quote_id = None
        self.table = None
        self.data = []

    def GetNumberRows(self):
        """Return the number of rows on display."""
        try:
            return len(self.data)
        except TypeError:
            return 0

    def GetNumberCols(self):
        """Return the number of columns."""
        return self.quote.n_cols(self.table)

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
        except IndexError:
            return None

    def GetColLabelValue(self, col):
        """Return the column label."""
        return self.quote.col_label(self.table, col)

    def GetTypeName(self, _row, col):
        """Return the type name."""
        return self.quote.col_type(col)

    def CanGetValueAs(self, row, col, type_name):
        """Test if value can be received as type."""
        col_type = self.GetTypeName(row, col).split(":")[0]
        if type_name == col_type:
            return True
        return False

    def CanSetValueAs(self, row, col, type_name):
        """Test if value can be set as type."""
        return self.CanGetValueAs(row, col, type_name)

    def SetValue(self, row, col, value):
        """Update the database with a new value."""
        # Interpret an empty value as None.
        if value == "":
            value = None

        # Set value to a valid row with Primary Key.
        primary_key = self.get_rowid(row)
        if primary_key:
            if isinstance(value, float):
                value = Decimal(value)

            if self.quote.set_cell(self.table, primary_key, col, value):
                self.quote.table_update(self.table, col)
            else:
                print("\nGridBase.SetValue update value failed.")
                # print(f"\ttable: {self.table}")
                # print(f"\t(row, col): ({row}, {col})")
                # print(f"\tpk_value: {pk_value}")
                # print(f"\tvalue: {value}")

    def AppendRows(self, numRows):
        """Append rows to the grid."""
        msg = wxg.GridTableMessage(self, wxg.GRIDTABLE_NOTIFY_ROWS_APPENDED, numRows)
        return self.GetView().ProcessTableMessage(msg)

    def DeleteRows(self, pos, numRows):
        """Delete rows from the grid at pos."""
        msg = wxg.GridTableMessage(self, wxg.GRIDTABLE_NOTIFY_ROWS_DELETED, pos, numRows)
        return self.GetView().ProcessTableMessage(msg)
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


    def get_rowid(self, row):
        """Return the rowid of given row."""
        try:
            return self.data[row][0]
        except IndexError:
            return None

class Table(wxg.Grid):
    """."""
    def __init__(self, parent, quote):
        super().__init__(parent)
        self.quote: Quote = quote

        table = TableBase(quote)
        self.SetTable(table, True, self.GridSelectRows)

        self.SetRowLabelSize(35)
        # self.EnableDragColMove(True)
        self.RegisterDataType("decimal", None, GridDecimalEditor())
