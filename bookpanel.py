from decimal import Decimal

import wx

from search_panel import SearchPanel
from offer_panel import OfferPanel
from group_panel import GroupPanel
from db import Database
from sizes import Sizes


class BookPanel(wx.Panel):
    def __init__(self, parent, db: Database):
        super().__init__(parent)
        self.db = db
        self.selected_offer: int = None
        self.selected_group: int = None
        self.book = wx.Notebook(self)
        self.search = SearchPanel(self.book, db)
        self.group = GroupPanel(self.book, db)
        self.offer = OfferPanel(self.book, db)
        self.book.AddPage(self.search, "Tietokanta")
        self.book.AddPage(self.offer, "Tarjous")
        self.book.AddPage(self.group, "Ryhmä")

        self.Bind(wx.EVT_BOOKCTRL_PAGE_CHANGED, self.on_page_changed, self.book)

        sizer = wx.BoxSizer(wx.VERTICAL)

        sizer.Add(self.book, 1, wx.EXPAND)
        self.SetSizer(sizer)

    def select_offer(self, offer_id: int):
        if offer_id != self.selected_offer:
            self.group.set_id(None)
        self.search.select_offer(offer_id)
        self.offer.set_offer_id(offer_id)
        self.selected_offer = offer_id
    
    def select_group(self, group_id: int):
        """Select the active group."""
        self.group.set_id(group_id)
        self.search.select_group(group_id)

    def on_page_changed(self, evt):
        page = self.book.GetPage(evt.GetSelection())
        page.update()


if __name__ == '__main__':
    app = wx.App()

    database = Database(print_err=True)
    offer_id = database.offers.insert_empty()
    group_id = database.groups.insert_empty(offer_id)
    database.groups.update(group_id, 2, "Testi ryhmä pitkällä nimellä")
    pr_id = database.group_products.insert_empty(group_id)
    part_id = database.group_parts.insert_empty(pr_id)
    database.group_parts.update(part_id, 10, Decimal("123.45"))

    frame = wx.Frame(None, title="OfferPanelTest")
    panel = BookPanel(frame, database)

    panel.select_offer(offer_id)
    panel.select_group(group_id)
    # panel.set_offer_id(offer_id)
    # panel.update_list()

    Sizes.scale(frame)
    frame_size = (Sizes.frame_w, Sizes.frame_h)
    frame.SetClientSize(frame_size)

    frame.Show()
    app.MainLoop()
