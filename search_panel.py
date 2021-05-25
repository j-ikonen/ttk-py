import wx

import table as tb


TITLE = "Hae tietokannasta"
BTN_SEARCH = "Etsi"
BTN_AC = "Lisää hakuehto"
BTN_DC = "Poista hakuehto"
SEARCH_COND = "Hakuehdot"
BORDER = 5


class SearchPanel(wx.Panel):
    def __init__(self, parent, db: tb.OfferTables, table: str="offers"):
        super().__init__(parent)

        self.table_labels = [
            "Tarjoukset",
            "Materiaalit",
            "Tuotteet",
            "Osat"
        ]
        self.tables = [
            "offers",
            "materials",
            "products",
            "parts"
        ]
        self.cond_labels = [[], [], [], []]
        self.op_labels = ["=", "like", "!=", ">", "<", ">=", "<=", "!>", "!<"]
        self.conditions = {}
        self.cond_sizers = []

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


        sizer_top = wx.BoxSizer(wx.HORIZONTAL)
        # self.sizer_conditions = wx.StaticBoxSizer(wx.VERTICAL, self, SEARCH_COND)
        sizer = wx.BoxSizer(wx.VERTICAL)

        sizer_top.Add(title, 0, wx.RIGHT, BORDER)
        sizer_top.Add(self.choice_table, 0, wx.RIGHT, BORDER)
        sizer_top.Add(self.btn_search, 0, wx.RIGHT, BORDER)
        sizer_top.Add(self.btn_add_condition, 0, wx.RIGHT, BORDER)
        sizer_top.Add(self.btn_show_cond, 0, wx.RIGHT, BORDER)

        sizer.Add(sizer_top, 0, wx.ALL, BORDER)
        for n in range(len(self.table_labels)):
            box_sizer = wx.StaticBoxSizer(wx.VERTICAL, self, SEARCH_COND)
            box_sizer.AddSpacer(BORDER)
            self.cond_sizers.append(box_sizer)
            self.add_condition(n)
            sizer.Add(box_sizer, 0, wx.ALL, BORDER)
        # sizer.Add(self.sizer_conditions, 0, wx.ALL, BORDER)

        self.SetSizer(sizer)
        self.set_table_choice(self.tables.index(table))
        self.Layout()

    def get_table(self):
        """Return the selected table name or None if nothing is selected."""
        sel = self.table_selection()
        if sel == None:
            return None
        return self.tables[sel]

    def add_condition(self, table: int):
        """Add a condition to search condition box in table index."""
        sizer_table = self.cond_sizers[table]
        box: wx.StaticBox = sizer_table.GetStaticBox()

        self.Freeze()   # Prevent flicker when creating the new windows.

        btn_del = wx.Button(box, label=BTN_DC)
        key_choice = wx.Choice(box, size=(120, -1), choices=self.cond_labels[table])
        op_choice = wx.Choice(box, size=(45, -1), choices=self.op_labels)
        text = wx.TextCtrl(box, size=(200, -1))

        sizer_con = wx.BoxSizer(wx.HORIZONTAL)
        sizer_con.Add(btn_del, 0, wx.RIGHT, BORDER)
        sizer_con.Add(key_choice, 0, wx.RIGHT, BORDER)
        sizer_con.Add(op_choice, 0, wx.RIGHT, BORDER)
        sizer_con.Add(text, 0, wx.RIGHT, BORDER)
        sizer_table.Add(sizer_con, 0, wx.LEFT|wx.BOTTOM|wx.RIGHT, BORDER)

        self.Thaw()

        self.Bind(wx.EVT_CHOICE, self.on_choice_key, key_choice)
        self.Bind(wx.EVT_CHOICE, self.on_choice_op, op_choice)
        self.Bind(wx.EVT_TEXT_ENTER, self.on_text_enter, text)
        self.Bind(wx.EVT_BUTTON, self.on_btn_del, btn_del)


    def on_choice_key(self, evt):
        """."""
        print("on choice key")

    def on_choice_op(self, evt):
        """."""
        print("on choice op")

    def on_text_enter(self, evt):
        """."""
        print("on text enter")

    def on_btn_del(self, evt):
        """Delete the search condition row."""
        sel = self.table_selection()
        if sel is None:
            return

        sizer = evt.GetEventObject().GetContainingSizer()   # Get sizer that has button
        sizer.Clear(True)   # Destroy the windows in the sizer.
        self.cond_sizers[sel].Remove(sizer) # Destroy the now empty sizer.

        self.Layout()

    def on_table_choice(self, evt):
        """Change the panel to search from chosen table."""
        sel = self.table_selection()
        if sel is not None:
            for n, sizer in enumerate(self.cond_sizers):
                box: wx.StaticBox = sizer.GetStaticBox()
                if n != sel:
                    box.Show(False)
                else:
                    box.Show(True)
        self.Layout()

    def on_add_condition(self, evt):
        """Add a search condition line."""
        sel = self.table_selection()
        if sel is None:
            return
        self.add_condition(sel)
        self.Layout()

    def on_search(self, evt):
        """Search from database with conditions."""
        print("search")

    def on_show_conditions(self, evt):
        """Show or hide search conditions."""
        sel = self.table_selection()
        if sel is None:
            return
        box: wx.StaticBox = self.cond_sizers[sel].GetStaticBox()
        box.Show(not box.IsShown())

    def table_selection(self):
        """Return the index of selected item in table choice window."""
        selection = self.choice_table.GetSelection()
        if selection == wx.NOT_FOUND:
            return None
        else:
            return selection

    def set_table_choice(self, table_idx):
        """Set the index of selected item in table choice window."""
        self.choice_table.SetSelection(table_idx)
        self.on_table_choice(None)


if __name__ == '__main__':
    app = wx.App()

    frame = wx.Frame(None, size=(1500, 800))
    db = tb.OfferTables()
    panel = SearchPanel(frame, db)
    frame.Show()

    app.MainLoop()