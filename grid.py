import wx
from wx.core import DataObject
import wx.grid

import data

class CustomDataTable(wx.grid.GridTableBase):
    def __init__(self, labels, types, data, obj):
        """Custom table for lists of Predef, Material, Product or Part objects.

        Args:
            labels (list): Column label strings in a list.
            types (list): Column types in a list. (i.e. wx.grid.GRID_VALUE_STRING)
            data (list): Data to fill the grid with. (i.e. [['r0c0', 'r0c1'], ['r1c0', 'r1c1']])
        """
        super().__init__()

        self.column_labels = labels
        self.data_types = types
        self.data = data
        self.obj = obj

    def GetNumberRows(self):
        if self.data is None:
            return 0
        return len(self.data) + 1

    def GetNumberCols(self):
        return len(self.column_labels)

    def IsEmptyCell(self, row, col):
        try:
            return not self.data[row][col]
        except IndexError:
            return True

    def GetValue(self, row, col):
        try:
            return self.data[row][col]
        except IndexError:
            return ''

    def SetValue(self, row, col, value):
        def innerSetValue(row, col, value):
            try:
                self.data[row][col] = value
            except IndexError:
                # Add a new row.
                self.data.append(self.obj.new())
                innerSetValue(row, col, value)

                # Tell the grid a row was added.
                msg = wx.grid.GridTableMessage(self, wx.grid.GRIDTABLE_NOTIFY_ROWS_APPENDED, 1)
                self.GetView().ProcessTableMessage(msg)

        innerSetValue(row, col, value)

    def GetColLabelValue(self, col):
        return self.column_labels[col]

    def GetTypeName(self, row, col):
        return self.data_types[col]

    def CanGetValueAs(self, row, col, type_name):
        col_type = self.data_types[col].split(':')[0]
        if type_name == col_type:
            return True
        else:
            return False
    
    def CanSetValueAs(self, row, col, type_name):
        return self.CanGetValueAs(row, col, type_name)

    def AppendRows(self, numRows=1):
        for n in range(numRows):
            self.data.append(self.obj.new())
        msg = wx.grid.GridTableMessage(self, wx.grid.GRIDTABLE_NOTIFY_ROWS_APPENDED, numRows)
        self.GetView().ProcessTableMessage(msg)
        return True

    def DeleteRows(self, pos=0, numRows=1):
        for n in range(numRows):
            try:
                del self.data[pos]
            except IndexError as e:
                print(f"CustomTable.DeleteRows: {e}")
                msg = wx.grid.GridTableMessage(self, wx.grid.GRIDTABLE_NOTIFY_ROWS_DELETED, n)
                self.GetView().ProcessTableMessage(msg)
                print(f"DELETE_ROWS: n: {n}")
                return False
        msg = wx.grid.GridTableMessage(self, wx.grid.GRIDTABLE_NOTIFY_ROWS_DELETED, numRows)
        self.GetView().ProcessTableMessage(msg)
        print(f"DELETE_ROWS: n: {numRows}")
        return True

    def NotifyRowChange(self, oldlen, newlen):
        if oldlen < newlen:
            rows_added = newlen - oldlen
            msg = wx.grid.GridTableMessage(
                self,
                wx.grid.GRIDTABLE_NOTIFY_ROWS_APPENDED,
                rows_added
            )
        elif newlen < oldlen:
            rows_deleted = oldlen - newlen
            msg = wx.grid.GridTableMessage(
                self,
                wx.grid.GRIDTABLE_NOTIFY_ROWS_DELETED,
                newlen,
                rows_deleted
            )
        else: 
            return

        self.GetView().ProcessTableMessage(msg)

class CustomGrid(wx.grid.Grid):
    def __init__(self, parent, obj, data=[]):
        super().__init__(parent)

        self.labels = obj.get_labels()
        self.types = obj.get_types()
        self.read_only = obj.get_readonly()
        self.tab = obj.get_tab()
        self.data = data
        self.obj = obj
        self.selected_row = None

        table = CustomDataTable(self.labels, self.types, self.data, obj)
        self.SetTable(table, True)

        self.SetRowLabelSize(25)
        self.SetMargins(0,0)
        self.AutoSizeColumns(False)

        self.Bind(wx.grid.EVT_GRID_CELL_CHANGED, self.on_cell_changed)
        self.Bind(wx.grid.EVT_GRID_CELL_CHANGING, self.on_cell_changing)
        self.Bind(wx.grid.EVT_GRID_SELECT_CELL, self.on_select_cell)
        self.Bind(wx.grid.EVT_GRID_TABBING, self.on_tab)
        self.Bind(wx.grid.EVT_GRID_EDITOR_SHOWN, self.on_editor_shown)

    def on_tab(self, evt):
        # print("On TAB")
        if self.IsCellEditControlEnabled():
            self.DisableCellEditControl()

        col = evt.GetCol()
        row = evt.GetRow()
        if evt.ShiftDown():
            # Move to the last col of previous row.
            if col == 0 and row > 0:
                self.SetGridCursor(row - 1, self.GetNumberCols() - 1)
            # Move back until at the first cell.
            elif col > 0 or row > 0:
                self.SetGridCursor(row, col - 1)

        elif evt.ControlDown():
            # Move to first cell of next row until at the end of grid.
            if row < self.GetNumberRows() - 1:
                self.SetGridCursor(row + 1, 0)
        else:
            # Wrap to next row when tab at last column.
            if col == self.GetNumberCols() - 1:
                # Do nothing if at the end of grid.
                if row < self.GetNumberRows() - 1:
                    self.SetGridCursor(row + 1, 0)
            # Move to next Column
            else:
                self.SetGridCursor(row, self.tab[col])


    def on_cell_changing(self, evt):
        # print("On Cell Changing")
        pass

    def on_cell_changed(self, evt):
        row = evt.GetRow()
        col = evt.GetCol()
        value = self.GetCellValue(row, col)
        print(f"CustomGrid.on_cell_changed")
        # Changing cell for uninitalized data.

        try:
            self.data[row].set(col, value)
        except IndexError:
            print(f"Grid.on_cell_changed - IndexError Grid draws more cells than in data.")
        if row >= len(self.data):
            self.SetGridCursor(self.GetGridCursorCoords())
        evt.Skip()

    def on_select_cell(self, evt):
        print(f"Grid - Selected cell (row, col): ({evt.GetRow()}, {evt.GetCol()})")
        self.selected_row = evt.GetRow()
        evt.Skip()

    def on_editor_shown(self, evt):
        if evt.GetCol() in self.read_only:
            print(f"Grid.on_editor_shown - Column {evt.GetCol()} is read only.")
            evt.Veto()
        evt.Skip()

    def update_data(self, data, reset_selection=False):
        try:
            old = len(self.data)
        except TypeError:
            old = -1

        self.data = data
        self.GetTable().data = data

        if data is None:
            self.GetTable().NotifyRowChange(old, -1)
        else:
            new = len(data)
            self.GetTable().NotifyRowChange(old, new)

        if reset_selection:
            self.selected_row = None
            self.ClearSelection()

if __name__ == '__main__':
    app = wx.App()

    griddata = [
        data.Product("00", "01"),
        data.Product("10", "11"),
        data.Product("20", "21"),
        data.Product("30", "31")
    ]
    griddata2 = [
        data.Product("000", "010"),
        data.Product("100", "110")
    ]
    empty = []

    frame = wx.Frame(
        None,
        title="GridTest",
        size=(800,600),
        style=wx.DEFAULT_FRAME_STYLE|wx.FULL_REPAINT_ON_RESIZE
    )

    print("Frame init done")
    panel = wx.Panel(frame)
    grid = CustomGrid(panel, data.Product(), None)

    gridsizer = wx.BoxSizer(wx.VERTICAL)
    gridsizer.Add(grid, 1, wx.GROW|wx.ALL, 5)
    panel.SetSizer(gridsizer)
    print("Grid init done")
    grid.update_data(griddata, True)
    # griddata[2].desc = "Desc"
    frame.Show()
    frame.Layout()
    app.MainLoop()