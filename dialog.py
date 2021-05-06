from copy import deepcopy
from setup_grid import SetupGrid
from ttk_data import FIELD_LABEL, FIELD_TYPE, str2type

import wx
import wx.dataview as dv

from database import Database


DBD_TITLE = "Tietokanta"
DBD_SIZE = (1000, 600)
DBD_CH_COLL_SIZE = (80, -1)
DBD_CH_KEY_SIZE = (80, -1)
DBD_TC_SIZE = (120, -1)
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

DBD_BTN_OFFER_ADD = "Lisää"
DBD_BTN_OFFER_DEL = "Poista"
DBD_TXT_OFFER = "Tarjoukseen lisättävät"


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
    def __init__(self, parent, collections, child_setups, active_collection=None, key='code', value=""):
        """Initialize a database dialog.
        
        Args:
            - parent: Parent wx.Window.
            - collections (dict): Dictionary collection_name: collection_setup
            - active_collection (str): Key to the collection to be opened.
            Defaults to idx 0 in collections.
            - key (str): Key to a field in collection. Defaults to 'code'.
            - value (str): Search value. Defaults to "".
        """
        super().__init__(
            parent,
            title=DBD_TITLE,
            size=DBD_SIZE,
            style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER
        )

        self.CenterOnParent()

        self.collections: dict = collections
        self.collection = active_collection
        if self.collection is None:
            self.collection = list(self.collections.keys())[0]
        self.setup = self.collections[self.collection]
        self.key = key
        self.search_value = value
        self.child_setups = child_setups
        self.objects = []

        # {collection: [{obj_key: obj_val}]}
        self.to_offer = {key: [] for key in self.collections.keys()}

        self.collection_keys = list(self.collections.keys())
        self.column_keys = list(self.setup['fields'].keys())

        self.collection_choices = [
            self.collections[key]['label'] for key in self.collection_keys
        ]
        self.column_choices = [
            self.setup['fields'][key][FIELD_LABEL] for key in self.column_keys
        ]

        self.collection_sel = self.collection_keys.index(self.collection)
        self.column_sel = 0

        # Init UI elements.
        self.ch_coll = wx.Choice(self, size=DBD_CH_COLL_SIZE, choices=self.collection_choices)
        self.ch_key = wx.Choice(self, size=DBD_CH_KEY_SIZE, choices=self.column_choices)
        self.tc_sval = wx.TextCtrl(self, value=self.search_value, size=DBD_TC_SIZE)
        self.ls_res = dv.DataViewListCtrl(self)
        self.ls_to_offer = dv.DataViewListCtrl(self)
        self.btn_add = wx.Button(self, label=DBD_BTN_ADD)
        self.btn_offer_add = wx.Button(self, label=DBD_BTN_OFFER_ADD)
        self.btn_offer_del = wx.Button(self, label=DBD_BTN_OFFER_DEL)
        self.txt_to_offer = wx.StaticText(self, label=DBD_TXT_OFFER)

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
            self.ls_to_offer.AppendTextColumn(label)

        # Dialog ending buttons.
        btn_ok = wx.Button(self, wx.ID_OK)
        btn_cancel = wx.Button(self, wx.ID_CANCEL)
        btn_ok.SetDefault()

        # Set Event Bindings.
        self.Bind(wx.EVT_CHOICE, self.on_ch_coll, self.ch_coll)
        self.Bind(wx.EVT_CHOICE, self.on_ch_key, self.ch_key)
        self.Bind(wx.EVT_TEXT, self.on_text, self.tc_sval)
        self.Bind(wx.EVT_BUTTON, self.on_btn_add, self.btn_add)
        self.Bind(wx.EVT_BUTTON, self.on_btn_offer_add, self.btn_offer_add)
        self.Bind(wx.EVT_BUTTON, self.on_btn_offer_del, self.btn_offer_del)

        # Set sizers.
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer_search = wx.BoxSizer(wx.HORIZONTAL)
        sizer_offer = wx.BoxSizer(wx.HORIZONTAL)
        sizer_btn = wx.StdDialogButtonSizer()

        # DB row
        sizer_search.Add(self.ch_coll, 0, wx.EXPAND|wx.RIGHT, BORDER)
        sizer_search.Add(self.ch_key, 0, wx.EXPAND|wx.RIGHT, BORDER)
        sizer_search.Add(self.tc_sval, 0, wx.EXPAND|wx.RIGHT, BORDER)
        sizer_search.Add(self.btn_add, 0, wx.EXPAND|wx.RIGHT, BORDER)
        
        # Offer row
        sizer_offer.Add(self.txt_to_offer, 0, wx.EXPAND|wx.RIGHT, BORDER)
        sizer_offer.Add(self.btn_offer_add, 0, wx.EXPAND|wx.RIGHT, BORDER)
        sizer_offer.Add(self.btn_offer_del, 0, wx.EXPAND|wx.RIGHT, BORDER)

        # Dialog button row
        sizer_btn.AddButton(btn_ok)
        sizer_btn.AddButton(btn_cancel)
        sizer_btn.Realize()

        sizer.Add(sizer_search, 0, wx.ALL, BORDER)
        sizer.Add(self.ls_res, 1, wx.EXPAND)
        sizer.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.ALL, BORDER)
        sizer.Add(sizer_offer, 0, wx.ALL, BORDER)
        sizer.Add(self.ls_to_offer, 1, wx.EXPAND)
        sizer.Add(wx.StaticLine(self), 0, wx.EXPAND)
        sizer.Add(sizer_btn, 0, wx.ALL, BORDER)

        self.SetSizer(sizer)
        self.search_db(self.search_value)

    def on_ch_coll(self, evt):
        """Change the dialog to search from chosen collection."""
        self.collection_sel = self.ch_coll.GetSelection()
        self.column_sel = 0

        self.collection = self.collection_keys[self.collection_sel]
        self.setup = self.collections[self.collection]

        # if self.collection not in self.to_offer:
        #     self.to_offer[self.collection] = []

        # Get new column information.
        self.column_keys = list(self.setup['fields'].keys())
        self.column_choices = [
            self.setup['fields'][key][FIELD_LABEL] for key in self.column_keys
        ]
        self.key = self.column_keys[self.column_sel]

        # Set new columns to Choice.
        self.ch_key.Set(self.column_choices)

        # Set choice selections.
        self.ch_key.SetSelection(self.column_sel)
        self.ch_coll.SetSelection(self.collection_sel)

        # Clear the lists.
        self.ls_res.DeleteAllItems()
        self.ls_res.ClearColumns()
        self.ls_to_offer.DeleteAllItems()
        self.ls_to_offer.ClearColumns()

        # Add new columns to lists.
        for label in self.column_choices:
            self.ls_res.AppendTextColumn(label)
            self.ls_to_offer.AppendTextColumn(label)

        # Fill the to_offer list with already added objects.
        for obj in self.to_offer[self.collection]:
            strlist = [str(obj[key]) for key in self.column_keys]
            self.ls_to_offer.AppendItem(strlist)

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
        selected_row = self.ls_res.ItemToRow(self.ls_res.GetSelection())
        if selected_row == wx.NOT_FOUND:
            obj = None
        else:
            obj = self.objects[selected_row]
        try:
            del obj['_id']
        except:
            pass
        if 'child' in self.setup:
            child_setup = self.child_setups[self.collection + '.' + self.setup['child']]
        else:
            child_setup = None

        print(f"\non_btn_add obj: {obj}")
        # Open dialog to add new item to Database.
        with DbAddDialog(self, self.setup, child_setup, obj) as dlg:
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

    def on_btn_offer_add(self, evt):
        """Handle button event for adding item from database to to_offer list."""
        for item in self.ls_res.GetSelections():
            row = self.ls_res.ItemToRow(item)
            obj = deepcopy(self.objects[row])

            try:
                del obj['_id']
            except:
                pass

            strlist = [str(obj[key]) for key in self.column_keys]
            self.ls_to_offer.AppendItem(strlist)
            self.to_offer[self.collection].append(obj)

    def on_btn_offer_del(self, evt):
        """Handle button event for deleting item from to_offer list."""
        for item in self.ls_to_offer.GetSelections():
            row = self.ls_to_offer.ItemToRow(item)
            self.ls_to_offer.DeleteItem(row)
            del self.to_offer[self.collection][row]

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
                try:
                    val = str(obj[key])
                except KeyError as e:
                    print(f"KeyError {e} GridData({self.collection}) - " +
                           "Item from database is missing a key compared to " +
                           "what is defined in application.\n")
                    val = ""
                string_list.append(val)
            # print(f"DbDialog.search_db - string_list len: {len(string_list)}")
            self.ls_res.AppendItem(string_list)


DBAD_TITLE = "Lisää tietokantaan {}"
DBAD_SIZE = (400, 400)
BTN_ADD = "Lisää"
DBAD_GRID_COL_W = 250

import wx.grid as wxg


class DbAddDialog(wx.Dialog):
    def __init__(self, parent, setup, child_setup=None, obj=None):
        """Dialog for adding or editing items to database.
        
        Args:
            parent: Parent wx.Window.
            collection: Name of database collection. Same as name of GridData.
            setup: Dictionary for formatting items.
            obj: For pre filling fields with data from obj. Default None for default fields.
        """
        self.setup: dict = setup
        self.child_setup: dict = child_setup

        if child_setup is None:
            self.child_name = None
        else:
            self.child_name = setup['child']

        self.object: dict = {k: v[0] for k, v in self.setup['fields'].items()}
        if self.child_name is not None:
            self.object[self.child_name] = []

        # Overwrite default object fields with ones from arg obj.
        if obj:
            for k, v in obj.items():
                if k in self.object:
                    self.object[k] = deepcopy(v)

        super().__init__(
            parent,
            title=DBAD_TITLE.format(setup['label']),
            size=DBAD_SIZE,
            style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER
        )
        self.CenterOnParent()

        self.grid = SetupGrid(self, self.setup)
        self.grid.change_data(self.object)

        self.Bind(wxg.EVT_GRID_CELL_CHANGED, self.on_cell_changed, self.grid)

        if self.child_setup is not None:
            self.child_list = dv.DataViewListCtrl(self)
            child_add = wx.Button(self, label=BTN_ADD)
            child_label = wx.StaticText(self, label=self.child_setup['label'])

            for value in self.child_setup['fields'].values():
                self.child_list.AppendTextColumn(value[FIELD_LABEL])

            self.Bind(wx.EVT_BUTTON, self.on_btn_child_add, child_add)

            for child in self.object[self.setup['child']]:
                strlist = [str(v) for v in child.values()]
                self.child_list.AppendItem(strlist)

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

        sizer.Add(self.grid, 0, wx.EXPAND|wx.ALL, BORDER)

        if self.child_setup is not None:
            sizer.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.TOP, BORDER)
            sizer_child_label = wx.BoxSizer(wx.HORIZONTAL)
            sizer_child_label.Add(child_add, 0, wx.EXPAND|wx.ALL, BORDER)
            sizer_child_label.Add(child_label, 0, wx.EXPAND|wx.ALL, BORDER)
            sizer.Add(sizer_child_label, 0, wx.EXPAND)
            sizer.Add(self.child_list, 1, wx.EXPAND|wx.ALL, BORDER)

        sizer.Add(wx.StaticLine(self), 0, wx.EXPAND)
        sizer.Add(sizer_btn, 0, wx.ALL, BORDER)

        self.SetSizer(sizer)
        sizer.Fit(self)

    def on_cell_changed(self, evt):
        """Update the edited value to the item to add."""
        row = evt.GetRow()
        key = list(self.object)[row]   # Uses all fields instead of columns.
        value = str2type(self.setup['fields'][key][FIELD_TYPE], self.grid.GetCellValue(row, 0))
        self.object[key] = value

    def on_btn_child_add(self, evt):
        """Open dialog for adding a child item."""
        with DbAddDialog(self, self.child_setup) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                if not isinstance(self.object[self.child_name], list):
                    self.object[self.child_name] = []

                self.object[self.child_name].append(deepcopy(dlg.object))

                str_list = [str(val) for val in dlg.object.values()]
                self.child_list.AppendItem(str_list)

    def on_btn_child_delete(self, evt):
        """Delete selected children from child_list."""
        selected = self.child_list.GetSelections()
        sel_idx = []
        for item in selected:
            sel_idx.append(self.child_list.ItemToRow(item))
        sel_idx.sort(reverse=True)
        for idx in sel_idx:
            self.child_list.DeleteItem(self.child_list.RowToItem(idx))
            try:
                del self.object[self.setup['child']][idx]
            except:
                pass
