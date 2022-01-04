"""Main panel containing group selection and editing."""

import wx
import wx.dataview as dv

from gui.group_list import GroupList
from gui.group_panel import GroupPanel
from gui.table import Table
from quote import Quote
import values as val


class MainPanel(wx.Panel):
    """."""
    def __init__(self, parent, quote):
        super().__init__(parent)

        self.quote = quote
        self.group_list = GroupList(self, quote)
        self.group_panel = GroupPanel(self, quote)
        self.quote_btn = wx.Button(self, label="Valitse tarjous")
        # self.group_label = wx.StaticText(self, label="Ryhmät:")
        self.new_group_btn = wx.Button(self, label="Uusi")
        self.del_group_btn = wx.Button(self, label="Poista")
        self.materials_table = Table(self, quote)

        self.Bind(wx.EVT_BUTTON, self.on_quote, self.quote_btn)
        self.Bind(wx.EVT_BUTTON, self.on_new_group, self.new_group_btn)
        self.Bind(wx.EVT_BUTTON, self.on_del_group, self.del_group_btn)
        self.quote.state.bind(val.EVT_OPEN_QUOTE, self.on_open_quote)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer_left = wx.BoxSizer(wx.VERTICAL)
        sizer_group_btns = wx.BoxSizer(wx.HORIZONTAL)

        sizer_group_btns.Add(self.del_group_btn, 1, wx.EXPAND)
        sizer_group_btns.Add(self.new_group_btn, 1, wx.EXPAND)

        sizer_left.Add(self.quote_btn, 0, wx.EXPAND)
        # sizer_left.Add(self.group_label, 0, wx.EXPAND|wx.ALL, 5)
        sizer_left.Add(self.group_list, 1, wx.EXPAND)
        sizer_left.Add(sizer_group_btns, 0, wx.EXPAND)

        sizer.Add(sizer_left, 0, wx.EXPAND)
        sizer.Add(self.group_panel, 0, wx.EXPAND)
        self.SetSizer(sizer)

    def on_quote(self, _evt):
        """Open the quote control dialog."""
        with QuoteDialog(self, self.quote) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                sel = dlg.get_selection()
                if sel:
                    self.quote.open_quote(sel[0], sel[1])
                else:
                    print("No quote selected.")

    def on_open_quote(self):
        """Handle changing the button label for quote."""
        label = self.quote.state.open_quote_label
        if not label:
            label = "Valitse tarjous"
        self.quote_btn.SetLabel(label)

    def on_new_group(self, _evt):
        """Handle new group event"""
        self.quote.new_group()
        self.quote.state.event(val.EVT_NEW_GROUP)

    def on_del_group(self, _evt):
        """Handle delete group event"""
        self.quote.state.event(val.EVT_DELETE_GROUP)


class QuoteDialog(wx.Dialog):
    """Dialog for creating, opening and deleting quotes."""
    def __init__(self, parent, quote):
        super().__init__(parent, title="Valitse Tarjous",
                         style=wx.RESIZE_BORDER)

        self.quote: Quote = quote
        self.new_quote_btn = wx.Button(self, label="Uusi")
        self.search = wx.SearchCtrl(self)
        self.result: dv.DataViewListCtrl = dv.DataViewListCtrl(self, size=(-1, 350))
        line = wx.StaticLine(self, size=(20, -1), style=wx.LI_HORIZONTAL)
        btn_ok = wx.Button(self, wx.ID_OK)
        btn_no = wx.Button(self, wx.ID_CANCEL)

        self.result.AppendTextColumn("Tarjoukset")
        btn_ok.SetDefault()

        self.Bind(wx.EVT_SEARCH, self.on_search, self.search)
        self.Bind(wx.EVT_BUTTON, self.on_new, self.new_quote_btn)

        sizer = wx.BoxSizer(wx.VERTICAL)
        btn_sizer = wx.StdDialogButtonSizer()

        btn_sizer.AddButton(btn_ok)
        btn_sizer.AddButton(btn_no)
        btn_sizer.Realize()

        sizer.Add(self.new_quote_btn, 0, wx.EXPAND)
        sizer.Add(self.search, 0, wx.EXPAND)
        sizer.Add(self.result, 1, wx.EXPAND)
        sizer.Add(line, 0, wx.EXPAND|wx.RIGHT|wx.TOP|wx.LEFT, 5)
        sizer.Add(btn_sizer, 0, wx.EXPAND|wx.ALL, 5)

        self.SetSizer(sizer)
        sizer.Fit(self)

    def on_search(self, evt):
        """Handle search event."""
        self.do_search(evt.GetString())

    def on_new(self, _evt):
        """Create a new quote."""
        name = self.search.GetValue()
        if name == "":
            print("Can not create a quote with an empty name string.")
            return
        self.quote.new_quote(name)
        self.do_search(name)
        self.result.SelectRow(0)

    def get_selection(self):
        """Return the selected item as [id, name]."""
        item = self.result.GetSelection()
        if item.IsOk():
            row = self.result.ItemToRow(item)
            return [self.result.GetItemData(item), self.result.GetValue(row, 0)]
        return None

    def do_search(self, name):
        """Do a search and fill the result list."""
        self.result.DeleteAllItems()
        quotes = self.quote.get_quotes(name)
        for row in quotes:
            self.result.AppendItem([row[1]], row[0])


if __name__ == '__main__':
    print("main_panel.py")
