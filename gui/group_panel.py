"""Panel for editing group data."""

import wx

# import values as val
import event as evt
import values as val
from gui.table import Table


class GroupPanel(wx.Panel, evt.EventHandler):
    """Display data of opened group."""
    def __init__(self, parent, quote):
        super().__init__(parent)

        self.quote = quote
        self.title = wx.TextCtrl(self, size=(250, -1), style=wx.TE_PROCESS_ENTER)
        self.materials_table = Table(self, quote, val.TBL_MATERIAL)

        self.title.Bind(wx.EVT_TEXT_ENTER, self.on_title_enter)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.title)
        sizer.Add(self.materials_table, 1, wx.EXPAND)
        self.SetSizer(sizer)

        # self.quote.state.bind(val.EVT_SELECT_GROUP, self.update)
        self.bind(evt.GROUP_SELECT, self.update_group_name)
        self.bind(evt.GROUP_SELECT, self.materials_table.update)

    def update_group_name(self, _event):
        """Call when quote.open_group has changed to update display"""
        self.title.SetValue(self.quote.get_group_name())

    def on_title_enter(self, _evt):
        """Update the name of the open group"""
        if self.quote.state.open_group is None:
            print("No group selected.")
            return

        name = self.title.GetValue()
        self.quote.set_group_name(name)
