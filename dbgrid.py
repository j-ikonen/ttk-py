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
from asteval import Interpreter

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
        # if self.is_changed:
        #     self.is_changed = False
        #     self.update_data(row)
        try:
            return self.data[row][self.columns[col]]
        except IndexError:
            return ""

    def SetValue(self, row, col, value):
        print(f"SetValue {row}, {col}, {value}")

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
                pass
                # self.is_changed = True
                # self.update_data(row)

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
                    # self.is_changed = True
                    
                    msg = wxg.GridTableMessage(
                        self,
                        wxg.GRIDTABLE_NOTIFY_ROWS_APPENDED,
                        1
                    )
                    self.GetView().ProcessTableMessage(msg)
                    # self.update_data(row)

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

    def update_data(self, row):
        """Return True if update is ok do do."""
        if self.fk_value is None:
            return False

        self.Clear()
        self.data.clear()
        print(f"Updating {type(self)}")
        return True

    def set_fk_value(self, value):
        """Set the foreign key value used to find grid data.

        Parameters
        ----------
        value : Iterable
            List of foreign keys for this table.
        """
        self.fk_value = value

        oldlen = self.GetNumberRows()
        # self.is_changed = True
        self.update_data(None)
        self.GetView().Update()
        newlen = self.GetNumberRows()
        self.change_number_rows(oldlen, newlen)
        # print(f"old: {oldlen}, new: {newlen}")

    def change_number_rows(self, old, new):
        
        if new > old:
            msg = wxg.GridTableMessage(
                self,
                wxg.GRIDTABLE_NOTIFY_ROWS_APPENDED,
                new - old
            )
        elif old > new:
            msg = wxg.GridTableMessage(
                self,
                wxg.GRIDTABLE_NOTIFY_ROWS_DELETED,
                new,
                old - new
            )
        else:
            return

        self.GetView().ProcessTableMessage(msg)

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

    def get_all_column_labels(self):
        return self.col_labels

    def get_visible(self):
        return self.db.get_visible(self.tablename)

    def get_visible_columns(self):
        return self.columns

    def show_column(self, col):
        self.columns.append(col)
        self.AppendCols(1)
        self.db.set_visible(self.tablename, col, True)
        self.GetView().Refresh()
        self.GetView().Update()
        return self.get_col_width(self.GetNumberCols() - 1)[0]

    def hide_column(self, col):
        gridcol = self.columns.index(col)
        del self.columns[gridcol]
        self.DeleteCols(gridcol, 1)
        self.db.set_visible(self.tablename, col, False)
        self.GetView().Refresh()
        self.GetView().Update()

    def DeleteCols(self, pos, numCols):
        # return super().DeleteCols(pos=pos, numCols=numCols)
        msg = wxg.GridTableMessage(
            self,
            wxg.GRIDTABLE_NOTIFY_COLS_DELETED,
            pos,
            numCols
        )
        self.GetView().ProcessTableMessage(msg)
        return True
    
    def AppendCols(self, numCols):
        # return super().AppendCols(numCols=numCols)
        msg = wxg.GridTableMessage(
            self,
            wxg.GRIDTABLE_NOTIFY_COLS_APPENDED,
            numCols
        )
        self.GetView().ProcessTableMessage(msg)
        return True

class GroupMaterialsTable(DatabaseGridTable):
    def __init__(self, db: tb.OfferTables):
        super().__init__(db)

        self.tablename = "offer_materials"
        setup = db.get_columns(self.tablename)
        self.pk = ["id"]
        self.fk = ["group_id"]
        self.fk_value = None
        self.pk_column = [0]
        # self.columns = [i for i in range(14)]
        self.columns = self.get_visible()
        self.col_keys = [val[tb.KEY] for val in setup]
        self.col_labels = [val[tb.LABEL] for val in setup]
        self.col_types = [val[tb.TYPE] for val in setup]
        self.col_widths = [val[tb.WIDTH] for val in setup]
        self.unique = []
        self.read_only = []
        # self.ro_dependency = [8, 9, 10, 11, 12]
        self.cant_update = [13]

        for n, val in enumerate(setup):
            if val[tb.UNIQUE] == 1:
                self.unique.append(n)
            if val[tb.READ_ONLY] == 1:
                self.read_only.append(n)

        # self.fk_value = ["uusi ryhmä"]

    def update_data(self, row):
        if super().update_data(row):

            res = self.db.get_omaterials(self.fk_value[0])
            for datarow in res:
                self.data.append(list(datarow))
        self.GetView().Refresh()

class GroupProductsTable(DatabaseGridTable):
    def __init__(self, db: tb.OfferTables):
        super().__init__(db)

        self.tablename = "offer_products"
        setup = db.get_columns(self.tablename)
        self.pk = ["id"]
        self.fk = ["group_id"]
        self.fk_value = None
        self.pk_column = [0]
        self.columns = self.get_visible()
        self.col_keys = [val[tb.KEY] for val in setup]
        self.col_labels = [val[tb.LABEL] for val in setup]
        self.col_types = [val[tb.TYPE] for val in setup]
        self.col_widths = [val[tb.WIDTH] for val in setup]
        self.unique = []
        self.read_only = []
        # self.ro_dependency = [8, 9, 10, 11, 12]
        self.cant_update = [13]

        for n, val in enumerate(setup):
            if val[tb.UNIQUE] == 1:
                self.unique.append(n)
            if val[tb.READ_ONLY] == 1:
                self.read_only.append(n)

        # self.fk_value = ["uusi ryhmä"]

    def update_data(self, row):
        if super().update_data(row):
            res = self.db.get_oproducts(self.fk_value[0])
            print("\n")
            for datarow in res:
                # print("PROD: {}".format(datarow[12]))
                # print(datarow)
                self.data.append(list(datarow))

            self.GetView().Refresh()

class GroupPartsTable(DatabaseGridTable):
    def __init__(self, db: tb.OfferTables):
        super().__init__(db)

        self.tablename = "offer_parts"
        setup = db.get_columns(self.tablename)
        self.pk = ["id"]
        self.fk = ["product_id"]
        self.fk_value = None
        self.pk_column = [0]
        self.columns = self.get_visible()
        self.col_keys = [val[tb.KEY] for val in setup]
        self.col_labels = [val[tb.LABEL] for val in setup]
        self.col_types = [val[tb.TYPE] for val in setup]
        self.col_widths = [val[tb.WIDTH] for val in setup]
        self.unique = []
        self.read_only = []
        # self.ro_dependency = [8, 9, 10, 11, 12]
        self.cant_update = []
        self.coded = [11, 12, 13]
        self.coded_tar = [8, 9, 10]
        self.aeval = Interpreter()
        self.parse_done = False
        self.code2col = {
            "määrä": 4,
            "leveys": 8,
            "pituus": 9,
            "mpaksuus": 15,
            "mhinta": 16,
            "tleveys": 17,
            "tkorkeus": 18,
            "tsyvyys": 19
        }

        for n, val in enumerate(setup):
            if val[tb.UNIQUE] == 1:
                self.unique.append(n)
            if val[tb.READ_ONLY] == 1:
                self.read_only.append(n)

        # self.fk_value = ["uusi ryhmä"]

    def update_data(self, row):
        if super().update_data(row):

            res = self.db.get_oparts(self.fk_value[0])
            print("\n")
            for datarow in res:
                self.data.append(list(datarow))
            self.GetView().Refresh()

    # def GetValue(self, row, col):
    #     value = super().GetValue(row, col)
    #     datacol = self.GetDataCol(col)
    #     # Get value from a code cell.
    #     if datacol in self.coded:
    #         val_from_code = self.parse_code(row, value)
    #         if val_from_code is not None:
    #             tar_col = self.columns.index(self.coded_tar[self.coded.index(datacol)])
    #             old_value = super().GetValue(row, tar_col)
    #             if val_from_code != old_value:
    #                 print(f"parsed new, old: {val_from_code}, {old_value}")
    #                 self.SetValue(row, tar_col, val_from_code)

    #     # Get value from cell that receives value from code.
    #     elif datacol in self.coded_tar:
    #         code_col = self.coded[self.coded_tar.index(datacol)]
    #         code = super().GetValue(row, code_col)
    #         parsed_value = self.parse_code(row, code)
    #         if parsed_value is not None:
    #             old_value = super().GetValue(row, datacol)
    #             if parsed_value != old_value:
    #                 print(f"parsed new, old: {parsed_value}, {old_value}")
    #                 self.SetValue(row, datacol, parsed_value)
    #                 return parsed_value
    #     return value

    def parse_code(self, row, code: str):
        if code is not None and len(code) > 0 and code[0] == "=":
            parsed_code: str = code[1:]
            codelist = parsed_code.split(" ")
            for item in codelist:
                if item[0] == '"':
                    try:
                        (source, colcode) = item.split(".")
                        # print(f"{source}, {colcode}")
                    except ValueError:
                        print('Syntax to refer to another part: "part".sarake')
                        src_row = row
                        colcode = item
                    else:
                        src_row = self.find_row(source.strip('"'))
                        if src_row is None:
                            src_row = row
                else:
                    src_row = row
                    colcode = item

                try:
                    # print(f"code2col: {self.code2col}, colcode: {colcode}")
                    col = self.code2col[colcode]
                except:
                    itemval = 0.0
                else:
                    itemval = str(self.data[src_row][col])
                    parsed_code = parsed_code.replace(item, itemval)

            returnvalue = self.aeval(parsed_code)
            # print("GroupPartsTable.parse_code")
            # print("\tcode:  {}".format(parsed_code))
            # print("\tvalue: {}".format(returnvalue))
            return returnvalue
        else:
            return None

    def find_row(self, value):
        # print(f"FIND ROW: {value}")
        for row, datarow in enumerate(self.data):
            if datarow[2] == value:
                return row
        return None

class GroupPredefsTable(DatabaseGridTable):
    def __init__(self, db: tb.OfferTables):
        super().__init__(db)

        self.tablename = "offer_predefs"
        setup = db.get_columns(self.tablename)
        self.pk = ["id"]
        self.fk = ["group_id"]
        self.fk_value = None
        self.pk_column = [0]
        self.columns = self.get_visible()
        self.col_keys = [val[tb.KEY] for val in setup]
        self.col_labels = [val[tb.LABEL] for val in setup]
        self.col_types = [val[tb.TYPE] for val in setup]
        self.col_widths = [val[tb.WIDTH] for val in setup]
        self.unique = []
        self.read_only = []
        # self.ro_dependency = [8, 9, 10, 11, 12]
        self.cant_update = []

        for n, val in enumerate(setup):
            if val[tb.UNIQUE] == 1:
                self.unique.append(n)
            if val[tb.READ_ONLY] == 1:
                self.read_only.append(n)

        # self.fk_value = ["uusi ryhmä"]

    def update_data(self, row):
        if super().update_data(row):

            res = self.db.get_opredefs(self.fk_value[0])
            for datarow in res:
                self.data.append(list(datarow))
            self.GetView().Refresh()


class TestGrid(wxg.Grid):
    def __init__(self, parent, db, name):
        super().__init__(parent, style=wx.WANTS_CHARS|wx.HD_ALLOW_REORDER)

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
        self.labels = table.get_all_column_labels()
        self.col_ids = wx.NewIdRef(len(self.labels))

        for col in range(self.GetNumberCols()):
            width = table.get_col_width(col)
            self.SetColSize(col, width[0])

        self.SetRowLabelSize(35)
        self.EnableDragColMove(True)
        # self.UseNativeColHeader(True)


        self.Bind(wx.EVT_MENU_RANGE, self.on_col_menu, id=self.col_ids[0], id2=self.col_ids[-1])
        self.Bind(wxg.EVT_GRID_EDITOR_SHOWN, self.on_show_editor)
        self.Bind(wxg.EVT_GRID_CELL_CHANGED, self.on_cell_changed)
        self.Bind(wxg.EVT_GRID_COL_SIZE, self.on_col_size)
        self.Bind(wxg.EVT_GRID_CMD_LABEL_RIGHT_CLICK, self.on_label_menu)
        self.Bind(wxg.EVT_GRID_COL_MOVE, self.on_col_move)
        self.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        # self.Refresh()
    
    def on_cell_changed(self, evt):
        """Update the data of this grid on edit."""
        self.GetTable().update_data(None)
        evt.Skip()

    def on_col_size(self, evt):
        """Save new columns size to columns table."""
        col = evt.GetRowOrCol()
        width = self.GetColSize(col)
        self.GetTable().set_col_width(col, width)
        evt.Skip()

    def on_col_move(self, evt):
        """Save the new order."""
        col = evt.GetCol()
        pos = self.GetColPos(col)
        wx.CallAfter(self.col_moved, col, pos)
        # print("NEW COLUMN ORDER FOR id: {}, old_pos: {}".format(col, pos))

    def col_moved(self, col_id, old_pos):
        pass
        # colpos = self.GetColPos(col_id)
        # print("New col pos: {}, old pos: {}".format(colpos, old_pos))

    def on_key_down(self, evt):
        print("KEY DOWN")
        evt.Skip()

    def on_label_menu(self, evt):
        """Open menu to select visible columns."""
        print("LABEL MENU")
        menu = wx.Menu()
        table = self.GetTable()

        for n, colid in enumerate(self.col_ids):
            menu.AppendCheckItem(colid, self.labels[n], "Muuta sarakkeen näkyvyyttä")
        
        columns = table.get_visible_columns()
        for col in columns:
            menu.Check(self.col_ids[col], True)
        
        self.PopupMenu(menu)
        menu.Destroy()
        evt.Skip()
    
    def on_col_menu(self, evt):
        """Show or hide the checked column."""
        is_checked = evt.IsChecked()
        col = self.col_ids.index(evt.GetId())
        table = self.GetTable()
        print("check: {}, col: {}".format(is_checked, col))
        if is_checked:
            w = table.show_column(col)
            gridcol = table.columns.index(col)
            self.SetColSize(gridcol, w)
            print(w)
            print(gridcol)
        else:
            table.hide_column(col)

    def on_show_editor(self, evt):
        """Veto edits in read only columns."""
        gridcol = evt.GetCol()
        col = self.GetTable().GetDataCol(gridcol)
        if col in self.read_only:
            label = self.GetTable().GetColLabelValue(gridcol)
            print(f"Column '{label}' is read only.")
            evt.Veto()
        evt.Skip()

    def set_fk_value(self, fk):
        """Set the foreign key for the table of this grid."""
        self.GetTable().set_fk_value(fk)


class GroupPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)

        self.grid_pdef = TestGrid(self, db, "offer_predefs")
        self.grid_mats = TestGrid(self, db, "offer_materials")
        self.grid_prod = TestGrid(self, db, "offer_products")
        self.grid_part = TestGrid(self, db, "offer_parts")

        self.grid_pdef.set_fk_value(["RyhmäID"])
        self.grid_mats.set_fk_value(["RyhmäID"])
        self.grid_prod.set_fk_value(["RyhmäID"])
        self.grid_part.set_fk_value(None)

        self.Bind(wxg.EVT_GRID_SELECT_CELL, self.on_product_selection, self.grid_prod)
        self.Bind(wxg.EVT_GRID_CELL_CHANGED, self.on_cell_changed, self.grid_pdef)
        self.Bind(wxg.EVT_GRID_CELL_CHANGED, self.on_cell_changed, self.grid_mats)
        self.Bind(wxg.EVT_GRID_CELL_CHANGED, self.on_cell_changed, self.grid_prod)
        self.Bind(wxg.EVT_GRID_CELL_CHANGED, self.on_cell_changed, self.grid_part)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.grid_mats, 1, wx.EXPAND)
        sizer.Add(self.grid_prod, 1, wx.EXPAND)
        sizer.Add(self.grid_part, 1, wx.EXPAND)
        sizer.Add(self.grid_pdef, 1, wx.EXPAND)
        self.SetSizer(sizer)

    def on_product_selection(self, evt):
        row = evt.GetRow()
        product_id = self.grid_prod.GetTable().GetPkValue(row)
        self.grid_part.set_fk_value(product_id)

    def on_cell_changed(self, evt):
        eobj = evt.GetEventObject()
        if eobj == self.grid_pdef or eobj == self.grid_mats:
            print("CHANGE IN GRID PDEF")
            self.grid_part.GetTable().update_data(None)
            # grid_part.Update required for products to get updated coded values.
            self.grid_part.Update()
            self.grid_prod.GetTable().update_data(None)
            self.grid_prod.Update()

        elif eobj == self.grid_prod:
            print("CHANGE IN GRID PROD")
            self.grid_part.GetTable().update_data(None)
            self.grid_part.Update()
            self.grid_prod.GetTable().update_data(None)

        elif eobj == self.grid_part:
            print("CHANGE IN GRID PART")
            self.grid_part.Update()
            self.grid_prod.GetTable().update_data(None)
            # self.grid_part.GetTable().update_data(None)

        evt.Skip()


if __name__ == '__main__':
    app = wx.App()

    frame = wx.Frame(None, size=(1300, 1000))
    db = tb.OfferTables()
    panel = GroupPanel(frame)
    frame.Show()

    app.MainLoop()
