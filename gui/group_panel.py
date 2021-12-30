"""Panel for editing group data."""

import wx

import values as val


class GroupPanel(wx.Panel):
    """Display data of opened group."""
    def __init__(self, parent, quote):
        super().__init__(parent)

        self.quote = quote
        self.title = wx.TextCtrl(self, size=(250, -1), style=wx.TE_PROCESS_ENTER)

        self.title.Bind(wx.EVT_TEXT_ENTER, self.on_title_enter)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.title)
        self.SetSizer(sizer)

        self.quote.register(val.SELECT_GROUP, self.update)

    def update(self):
        """Call when quote.open_group has changed to update display"""
        self.title.SetValue(self.quote.get_group_title())

    def on_title_enter(self, _evt):
        """Update the name of the open group"""
        if self.quote.open_group is None:
            print("No group selected.")
            return

        name = self.title.GetValue()
        self.quote.set_group_name(name)
