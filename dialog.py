import wx
from wx.core import NotebookNameStr
import wx.dataview as dv

from data import GridData, convert
from database import Database


DBD_TITLE = "Tietokanta"
DBD_SIZE = (1000, 600)
DBD_CH_COLL_SIZE = (80, -1)
DBD_CH_KEY_SIZE = (80, -1)
DBD_TC_SIZE = (80, -1)
DBD_COLL = ['materials', 'products']
DBD_COLL_LABEL = {
    'Materiaalit': 'materials',
    'Tuotteet': 'products'
}
DBD_BTN_ADD = "Lisää/Muokkaa"
SMALL_BORDER = 2
BORDER = 5
DBD_REPLACE_TITLE = "Korvaa dokumentti"
DBD_REPLACE_MSG = "Dokumentti koodilla '{}' on tietokannassa.\nKorvaa uudella dokumentilla?"
DBD_REPLACE_SIZE = (300, 200)


class ConfirmDialog(wx.Dialog):
    def __init__(self, parent, title, msg):
        super().__init__(
            parent,
            title=title,
            size=DBD_REPLACE_SIZE
        )
        self.CenterOnParent()

        txt_msg = wx.StaticText(self, label=msg, style=wx.TEXT_ALIGNMENT_CENTER)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer_btn = wx.StdDialogButtonSizer()

        btn_ok = wx.Button(self, wx.ID_OK)
        btn_cancel = wx.Button(self, wx.ID_CANCEL)
        btn_ok.SetDefault()

        sizer_btn.AddButton(btn_ok)
        sizer_btn.AddButton(btn_cancel)
        sizer_btn.Realize()

        sizer.Add(txt_msg, 0, wx.EXPAND|wx.ALL, BORDER*3)
        sizer.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.LEFT|wx.RIGHT, BORDER)
        sizer.Add(sizer_btn, 0, wx.EXPAND|wx.ALL, BORDER)

        self.SetSizer(sizer)
        sizer.Fit(self)


class DbDialog(wx.Dialog):
    def __init__(self, parent, collection, key=None, value=""):
        """Initialize a database dialog.
        
        Args:
            - parent: Parent wx.Window.
            - collection (str): Name of database collection.
            - key (str): Key to a field in collection.
            - value (str): Search value.
        """
        super().__init__(
            parent,
            title=DBD_TITLE,
            size=DBD_SIZE,
            style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER
        )

        self.CenterOnParent()

        self.collection = collection
        self.key = key
        self.search_value = value
        self.sample = GridData(self.collection)
        self.objects = []

        self.collection_keys = GridData.get_db_keys()
        self.column_keys = self.sample.get_columns()

        self.collection_choices = [self.sample.get_label(key, True) for key in self.collection_keys]
        self.column_choices = [self.sample.get_label(key) for key in self.column_keys]

        self.collection_sel = self.collection_keys.index(self.collection)
        self.column_sel = 0

        # Init UI elements.
        self.ch_coll = wx.Choice(self, size=DBD_CH_COLL_SIZE, choices=self.collection_choices)
        self.ch_key = wx.Choice(self, size=DBD_CH_KEY_SIZE, choices=self.column_choices)
        self.tc_sval = wx.TextCtrl(self, value=self.search_value, size=DBD_TC_SIZE)
        self.ls_res = dv.DataViewListCtrl(self)
        self.btn_add = wx.Button(self, label=DBD_BTN_ADD)

        # Set the collection and column choice selection.
        if self.key is None:
            self.key = self.column_keys[self.column_sel]
        else:
            self.column_sel = self.column_keys.index(self.key)

        self.ch_key.SetSelection(self.column_sel)
        self.ch_coll.SetSelection(self.collection_sel)

        # Set the list columns.
        for label in self.column_choices:
            self.ls_res.AppendTextColumn(label)

        # Dialog ending buttons.
        btn_ok = wx.Button(self, wx.ID_OK)
        btn_cancel = wx.Button(self, wx.ID_CANCEL)
        btn_ok.SetDefault()

        # Set Event Bindings.
        self.Bind(wx.EVT_CHOICE, self.on_ch_coll, self.ch_coll)
        self.Bind(wx.EVT_CHOICE, self.on_ch_key, self.ch_key)
        self.Bind(wx.EVT_TEXT, self.on_text, self.tc_sval)
        self.Bind(wx.EVT_BUTTON, self.on_btn_add, self.btn_add)

        # Set sizers.
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer_search = wx.BoxSizer(wx.HORIZONTAL)
        sizer_btn = wx.StdDialogButtonSizer()

        sizer_search.Add(self.ch_coll, 0, wx.EXPAND|wx.RIGHT, BORDER)
        sizer_search.Add(self.ch_key, 0, wx.EXPAND|wx.RIGHT, BORDER)
        sizer_search.Add(self.tc_sval, 0, wx.EXPAND|wx.RIGHT, BORDER)
        sizer_search.Add(self.btn_add, 0, wx.EXPAND|wx.RIGHT, BORDER)

        sizer_btn.AddButton(btn_ok)
        sizer_btn.AddButton(btn_cancel)
        sizer_btn.Realize()

        sizer.Add(sizer_search, 0, wx.ALL, BORDER)
        sizer.Add(self.ls_res, 1, wx.EXPAND)
        sizer.Add(wx.StaticLine(self), 0, wx.EXPAND)
        sizer.Add(sizer_btn, 0, wx.ALL, BORDER)

        self.SetSizer(sizer)
        self.search_db(self.search_value)

    def on_ch_coll(self, evt):
        """Change the dialog to search from chosen collection."""
        self.collection_sel = self.ch_coll.GetSelection()
        self.column_sel = 0

        self.collection = self.collection_keys[self.collection_sel]
        self.sample = GridData(self.collection)

        self.column_keys = self.sample.get_columns()
        self.column_choices = [self.sample.get_label(key) for key in self.column_keys]
        self.key = self.column_keys[self.column_sel]

        self.ch_key.Set(self.column_choices)

        self.ch_key.SetSelection(self.column_sel)
        self.ch_coll.SetSelection(self.collection_sel)

        self.ls_res.DeleteAllItems()
        self.ls_res.ClearColumns()

        for label in self.column_choices:
            self.ls_res.AppendTextColumn(label)
        # print(f"DbDialog.on_ch_coll columns: \n\t{self.ls_res.GetColumnCount()}" +
        #       f"\n\tlen self.column_keys {len(self.column_keys)}" +
        #       f"\n\tlen self.column_choices {len(self.column_choices)}")

        self.tc_sval.Clear()
        self.search_value = ""
        self.search_db(self.search_value)

    def on_ch_key(self, evt):
        """Update key with selection."""
        self.ls_res.DeleteAllItems()
        self.key = self.column_keys[evt.GetSelection()]
        self.search_db(self.search_value)

    def on_text(self, evt):
        """Add mathes from the db with textctrl and key choice to the list."""
        self.search_value = self.tc_sval.GetValue()
        self.search_db(self.search_value)

    def on_btn_add(self, evt):
        """Open a dialog for adding or editing a database entry."""
        print("DbDialog.on_btn_add")
        obj = self.objects[self.ls_res.GetSelectedRow()]
        try:
            del obj['_id']
        except:
            pass
        # Open dialog to add new item to Database.
        with DbAddDialog(self, self.collection, self.sample, obj) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                # Check if item with given 'code already exists.
                code = dlg.object['code']
                filter = {'code': code}
                find_obj = Database(self.collection).find(filter)

                # Insert the created item if it does not exist.
                if find_obj is None:
                    oid = Database(self.collection).insert(dlg.object)
                    print(f"DbDialog.on_btn_add - Added item {code} " +
                          f"with oid: {str(oid)}")
                    # Redo the search to update added items to list.
                    if oid:
                        self.search_db(self.search_value)

                # Ask for confirmation and replace or cancel the adding of item.
                else:
                    title = DBD_REPLACE_TITLE
                    msg = DBD_REPLACE_MSG.format(code)
                    with ConfirmDialog(self, title, msg) as dlg_confirm:
                        if dlg_confirm.ShowModal() == wx.ID_OK:
                            count = Database(self.collection).replace(filter, dlg.object)
                            if count > 0:
                                print(f"DbDialog.on_btn_add - Replaced item '{code}'")
                                # Redo the search to update added items to list.
                                self.search_db(self.search_value)

                            else:
                                print(f"DbDialog.on_btn_add - Item '{code}' was not replaced.")


    def search_db(self, value):
        """Search the database and add matches to list."""
        # Set filter and get data from database.
        pattern = ("\w*" + value + "\w*")
        filter = {self.key: {'$regex': pattern, '$options': 'i'}}
        self.objects = list(Database(self.collection).find(filter, True))

        # Set data to list.
        self.ls_res.DeleteAllItems()
        for obj in self.objects:
            string_list = []
            for key in self.column_keys:
                string_list.append(str(obj[key]))
            # print(f"DbDialog.search_db - string_list len: {len(string_list)}")
            self.ls_res.AppendItem(string_list)


DBAD_TITLE = "Lisää tietokantaan {}"
DBAD_SIZE = (400, 600)
BTN_ADD = "Lisää"
DBAD_GRID_COL_W = 250

import wx.grid as wxg


class DbAddDialog(wx.Dialog):
    def __init__(self, parent, collection, grid_data, obj=None):
        self.gd: GridData = grid_data
        self.gd_children: dict = {child: GridData(child) for child in self.gd.get_children()}
        self.child_lists = {}
        self.child_add_btns = {}
        self.child_labels = {}
        self.object: dict = self.gd.get_default_dict() if obj is None else obj

        super().__init__(
            parent,
            title=DBAD_TITLE.format(self.gd.get_label(collection, True)),
            size=DBAD_SIZE,
            style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER
        )
        self.CenterOnParent()

        self.grid = wxg.Grid(self)
        self.grid.CreateGrid(len(self.object) - len(self.gd_children), 1)
        for n, (k, v) in enumerate(self.object.items()):
            if k not in self.gd_children:
                if isinstance(v, int):
                    self.grid.SetCellEditor(n, 0, wxg.GridCellNumberEditor())
                    self.grid.SetCellRenderer(n, 0, wxg.GridCellNumberRenderer())
                elif isinstance(v, float):
                    self.grid.SetCellEditor(n, 0, wxg.GridCellFloatEditor(6, 2))
                    self.grid.SetCellRenderer(n, 0, wxg.GridCellFloatRenderer(6, 2))
                    self.grid.SetCellValue(n, 0, str(v).replace('.', ','))
                    self.grid.SetRowLabelValue(n, self.gd.get_label(k))
                    continue
                elif isinstance(v, (list, dict)):
                    continue
                self.grid.SetCellValue(n, 0, str(v))
                self.grid.SetRowLabelValue(n, self.gd.get_label(k))

        self.grid.SetColLabelSize(1)
        self.grid.SetColSize(0, DBAD_GRID_COL_W)
        self.Bind(wxg.EVT_GRID_CELL_CHANGED, self.on_cell_changed, self.grid)

        for child_key in self.gd_children.keys():
            child_list = dv.DataViewListCtrl(self)
            child_add = wx.Button(self, label=BTN_ADD)
            child_label = wx.StaticText(self, label=self.gd.get_label(child_key))

            default = self.gd_children[child_key].get_default_dict()
            for key in default.keys():
                child_list.AppendTextColumn(self.gd_children[child_key].get_label(key))

            self.child_lists[child_key] = child_list
            self.child_add_btns[child_key] = child_add
            self.child_labels[child_key] = child_label

            self.Bind(wx.EVT_BUTTON, self.on_btn_child_add, self.child_add_btns[child_key])

        # Dialog ending buttons.
        btn_ok = wx.Button(self, wx.ID_OK)
        btn_cancel = wx.Button(self, wx.ID_CANCEL)
        btn_ok.SetDefault()

        # Set sizers.
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer_btn = wx.StdDialogButtonSizer()

        sizer_btn.AddButton(btn_ok)
        sizer_btn.AddButton(btn_cancel)
        sizer_btn.Realize()

        sizer.Add(self.grid, 1, wx.EXPAND|wx.ALL, BORDER)

        for key, btn in self.child_add_btns.items():
            sizer.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.TOP, BORDER)
            sizer_child_label = wx.BoxSizer(wx.HORIZONTAL)
            sizer_child_label.Add(btn, 0, wx.EXPAND|wx.ALL, BORDER)
            sizer_child_label.Add(self.child_labels[key], 0, wx.EXPAND|wx.ALL, BORDER)
            sizer.Add(sizer_child_label, 0, wx.EXPAND)
            sizer.Add(self.child_lists[key], 1, wx.EXPAND|wx.ALL, BORDER)

        sizer.Add(wx.StaticLine(self), 0, wx.EXPAND)
        sizer.Add(sizer_btn, 0, wx.ALL, BORDER)

        self.SetSizer(sizer)
        sizer.Fit(self)

    def on_cell_changed(self, evt):
        """Update the edited value to the item to add."""
        row = evt.GetRow()
        key = self.gd.get_key(row)
        value = self.grid.GetCellValue(row, 0)
        self.object[key] = convert(self.gd.get_type(row), value)

    def on_btn_child_add(self, evt):
        """Open dialog for adding a child item."""
        collection = ""
        for key, btn in self.child_add_btns.items():
            if btn == evt.GetEventObject():
                collection = key

        if collection != "":
            with DbAddDialog(self, collection, self.gd_children[key]) as dlg:
                if dlg.ShowModal() == wx.ID_OK:
                    self.object[collection] = {k: v for k, v in dlg.object.items()}
                    str_list = []
                    for value in dlg.object.values():
                        str_list.append(str(value))
                    self.child_lists[collection].AppendItem(str_list)
