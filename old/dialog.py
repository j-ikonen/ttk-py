from copy import deepcopy
import table as tb

import wx
import wx.dataview as dv

from setup_grid import SetupGrid
from database import Database
from setup import Setup


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
DBD_BTN_DEL = "Poista"
SMALL_BORDER = 2
BORDER = 5
DBD_REPLACE_TITLE = "Korvaa dokumentti"
DBD_REPLACE_MSG = "Dokumentti koodilla '{}' on tietokannassa.\nKorvaa uudella dokumentilla?"
DBD_REPLACE_SIZE = (300, 200)

DBD_BTN_OFFER_ADD = "Lisää"
DBD_BTN_OFFER_DEL = "Poista"
DBD_TXT_OFFER = "Tarjoukseen lisättävät"

DEL_FROM_DB_MSG = "Poista valinnat tietokannasta?"
DEL_FROM_DB_CAP = "Vahvista poistaminen"


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
    def __init__(self, parent, setup, collections, active_collection=None, key='code', value=""):
        """Initialize a database dialog.
        
        Args:
            - parent: Parent wx.Window.
            - setup (Setup): The page setup containing the database object definitions.
            - collections (dict): Dictionary collection_name: Setup of collection
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

        self.setup_db: Setup = self.collections[self.collection]
        self.setup: Setup = setup
        self.setup_current = self.setup.get_grandchild("data", self.collection)
        self.fields = self.setup_current["fields"]
        self.columns = self.setup_current["columns"]

        self.key = key
        self.search_value = value
        self.objects = []

        # {collection: [{obj_key: obj_val}]}
        self.to_offer = {key: [] for key in self.collections.keys()}

        self.collection_keys = list(self.collections.keys())
        self.column_keys = list(self.fields.keys())

        self.collection_choices = [
            self.setup["data"][key]['label'] for key in self.collection_keys
        ]
        self.column_choices = [
            self.fields[key]["label"] for key in self.column_keys
        ]

        # Init UI elements.
        self.ch_coll = wx.Choice(self, size=DBD_CH_COLL_SIZE, choices=self.collection_choices)
        self.ch_key = wx.Choice(self, size=DBD_CH_KEY_SIZE, choices=self.column_choices)
        self.tc_sval = wx.TextCtrl(self, value=self.search_value, size=DBD_TC_SIZE)
        self.ls_res = dv.DataViewListCtrl(self, style=dv.DV_MULTIPLE|dv.DV_ROW_LINES)
        self.ls_to_offer = dv.DataViewListCtrl(self, style=dv.DV_MULTIPLE|dv.DV_ROW_LINES)
        self.btn_add = wx.Button(self, label=DBD_BTN_ADD)
        self.btn_del = wx.Button(self, label=DBD_BTN_DEL)
        self.btn_offer_add = wx.Button(self, label=DBD_BTN_OFFER_ADD)
        self.btn_offer_del = wx.Button(self, label=DBD_BTN_OFFER_DEL)
        self.txt_to_offer = wx.StaticText(self, label=DBD_TXT_OFFER)

        # Set the collection and column choice selection.
        self.collection_sel = self.collection_keys.index(self.collection)
        self.column_sel = 0

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
        self.Bind(wx.EVT_TEXT, self.on_text, self.tc_sval)
        self.Bind(wx.EVT_CHOICE, self.on_ch_coll, self.ch_coll)
        self.Bind(wx.EVT_CHOICE, self.on_ch_key, self.ch_key)
        self.Bind(wx.EVT_BUTTON, self.on_btn_add, self.btn_add)
        self.Bind(wx.EVT_BUTTON, self.on_btn_del, self.btn_del)
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
        sizer_search.Add(self.btn_del, 0, wx.EXPAND|wx.RIGHT, BORDER)
        
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
        self.setup_db = self.collections[self.collection]
        self.setup_current = self.setup.get_grandchild("data", self.collection)
        self.fields = self.setup_current["fields"]
        self.columns = self.setup_current["columns"]

        # Get new column information.
        self.column_keys = list(self.fields.keys())
        self.column_choices = [
            self.fields[key]["label"] for key in self.column_keys
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

        # Fill the new to_offer list with already added objects.
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
        # print("DbDialog.on_btn_add")
        selected_row = self.ls_res.ItemToRow(self.ls_res.GetSelection())
        if selected_row == wx.NOT_FOUND:
            obj = None
        else:
            obj = self.objects[selected_row]

        # Open dialog to add new item to Database.
        with DbAddDialog(self, self.setup_current, obj) as dlg:

            if dlg.ShowModal() == wx.ID_OK:
                # Check if item with given 'code' already exists.
                filter = {k: dlg.object[k] for k in self.setup_db["unique_keys"]}
                count = Database(self.collection).count(filter)

                # If document exists, ask for confirmation. Return if canceled.
                if count > 0:
                    title = DBD_REPLACE_TITLE
                    msg = DBD_REPLACE_MSG.format(filter)

                    with ConfirmDialog(self, title, msg) as dlg_confirm:
                        if dlg_confirm.ShowModal() == wx.ID_CANCEL:
                            return

                # Upsert the object to database and refresh the search.
                count = Database(self.collection).replace(filter, dlg.object, True)
                self.search_db(self.search_value)

    def on_btn_del(self, evt):
        """Delete selected items from database."""
        selected_objects = []
        for item in self.ls_res.GetSelections():
            row = self.ls_res.ItemToRow(item)
            obj = self.objects[row]
            selected_objects.append(obj)

        if len(selected_objects) > 0:
            msg = DEL_FROM_DB_MSG
            title = DEL_FROM_DB_CAP
            with ConfirmDialog(self, title, msg) as dlg:
                if dlg.ShowModal() == wx.ID_OK:
                    for obj in selected_objects:
                        flt = {k: obj[k] for k in self.setup_db["unique_keys"]}
                        Database(self.collection).delete(flt)
                    self.search_db(self.search_value)

    def on_btn_offer_add(self, evt):
        """Handle button event for adding item from database to to_offer list."""
        for item in self.ls_res.GetSelections():
            row = self.ls_res.ItemToRow(item)
            obj = deepcopy(self.objects[row])

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
            
            try:
                del obj["_id"]
            except KeyError:
                pass

            string_list = []
            for key in self.column_keys:
                try:
                    val = str(obj[key])
                except KeyError as e:
                    print(f"KeyError {e} GridData({self.collection}) - " +
                           "Item from database is missing a key compared to " +
                           "what is defined in setup.\n")
                    val = ""
                string_list.append(val)
            self.ls_res.AppendItem(string_list)


DBAD_TITLE = "Lisää tietokantaan '{}'"
DBAD_SIZE = (400, 400)
BTN_ADD = "Lisää"
BTN_DEL = "Poista"
DBAD_GRID_COL_W = 250


class DbAddDialog(wx.Dialog):
    def __init__(self, parent, setup, obj=None):
        """Dialog for adding or editing items to database.
        
        Args:
            parent: Parent wx.Window.
            collection: Name of database collection. Same as name of GridData.
            setup: Setup at object to add.
            obj: For pre filling fields with data from obj. Default None for default fields.
        """
        self.setup: Setup = setup

        self.child_setups = {}
        if "child_data" in self.setup:
            for child_key in self.setup["child_data"].keys():
                self.child_setups[child_key] = setup.get_grandchild("child_data", child_key)

        self.object: dict = self.setup.get_default_object()

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

        self.grid = SetupGrid(self, tb.OfferTables(), "", "")
        self.grid.change_data(self.object, ("",))

        sizer_children = wx.BoxSizer(wx.VERTICAL)
        self.child_lists = {}   # child_key: ListCtrl
        self.add_buttons = {}
        self.del_buttons = {}

        # Create the lists for adding children to the object.
        for ckey, csetup in self.child_setups.items():
            clist = dv.DataViewListCtrl(self)
            child_add = wx.Button(self, label=BTN_ADD)
            child_del = wx.Button(self, label=BTN_DEL)
            child_label = wx.StaticText(self, label=csetup['label'])

            for value in csetup['fields'].values():
                clist.AppendTextColumn(value["label"])

            self.Bind(wx.EVT_BUTTON, self.on_btn_child_add, child_add)
            self.Bind(wx.EVT_BUTTON, self.on_btn_child_del, child_del)
            
            for child in self.object[ckey]:
                strlist = [str(child[k]) for k in csetup["fields"].keys()]
                # strlist = [str(v) for v in child.values()]
                clist.AppendItem(strlist)

            # Add the child elements to a sizer.
            sizer_child_label = wx.BoxSizer(wx.HORIZONTAL)
            sizer_child_label.Add(child_add, 0, wx.EXPAND|wx.RIGHT, BORDER)
            sizer_child_label.Add(child_del, 0, wx.EXPAND|wx.RIGHT, BORDER)
            sizer_child_label.Add(child_label, 0, wx.EXPAND|wx.RIGHT, BORDER)

            sizer_children.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.TOP, BORDER)
            sizer_children.Add(sizer_child_label, 0, wx.EXPAND|wx.ALL, BORDER)
            sizer_children.Add(clist, 1, wx.EXPAND|wx.ALL, BORDER)
            self.child_lists[ckey] = clist
            self.add_buttons[ckey] = child_add
            self.del_buttons[ckey] = child_del

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
        sizer.Add(sizer_children, 1, wx.EXPAND)

        sizer.Add(wx.StaticLine(self), 0, wx.EXPAND)
        sizer.Add(sizer_btn, 0, wx.ALL, BORDER)

        self.SetSizer(sizer)
        sizer.Fit(self)

    def on_btn_child_add(self, evt):
        """Open dialog for adding a child item."""
        eobj = evt.GetEventObject()
        key = None
        for k, btn in self.add_buttons.items():
            if eobj == btn:
                key = k
        if key is None:
            print("DbAddDialog.on_btn_child_add - no match with eobj")
            return

        csetup = self.child_setups[key]
        with DbAddDialog(self, csetup) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                if key not in self.object or not isinstance(self.object[key], list):
                    self.object[key] = []

                self.object[key].append(deepcopy(dlg.object))

                str_list = [str(val) for val in dlg.object.values()]
                self.child_lists[key].AppendItem(str_list)

    def on_btn_child_del(self, evt):
        """Delete selected children from child_list."""
        eobj = evt.GetEventObject()
        key = None
        for k, btn in self.del_buttons.items():
            if eobj == btn:
                key = k
        if key is None:
            print("DbAddDialog.on_btn_child_del - no match with eobj")
            return

        listctrl = self.child_lists[key]
        selected = listctrl.GetSelections()
        selected_rows = []

        # Get the index list of selected items.
        for item in selected:
            selected_rows.append(listctrl.ItemToRow(item))
        selected_rows.sort(reverse=True)

        for row in selected_rows:
            listctrl.DeleteItem(self.child_list.RowToItem(row))
            try:
                del self.object[key][row]
            except:
                pass
