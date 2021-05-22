"""
TODO
----
    Save to database context menu option.
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
        self.dbcols = []

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

        if value is None or value == "":
            return True
        else:
            return False

    def GetValue(self, row, col):
        try:
            return self.data[row][self.columns[col]]
        except IndexError:
            return ""

    def SetValue(self, row, col, value):
        # Can not set a value if foreign key is not defined.
        if self.fk_value is None:
            print(f"Foreign key {self.fk} is not defined.")
            return

        # Can not set a value if value is a dublicate in a unique column.
        datacol = self.GetDataCol(col)
        if datacol in self.unique and self.is_dublicate(datacol, value):
            print(f"Column {self.GetColLabelValue(col)} is unique, " +
                  f"'{value}' already exists.")

        # Set the value to db if possible.
        elif datacol not in self.cant_update:
            pkval = self.GetPkValue(row)

            # Update requires a valid existing primary key.
            if pkval is not None:
                self.db.update_one(
                    self.tablename,
                    self.col_keys[datacol],
                    self.pk,
                    [value] + pkval
                )
            # No pk value in the row so insert new row to db.
            else:
                self.append_new_row(datacol, value)

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
        self.GetView().ForceRefresh()
        # self.GetView().Refresh()
        # self.GetView().Update()
        return self.get_col_width(self.GetNumberCols() - 1)[0]

    def hide_column(self, col):
        gridcol = self.columns.index(col)
        del self.columns[gridcol]
        self.DeleteCols(gridcol, 1)
        self.db.set_visible(self.tablename, col, False)
        self.GetView().ForceRefresh()
        # self.GetView().Refresh()
        # self.GetView().Update()

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
        # self.GetView().ForceRefresh()
        self.GetView().PostSizeEventToParent()
        return True

    def DeleteCols(self, pos, numCols):
        # return super().DeleteCols(pos=pos, numCols=numCols)
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
        # return super().AppendCols(numCols=numCols)
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


class GroupMaterialsTable(DatabaseGridTable):
    def __init__(self, db: tb.OfferTables):
        super().__init__(db)

        self.tablename = "offer_materials"
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
        self.cant_update = [13]
        self.dbcols = [n for n in range(13)]

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
        self.columns = self.get_visible()
        self.col_keys = [val[tb.KEY] for val in setup]
        self.col_labels = [val[tb.LABEL] for val in setup]
        self.col_types = [val[tb.TYPE] for val in setup]
        self.col_widths = [val[tb.WIDTH] for val in setup]
        self.unique = []
        self.read_only = []
        # self.ro_dependency = [8, 9, 10, 11, 12]
        self.cant_update = [13]
        self.dbcols = [n for n in range(12)]

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
        self.dbcols = [n for n in range(14)]
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
        self.columns = self.get_visible()
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
        self.cursor_text = ""
        self.copy_rows = []
        self.copy_cells = []
        self.history = {}

        for col in range(self.GetNumberCols()):
            width = table.get_col_width(col)
            self.SetColSize(col, width[0])

        self.SetRowLabelSize(35)
        self.EnableDragColMove(True)
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

    def delete(self):
        """Delete the selected rows. Return True if deleted something."""
        selected = self.GetSelectedRows()
        if len(selected) == 0:
            return False

        self.save_state()
        selected.sort(reverse=True)
        # Do not delete the empty last row.
        if selected[0] == self.GetNumberRows() - 1:
            del selected[0]

        table = self.GetTable()
        for row in selected:
            table.DeleteRows(row, 1)
        self.GetTable().update_data(None)
        self.GetParent().update_depended_grids(self)
        return True

    def paste(self):
        """Paste the copied values to selection.

        Depending on if last copy was on rows or blocks,
        append all copied rows to end of grid or
        paste as many blocks as there are selected blocks.
        """
        if len(self.copy_rows) > 0:
            self.save_state()
            self.GetTable().append_rows(self.copy_rows, True)
            self.GetParent().update_depended_grids(self)
        else:
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
                            # print("SET: {}, r,c: {},{}".format(value, row + r_offset, col + c_offset))
                            table.SetValue(row + r_offset, col + c_offset, value)

                table.update_data(None)

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

    def save_state(self):
        """Save the current data state in table to history."""
        table: DatabaseGridTable = self.GetTable()
        self.history[tuple(table.get_fk_value())].append(table.get_data())

    def on_cell_changing(self, evt):
        """Save the state to history before cell change."""
        self.save_state()

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
        pos = self.GetColPos(col)
        wx.CallAfter(self.col_moved, col, pos)
        evt.Skip()
        # print("NEW COLUMN ORDER FOR id: {}, old_pos: {}".format(col, pos))

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

        evt.Skip()

    def on_label_lclick(self, evt):
        """Set focus on lclick on label."""
        self.SetFocus()
        evt.Skip()

    def on_context_menu(self, evt):
        """Open the context menu for the grid."""
        menu = wx.Menu()
        row = evt.GetRow()
        col = evt.GetCol()

        # Clear selection and set grid cursor to clicked cell if
        # right click was not in a selected cell.
        if not self.IsInSelection(row, col):
            self.ClearSelection()
            self.SetGridCursor(row, col)

        # if not hasattr(self, "id_copy"):
        #     self.id_copy = wx.NewIdRef()
        #     self.id_cut = wx.NewIdRef()
        #     self.id_paste = wx.NewIdRef()
        #     self.id_undo = wx.NewIdRef()
        #     self.id_del = wx.NewIdRef()

        menu.Append(wx.ID_UNDO)
        menu.Append(wx.ID_CUT)
        menu.Append(wx.ID_COPY)
        menu.Append(wx.ID_PASTE)
        menu.Append(wx.ID_DELETE)
        self.PopupMenu(menu)

        menu.Destroy()
        evt.Skip()

    def on_copy(self, evt):
        """Do action selected in context menu."""
        self.copy()

    def on_cut(self, evt):
        """Do action selected in context menu."""
        # self.cut()
        pass

    def on_paste(self, evt):
        """Do action selected in context menu."""
        self.paste()

    def on_undo(self, evt):
        """Do action selected in context menu."""
        self.undo()

    def on_delete(self, evt):
        """Do action selected in context menu."""
        self.delete()

    def on_label_menu(self, evt):
        """Open menu to select visible columns. Set focus on this grid."""
        # print("LABEL MENU")
        self.SetFocus()
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
        if is_checked:
            w = table.show_column(col)
            gridcol = table.columns.index(col)
            self.SetColSize(gridcol, w)
        else:
            table.hide_column(col)

        self.PostSizeEventToParent()
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
        # Clear copy and grid cursor variables.
        self.copy_rows.clear()
        self.copy_cells.clear()
        self.cursor_text = ""
        self.GetTable().set_fk_value(fk)


BORDER = 5
PARTS_NO_SELECTION = "Osat - Tuotetta ei ole valittu"
PARTS_LABEL = "Osat tuotteeseen '{}'"
PARTS_LABEL_ROW = "Osat tuotteeseen rivillä {}"
PARTS_LABEL_NO_CODE = "Osat - Rivin {} tuotteella ei ole koodia."


class GroupPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)

        self.copy = []

        self.grid_pdef = TestGrid(self, db, "offer_predefs")
        self.grid_mats = TestGrid(self, db, "offer_materials")
        self.grid_prod = TestGrid(self, db, "offer_products")
        self.grid_part = TestGrid(self, db, "offer_parts")

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
        

if __name__ == '__main__':
    app = wx.App()

    frame = wx.Frame(None, size=(1500, 800))
    db = tb.OfferTables()
    panel = GroupPanel(frame)
    frame.Show()

    app.MainLoop()
