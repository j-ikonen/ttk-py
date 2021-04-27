import wx
import wx.dataview as dv

from data import GridData
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

class DbDialog(wx.Dialog):
    def __init__(self, parent, collection, key="", value=""):
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

        self.collection = collection
        self.key = key
        self.search_value = value
        self.sample = GridData(self.collection)

        self.CenterOnParent()

        # Init variables for UI elements.
        ls_coll = list(DBD_COLL_LABEL.keys())
        ls_key = []

        for n in range(self.sample.get_n_columns()):
            ls_key.append(self.sample.get_label(n))

        # Init UI elements.
        self.ch_coll = wx.Choice(self, size=DBD_CH_COLL_SIZE, choices=ls_coll)
        self.ch_key = wx.Choice(self, size=DBD_CH_KEY_SIZE, choices=ls_key)
        self.tc_sval = wx.TextCtrl(self, value=self.search_value, size=DBD_TC_SIZE)
        self.ls_res = dv.DataViewListCtrl(self)
        self.btn_add = wx.Button(self, label=DBD_BTN_ADD)

        for n in range(len(ls_coll)):
            if DBD_COLL_LABEL[ls_coll[n]] == self.collection:
                self.ch_coll.SetSelection(n)

        for n, label in enumerate(ls_key):
            self.ls_res.AppendTextColumn(label)
            if self.key == self.sample.columns[self.collection][n]:
                self.ch_key.SetSelection(n)

        if self.ch_key.GetSelection() == wx.NOT_FOUND:
            sel = 0
            self.ch_key.SetSelection(sel)
            self.key = self.sample.columns[self.collection][sel]

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

    def on_ch_coll(self, evt):
        """Change the dialog to search from chosen collection."""
        self.ls_res.DeleteAllItems()
        self.collection = DBD_COLL_LABEL[evt.GetString()]
        self.sample = GridData(self.collection)

        col_keys = []
        for n in range(self.sample.get_n_columns()):
            label = self.sample.get_label(n)
            col_keys.append(label)
            self.ls_res.AppendTextColumn(label)

        self.ch_key.Set(col_keys)
        self.ch_key.SetSelection(0)
        self.key = self.sample.columns[self.collection][evt.GetSelection()]
        self.tc_sval.Clear()

    def on_ch_key(self, evt):
        """Update key with selection."""
        self.ls_res.DeleteAllItems()
        self.key = self.sample.columns[self.collection][evt.GetSelection()]

    def on_text(self, evt):
        """Add mathes from the db with textctrl and key choice to the list."""
        self.search_value = self.tc_sval.GetValue()
        pattern = ("\w*" + self.search_value + "\w*")
        self.ls_res.DeleteAllItems()

        filter = {self.key: {'$regex': pattern, '$options': 'i'}}
        print(f"DbDialog.on_text filter: {filter}")
        objects = list(Database(self.collection).find(filter, True))
        for obj in objects:
            ls_row = []
            for key in self.sample.columns[self.collection]:
                val = obj[key]
                if isinstance(val, dict):
                    container_string = f"{len(val)} osainen Dictionary"
                    ls_row.append(container_string)
                elif isinstance(val, list):
                    container_string = f"{len(val)} osainen lista"
                    ls_row.append(container_string)
                else:
                    ls_row.append(str(val))
                self.ls_res.AppendItem(ls_row)

    def on_btn_add(self, evt):
        """Open a dialog for adding or editing a database entry."""
        print("DbDialog.on_btn_add")
