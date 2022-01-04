"""A list panel for groups in a quote"""
import wx
import wx.dataview as dv

#import values as val
from quote import Quote
import event as evt


class GroupList(wx.Panel, evt.EventHandler):
    """A list panel for groups in a quote

    Parameters
    ----------
    quote: Data class for group names and ids.
        Must implement functions:
            list<list<GroupName, GroupID>> get_group_list
            delete_groups(list_of_group_ids)
            select_group(group_id)
    """
    def __init__(self, parent, quote):
        super().__init__(parent, size=(170, -1))

        self.quote: Quote = quote
        self.dvlc = dv.DataViewListCtrl(self, style=dv.DV_MULTIPLE)#|dv.DV_NO_HEADER)
        self.dvlc.AppendTextColumn("Ryhmät", width=170,
            mode=dv.DATAVIEW_CELL_ACTIVATABLE)

        self.dvlc.Bind(dv.EVT_DATAVIEW_ITEM_CONTEXT_MENU, self.on_context_menu)
        self.dvlc.Bind(dv.EVT_DATAVIEW_ITEM_ACTIVATED, self.on_activate)

        sizer = wx.BoxSizer()
        sizer.Add(self.dvlc, 1, wx.EXPAND)
        self.SetSizer(sizer)

        # self.quote.state.bind(val.EVT_GROUP_NAME, self.update)
        # self.quote.state.bind(val.EVT_OPEN_QUOTE, self.update)
        # self.quote.state.bind(val.EVT_NEW_GROUP, self.update)
        # self.quote.state.bind(val.EVT_DELETE_GROUP, self.delete)
        # self.bind(evt.GROUP_NAME, self.update_name)
        # self.bind(evt.GROUP_NEW, self.update)
        # self.bind(evt.GROUP_DELETE, self.update)
        # self.bind(evt.QUOTE_OPEN, self.update)
        self.bind(evt.GROUP_CHANGE, self.update)

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

    def on_activate(self, event):
        """."""
        self.quote.select_group(self.dvlc.GetItemData(event.GetItem()))
#        print(f"ACTIVATE: {self.dvlc.GetItemData(evt.GetItem())}")

    def on_popup_del(self, _evt):
        """Delete the selected items"""
        self.delete()

    def delete(self):
        """Delete the selected items"""
        self.quote.delete_groups(self.selected())

    def update(self, _data):
        """Update the contents"""
        self.dvlc.DeleteAllItems()
        try:
            values = self.quote.get_group_list()
        except AttributeError:
            print("GroupList has no item source.")
        else:
            for item in values:
                self.dvlc.AppendItem([item[1]], item[0])

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

        def select_group(self):
            """."""
            # print("TestQuote.select_group()")

    app = wx.App()

    frame = wx.Frame(None, title="GroupList test", size=(350,400))
    panel = GroupList(frame, TestQuote())

    # Sizes.scale(frame)
    # frame_size = (Sizes.frame_w, Sizes.frame_h)
    # frame.SetClientSize(frame_size)

    panel.update([None])

    frame.Show()
    app.MainLoop()
