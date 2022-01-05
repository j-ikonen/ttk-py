"""Grid classes for showing the data inside groups."""
#pylint: disable=invalid-name

from decimal import Decimal

#import wx
import wx.grid as wxg

from quote import Quote
from gui.grid_decimal_editor import GridDecimalEditor
import event as evt


class TableBase(wxg.GridTableBase):
    """."""
    def __init__(self, quote, table):
        super().__init__()
        self.quote: Quote = quote
        self.table = table
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
        return self.quote.col_type(self.table, col)

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

            if not self.quote.set_cell(self.table, primary_key, col, value):
                print("\nGridBase.SetValue update value failed.")
                # print(f"\ttable: {self.table}")
                # print(f"\t(row, col): ({row}, {col})")
                # print(f"\tpk_value: {pk_value}")
                # print(f"\tvalue: {value}")
            else:
                self.data[row][col] = value

    def AppendRows(self, numRows):
        """Append rows to the grid."""
        msg = wxg.GridTableMessage(
            self,
            wxg.GRIDTABLE_NOTIFY_ROWS_APPENDED,
            numRows)
        return self.GetView().ProcessTableMessage(msg)

    def DeleteRows(self, pos, numRows):
        """Delete rows from the grid at pos."""
        msg = wxg.GridTableMessage(
            self,
            wxg.GRIDTABLE_NOTIFY_ROWS_DELETED,
            pos,
            numRows)
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

    # pylint: disable=no-self-use
    def CanMeasureColUsingSameAttr(self, _col):
        """Use same attributes for all rows of a column."""
        return True


    def get_rowid(self, row):
        """Return the rowid of given row."""
        try:
            return self.data[row][0]
        except IndexError:
            return None

    def update_rows(self, old, new):
        """Update the number of rows displayed."""
        diff = new - old
        if diff > 0:
            self.AppendRows(diff)
        elif diff < 0:
            self.DeleteRows(0, abs(diff))


class Table(wxg.Grid, evt.EventHandler):
    """."""
    def __init__(self, parent, quote, table):
        super().__init__(parent)
        self.quote: Quote = quote
        self.table = table

        self.SetTable(TableBase(quote, table), True, self.GridSelectRows)
        self.SetRowLabelSize(35)
        # self.EnableDragColMove(True)
        self.RegisterDataType("decimal", None, GridDecimalEditor())

        # Set column attributes.
        read_only_list = self.db().get_column_read_only()
        for col, ro in enumerate(read_only_list):
            if ro == 1:
                attr = wxg.GridCellAttr()
                attr.SetReadOnly(True)
                self.SetColAttr(col, attr)

        self.Bind(wxg.EVT_GRID_CELL_CHANGED, self.on_cell_changed) # Refresh
        self.Bind(wxg.EVT_GRID_CELL_CHANGING, self.on_cell_changing) # Check if has fk

        self.append_row()

    ###########################################
    ## wx.EVENT HANDLERS
    ###########################################
    def on_cell_changing(self, wxevt):
        """Veto cell change event if change is not allowed."""
        if self.quote.state.open_group:
            wxevt.Skip()
        else:
            print("Cell changing is disabled when no group is opened.")
            wxevt.Veto()

    def on_cell_changed(self, wxevt):
        """Refresh the grid on changed cell."""
        self.undo_barrier()
        # event_data = [
        #     self.table,
        #     self.quote.state.open_group,
        #     wxevt.GetCol(),
        #     wxevt.GetValue()]
        # self.notify(evt.TABLE_CELL, evt.Event(self, event_data))

        wxevt.Skip()

    ###########################################
    ## UNDO FUNCTIONS
    ###########################################
    def undo_barrier(self):
        """Set an undo barrier."""
        self.quote.undo_barrier(self.table, self.group())

    ###########################################
    ## TABLE MANIPULATION
    ###########################################
    def append_row(self):
        """Append a row by inserting a new row to database."""
        self.quote.new_table_row(self.table)


    def update(self, _data):
        """Update the contents of this table."""
        content = self.GetTable().data
        try:
            oldn = len(content)
        except TypeError:
            oldn = 0

        content = self.db().select(self.group())

        try:
            newn = len(content)
        except TypeError:
            newn = 0

        self.GetTable().update_rows(oldn, newn)
        self.ForceRefresh()

    ###########################################
    ## HELPERS
    ###########################################
    def db(self):
        """Get the database object."""
        return self.quote.select_table(self.table)

    def group(self):
        """Get the group id."""
        return self.quote.state.open_group
