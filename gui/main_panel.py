"""Main panel containing group selection and editing."""

import wx

from gui.group_list import GroupList
from gui.group_panel import GroupPanel


class MainPanel(wx.Panel):
    """."""
    def __init__(self, parent, quote):
        super().__init__(parent)

        self.quote = quote
        self.group_list = GroupList(self, quote)
        self.group_panel = GroupPanel(self, quote)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.group_list, 0, wx.EXPAND)
        sizer.Add(self.group_panel, 0, wx.EXPAND)
        self.SetSizer(sizer)


if __name__ == '__main__':
    print("main_panel.py")
