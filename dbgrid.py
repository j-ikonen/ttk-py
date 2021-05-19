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
        self.is_changed = True
        self.tablename = None
        self.pk = []
        self.fk = []
        self.fk_value = None
        self.pk_column = []
        self.columns = []
        self.col_keys = []
        self.col_labels = []
        self.col_types = []
        self.col_widths = []
        self.unique = []
        self.read_only = []
        self.ro_dependency = []
        self.cant_update = []

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
        # print(f"GetValue {row}, {col}")
        if self.is_changed:
            self.update_data(row)
        try:
            return self.data[row][self.columns[col]]
        except IndexError:
            return ""

    def SetValue(self, row, col, value):
        # print(f"SetValue {row}, {col}, {value}")

        if self.fk_value is None:
            print(f"Foreign key {self.fk} is not defined.")
            return

        tablecol = self.columns[col]

        if tablecol in self.unique:
            for rowdata in self.data:
                if rowdata[tablecol] == value:
                    print(f"Column is unique, '{value}' already exists.")
                    return

        elif tablecol not in self.cant_update:

            # Update requires a valid existing primary key.
            pkval = self.GetPkValue(row)
            if pkval is not None:
                update_success = self.db.update_one(
                    self.tablename,
                    self.col_keys[tablecol],
                    self.pk,
                    [value] + pkval
                )
            else:
                update_success = False


            if update_success:
                self.is_changed = True

            else:
                new_id = [str(ObjectId())]
                try:
                    insert_success = self.db.insert(
                        self.tablename,
                        self.pk + self.fk + [self.col_keys[tablecol]],
                        new_id + self.fk_value + [value]
                    )
                except KeyError:
                    print(f"Column {tablecol} not defined properly for insert.")
                    insert_success = False

                if insert_success:
                    self.is_changed = True
                    
                    msg = wxg.GridTableMessage(
                        self,
                        wxg.GRIDTABLE_NOTIFY_ROWS_APPENDED,
                        1
                    )
                    self.GetView().ProcessTableMessage(msg)

                else:
                    print(f"{type(self)}.SetValue insert not successful.")


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
            try:
                pk_val.append(self.data[row][idx])
            except IndexError:
                return None
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
    
    # def UpdateReadOnly(self, row):
    #     return
    
    # def ChangedDependency(self, col):
    #     datacol = self.GetDataCol(col)
    #     if datacol in self.ro_dependency:
    #         return True
    #     else:
    #         return False

    # def OnCellChanged(self, row, col):
    #     if self.fk_value is None:
    #         return

    #     elif self.ChangedDependency(col):
    #         self.UpdateReadOnly(row)

    # def UpdateReadOnly(self, row):
    #     read_only_data = self.db.get(
    #         self.tablename,
    #         [self.col_keys[c] for c in self.read_only],
    #         self.pk,
    #         self.GetPkValue(row)
    #     )
    #     print(read_only_data)
    #     for n, value in enumerate(read_only_data):
    #         try:
    #             col = self.columns.index(self.read_only[n])
    #             if self.data[row][self.read_only[n]] == value:
    #                 continue

    #         except ValueError:
    #             self.data[row][self.read_only[n]] = value
    #         else:
    #             self.SetValue(row, col, value)

        # return super().UpdateReadOnly(row)

    def update_data(self, row):
        self.is_changed = False
        return
    
    def set_fk_value(self, value):
        """Set the foreign key value used to find grid data.

        Parameters
        ----------
        value : Iterable
            List of foreign keys for this table.
        """
        self.fk_value = value

    def get_col_width(self, col):
        datacol = self.GetDataCol(col)
        width = self.db.get(
            "columns",
            ["width"],
            ["tablename", "key"],
            [self.tablename, self.col_keys[datacol]]
        )
        return width

    def set_col_width(self, col, width):
        datacol = self.GetDataCol(col)
        # self.col_widths[datacol] = width
        self.db.update_one(
            "columns",
            "width",
            ["tablename", "key"],
            [width, self.tablename, self.col_keys[datacol]]
        )


class GroupMaterialsTable(DatabaseGridTable):
    def __init__(self, db: tb.OfferTables):
        super().__init__(db)

        self.tablename = "offer_materials"
        setup = db.get_columns(self.tablename)
        self.pk = ["id"]
        self.fk = ["group_id"]
        self.fk_value = None
        self.pk_column = [0]
        self.columns = [i for i in range(14)]
        self.col_keys = [val[tb.KEY] for val in setup]
        self.col_labels = [val[tb.LABEL] for val in setup]
        self.col_types = [val[tb.TYPE] for val in setup]
        self.col_widths = [val[tb.WIDTH] for val in setup]
        self.unique = []
        self.read_only = []
        self.ro_dependency = [8, 9, 10, 11, 12]
        self.cant_update = [13]

        for n, val in enumerate(setup):
            if val[tb.UNIQUE] == 1:
                self.unique.append(n)
            if val[tb.READ_ONLY] == 1:
                self.read_only.append(n)

        # self.fk_value = ["uusi ryhmä"]

    def update_data(self, row):
        self.data.clear()
        if self.fk_value is None:
            return

        print("UPDATE DATA")
        res = self.db.get_omaterials(self.fk_value[0])
        for datarow in res:
            self.data.append(list(datarow))

        return super().update_data(row)


class GroupProductsTable(DatabaseGridTable):
    def __init__(self, db: tb.OfferTables):
        super().__init__(db)


class GroupPartsTable(DatabaseGridTable):
    def __init__(self, db: tb.OfferTables):
        super().__init__(db)


class GroupPredefsTable(DatabaseGridTable):
    def __init__(self, db: tb.OfferTables):
        super().__init__(db)


class TestGrid(wxg.Grid):
    def __init__(self, parent, db, name):
        super().__init__(parent)

        table = None
        if name == "offer_materials":
            table = GroupMaterialsTable(db)
        elif name == "offer_products":
            table = GroupProductsTable(db)
        elif name == "offer_parts":
            table = GroupPartsTable(db)
        elif name == "offer_predefs":
            table = GroupPredefsTable(db)

        self.SetTable(table, True)
        self.read_only = table.read_only
        table.set_fk_value(["TuoteID"])

        for col in range(self.GetNumberCols()):
            width = table.get_col_width(col)
            self.SetColSize(col, width[0])

        self.SetRowLabelSize(35)

        self.Bind(wxg.EVT_GRID_EDITOR_SHOWN, self.on_show_editor)
        self.Bind(wxg.EVT_GRID_CELL_CHANGED, self.on_cell_changed)
        self.Bind(wxg.EVT_GRID_COL_SIZE, self.on_col_size)
        self.Refresh()
    
    def on_cell_changed(self, evt):
        # self.GetTable().OnCellChanged(evt.GetRow(), evt.GetCol())
        pass

    def on_col_size(self, evt):
        # width = evt.GetWidth()
        col = evt.GetRowOrCol()
        width = self.GetColSize(col)
        self.GetTable().set_col_width(col, width)

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

    frame = wx.Frame(None, size=(1300, 1000))
    db = tb.OfferTables()

    panel = wx.Panel(frame)
    grid_mats = TestGrid(panel, db, "offer_materials")
    grid_prod = TestGrid(panel, db, "offer_products")
    grid_part = TestGrid(panel, db, "offer_parts")
    grid_pdef = TestGrid(panel, db, "offer_predefs")
    sizer = wx.BoxSizer(wx.VERTICAL)
    sizer.Add(grid_mats, 1, wx.EXPAND)
    sizer.Add(grid_prod, 1, wx.EXPAND)
    sizer.Add(grid_part, 1, wx.EXPAND)
    sizer.Add(grid_pdef, 1, wx.EXPAND)
    panel.SetSizer(sizer)
    frame.Show()

    app.MainLoop()
