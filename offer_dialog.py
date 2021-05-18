import wx
import wx.dataview as dv

import table as tb

BORDER = 5
TITLE_OPEN_OFFER = "Avaa tarjous"
LABEL_NAME = "Tarjouksen Nimi"


class OfferDialog(wx.Dialog):
    def __init__(self, parent, tables, open_offers):
        super().__init__(
            parent,
            title=TITLE_OPEN_OFFER,
            style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER
        )
        self.CenterOnParent()

        self.tables: tb.OfferTables = tables
        self.open_offers = open_offers
        self.selected_id = None
        self.list_ids = []

        self.search = wx.SearchCtrl(self, size=(180,-1))
        self.listctrl = dv.DataViewListCtrl(self)

        btn_ok = wx.Button(self, wx.ID_OK)
        btn_cancel = wx.Button(self, wx.ID_CANCEL)


        self.listctrl.AppendTextColumn(LABEL_NAME)
        btn_ok.SetDefault()

        self.Bind(wx.EVT_SEARCH, self.on_search, self.search)
        self.Bind(dv.EVT_DATAVIEW_SELECTION_CHANGED, self.on_selection, self.listctrl)
        self.Bind(dv.EVT_DATAVIEW_ITEM_ACTIVATED, self.on_activate, self.listctrl)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer_label = wx.BoxSizer(wx.HORIZONTAL)
        sizer_btn = wx.StdDialogButtonSizer()

        sizer_label.Add(self.search, 0, wx.EXPAND)

        sizer_btn.AddButton(btn_ok)
        sizer_btn.AddButton(btn_cancel)
        sizer_btn.Realize()

        sizer.Add(sizer_label, 0, wx.EXPAND|wx.LEFT|wx.TOP|wx.RIGHT, BORDER)
        sizer.Add(self.listctrl, 1, wx.EXPAND|wx.ALL, BORDER)
        sizer.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.LEFT|wx.RIGHT, BORDER)
        sizer.Add(sizer_btn, 0, wx.ALL, BORDER)
        self.SetSizer(sizer)

    def on_activate(self, evt):
        """Return from dialog on list item activation."""
        item = evt.GetItem()
        if item.IsOk():
            row = self.listctrl.ItemToRow(item)
            self.selected_id = self.list_ids[row]
            self.EndModal(wx.ID_OK)
        else:
            self.selected_id = None

    def on_search(self, evt):
        """Find search results from offers table
        
        Fill the list with the ones not opened.
        """
        value = evt.GetString()
        
        data = self.tables.get(
            "offers",
            ["id", "name"],
            ["name"],
            ["%" + value + "%"],
            True,
            " LIKE "
        )

        self.listctrl.DeleteAllItems()
        self.list_ids.clear()
        for row in data:
            if row[0] not in self.open_offers:
                self.listctrl.AppendItem([row[1]])
                self.list_ids.append(row[0])

    def on_selection(self, evt):
        """Set the selected item."""
        item = evt.GetItem()
        if item.IsOk():
            row = self.listctrl.ItemToRow(item)
            self.selected_id = self.list_ids[row]
        else:
            self.selected_id = None