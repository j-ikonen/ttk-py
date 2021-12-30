"""Main panel containing group selection and editing."""

import wx

from gui.group_list import GroupList


class MainPanel(wx.Panel):
    """."""
    def __init__(self, parent, quote):
        super().__init__(parent)

        self.quote = quote
        self.group_list = GroupList(self, quote)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.group_list, 0, wx.EXPAND)
        sizer.Add(wx.Panel(self), 0, wx.EXPAND)
        self.SetSizer(sizer)


if __name__ == '__main__':
    print("main_panel.py")
