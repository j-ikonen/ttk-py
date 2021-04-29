import wx
import wx.grid
import wx.dataview as dv

from data import GridData
from database import Database, EDITED_CHAR, EDITED_DIFF_MATCH, EDITED_MATCH, EDITED_NO_MATCH


GRIDMENU_EDIT_OBJECT = "Muokkaa"
GOD_TITLE = "Muokkaa"
GOD_LABEL = "Muokkaa valitun esineen ominaisuuksia."
GOD_EDIT_SIZE = (250, -1)
GRIDMENU_ITDB = "Syötä tietokantaan"
GRIDMENU_ITDB_HELP = "Syötä tietokantaan"
GRIDMENU_EDIT_OBJECT_HELP = "Muokkaa koodeja."
GRID_ITDB_NO_SELECTION = "Ei valintaa, jota syöttää tietokantaan."
GRIDMENU_FFDB = "Etsi tietokannasta"
GRIDMENU_FFDB_HELP = "Etsi tietokannasta"
GIRD_ITDB_INS_IDS = "\tInserted ids: {}"

ITDD_TITLE = "Syötä Tietokantaan"
BORDER = 5
CH_CLL_SIZE = (80, -1)
CLL_DICT = {'Materiaalit': 'materials', 'Tuotteet': 'products'}

LABELS = {'materials': 'Materiaalit', 'products': 'Tuotteet'}
FFDB_TITLE = "Etsi tietokannasta: '{}'"
FFDB_TE_SIZE = (120, -1)

GRIDMENU_DELSEL = "Poista"
GRIDMENU_DELSEL_HELP = "Poista valitut rivit."
GRIDMENU_COPY = "Kopioi"
GRIDMENU_COPY_HELP = "Kopioi valitut solut."
GRIDMENU_PASTE = "Liitä"
GRIDMENU_PASTE_HELP = "Liitä kopioidut valittuihin soluihin."
CLR_CELL_EDITED_NO_MATCH = (255, 210, 210)
CLR_CELL_EDITED_DIFF_MATCH = (210, 210, 255)
CLR_CELL_EDITED_MATCH = (210, 255, 210)
CLR_WHITE = (255, 255, 255)


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
        if self.obj is None:
            return 0
        return len(self.obj) + 1

    def GetNumberCols(self):
        return self.obj.get_n_columns()

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
            newlen = len(self.obj)
            msg = wx.grid.GridTableMessage(
                self,
                wx.grid.GRIDTABLE_NOTIFY_ROWS_DELETED,
                newlen,
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
            self.GetView().Refresh()
            return

        self.GetView().ProcessTableMessage(msg)
    
    def set_data(self, data: GridData):
        if isinstance(data, GridData):
            self.obj = data
        else:
            raise TypeError(f"CustomDataTable.obj must be <GridData> not '{type(data)}'")


class CustomGrid(wx.grid.Grid):
    def __init__(self, parent, data: GridData):
        super().__init__(parent)

        self.data = data
        self.empty_data = GridData(data.name)
        self.name = data.name
        self.selected_row = None
        self.rclick_row = None
        self.copied = []

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

    def append(self, obj):
        """Append a row with data from obj to grid."""
        oldlen = len(self.data)
        self.data.append(obj)
        self.GetTable().NotifyRowChange(oldlen, len(self.data))

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
                    self.SetGridCursor(row, GridData.tab_to[self.name][col])
                except IndexError:
                    # Move to first cell of next row until at the end of grid.
                    if row < self.GetNumberRows() - 1:
                        self.SetGridCursor(row + 1, 0)



    def on_cell_changing(self, evt):
        if self.data == self.empty_data:
            print("CustomGrid.on_cell_changing - Veto change for grid using empty_data.")
            evt.Veto()

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
        print(f"Grid '{self.data.name}' - Selected cell (row, col):" +
              f" ({evt.GetRow()}, {evt.GetCol()})")
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
        selected = self.GetSelectedRows()

        # Do id assignment and event binding only once.
        if not hasattr(self, 'copy_id'):
            self.copy_id = wx.NewIdRef()
            self.paste_id = wx.NewIdRef()
            self.edit_object_id = wx.NewIdRef()
            self.del_sel_id = wx.NewIdRef()
            self.itdb_id = wx.NewIdRef()        # Insert To DataBase
            self.ffdb_id = wx.NewIdRef()        # Find from DataBase

            self.Bind(wx.EVT_MENU, self.on_copy, id=self.copy_id)
            self.Bind(wx.EVT_MENU, self.on_paste, id=self.paste_id)
            self.Bind(wx.EVT_MENU, self.on_edit_object, id=self.edit_object_id)
            self.Bind(wx.EVT_MENU, self.on_delete_selected, id=self.del_sel_id)
            self.Bind(wx.EVT_MENU, self.on_insert_to_db, id=self.itdb_id)
            self.Bind(wx.EVT_MENU, self.on_find_from_db, id=self.ffdb_id)

        menu = wx.Menu()
        menu.Append(self.copy_id, GRIDMENU_COPY, GRIDMENU_COPY_HELP)
        menu.Append(self.paste_id, GRIDMENU_PASTE, GRIDMENU_PASTE_HELP)
        menu.AppendSeparator()
        menu.Append(self.edit_object_id, GRIDMENU_EDIT_OBJECT, GRIDMENU_EDIT_OBJECT_HELP)
        menu.Append(self.del_sel_id, GRIDMENU_DELSEL, GRIDMENU_DELSEL_HELP)

        # Append database menuitems if grid has database items.
        if self.data.name == 'materials' or self.data.name == 'products':
            menu.AppendSeparator()
            menu.Append(self.itdb_id, GRIDMENU_ITDB, GRIDMENU_ITDB_HELP)
            menu.Append(self.ffdb_id, GRIDMENU_FFDB, GRIDMENU_FFDB_HELP)

            if not selected:
                menu.Enable(self.itdb_id, False)

        # Alternate item initialization for editing MenuItem properties.
        # item = wx.MenuItem(menu, self.edit_object_id, GRIDMENU_EDIT_OBJECT")
        # menu.Append(item)

        # Gray out menuitems that require row selections.
        if not selected:
            menu.Enable(self.copy_id, False)
            menu.Enable(self.del_sel_id, False)

        # Gray out paste if nothing is copied or cut.
        if not self.copied:
            menu.Enable(self.paste_id, False)

        self.PopupMenu(menu)
        menu.Destroy()
        self.rclick_row = None

    def on_copy(self, evt):
        """Copy the selected cells."""
        print("\nCustomGrid.on_copy")
        selection = self.GetSelectedRows()
        selection.sort(reverse=True)
        objs = self.data.to_dict()
        self.copied = []

        for n in selection:
            self.copied.append(objs[n])

        # if not selection:
        #     selection = self.GetSelectedBlocks()

    def on_paste(self, evt):
        """Paste the copied selection to new selection."""
        print("\nCustomGrid.on_paste")
        oldlen = len(self.data)

        for obj in self.copied:
            self.data.append(obj)

        newlen = len(self.data)
        self.GetTable().NotifyRowChange(oldlen, newlen)
        # if not selection:
        #     selection = self.GetSelectedBlocks()

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

    def on_delete_selected(self, evt):
        print("\nCustomGrid.on_delete_selected")
        selected = self.GetSelectedRows()
        selected.sort(reverse=True)
        print(f"\tDelete rows: {selected}")
        for index in selected:
            self.DeleteRows(index)
            # if self.data.delete(index) != 1:
            #     raise IndexError(
            #         f"\tCustomGrid.on_delete_selected Failed to delete at index {index}"
            #     )
        # self.Refresh()

    def on_insert_to_db(self, evt):
        print("\nCustomGrid.on_insert_to_db")
        selected = self.GetSelectedRows()
        data = self.data.to_dict()
        to_db = []
        for row in selected:
            to_db.append(data[row])
        
        if len(to_db) > 0:
            ids = Database(self.name).insert(to_db)
            print(GIRD_ITDB_INS_IDS.format(ids))
        else:
            print(GRID_ITDB_NO_SELECTION)

    def on_find_from_db(self, evt):
        print("CustomGrid.on_find_from_db")

        # print("\nBEFORE")
        # pprint(self.data.data)
        # print("\n")

        with FindFromDbDialog(self, self.data.name) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                print(f"\tFound items: {len(dlg.selected_items)}")
                if len(dlg.selected_items) > 0:
                    obj = dlg.selected_items[0]

                    try:
                        del obj['_id']
                    except KeyError:
                        pass

                    for item in [obj]:
                        oldrow = len(self.data)
                        self.data.append(item)
                        newrow = len(self.data)
                        self.GetTable().NotifyRowChange(oldrow, newrow)

        # print("\nAFTER")
        # pprint(self.data.data)
        # print("\n")

    def set_data(self, data: GridData):
        if isinstance(data, GridData):
            self.data = data
            self.GetTable().set_data(data)
        else:
            self.empty_data.data = []
            self.data = self.empty_data
            self.GetTable().set_data(self.empty_data)
            raise TypeError(f"CustomGrid.data must be <GridData> not {type(data)}")

    def set_edited_cell(self, row):
        """Set the backgroundcolor of cell for key 'edited'."""
        try:
            col = self.data.get_columns().index('edited')
        except ValueError as e:
            print(f"ValueError - {e} - CustomGrid.set_edited_cell grid has no column 'edited'")
            return
        value = self.GetCellValue(row, col)
        if value == EDITED_CHAR[EDITED_NO_MATCH]:
            self.SetCellBackgroundColour(row, col, CLR_CELL_EDITED_NO_MATCH)
        elif value == EDITED_CHAR[EDITED_DIFF_MATCH]:
            self.SetCellBackgroundColour(row, col, CLR_CELL_EDITED_DIFF_MATCH)
        elif value == EDITED_CHAR[EDITED_MATCH]:
            self.SetCellBackgroundColour(row, col, CLR_CELL_EDITED_MATCH)
        else:
            self.SetCellBackgroundColour(row, col, CLR_WHITE)

    def update_data(self, data: GridData, reset_selection=False):
        """Update GridData with given data.

        Args:
            data (list): New data to replace GridData.data with.
            reset_selection (bool): Will the selection be reset with update.
        """
        try:
            oldlen = len(self.data)
        except TypeError:
            oldlen = -1

        if data is None:
            self.empty_data.data = []
            self.set_data(self.empty_data)
        else:
            self.set_data(data)

        # Updated grid is empty.
        # if data is None:
        #     self.GetTable().NotifyRowChange(oldlen, -1)
        # else:
        new = len(self.data)
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


class FindFromDbDialog(wx.Dialog):
    def __init__(self, parent, collection):
        super().__init__()

        self.Create(
            parent,
            size=(600, 400),
            title=FFDB_TITLE.format(LABELS[collection]),
            style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.CenterOnParent()

        self.collection = collection
        data = GridData(collection)

        self.col_labels = {}
        for col in data.get_keys():
            self.col_labels[data.get_label(col)] = col

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer_first = wx.BoxSizer(wx.HORIZONTAL)

        self.choice_key = None
        self.selected_items = []
        self.choice = wx.Choice(
            self,
            size=CH_CLL_SIZE,
            choices=list(self.col_labels.keys())
        )
        self.textedit = wx.TextCtrl(self, size=FFDB_TE_SIZE)
        self.listctrl = dv.DataViewListCtrl(self)
        self.listctrl.AppendTextColumn("ObjectID")
        for label, key in self.col_labels.items():
            self.listctrl.AppendTextColumn(label)

        sizer_first.Add(self.choice, 0, wx.EXPAND|wx.ALL, BORDER)
        sizer_first.Add(self.textedit, 0, wx.EXPAND|wx.ALL, BORDER)

        self.Bind(wx.EVT_CHOICE, self.on_col_choice, self.choice)
        self.Bind(wx.EVT_TEXT, self.on_text_edit, self.textedit)

        sizer.Add(sizer_first, 0, wx.EXPAND)
        sizer.Add(self.listctrl, 1, wx.EXPAND)

        self.choice.SetSelection(0)
        self.choice_key = self.col_labels['Koodi']

        # Ok / Cancel buttons to bottom of dialog.
        line = wx.StaticLine(self)
        sizer.Add(line, 0, wx.EXPAND|wx.RIGHT|wx.TOP, BORDER)
        
        btnsizer = wx.StdDialogButtonSizer()
        btn = wx.Button(self, wx.ID_OK)
        btn.SetDefault()
        btnsizer.AddButton(btn)

        btn = wx.Button(self, wx.ID_CANCEL)
        btnsizer.AddButton(btn)

        btnsizer.Realize()
        sizer.Add(btnsizer, 0, wx.ALL, BORDER)
        self.SetSizer(sizer)
        # sizer.Fit(self)

    def on_col_choice(self, evt):
        self.choice_key = self.col_labels[evt.GetString()]

    def on_text_edit(self, evt):
        """Search database for anything matching given text with key from choice."""
        value = self.textedit.GetValue()
        pattern = ("\w*" + value + "\w*")
        self.listctrl.DeleteAllItems()
        self.selected_items = []

        if self.choice_key is not None:
            filter = {self.choice_key: {'$regex': pattern, '$options': 'i'}}
            objects = list(Database(self.collection).find(filter, True))
            for obj in objects:
                strlist = []
                for val in obj.values():
                    strlist.append(str(val))
                self.listctrl.AppendItem(strlist)

            if len(objects) > 0:
                self.selected_items.append(objects[0])


class InsertToDbDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__()

        self.Create(parent, title=ITDD_TITLE)
        self.CenterOnParent()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer_choice = wx.BoxSizer(wx.HORIZONTAL)

        cll_labels = list(CLL_DICT.keys())
        materials = GridData.materials()
        products = GridData.products()

        self.grid_materials = CustomGrid(self, materials)
        self.grid_products = CustomGrid(self, products)
        self.choice = wx.Choice(self, size=CH_CLL_SIZE, choices=cll_labels)

        self.Bind(wx.EVT_CHOICE, self.on_coll_choice, self.choice)

        sizer_choice.Add(self.choice, 0, wx.EXPAND|wx.ALL, BORDER)


        sizer.Add(sizer_choice, 0, wx.EXPAND)

        # Ok / Cancel buttons to bottom of dialog.
        line = wx.StaticLine(self)
        sizer.Add(line, 0, wx.EXPAND|wx.RIGHT|wx.TOP, BORDER)
        
        btnsizer = wx.StdDialogButtonSizer()
        btn = wx.Button(self, wx.ID_OK)
        btn.SetDefault()
        btnsizer.AddButton(btn)

        btn = wx.Button(self, wx.ID_CANCEL)
        btnsizer.AddButton(btn)

        btnsizer.Realize()
        sizer.Add(btnsizer, 0, wx.ALL, BORDER)
        self.SetSizer(sizer)
        sizer.Fit(self)
    
    def on_coll_choice(self, evt):
        collection = CLL_DICT[evt.GetString()]
        print(f"InsertToDbDialog.on_coll_choice collection: {collection}")
