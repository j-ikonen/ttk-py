from decimal import Decimal

import wx

from bookpanel import BookPanel
from sizes import Sizes
from db import Database


class SelectionPanel(wx.Panel):
    def __init__(self, parent, db: Database):
        super().__init__(parent)

        self.db = db
        self.book = BookPanel(self, db)
        self.choice_offer = wx.Choice(self)
        self.choice_group = wx.Choice(self)
        self.btn_new_group = wx.Button(self, label="Uusi ryhmä")
        self.btn_change_group = wx.Button(self, label="Muuta ryhmän nimeä")
        self.btn_new_offer = wx.Button(self, label="Uusi tarjous")
        self.btn_close_offer = wx.Button(self, label="Sulje tarjous")
        # self.btn_open_offer = wx.Button(self, label="Avaa tarjous")
        self.btn_del_offer = wx.Button(self, label="Poista tarjous")
        self.btn_del_group = wx.Button(self, label="Poista ryhmä")

        self.Bind(wx.EVT_BUTTON, self.on_close_offer, self.btn_close_offer)

        sizer_left = wx.BoxSizer(wx.VERTICAL)
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        sizer_left.Add(self.choice_offer, 0, wx.EXPAND)
        sizer_left.Add(self.choice_group, 0, wx.EXPAND)
        sizer_left.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.ALL, Sizes.m)
        sizer_left.Add(self.btn_new_group, 0, wx.EXPAND)
        sizer_left.Add(self.btn_change_group, 0, wx.EXPAND)
        sizer_left.Add(self.btn_new_offer, 0, wx.EXPAND)
        # sizer_left.Add(self.btn_open_offer, 0, wx.EXPAND)
        sizer_left.Add(self.btn_close_offer, 0, wx.EXPAND)
        sizer_left.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.ALL, Sizes.m)
        sizer_left.Add(self.btn_del_offer, 0, wx.EXPAND)
        sizer_left.Add(self.btn_del_group, 0, wx.EXPAND)

        sizer.Add(sizer_left, 0, wx.EXPAND)
        sizer.Add(self.book, 1, wx.EXPAND)
        self.SetSizer(sizer)

    def select_group(self, group_id: int):
        """Set the given group as active."""
        self.book.select_group(group_id)

    def select_offer(self, offer_id: int):
        """Set the given offer as active."""
        self.book.select_offer(offer_id)

    def on_close_offer(self, evt):
        """Handle event for opening an offer."""
        self.db.open_offers.remove(self.book.selected_offer)
        self.choice_offer.Clear()
        self.update_choices()
    
    def update_choices(self):
        """Update the contents of the choice windows."""
        offers = self.db.get_open_offer_labels()


if __name__ == '__main__':
    app = wx.App()

    database = Database(print_err=True)
    offer_id = database.offers.insert_empty()
    group_id = database.groups.insert_empty(offer_id)
    database.groups.update(group_id, 2, "Testi ryhmä pitkällä nimellä")
    pr_id = database.group_products.insert_empty(group_id)
    part_id = database.group_parts.insert_empty(pr_id)
    database.group_parts.update(part_id, 10, Decimal("123.45"))

    frame = wx.Frame(None, title="SelectionPanelTest")
    panel = SelectionPanel(frame, database)

    panel.select_offer(offer_id)
    panel.select_group(group_id)

    Sizes.scale(frame)
    frame_size = (Sizes.frame_w, Sizes.frame_h)
    frame.SetClientSize(frame_size)

    frame.Show()
    app.MainLoop()
