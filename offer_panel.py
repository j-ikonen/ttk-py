import wx

from db import Database
from sizes import Sizes


class OfferPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)


if __name__ == '__main__':
    app = wx.App()

    database = Database(print_err=True)
    frame = wx.Frame(None, title="OfferPanelTest")
    panel = OfferPanel(frame)

    Sizes.scale(frame)
    frame_size = (Sizes.frame_w, Sizes.frame_h)
    frame.SetClientSize(frame_size)

    frame.Show()
    app.MainLoop()
