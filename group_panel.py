import wx

from db import Database
from grid import DbGrid

from sizes import Sizes


class GroupPanel(wx.Panel):
    def __init__(self, parent, db: Database):
        super().__init__(parent)

        self.group_id: int = None

        self.predefs = DbGrid(self, db.group_predefs)
        self.materials = DbGrid(self, db.group_materials)
        self.products = DbGrid(self, db.group_products)
        self.parts = DbGrid(self, db.group_parts)

        sizer_v = wx.BoxSizer(wx.VERTICAL)
        sizer_h = wx.BoxSizer(wx.HORIZONTAL)

        sizer_v.Add(self.materials, 1, wx.EXPAND|wx.BOTTOM, Sizes.s)
        sizer_v.Add(self.products, 1, wx.EXPAND)
        sizer_v.Add(self.parts, 1, wx.EXPAND|wx.TOP, Sizes.s)

        sizer_h.Add(self.predefs, 0, wx.EXPAND|wx.RIGHT, Sizes.s)
        sizer_h.Add(sizer_v, 1, wx.EXPAND)

        self.SetSizer(sizer_h)


    def set_id(self, id: int):
        self.group_id = id

        self.predefs.set_fk(id)
        self.materials.set_fk(id)
        self.products.set_fk(id)


if __name__ == '__main__':
    db = Database(":memory:", False, True, True)

    app = wx.App()

    frame = wx.Frame(None, title="GroupPanelTest")

    Sizes.scale(frame)
    frame_size = (Sizes.frame_w, Sizes.frame_h)

    # frame.SetClientSize(frame.FromDIP(wx.Size(1200, 600)))
    frame.SetClientSize(frame_size)
    panel = GroupPanel(frame, db)

    frame.Show()
    app.MainLoop()
