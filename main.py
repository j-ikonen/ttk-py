"""Main application"""
import wx

from gui.main_panel import MainPanel
from quote import Quote


def main():
    """Main app"""

    app = wx.App()

    frame = wx.Frame(None, title="TTK-PY", size=(800,600))
    MainPanel(frame, Quote())

    # Sizes.scale(frame)
    # frame_size = (Sizes.frame_w, Sizes.frame_h)
    # frame.SetClientSize(frame_size)


    frame.Show()
    app.MainLoop()


if __name__ == '__main__':
    main()
