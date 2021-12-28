"""A list panel for groups in a quote"""
import wx
import wx.dataview as dv


class GroupList(wx.Panel):
    """A list panel for groups in a quote"""
    def __init__(self, parent, quote):
        super().__init__(parent)

        self.quote = quote
        self.dvlc = dv.DataViewListCtrl(self, style=dv.DV_MULTIPLE)
        self.dvlc.AppendTextColumn("Ryhmä", width=170,
            mode=dv.DATAVIEW_CELL_ACTIVATABLE)

        self.dvlc.Bind(dv.EVT_DATAVIEW_ITEM_CONTEXT_MENU, self.on_context_menu)

        sizer = wx.BoxSizer()
        sizer.Add(self.dvlc, 1, wx.EXPAND)

        self.SetSizer(sizer)

    def on_context_menu(self, _evt):
        """Open context menu"""
        print("CONTEXT MENU EVENT")
        if not hasattr(self, "id_del"):
            # pylint: disable=attribute-defined-outside-init
            self.id_del = wx.NewIdRef()
            self.Bind(wx.EVT_MENU, self.on_popup_del, id=self.id_del)
        
        menu = wx.Menu()
        menu.Append(self.id_del, "Poista")
        self.PopupMenu(menu)
        menu.Destroy()

    def on_popup_del(self, _evt):
        """Delete the selected items"""
        self.quote.delete_groups(self.selected())
        self.update()

    def update(self):
        """Update the contents"""
        self.dvlc.DeleteAllItems()
        try:
            values = self.quote.get_group_list()
        except AttributeError:
            print("GroupList has no item source.")
        else:
            for item in values:
                self.dvlc.AppendItem([item[0]], item[1])

    def selected(self) -> list:
        """Return the data of selected list items"""
        return [self.dvlc.GetItemData(item) for item in self.dvlc.GetSelections()]


if __name__ == '__main__':

    class TestQuote:
        """Mock class for quote."""
        def __init__(self):
            self.data = [["Ryhmä1", 1], ["Toinen", 2], ["Kolmas", 3]]

        def get_group_list(self):
            """."""
            return self.data

        def delete_groups(self, items):
            """."""
            self.data = [i for i in self.data if i[1] not in items]

    app = wx.App()

    frame = wx.Frame(None, title="GroupList test", size=(350,400))
    panel = GroupList(frame, TestQuote())

    # Sizes.scale(frame)
    # frame_size = (Sizes.frame_w, Sizes.frame_h)
    # frame.SetClientSize(frame_size)

    panel.update()

    frame.Show()
    app.MainLoop()
