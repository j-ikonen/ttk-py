"""
TODO
----
"""

from dialog import ConfirmDialog
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
        self.dbtablename = None
        self.pk = []
        self.fk = []
        self.fk_value = None
        self.pk_column = []
        self.columns = []
        self.col_keys = []
        self.col_labels = []
        self.col_visible = []
        self.col_types = []
        self.col_widths = []
        self.unique = []
        self.read_only = []
        self.ro_dependency = []
        self.cant_update = []
        self.dbcols = []

    def GetNumberRows(self):
        return len(self.data) + 1

    def GetNumberCols(self):
        return len(self.col_labels)

    def GetDataCol(self, col):
        # return col
        return col

    def IsEmptyCell(self, row, col):
        try:
            value = self.data[row][col]
        except IndexError:
            return True

        if value is None or value == "":
            return True
        else:
            return False

    def GetValue(self, row, col):
        try:
            return self.data[row][col]
        except IndexError:
            return ""

    def SetValue(self, row, col, value):
        # Can not set a value if foreign key is not defined.
        if self.fk_value is None:
            print(f"Foreign key {self.fk} is not defined.")
            return

        # Can not set a value if value is a dublicate in a unique column.
        # col = self.GetDataCol(col)
        if col in self.unique and self.is_dublicate(col, value):
            print(f"Column {self.GetColLabelValue(col)} is unique, " +
                  f"'{value}' already exists.")

        # Set the value to db if possible.
        elif col not in self.cant_update:
            pkval = self.GetPkValue(row)

            # Update requires a valid existing primary key.
            if pkval is not None:
                self.db.update_one(
                    self.tablename,
                    self.col_keys[col],
                    self.pk,
                    [value] + pkval
                )
            # No pk value in the row so insert new row to db.
            else:
                self.append_new_row(col, value)

    def is_dublicate(self, col, value):
        """Return True if the column contains the value."""
        for rowdata in self.data:
            if rowdata[col] == value:
                return True
        return False

    def append_new_row(self, col, value):
        """Append a new row by inserting it to database.

        Alert the grid to update the display on successful db insert.

        Parameters
        ----------
        col : int
            Column for value that is entered to db with insert.
        value : Any
            Value to go with insert.

        Returns
        -------
        bool
            True on successful insert, else otherwise.
        """
        new_id = [str(ObjectId())]
        try:
            success = self.db.insert(
                self.tablename,
                self.pk + self.fk + [self.col_keys[col]],
                new_id + self.fk_value + [value]
            )
        except KeyError as e:
            print(f"KeyError: {e} in DatabaseGridTable.append_new_row\n" +
                  f"Column {col} not defined properly for insert.\n" +
                  f"pk: {self.pk}, fk: {self.fk}, col: {col}, " +
                  f"key: {self.col_keys[col]}, fk_val: {self.fk_value}, val: {value}")
            return False
        else:
            if success:
                self.AppendRows(1)
            else:
                print(f"{type(self)}.append_new_row insert not successful.")

            return success

    def append_rows(self, data, replace_id=True):
        """Append a given row of data to table.

        Replaces the id with new one 

        Parameters
        ----------
        rowdata : list
            List of data to append.
        replace_id : bool
            True to replace id for appending copied rows.
        """
        dbkeys = [key for n, key in enumerate(self.col_keys) if n in self.dbcols]
        values = []
        for rowdata in data:
            rowvals = []
            for col in self.dbcols:
                if col in self.pk_column and replace_id:
                    rowvals.append(str(ObjectId()))
                else:
                    rowvals.append(rowdata[col])
            values.append(rowvals)

        self.db.insert(self.tablename, dbkeys, values, True)
        self.update_data(None)
        self.AppendRows(len(data))

    def AppendRows(self, numRows):
        """Notify the grid of appended rows, post size event to refresh new size."""
        msg = wxg.GridTableMessage(
            self,
            wxg.GRIDTABLE_NOTIFY_ROWS_APPENDED,
            numRows
        )
        self.GetView().ProcessTableMessage(msg)
        self.GetView().PostSizeEventToParent()

    def GetColLabelValue(self, col):
        return self.col_labels[col]
    
    def GetTypeName(self, row, col):
        return self.col_types[col]
    
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

    def get_dbpk_value(self, row):
        pk_val = []
        for key in self.dbpk:
            col = self.col_keys.index(key)
            try:
                pk_val.append(self.data[row][col])
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
        # print(f"Updating {type(self)}")
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
        self.update_data(None)
        self.GetView().ForceRefresh()
        newlen = self.GetNumberRows()
        self.change_number_rows(oldlen, newlen)

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
        self.GetView().PostSizeEventToParent()

    def get_col_width(self, col):
        datacol = self.GetDataCol(col)
        width = self.db.get(
            "columns",
            ["width"],
            ["tablename", "key"],
            [self.tablename, self.col_keys[datacol]]
        )
        return width[0]

    def set_col_width(self, col, width):
        datacol = self.GetDataCol(col)
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
        return self.col_visible
    # def get_visible_columns(self):
    #     return self.columns

    def show_column(self, col):
        # self.columns.append(col)
        # self.AppendCols(1)
        if self.db.set_visible(self.tablename, col, True):
            width = self.get_col_width(col)
            if width == 0:
                width = 60
            self.col_visible[col] = True
            self.GetView().SetColSize(col, width)
        # self.GetView().ForceRefresh()
            return width

    def hide_column(self, col):
        # gridcol = self.columns.index(col)
        # del self.columns[gridcol]
        if self.db.set_visible(self.tablename, col, False):
            self.GetView().HideCol(col)
            self.col_visible[col] = False
        # self.DeleteCols(gridcol, 1)
        # self.GetView().ForceRefresh()

    def is_col_visible(self, col):
        return self.col_visible[col]

    def set_visibility(self):
        """Set the visibility status of a list of columns."""
        for col in range(self.GetNumberCols()):
            if self.col_visible[col]:
                self.show_column(col)
            else:
                self.hide_column(col)

    def DeleteRows(self, pos, numRows):
        """Delete the rows and their data."""
        for row in range(pos, pos + numRows):
            pkval = self.GetPkValue(row)
            if pkval is not None:
                self.db.delete(self.tablename, self.pk, pkval)

        for n in range(numRows):
            del self.data[pos]

        msg = wxg.GridTableMessage(
            self,
            wxg.GRIDTABLE_NOTIFY_ROWS_DELETED,
            pos,
            numRows
        )
        self.GetView().ProcessTableMessage(msg)
        self.GetView().PostSizeEventToParent()
        return True

    def DeleteCols(self, pos, numCols):
        msg = wxg.GridTableMessage(
            self,
            wxg.GRIDTABLE_NOTIFY_COLS_DELETED,
            pos,
            numCols
        )
        self.GetView().ProcessTableMessage(msg)
        self.GetView().PostSizeEventToParent()
        return True
    
    def AppendCols(self, numCols):
        msg = wxg.GridTableMessage(
            self,
            wxg.GRIDTABLE_NOTIFY_COLS_APPENDED,
            numCols
        )
        self.GetView().ProcessTableMessage(msg)
        self.GetView().PostSizeEventToParent()
        return True

    def get_rowdata(self, row):
        """Return a copy of the data in given row."""
        return [value for value in self.data[row]]

    def get_blockdata(self, block):
        """Return the data contained in given block."""
        data = []
        for row in range(block.GetTopRow(), block.GetBottomRow() + 1):
            rowdata = []
            for col in range(block.GetLeftCol(), block.GetRightCol() + 1):
                rowdata.append(self.GetValue(row, col))
            data.append(rowdata)
        return data

    def get_data(self):
        """Get a copy of the data."""
        return [[v for v in row] for row in self.data]

    def get_fk_value(self):
        """Return value of foreign key."""
        return self.fk_value

    def save_to_db(self, rows, key, value):
        """Save the given rows to database.
        
        Open confirm dialog for replace if row exists.

        Parameters
        ----------
        rows : list
            List of row indexes.
        key : Iterable
            Key to add to all rows.
        value : Iterable
            Value to add to key at all rows.

        Returns
        -------
        bool
            True if successul.
        """
        if self.dbtablename is not None:
            keys = self.save_keys
            if key is not None:
                keys += key

            
            todb = []
            for row in rows:
                res = self.db.get(
                    self.dbtablename,
                    self.dbpk,
                    self.dbpk,
                    self.get_dbpk_value(row)
                )
                isok = True
                if len(res) > 0:
                    msg = ("Koodi '{}' löytyy tietokannasta.".format(res[0])
                          +" Korvataanko valitulla rivillä?")
                    title = "Korvataanko?"
                    with ConfirmDialog(self.GetView(), title, msg) as dlg:
                        if dlg.ShowModal() != wx.ID_OK:
                            isok = False

                if isok:
                    datarow = []
                    for k in self.save_keys:
                        datarow.append(self.data[row][self.col_keys.index(k)])

                    if value is not None:
                        datarow.append(value)
                    
                    todb.append(datarow)

            return self.db.insert(self.dbtablename, keys, todb, True, True)
        else:
            return False

    def can_save_to_db(self):
        """Return True if this table can save the data to a database."""
        return False if self.dbtablename is None else True

    def find_value(self, key, find_key, find_value):
        """Return a value at col key and row where col find_key has value find_value."""
        col = self.col_keys.index(key)
        fcol = self.col_keys.index(find_key)
        for rowdata in self.data:
            print("{} == {} ?".format(rowdata[fcol], find_value))
            if rowdata[fcol] == find_value:
                return rowdata[col]
        return None

class GroupMaterialsTable(DatabaseGridTable):
    def __init__(self, db: tb.OfferTables):
        super().__init__(db)

        self.tablename = "offer_materials"
        self.dbtablename = "materials"
        setup = db.get_columns(self.tablename)
        self.pk = ["id"]
        self.fk = ["group_id"]
        self.fk_value = None
        self.pk_column = [0]
        # self.columns = self.get_visible()
        self.columns = [n for n in range(len(setup))]
        self.col_visible = self.get_visible()
        self.col_keys = [val[tb.KEY] for val in setup]
        self.col_labels = [val[tb.LABEL] for val in setup]
        self.col_types = [val[tb.TYPE] for val in setup]
        self.col_widths = [val[tb.WIDTH] for val in setup]
        self.unique = []
        self.read_only = []
        self.cant_update = [13]
        self.dbcols = [n for n in range(13)]    # offer_materials
        self.dbpk = ["code"]
        self.save_keys = [
            "code",        
            "category",    
            "desc",        
            "prod",        
            "thickness",   
            "unit",        
            "cost",        
            "add_cost",    
            "edg_cost",    
            "loss",        
            "discount" 
        ]                  # materials

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
        self.GetView().ForceRefresh()

class GroupProductsTable(DatabaseGridTable):
    def __init__(self, db: tb.OfferTables):
        super().__init__(db)

        self.tablename = "offer_products"
        setup = db.get_columns(self.tablename)
        self.pk = ["id"]
        self.fk = ["group_id"]
        self.fk_value = None
        self.pk_column = [0]
        # self.columns = self.get_visible()
        self.columns = [n for n in range(len(setup))]
        self.col_visible = self.get_visible()
        self.col_keys = [val[tb.KEY] for val in setup]
        self.col_labels = [val[tb.LABEL] for val in setup]
        self.col_types = [val[tb.TYPE] for val in setup]
        self.col_widths = [val[tb.WIDTH] for val in setup]
        self.unique = []
        self.read_only = []
        # self.ro_dependency = [8, 9, 10, 11, 12]
        self.cant_update = [13]
        self.dbcols = [n for n in range(12)]
        self.dbtablename = "products"
        self.dbpk = ["code"]
        self.save_keys = [
            "code",
            "category",
            "desc",
            "prod",
            "inst_unit",
            "width",
            "height",
            "depth",
            "work_time"
        ]
        for n, val in enumerate(setup):
            if val[tb.UNIQUE] == 1:
                self.unique.append(n)
            if val[tb.READ_ONLY] == 1:
                self.read_only.append(n)

        # self.fk_value = ["uusi ryhmä"]

    def update_data(self, row):
        if super().update_data(row):
            res = self.db.get_oproducts(self.fk_value[0])
            for datarow in res:
                self.data.append(list(datarow))

            self.GetView().ForceRefresh()


class GroupPartsTable(DatabaseGridTable):
    def __init__(self, db: tb.OfferTables):
        super().__init__(db)

        self.tablename = "offer_parts"
        setup = db.get_columns(self.tablename)
        self.pk = ["id"]
        self.fk = ["product_id"]
        self.fk_value = None
        self.pk_column = [0]
        # self.columns = self.get_visible()
        self.columns = [n for n in range(len(setup))]
        self.col_visible = self.get_visible()
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
        self.dbcols = [n for n in range(14)]
        self.dbtablename = "parts"
        self.dbpk = ["part", "product_code"]
        self.save_keys = [
            "code",
            "part",
            "desc",
            "default_mat",
            "width",
            "length",
            "code_width",
            "code_length",
            "cost"
        ]
        # self.code2col = {
        #     "määrä": 4,
        #     "leveys": 8,
        #     "pituus": 9,
        #     "mpaksuus": 15,
        #     "mhinta": 16,
        #     "tleveys": 17,
        #     "tkorkeus": 18,
        #     "tsyvyys": 19
        # }

        for n, val in enumerate(setup):
            if val[tb.UNIQUE] == 1:
                self.unique.append(n)
            if val[tb.READ_ONLY] == 1:
                self.read_only.append(n)

        # self.fk_value = ["uusi ryhmä"]

    def update_data(self, row):
        if super().update_data(row):
            res = self.db.get_oparts(self.fk_value[0])
            for datarow in res:
                self.data.append(list(datarow))
            self.GetView().ForceRefresh()


class GroupPredefsTable(DatabaseGridTable):
    def __init__(self, db: tb.OfferTables):
        super().__init__(db)

        self.tablename = "offer_predefs"
        setup = db.get_columns(self.tablename)
        self.pk = ["id"]
        self.fk = ["group_id"]
        self.fk_value = None
        self.pk_column = [0]
        # self.columns = self.get_visible()
        self.columns = [n for n in range(len(setup))]
        self.col_visible = self.get_visible()
        self.col_keys = [val[tb.KEY] for val in setup]
        self.col_labels = [val[tb.LABEL] for val in setup]
        self.col_types = [val[tb.TYPE] for val in setup]
        self.col_widths = [val[tb.WIDTH] for val in setup]
        self.unique = []
        self.read_only = []
        # self.ro_dependency = [8, 9, 10, 11, 12]
        self.cant_update = []
        self.dbcols = [n for n in range(4)]

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
            self.GetView().ForceRefresh()


class DbGrid(wxg.Grid):
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
        self.cursor_text = ""
        self.copy_rows = []
        self.copy_cells = []
        self.history = {}

        # for col in range(self.GetNumberCols()):
        #     width = table.get_col_width(col)
        #     self.SetColSize(col, width)
        table.set_visibility()

        self.SetRowLabelSize(35)
        self.EnableDragColMove(True)
        # self.EnableDragRowSize(False)
        # self.SetBackgroundColour((220, 200, 255))
        # self.SetLabelBackgroundColour((220, 200, 255))
        self.SetLabelBackgroundColour((225, 225, 255))
        self.SetForegroundColour((255,255,255))
        # self.SetGridLineColour((220, 150, 255))
        # self.SetDefaultCellBackgroundColour((235, 220, 255))
        # self.UseNativeColHeader(True)
        # colwin: wx.Window = self.GetGridColLabelWindow()
        # colwin.SetToolTip("LABEL")

        self.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        self.Bind(wx.EVT_MENU_RANGE, self.on_col_menu, id=self.col_ids[0], id2=self.col_ids[-1])
        
        self.Bind(wx.EVT_MENU, self.on_copy, id=wx.ID_COPY)
        self.Bind(wx.EVT_MENU, self.on_cut, id=wx.ID_CUT)
        self.Bind(wx.EVT_MENU, self.on_paste, id=wx.ID_PASTE)
        self.Bind(wx.EVT_MENU, self.on_undo, id=wx.ID_UNDO)
        self.Bind(wx.EVT_MENU, self.on_delete, id=wx.ID_DELETE)

        self.Bind(wxg.EVT_GRID_EDITOR_SHOWN, self.on_show_editor)
        self.Bind(wxg.EVT_GRID_SELECT_CELL, self.on_cell_selected)
        self.Bind(wxg.EVT_GRID_CELL_CHANGING, self.on_cell_changing)
        self.Bind(wxg.EVT_GRID_CELL_CHANGED, self.on_cell_changed)
        self.Bind(wxg.EVT_GRID_COL_SIZE, self.on_col_size)
        self.Bind(wxg.EVT_GRID_COL_MOVE, self.on_col_move)
        self.Bind(wxg.EVT_GRID_CELL_RIGHT_CLICK, self.on_context_menu)
        self.Bind(wxg.EVT_GRID_CMD_LABEL_RIGHT_CLICK, self.on_label_menu)
        self.Bind(wxg.EVT_GRID_LABEL_LEFT_CLICK, self.on_label_lclick)

    def copy(self):
        """Copy the selected rows or blocks. Clears the other.
        
        parent.copy var in form:
        Selected block: [ rows in block: [ cols in block: [] ] ]
        """
        selected = self.GetSelectedRows()
        selected.sort()
        self.copy_rows.clear()
        self.copy_cells.clear()
        if len(selected) == 0:
            selected_blocks = self.GetSelectedBlocks()
            parent = self.GetParent()
            parent.copy.clear()
            has_sel = False
            for block in selected_blocks:
                has_sel = True
                blockdata = self.GetTable().get_blockdata(block)
                parent.copy.append(blockdata)
            if not has_sel:
                crd = self.GetGridCursorCoords()
                value = self.GetTable().GetValue(crd.GetRow(), crd.GetCol())
                parent.copy.append([value])
            # print(parent.copy)
        else:
            for row in selected:
                rowdata = self.GetTable().get_rowdata(row)
                self.copy_rows.append(rowdata)

    def cut(self):
        """Cut the selected cells."""
        self.copy()
        self.delete()

    def delete(self):
        """Delete the selected rows. Return True if deleted something."""
        if self.IsSelection():
            self.save_state()
        else:
            return False

        selected = self.GetSelectedRows()
        table = self.GetTable()
        if len(selected) == 0:
            self.clear_selected()

        else:
            selected.sort(reverse=True)
            # Do not delete the empty last row.
            if selected[0] == self.GetNumberRows() - 1:
                del selected[0]

            for row in selected:
                table.DeleteRows(row, 1)

        table.update_data(None)
        self.GetParent().update_depended_grids(self)
        return True

    def paste(self):
        """Paste the copied values to selection.

        Depending on if last copy was on rows or blocks,
        append all copied rows to end of grid or
        paste as many blocks as there are selected blocks.
        """
        parent = self.GetParent()
        if len(parent.copy) > 0:
            table: DatabaseGridTable = self.GetTable()
            self.save_state()
            coords = [
                (block.GetTopRow(), block.GetLeftCol()) 
                for block in self.GetSelectedBlocks()
            ]
            if len(coords) == 0:
                coords = [self.GetGridCursorCoords()]

            for n, crd in enumerate(coords):
                if n >= len(parent.copy):
                    return
                r_offset = crd[0]
                c_offset = crd[1]
                for row, rowdata in enumerate(parent.copy[n]):
                    for col, value in enumerate(rowdata):
                        in_row = row + r_offset
                        in_col = col + c_offset
                        if in_col < self.GetNumberCols():
                            table.SetValue(in_row, in_col, value)
                        else:
                            print("Part of selection is out of bounds of the grid.")
                        table.update_data(None)

    def can_undo(self):
        """Return true if an action can be undone."""
        return (True 
            if len(self.history[tuple(self.GetTable().get_fk_value())]) > 0
            else False)

    def undo(self):
        """Undo the last action."""
        table: DatabaseGridTable = self.GetTable()
        key = tuple(table.get_fk_value())
        try:
            data = self.history[key].pop()
        except IndexError:
            print("UNDO - No saved data to use.")
        else:
            table.DeleteRows(0, self.GetNumberRows() - 1)
            table.append_rows(data, False)

    def save(self):
        """Save the selected items to database."""
        selected = self.GetSelectedRows()
        if len(selected) == 0:
            return False

        table: DatabaseGridTable = self.GetTable()
        if table.tablename == "offer_parts":
            key = ["product_code"]
            value = [self.GetParent().find("code", "id", table.fk_value)]
        else:
            key = None
            value = None
        if not table.save_to_db(selected, key, value):
            print("Error in saving to database.")

    def select_all(self):
        """Select all but the last empty row."""
        self.ClearSelection()
        for row in range(self.GetNumberRows() - 1):
            self.SelectRow(row, True)

    def clear_selected(self):
        """Clear the values from selected cells. Return true if something was deleted."""
        blocks = self.GetSelectedBlocks()
        did_del = False
        for b in blocks:
            if not did_del:
                did_del = True
            for row in range(b.GetTopRow(), b.GetBottomRow() + 1):
                for col in range(b.GetLeftCol(), b.GetRightCol() + 1):
                    self.SetCellValue(row, col, "")
        return did_del

    def save_state(self):
        """Save the current data state in table to history."""
        table: DatabaseGridTable = self.GetTable()
        self.history[tuple(table.get_fk_value())].append(table.get_data())

    def on_cell_changing(self, evt):
        """Save the state to history before cell change."""
        self.save_state()
        evt.Skip()

    def on_cell_changed(self, evt):
        """Update the data of this grid on edit."""
        self.GetTable().update_data(None)
        evt.Skip()

    def on_cell_selected(self, evt):
        """Change the grid cursor text to new position."""
        row = evt.GetRow()
        col = evt.GetCol()
        label = self.GetTable().GetColLabelValue(col)
        self.cursor_text = "({}, {})".format(row, label)
        evt.Skip()

    def on_col_size(self, evt):
        """Save new columns size to columns table."""
        col = evt.GetRowOrCol()
        width = self.GetColSize(col)
        self.GetTable().set_col_width(col, width)
        self.PostSizeEventToParent()
        evt.Skip()

    def on_col_move(self, evt):
        """Save the new order."""
        col = evt.GetCol()
        if not self.GetTable().is_col_visible(col):
            evt.Veto()
        pos = self.GetColPos(col)
        wx.CallAfter(self.col_moved, col, pos)
        evt.Skip()

    def col_moved(self, col_id, old_pos):
        pass
        # colpos = self.GetColPos(col_id)
        # print("New col pos: {}, old pos: {}".format(colpos, old_pos))

    def on_key_down(self, evt):
        keycode = evt.GetUnicodeKey()
        if keycode == wx.WXK_NONE:
            keycode = evt.GetKeyCode()

        # DEL
        if keycode == wx.WXK_DELETE:
            if self.delete():
                return

        # CTRL+C
        elif keycode == 67 and evt.GetModifiers() == wx.MOD_CONTROL:
            self.copy()

        # CTRL+V
        elif keycode == 86 and evt.GetModifiers() == wx.MOD_CONTROL:
            self.paste()

        # CTRL+Z
        elif keycode == 90 and evt.GetModifiers() == wx.MOD_CONTROL:
            self.undo()

        # CTRL+A
        elif keycode == 65 and evt.GetModifiers() == wx.MOD_CONTROL:
            self.select_all()

        evt.Skip()

    def on_label_lclick(self, evt):
        """Set focus on lclick on label."""
        self.SetFocus()
        evt.Skip()

    def can_paste(self):
        """Return true if a copy exists."""
        if len(self.GetParent().copy) > 0:
            return True
        else:
            return False

    def on_context_menu(self, evt):
        """Open the context menu for the grid."""
        self.SetFocus()
        menu = wx.Menu()
        row = evt.GetRow()
        col = evt.GetCol()
        table = self.GetTable()
        no_row_selected = len(self.GetSelectedRows()) == 0

        # Clear selection and set grid cursor to clicked cell if
        # right click was not in a selected cell.
        if not self.IsInSelection(row, col):
            self.ClearSelection()
            self.SetGridCursor(row, col)

        if not hasattr(self, "id_todb"):
            self.id_todb = wx.NewIdRef()
            self.Bind(wx.EVT_MENU, self.on_save, id=self.id_todb)

        # item = wx.MenuItem(menu, wx.ID_UNDO, "", "Undo the previous action.")
        # menu.Append(item)

        mi_undo: wx.MenuItem = menu.Append(wx.ID_UNDO)
        menu.Append(wx.ID_CUT)
        menu.Append(wx.ID_COPY)
        mi_paste = menu.Append(wx.ID_PASTE)
        menu.AppendSeparator()
        mi_delete = menu.Append(wx.ID_DELETE, "Poista\tDelete")

        # Only add db items if the grid table has database table.
        if table.can_save_to_db():
            menu.AppendSeparator()
            mi_save = menu.Append(self.id_todb, "Tallenna", "Tallenna valinta tietokantaan")

            if no_row_selected:
                mi_save.Enable(False)

        if not self.can_undo():
            mi_undo.Enable(False)

        if not self.can_paste():
            mi_paste.Enable(False)

        if no_row_selected:
            mi_delete.Enable(False)

        self.PopupMenu(menu)

        menu.Destroy()
        evt.Skip()

    def on_copy(self, evt):
        """Do action selected in context menu."""
        self.copy()

    def on_cut(self, evt):
        """Do action selected in context menu."""
        self.cut()

    def on_paste(self, evt):
        """Do action selected in context menu."""
        self.paste()

    def on_save(self, evt):
        """Do action selected in context menu."""
        self.save()

    def on_undo(self, evt):
        """Do action selected in context menu."""
        self.undo()

    def on_delete(self, evt):
        """Do action selected in context menu."""
        self.delete()

    def on_label_menu(self, evt):
        """Open menu to select visible columns. Set focus on this grid."""
        self.SetFocus()
        menu = wx.Menu()
        table = self.GetTable()

        for n, colid in enumerate(self.col_ids):
            menu.AppendCheckItem(colid, self.labels[n], "Muuta sarakkeen näkyvyyttä")

        is_visible = table.get_visible_columns()
        for col, vis in enumerate(is_visible):
            menu.Check(self.col_ids[col], vis)

        self.PopupMenu(menu)
        menu.Destroy()
        evt.Skip()

    def on_col_menu(self, evt):
        """Show or hide the checked column."""
        is_checked = evt.IsChecked()
        col = self.col_ids.index(evt.GetId())
        table = self.GetTable()

        if is_checked:
            table.show_column(col)
        else:
            table.hide_column(col)

        evt.Skip()

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
        # Init the history for a new foreign key.
        if fk is not None:
            key = tuple(fk)
            if key not in self.history:
                self.history[key] = []
        # Clear grid cursor variables before setting new values.
        self.cursor_text = ""
        self.GetTable().set_fk_value(fk)


BORDER = 5
PARTS_NO_SELECTION = "Osat - Tuotetta ei ole valittu"
PARTS_LABEL = "Osat tuotteeseen '{}'"
PARTS_LABEL_ROW = "Osat tuotteeseen rivillä {}"
PARTS_LABEL_NO_CODE = "Osat - Rivin {} tuotteella ei ole koodia."


class GroupPanel(wx.Panel):
    def __init__(self, parent, db):
        super().__init__(parent)

        self.copy = []
        self.group_pk = None

        self.grid_pdef = DbGrid(self, db, "offer_predefs")
        self.grid_mats = DbGrid(self, db, "offer_materials")
        self.grid_prod = DbGrid(self, db, "offer_products")
        self.grid_part = DbGrid(self, db, "offer_parts")

        self.label_pdef = wx.StaticText(self, label="Esimääritykset")
        self.label_mats = wx.StaticText(self, label="Materiaalit")
        self.label_prod = wx.StaticText(self, label="Tuotteet")
        self.label_part = wx.StaticText(self, label=PARTS_NO_SELECTION)

        self.cursor_pdef = wx.StaticText(self)
        self.cursor_mats = wx.StaticText(self)
        self.cursor_prod = wx.StaticText(self)
        self.cursor_part = wx.StaticText(self)

        self.set_fk(["RyhmäID"])
        self.SetBackgroundColour((230, 230, 245))

        self.Bind(wxg.EVT_GRID_SELECT_CELL, self.on_product_selection, self.grid_prod)
        self.Bind(wxg.EVT_GRID_SELECT_CELL, self.update_cursor_text, self.grid_pdef)
        self.Bind(wxg.EVT_GRID_SELECT_CELL, self.update_cursor_text, self.grid_mats)
        self.Bind(wxg.EVT_GRID_SELECT_CELL, self.update_cursor_text, self.grid_prod)
        self.Bind(wxg.EVT_GRID_SELECT_CELL, self.update_cursor_text, self.grid_part)
        self.Bind(wxg.EVT_GRID_CELL_CHANGED, self.on_cell_changed, self.grid_pdef)
        self.Bind(wxg.EVT_GRID_CELL_CHANGED, self.on_cell_changed, self.grid_mats)
        self.Bind(wxg.EVT_GRID_CELL_CHANGED, self.on_cell_changed, self.grid_prod)
        self.Bind(wxg.EVT_GRID_CELL_CHANGED, self.on_cell_changed, self.grid_part)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer_horz = wx.BoxSizer(wx.HORIZONTAL)
        sizer_right = wx.BoxSizer(wx.VERTICAL)
        sizer_left = wx.BoxSizer(wx.VERTICAL)
        sizer_pdef = self.grid_sizer(self.grid_pdef, self.label_pdef, self.cursor_pdef)
        sizer_mats = self.grid_sizer(self.grid_mats, self.label_mats, self.cursor_mats)
        sizer_prod = self.grid_sizer(self.grid_prod, self.label_prod, self.cursor_prod)
        sizer_part = self.grid_sizer(self.grid_part, self.label_part, self.cursor_part)

        self.sizer_parts = sizer_part

        sizer_right.Add(sizer_mats, 1, wx.EXPAND)
        sizer_right.Add(sizer_prod, 1, wx.EXPAND)
        sizer_right.Add(sizer_part, 1, wx.EXPAND)
        sizer_left.Add(sizer_pdef, 1, wx.EXPAND)
        sizer_horz.Add(sizer_left, 0, wx.EXPAND)
        sizer_horz.Add(sizer_right, 10, wx.EXPAND)
        sizer.Add(sizer_horz, 1, wx.EXPAND)
        self.SetSizer(sizer)

    def grid_sizer(self, grid, label, cursor_text):
        """Create a sizer for grid, it's label and cursor text."""
        sizer_grid = wx.BoxSizer(wx.VERTICAL)
        sizer_label = wx.BoxSizer(wx.HORIZONTAL)
        sizer_label.Add(label, 0, wx.RIGHT, BORDER * 3)
        sizer_label.Add(cursor_text, 0, wx.RIGHT, BORDER)
        sizer_grid.Add(sizer_label, 0, wx.EXPAND|wx.ALL, BORDER)
        sizer_grid.Add(grid, 1, wx.EXPAND)
        return sizer_grid

    def on_product_selection(self, evt):
        """Update parts grid and its labels with selected product."""
        row = evt.GetRow()
        product_id = self.grid_prod.GetTable().GetPkValue(row)
        self.grid_part.set_fk_value(product_id)
        try:
            col = self.grid_prod.GetTable().col_labels.index("Koodi")
        except ValueError:
            label = PARTS_LABEL_ROW.format(row)
        else:
            try:
                prod_code = self.grid_prod.GetTable().data[row][col]
            except IndexError:
                label = PARTS_NO_SELECTION
            else:
                if prod_code is None or prod_code == "":
                    label = PARTS_LABEL_NO_CODE.format(row)
                else:
                    label = PARTS_LABEL.format(prod_code)

        self.label_part.SetLabel(label)
        self.sizer_parts.Layout()   # Moves the labels to new positions
        evt.Skip()

    def on_cell_changed(self, evt):
        """Update the data on dependend grids on entering a value to a cell."""
        eobj = evt.GetEventObject()
        self.update_depended_grids(eobj)
        evt.Skip()

    def update_depended_grids(self, grid):
        """Update the dependend grids of the given grid."""
        if (grid == self.grid_pdef or
            grid == self.grid_mats or
            grid == self.grid_prod):

            self.grid_part.GetTable().update_data(None)
            self.grid_prod.GetTable().update_data(None)

        elif grid == self.grid_part:
            self.grid_prod.GetTable().update_data(None)

    def set_pk(self, pk):
        """Primary key of offer_groups, foreign key of the grids in this panel."""
        if pk is None:
            self.group_pk = None
            self.set_fk(None)
        else:
            self.group_pk = [pk]
            self.set_fk([pk])

    def get_pk(self):
        return self.group_pk[0]

    def set_fk(self, fk):
        """Set the foreign key for grids contained in this panel.

        Parameters
        ----------
        fk : Iterable
            The foreign key, usually group_id.
        """
        self.grid_pdef.set_fk_value(fk)
        self.grid_mats.set_fk_value(fk)
        self.grid_prod.set_fk_value(fk)
        self.grid_part.set_fk_value(None)

    def update_cursor_text(self, evt):
        """Update the cursor text label for relevant grid."""
        eobj = evt.GetEventObject()
        if eobj == self.grid_pdef:
            cursor_text = self.grid_pdef.cursor_text
            self.cursor_pdef.SetLabel(cursor_text)

        elif eobj == self.grid_mats:
            cursor_text = self.grid_mats.cursor_text
            self.cursor_mats.SetLabel(cursor_text)

        elif eobj == self.grid_prod:
            cursor_text = self.grid_prod.cursor_text
            self.cursor_prod.SetLabel(cursor_text)

        elif eobj == self.grid_part:
            cursor_text = self.grid_part.cursor_text
            self.cursor_part.SetLabel(cursor_text)

        evt.Skip()

    def find(self, key, find_key, find_value):
        return self.grid_prod.GetTable().find_value(key, find_key, find_value[0])


if __name__ == '__main__':
    app = wx.App()

    frame = wx.Frame(None, size=(1500, 800))
    db = tb.OfferTables()
    panel = GroupPanel(frame, db)
    frame.Show()

    app.MainLoop()
