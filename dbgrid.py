"""
TODO
----
    Create a diagram for SetValue logic.
    Get the value from database in GetValue.
    Create Parts custom table.

"""

import wx
import wx.grid as wxg
from bson.objectid import ObjectId

import table as tb


class DatabaseGridTable(wxg.GridTableBase):
    def __init__(self, db):
        super().__init__()

        self.db: tb.OfferTables = db
        self.data = []

    def GetNumberRows(self):
        return len(self.data) + 1

    def GetNumberCols(self):
        return len(self.columns)
    
    def GetDataCol(self, col):
        return self.columns[col]

    def IsEmptyCell(self, row, col):
        try:
            value = self.data[row][self.columns[col]]
        except IndexError:
            return True

        if value is None:
            return True
        else:
            return False

    def GetValue(self, row, col):
        try:
            return self.data[row][self.columns[col]]
        except IndexError:
            return ""

    def SetValue(self, row, col, value):
        def innerSetValue(row, col, value):
            try:
                idx = self.columns[col]

                if idx in self.unique:
                    for rowdata in self.data:
                        if rowdata[idx] == value:
                            print(f"Column is unique, '{value}' already exists.")
                            return

            except IndexError:
                print("Column not defined properly.")
                return
            insert_new = True
            try:
                if idx in self.cant_update or self.db.update_one(
                    self.tablename,
                    self.col_keys[idx],
                    self.pk,
                    [value] + self.GetPkValue(row)
                ):
                    self.data[row][idx] = value
                    insert_new = False
            except IndexError:
                pass

            # The row is not initialized yet.
            if insert_new:
                new_id = [str(ObjectId())]
                if self.db.insert(
                    self.tablename,
                    self.pk + self.fk + [self.col_keys[idx]],
                    new_id + self.fk_value + [value]
                ):
                    datarow = self.db.get(
                        self.tablename,
                        ["*"],
                        self.pk,
                        new_id
                    )
                    self.data.append(list(datarow))
                # try again until init done
                innerSetValue(row, col, value)

                msg = wxg.GridTableMessage(
                    self,
                    wxg.GRIDTABLE_NOTIFY_ROWS_APPENDED,
                    1
                )
                self.GetView().ProcessTableMessage(msg)

        if self.fk_value is None:
            print(f"Foreign key {self.fk} is not defined.")
            return

        innerSetValue(row, col, value)

    def GetColLabelValue(self, col):
        return self.col_labels[self.columns[col]]
    
    def GetTypeName(self, row, col):
        return self.col_types[self.columns[col]]
    
    def CanGetValueAs(self, row, col, type_name):
        col_type = self.GetTypeName(row, col).split(":")[0]
        if type_name == col_type:
            return True
        else:
            return False
    
    def CanSetValueAs(self, row, col, type_name):
        return self.CanGetValueAs(row, col, type_name)

    def GetPkValue(self, row):
        pk_val = []
        for idx in self.pk_column:
            pk_val.append(self.data[row][idx])
        return pk_val

    def GetValueAsDouble(self, row, col):
        try:
            return super().GetValueAsDouble(row, col)
        except TypeError:
            return 0.0

    def GetValueAsLong(self, row, col):
        try:
            return super().GetValueAsLong(row, col)
        except TypeError:
            return 0
    
    def GetValueAsBool(self, row, col):
        try:
            return super().GetValueAsBool(row, col)
        except TypeError:
            return False
    
    def UpdateReadOnly(self, row):
        return
    
    def ChangedDependency(self, col):
        datacol = self.GetDataCol(col)
        if datacol in self.ro_dependency:
            return True
        else:
            return False

    def OnCellChanged(self, row, col):
        if self.ChangedDependency(col):
            self.UpdateReadOnly(row)


class GroupMaterialsTable(DatabaseGridTable):
    def __init__(self, db: tb.OfferTables):
        super().__init__(db)

        self.tablename = "offer_materials"
        setup = db.get_columns(self.tablename)
        self.pk = ["id"]
        self.fk = ["group_id"]
        self.fk_value = None
        self.pk_column = [0]
        self.columns = [3, 6, 7, 8, 9, 10, 11, 12, 13]
        self.col_keys = [val[tb.KEY] for val in setup]
        self.col_labels = [val[tb.LABEL] for val in setup]
        self.col_types = [val[tb.TYPE] for val in setup]
        self.unique = []
        self.read_only = []
        self.ro_dependency = [8, 9, 10, 11, 12]
        self.cant_update = [13]

        for n, val in enumerate(setup):
            if val[tb.UNIQUE] == 1:
                self.unique.append(n)
            if val[tb.READ_ONLY] == 1:
                self.read_only.append(n)

        self.fk_value = ["uusi ryhmä"]

    def UpdateReadOnly(self, row):
        # datacol = self.GetDataCol(col)
        # if datacol in self.read_only:
        read_only_data = self.db.get(
            self.tablename,
            [self.col_keys[c] for c in self.read_only],
            self.pk,
            self.GetPkValue(row)
        )
        print(read_only_data)
        for n, value in enumerate(read_only_data):
            try:
                col = self.columns.index(self.read_only[n])
            except ValueError:
                self.data[row][self.read_only[n]] = value
            else:
                self.SetValue(row, col, value)

        return super().UpdateReadOnly(row)


class TestGrid(wxg.Grid):
    def __init__(self, parent, db):
        super().__init__(parent)

        table = GroupMaterialsTable(db)
        self.SetTable(table, True)
        self.read_only = table.read_only
        

        self.SetRowLabelSize(35)

        self.Bind(wxg.EVT_GRID_EDITOR_SHOWN, self.on_show_editor)
        self.Bind(wxg.EVT_GRID_CELL_CHANGED, self.on_cell_changed)
        self.Refresh()
    
    def on_cell_changed(self, evt):
        self.GetTable().OnCellChanged(evt.GetRow(), evt.GetCol())

    def on_show_editor(self, evt):
        """Veto edits in read only columns."""
        gridcol = evt.GetCol()
        col = self.GetTable().GetDataCol(gridcol)
        if col in self.read_only:
            label = self.GetTable().GetColLabelValue(gridcol)
            print(f"Column '{label}' is read only.")
            evt.Veto()
        evt.Skip()
    

    #     self.Bind(wxg.EVT_GRID_CELL_LEFT_DCLICK, self.on_left_dclick)
    
    # def on_left_dclick(self, evt):
    #     if self.CanEnableCellControl():
    #         self.EnableCellEditControl()


if __name__ == '__main__':
    app = wx.App()

    frame = wx.Frame(None, size=(800, 300))
    db = tb.OfferTables()
    grid = TestGrid(frame, db)
    frame.Show()

    app.MainLoop()
