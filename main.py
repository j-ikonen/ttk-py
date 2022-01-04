"""Main application"""
import wx

from gui.main_panel import MainPanel
from gui.frame import Frame
from quote import Quote


def main():
    """Main app"""

    quote = Quote()
    # Open for testing.
    quote.state.open_quote = 1
    quote.state.open_group = 1

    app = wx.App()

    frame = Frame()
    MainPanel(frame, quote)

    frame.Show()
    app.MainLoop()


if __name__ == '__main__':
    main()
