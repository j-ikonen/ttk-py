"""Main application"""
import wx

from gui.main_panel import MainPanel


def main():
    """Main app"""

    class TestQuote:
        """Mock class for quote."""
        def __init__(self):
            self.open_group = None
            self.data = [["Ryhmä1", 1], ["Toinen", 2], ["Kolmas", 3]]

        def get_group_list(self):
            """."""
            return self.data

        def delete_groups(self, items):
            """."""
            self.data = [i for i in self.data if i[1] not in items]

        def select_group(self, group_id):
            """."""
            self.open_group = group_id
            print(f"TestQuote.select_group({group_id})")

    app = wx.App()

    frame = wx.Frame(None, title="TTK-PY", size=(800,600))
    panel = MainPanel(frame, TestQuote())

    # Sizes.scale(frame)
    # frame_size = (Sizes.frame_w, Sizes.frame_h)
    # frame.SetClientSize(frame_size)


    frame.Show()
    app.MainLoop()


if __name__ == '__main__':
    main()
