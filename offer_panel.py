from decimal import Decimal
import wx
import wx.dataview as dv

from db import Database
from sizes import Sizes
from property_grid import PropertyGrid


class OfferPanel(wx.Panel):
    def __init__(self, parent, db: Database):
        super().__init__(parent)
        self.db = db
        self.grid: PropertyGrid = PropertyGrid(self, db.offers)
        self.list = self.init_list()
        self.offer_id: int = None

        self.update_list()

        # sizer = wx.BoxSizer(wx.VERTICAL)
        sizer_hor = wx.BoxSizer(wx.HORIZONTAL)
        sizer_hor.Add(self.grid, 1, wx.EXPAND)
        sizer_hor.Add(self.list, 1, wx.EXPAND)

        self.SetSizer(sizer_hor)

    def set_offer_id(self, value: int):
        """Set the offer ID value."""
        self.offer_id = value
        self.grid.set_fk(self.offer_id)
        # self.Refresh()
    
    def init_list(self) -> dv.DataViewListCtrl:
        list = dv.DataViewListCtrl(self)
        list.AppendTextColumn("Ryhmä")
        list.AppendTextColumn("Hinta")
        return list
    
    def update_list(self):
        self.list.DeleteAllItems()
        if self.offer_id is None:
            return

        groups = self.db.get_groups(self.offer_id)  # [(id, name, cost), ...]
        total = Decimal("0.00")
        width = 0
        font = wx.Font()
        dc = wx.ScreenDC()

        # Get the label size and total cost.
        dc.SetFont(font)
        for (id, name, cost) in groups:
            self.list.AppendItem((name, str(cost)), id)
            w, _ = dc.GetTextExtent(name)
            if w > width:
                width = w
            # print(width)
            total += cost

        self.list.AppendItem(("YHTEENSÄ", str(total)))
        col: dv.DataViewColumn = self.list.GetColumn(0)
        col.SetWidth(width)

    def update(self):
        """Update the panel content."""
        self.grid.update_content()
        self.update_list()


if __name__ == '__main__':
    app = wx.App()

    database = Database(print_err=True)
    offer_id = database.offers.insert_empty()
    group_id = database.groups.insert_empty(offer_id)
    database.groups.update(group_id, 2, "Testi ryhmä pitkällä nimellä")
    pr_id = database.group_products.insert_empty(group_id)
    # database.group_products.update(pr_id, 2, "Testi ryhmä")
    part_id = database.group_parts.insert_empty(pr_id)
    database.group_parts.update(part_id, 10, Decimal("123.45"))

    frame = wx.Frame(None, title="OfferPanelTest")
    panel = OfferPanel(frame, database)
    panel.set_offer_id(offer_id)
    panel.update_list()

    Sizes.scale(frame)
    frame_size = (Sizes.frame_w, Sizes.frame_h)
    frame.SetClientSize(frame_size)

    frame.Show()
    app.MainLoop()
