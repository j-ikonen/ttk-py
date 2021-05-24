import wx

import table as tb


TITLE = "Hae tietokannasta"
BTN_SEARCH = "Etsi"
BTN_AC = "Lisää hakuehto"
BTN_DC = "Poista hakuehto"
SEARCH_COND = "Hakuehdot"
BORDER = 5


class SearchPanel(wx.Panel):
    def __init__(self, parent, db: tb.OfferTables):
        super().__init__(parent)

        self.table_labels = [
            "Tarjoukset",
            "Materiaalit",
            "Tuotteet",
            "Osat"
        ]
        self.conditions = {}
        self.cond_labels = []
        self.cond_choices = []
        self.cond_texts = []
        self.cond_op = []
        self.op_labels = []

        self.db: tb.OfferTables = db
        title = wx.StaticText(self, label=TITLE)
        self.choice_table = wx.Choice(self, size=(85, -1), choices=self.table_labels)
        self.btn_add_condition = wx.Button(self, label=BTN_AC)
        self.btn_search = wx.Button(self, label=BTN_SEARCH)
        self.btn_show_cond = wx.Button(self, label=SEARCH_COND)

        self.Bind(wx.EVT_CHOICE, self.on_table_choice, self.choice_table)
        self.Bind(wx.EVT_BUTTON, self.on_add_condition, self.btn_add_condition)
        self.Bind(wx.EVT_BUTTON, self.on_search, self.btn_search)
        self.Bind(wx.EVT_BUTTON, self.on_show_conditions, self.btn_show_cond)

        self.set_table_choice(0)

        sizer_top = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_conditions = wx.StaticBoxSizer(wx.VERTICAL, self, SEARCH_COND)
        sizer = wx.BoxSizer(wx.VERTICAL)

        sizer_top.Add(title, 0, wx.RIGHT, BORDER)
        sizer_top.Add(self.choice_table, 0, wx.RIGHT, BORDER)
        sizer_top.Add(self.btn_search, 0, wx.RIGHT, BORDER)
        sizer_top.Add(self.btn_add_condition, 0, wx.RIGHT, BORDER)
        sizer_top.Add(self.btn_show_cond, 0, wx.RIGHT, BORDER)

        sizer.Add(sizer_top, 0, wx.ALL, BORDER)
        sizer.Add(self.sizer_conditions, 0, wx.ALL, BORDER)

        self.SetSizer(sizer)

    def add_condition(self):
        box: wx.StaticBox = self.sizer_conditions.GetStaticBox()
        key_choice = wx.Choice(box, size=(100, -1), choices=self.cond_labels)
        op_choice = wx.Choice(box, size=(65, -1), choices=self.op_labels)
        text = wx.TextCtrl(box, size=(120, -1))
        btn_del = wx.Button(box, label=BTN_DC)
        sizer_con = wx.BoxSizer(wx.HORIZONTAL)
        sizer_con.Add(btn_del, 0, wx.RIGHT, BORDER)
        sizer_con.Add(key_choice, 0, wx.RIGHT, BORDER)
        sizer_con.Add(op_choice, 0, wx.RIGHT, BORDER)
        sizer_con.Add(text, 0, wx.RIGHT, BORDER)
        return sizer_con

    def on_table_choice(self, evt):
        """Change the panel to search from chosen table."""
        print("table choice")

    def on_add_condition(self, evt):
        """Add a search condition line."""
        print("add condition")
        sizer = self.add_condition()
        self.sizer_conditions.Add(sizer, 0, wx.RIGHT|wx.LEFT|wx.TOP, BORDER)
        self.Layout()

    def on_search(self, evt):
        """Search from database with conditions."""
        print("search")

    def on_show_conditions(self, evt):
        """Show or hide search conditions."""
        box: wx.StaticBox = self.sizer_conditions.GetStaticBox()
        box.Show(not box.IsShown())

    def get_table_choice(self):
        """Return the index of selected item in table choice window."""
        selection = self.choice_table.GetSelection()
        if selection == wx.NOT_FOUND:
            return None
        else:
            return selection

    def set_table_choice(self, table_idx):
        """Set the index of selected item in table choice window."""
        self.choice_table.SetSelection(table_idx)


if __name__ == '__main__':
    app = wx.App()

    frame = wx.Frame(None, size=(1500, 800))
    db = tb.OfferTables()
    panel = SearchPanel(frame, db)
    frame.Show()

    app.MainLoop()