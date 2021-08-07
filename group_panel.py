import wx
import wx.grid as wxg

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

        self.txt_predefs = wx.StaticText(self, label="Esimääritykset")
        self.txt_materials = wx.StaticText(self, label="Materiaalit")
        self.txt_products = wx.StaticText(self, label="Tuotteet")
        self.txt_parts = wx.StaticText(self, label="Osat")
        self.txt_parts_parent = wx.StaticText(self, label="[ei valintaa]")

        self.predefs.register_on_cell_change(self.parts.update_content)
        self.predefs.register_on_cell_change(self.products.update_content)
        self.materials.register_on_cell_change(self.parts.update_content)
        self.materials.register_on_cell_change(self.products.update_content)
        self.products.register_on_cell_change(self.parts.update_content)
        # Recalculate possible changes in part costs due to product size change.
        self.products.register_on_cell_change(self.products.update_content)
        self.parts.register_on_cell_change(self.products.update_content)

        sizer_vr = wx.BoxSizer(wx.VERTICAL)
        sizer_vl = wx.BoxSizer(wx.VERTICAL)
        sizer_h = wx.BoxSizer(wx.HORIZONTAL)
        sizer_parts_label = wx.BoxSizer(wx.HORIZONTAL)

        sizer_vr.Add(self.txt_materials, 0, wx.EXPAND)
        sizer_vr.Add(self.materials, 1, wx.EXPAND|wx.BOTTOM, Sizes.s)
        sizer_vr.Add(self.txt_products, 0, wx.EXPAND)
        sizer_vr.Add(self.products, 1, wx.EXPAND|wx.BOTTOM, Sizes.s)

        sizer_parts_label.Add(self.txt_parts, 0, wx.EXPAND|wx.RIGHT, Sizes.m)
        sizer_parts_label.Add(self.txt_parts_parent, 0, wx.EXPAND)
        sizer_vr.Add(sizer_parts_label)
        sizer_vr.Add(self.parts, 1, wx.EXPAND)

        sizer_vl.Add(self.txt_predefs, 0, wx.EXPAND)
        sizer_vl.Add(self.predefs, 1, wx.EXPAND)

        sizer_h.Add(sizer_vl, 0, wx.EXPAND|wx.ALL, Sizes.s)
        sizer_h.Add(sizer_vr, 1, wx.EXPAND|wx.RIGHT|wx.TOP|wx.BOTTOM, Sizes.s)

        self.Bind(wxg.EVT_GRID_SELECT_CELL, self.on_select_product, self.products)

        self.SetSizer(sizer_h)

    def set_id(self, id: int):
        self.group_id = id

        self.predefs.set_fk(id)
        self.materials.set_fk(id)
        self.products.set_fk(id)
        self.parts.set_fk(None)

    def on_select_product(self, evt):
        row = evt.GetRow()
        if row == self.products.GetNumberRows() - 1:
            self.txt_parts_parent.SetLabel("[ei valintaa]")
            self.parts.set_fk(None)
        else:
            try:
                self.parts.set_fk(self.products.GetTable().GetValue(row, 0))
            except IndexError:
                self.txt_parts_parent.SetLabel("[ei valintaa]")
            else:
                self.txt_parts_parent.SetLabel(
                    "[{}]".format(self.products.GetCellValue(row, 2))
                )
        evt.Skip()

    def on_change_fk_test(self, evt):
        if self.group_id == 1:
            self.set_id(2)
        elif self.group_id == 2:
            self.set_id(1)
        else:
            self.set_id(1)

    def update(self):
        """Update the panel content."""
        self.predefs.update_content()
        self.materials.update_content()
        self.products.update_content()
        self.parts.update_content()


if __name__ == '__main__':
    db = Database(":memory:", False, True, True)

    app = wx.App()

    frame = wx.Frame(None, title="GroupPanelTest")
    panel = GroupPanel(frame, db)
    button = wx.Button(frame, label="Change Foreign Key")
    frame.Bind(wx.EVT_BUTTON, panel.on_change_fk_test)
    sizer = wx.BoxSizer(wx.VERTICAL)
    sizer.Add(button, 0)
    sizer.Add(panel, 1)
    frame.SetSizer(sizer)

    # frame.SetClientSize(frame.FromDIP(wx.Size(1200, 600)))
    Sizes.scale(frame)
    frame_size = (Sizes.frame_w, Sizes.frame_h)
    frame.SetClientSize(frame_size)

    frame.Show()
    app.MainLoop()
