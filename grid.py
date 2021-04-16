import wx
import wx.grid


class GridData:
    def __init__(self) -> None:
        pass
    def get(self, col):
        return None
    def set(self, col, value):
        pass
    def new(self):
        return type(self)()
    def get_labels(self):
        return []
    def get_types(self):
        return []
    def get_list(self):
        return []

class Product(GridData):
    def __init__(self, code="", desc="") -> None:
        super().__init__()
        self.code = code
        self.desc = desc
    def get(self, col):
        if col == 0: return self.code
        elif col == 1: return self.desc
    def set(self, col, value):
        if col == 0: self.code = value
        elif col == 1: self.desc = value
    def new(self):
        return Product()
    def get_labels(self):
        return ['Koodi', 'Kuvaus']
    def get_types(self):
        return [wx.grid.GRID_VALUE_STRING, wx.grid.GRID_VALUE_STRING]
    def get_list(self):
        return [self.code, self.desc]

class CustomGrid(wx.grid.Grid):
    def __init__(self, parent, obj, data=[]):
        super().__init__(parent)

        self.data = data    # i.e. [Product(), Product(), Product()]
        self.obj = obj

        labels = obj.get_labels()
        types = obj.get_types()
        print("Before CreateGrid")

        rawdata = []
        for row in range(len(data)):
            rawdata.append([])
            for col in range(len(labels)):
                rawdata[row].append(data[row].get(col))

        table = CustomDataTable(labels, types, rawdata)
        self.AssignTable(table, wx.grid.Grid.SelectRows)

        print("CreateGrid init done")
        for n in range(len(obj.get_types())):
            # Set column types
            attr = wx.grid.GridCellAttr()
            if obj.get_types()[n] == wx.grid.GRID_VALUE_STRING:
                attr.SetEditor(wx.grid.GridCellTextEditor())

            self.SetColAttr(n, attr)
            self.SetColLabelValue(n, obj.get_labels()[n])

        print("Attr and labels done")
        self.fill_grid(data)
        
        self.Bind(wx.grid.EVT_GRID_CELL_CHANGED, self.on_cell_changed)
        self.Bind(wx.grid.EVT_GRID_SELECT_CELL, self.on_select_cell)

        print("Init done")

    def on_cell_changed(self, evt):
        if self.data is not None:
            row = evt.GetRow()
            col = evt.GetCol()
            value = self.GetCellValue(row, col)
            try:
                self.data[row].set(col, value)
            except IndexError:
                self.data.append(self.obj.new())
                self.data[row].set(col, value)

    def on_select_cell(self, evt):
        print(f"Selected cell: row: {evt.GetRow()}, col: {evt.GetCol()}")
        evt.Skip()

    def fill_grid(self, data):
        for row in range(len(data)):
            for col in range(len(self.GetNumberCols())):
                self.SetCellValue(row, col, data[row].get(col))

class CustomDataTable(wx.grid.GridTableBase):
    def __init__(self, labels, types, data):
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

    def GetNumberRows(self):
        return len(self.data)

    def GetNumberCols(self):
        return len(self.data[0])

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
                self.data.append([''] * self.GetNumberCols())
                innerSetValue(row, col, value)

                # Tell the grid a row was added.
                msg = wx.grid.GridTableMessage(self, wx.grid.GRIDTABLE_NOTIFY_ROWS_APPENDED, 1)
                self.GetView().ProcessTableMessage(msg)

        innerSetValue(row, col, value)

    def GetColLabelValue(self, col):
        return self.column_labels[col]

    def GetTypeName(self, row, col):
        return self.data_types[col]

    # def Clear(self):
    #     rows = len(self.data)
    #     msg = wx.grid.GridTableMessage(self, wx.grid.GRIDTABLE_NOTIFY_ROWS_DELETED, rows)
    #     self.GetView().ProcessTableMessage(msg)
    #     self.data = []

    def AppendRows(self, numRows=1):
        for n in range(numRows):
            self.data.append([''] * self.GetNumberCols())
        msg = wx.grid.GridTableMessage(self, wx.grid.GRIDTABLE_NOTIFY_ROWS_APPENDED, numRows)
        self.GetView().ProcessTableMessage(msg)
        return True

    def DeleteRows(self, pos=0, numRows=1):
        for n in range(numRows):
            try:
                del self.data[pos]
            except IndexError as e:
                print(f"CustomTable.DeleteRows: {e}")
                return False
        msg = wx.grid.GridTableMessage(self, wx.grid.GRIDTABLE_NOTIFY_ROWS_DELETED, numRows)
        self.GetView().ProcessTableMessage(msg)
        print(f"DELETE_ROWS: n: {numRows}")
        return True


if __name__ == '__main__':
    app = wx.App(useBestVisual=True)

    griddata = [Product(), Product(), Product(), Product()]

    frame = wx.Frame()
    frame.Show()
    frame.Layout()
    print("Frame init done")
    grid = CustomGrid(frame, Product(), griddata)
    print("Grid init done")

    app.MainLoop()