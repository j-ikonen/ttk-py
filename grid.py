import wx
import wx.grid

from data import GridData


GRIDMENU_EDIT_OBJECT = "Muokkaa"
GOD_TITLE = "Muokkaa"
GOD_LABEL = "Muokkaa valitun esineen ominaisuuksia."
GOD_EDIT_SIZE = (250, -1)


class CustomDataTable(wx.grid.GridTableBase):
    def __init__(self, data):
        """Custom table for lists of Predef, Material, Product or Part objects.

        Args:
            labels (list): Column label strings in a list.
            types (list): Column types in a list. (i.e. wx.grid.GRID_VALUE_STRING)
            data (GridData): Data class
        """
        super().__init__()

        self.obj: GridData = data

    def GetNumberRows(self):
        if self.obj is None or self.obj.data is None:
            return 0
        return len(self.obj.data) + 1

    def GetNumberCols(self):
        return len(self.obj.columns)

    def IsEmptyCell(self, row, col):
        try:
            return not self.obj.get(row, col)
        except IndexError:
            return True

    def GetValue(self, row, col):
        value = self.obj.get(row, col)
        return value if value else ''

    def SetValue(self, row, col, value):
        def innerSetValue(row, col, value):
            if not self.obj.set(row, col, value):
                # Add a new row.
                self.obj.append()
                innerSetValue(row, col, value)

                # Tell the grid a row was added.
                msg = wx.grid.GridTableMessage(self, wx.grid.GRIDTABLE_NOTIFY_ROWS_APPENDED, 1)
                self.GetView().ProcessTableMessage(msg)

        innerSetValue(row, col, value)

    def GetColLabelValue(self, col):
        return self.obj.get_label(col)

    def GetTypeName(self, row, col):
        return self.obj.get_type(col)

    def CanGetValueAs(self, row, col, type_name):
        col_type = self.obj.get_type(col).split(':')[0]
        if type_name == col_type:
            return True
        else:
            return False
    
    def CanSetValueAs(self, row, col, type_name):
        return self.CanGetValueAs(row, col, type_name)

    def AppendRows(self, numRows=1):
        for n in range(numRows):
            self.obj.append()
        msg = wx.grid.GridTableMessage(
            self,
            wx.grid.GRIDTABLE_NOTIFY_ROWS_APPENDED,
            numRows
        )
        self.GetView().ProcessTableMessage(msg)
        return True

    def DeleteRows(self, pos=0, numRows=1):
        n_del = self.obj.delete(pos, numRows)
        
        if n_del > 0:
            msg = wx.grid.GridTableMessage(
                self,
                wx.grid.GRIDTABLE_NOTIFY_ROWS_DELETED,
                n_del
            )
            self.GetView().ProcessTableMessage(msg)
            print(f"DELETE_ROWS: n: {n_del}")
            return True
        else:
            return False

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
    def __init__(self, parent, data: GridData):
        super().__init__(parent)

        self.data = data
        self.selected_row = None
        self.rclick_row = None

        table = CustomDataTable(self.data)
        self.SetTable(table, True)

        self.SetRowLabelSize(25)
        self.SetMargins(0,0)
        self.AutoSizeColumns(False)

        self.Bind(wx.grid.EVT_GRID_CELL_CHANGED, self.on_cell_changed)
        self.Bind(wx.grid.EVT_GRID_CELL_CHANGING, self.on_cell_changing)
        self.Bind(wx.grid.EVT_GRID_SELECT_CELL, self.on_select_cell)
        self.Bind(wx.grid.EVT_GRID_TABBING, self.on_tab)
        self.Bind(wx.grid.EVT_GRID_EDITOR_SHOWN, self.on_editor_shown)
        self.Bind(wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.on_cell_rclick)

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
            else:
                try:
                    # Move to next Column
                    self.SetGridCursor(row, self.data.tab_to[col])
                except IndexError:
                    # Move to first cell of next row until at the end of grid.
                    if row < self.GetNumberRows() - 1:
                        self.SetGridCursor(row + 1, 0)



    def on_cell_changing(self, evt):
        # print("On Cell Changing")
        pass

    def on_cell_changed(self, evt):
        # row = evt.GetRow()
        # col = evt.GetCol()
        # value = self.GetCellValue(row, col)

        # print(f"CustomGrid.on_cell_changed r:{row}, c:{col}, v:{value}")

        # if not self.data.set(row, col, value):
        #     print(f"TRIED TO CHANGE A CELL THAT IS NOT INITIALIZED.")

        # Initialize new empty row if edit in last one.
        # print(f"\tROW: {row}, NUM ROWS: {self.GetNumberRows()}")
        # if row >= self.GetNumberRows() - 1:
        #     self.data.append()
        #     self.AppendRows()
        #     print("\tREFRESHED")
            # self.Refresh()

        # Keep cursor within intialized data.
        # if row >= len(self.data.data) - 1:
        #     self.SetGridCursor(self.GetGridCursorCoords())

        evt.Skip()

    def on_select_cell(self, evt):
        print(f"Grid - Selected cell (row, col): ({evt.GetRow()}, {evt.GetCol()})")
        self.selected_row = evt.GetRow()
        evt.Skip()

    def on_editor_shown(self, evt):
        col = evt.GetCol()
        if self.data.is_readonly(col):
            print(f"Grid.on_editor_shown - Column {col} is read only.")
            evt.Veto()
        evt.Skip()

    def on_cell_rclick(self, evt):
        self.rclick_row = evt.GetRow()

        # Do Event Binding only once.
        if not hasattr(self, 'edit_object_id'):
            self.edit_object_id = wx.NewIdRef()
            self.Bind(wx.EVT_MENU, self.on_edit_object, id=self.edit_object_id)

        menu = wx.Menu()
        menu.Append(self.edit_object_id, GRIDMENU_EDIT_OBJECT)

        # Alternate item initialization for editing MenuItem properties.
        # item = wx.MenuItem(menu, self.edit_object_id, GRIDMENU_EDIT_OBJECT")
        # menu.Append(item)

        self.PopupMenu(menu)
        menu.Destroy()
        self.rclick_row = None

    def on_edit_object(self, evt):
        """Handle event for editing code values."""
        row = self.rclick_row

        codes = self.data.get_codes(row)
        dlg = GridObjectDialog(self, codes)
        dlg.CenterOnScreen()

        val = dlg.ShowModal()
        if val == wx.ID_OK:
            # print("Grid.on_edit_object RETURN OK FROM DIALOG")
            for key, value in dlg.code_edits.items():
                codes[key] = value.GetValue()
            self.data.set_codes(row, codes)
        # else:
            # print("Grid.on_edit_object RETURN CANCEL FROM DIALOG")

        dlg.Destroy()
        self.Refresh()

    def update_data(self, data: list, reset_selection=False):
        """Update GridData with given data.
        
        Args:
            data (list): New data to replace GridData.data with.
            reset_selection (bool): Will the selection be reset with update.
        """
        try:
            oldlen = len(self.data.data)
        except TypeError:
            oldlen = -1

        self.data.data = data
        self.GetTable().obj.data = data

        # Updated grid is empty.
        if data is None or data is []:
            self.GetTable().NotifyRowChange(oldlen, -1)
        else:
            new = len(data)
            self.GetTable().NotifyRowChange(oldlen, new)
        
        # Reset selection when data is changed from one object to another.
        if reset_selection:
            self.selected_row = None
            self.ClearSelection()


class GridObjectDialog(wx.Dialog):
    def __init__(self, parent, data: dict, title=GOD_TITLE):
        """Handle dialog for updating object data not shown in grid.
        
        Args:
            parent: Parent wxWindow.
            data (dict): Dictionary of data to edit.
            title (str): Title string of dialog.
        """
        super().__init__()
        self.Create(parent, title=title)

        self.code_edits = {}

        label = wx.StaticText(self, label=GOD_LABEL)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        for key, value in data.items():
            key_label = wx.StaticText(self, label=key)
            value_ctrl = wx.TextCtrl(self, value=value, size=GOD_EDIT_SIZE)
            self.code_edits[key] = value_ctrl
            hsizer = wx.BoxSizer(wx.HORIZONTAL)
            hsizer.Add(key_label, 0, wx.ALL, 5)
            hsizer.Add(value_ctrl, 0, wx.ALL, 5)
            sizer.Add(hsizer, 0, wx.ALL, 5)

        line = wx.StaticLine(self, size=(20, -1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.EXPAND|wx.RIGHT|wx.TOP, 5)

        btnsizer = wx.StdDialogButtonSizer()

        btn = wx.Button(self, wx.ID_OK)
        btn.SetDefault()
        btnsizer.AddButton(btn)

        btn = wx.Button(self, wx.ID_CANCEL)
        btnsizer.AddButton(btn)
        btnsizer.Realize()

        sizer.Add(btnsizer, 0, wx.ALL, 5)
        self.SetSizer(sizer)
        sizer.Fit(self)
