import wx
import wx.adv
import wx.dataview as dv

import ttk_data as ttk
from tree_panel import TreePanel
from pages import Page, RootPage, ItemPage, ChildPage


FRAME_SIZE = (1200, 750)
LEFTWIN_SIZE = (270, FRAME_SIZE[1])
BOTWIN_SIZE = (FRAME_SIZE[0], 100)
BORDER = 5


class Panel(wx.Panel):
    def __init__(self, parent, data, setup):
        """Handle MainPanel windows.
        
        Args:
            - parent: Parent wx.Frame.
            - data (ttk.Data): Data class.
            - setup (dict): The setup information for data.
        """
        super().__init__(parent)

        self.treedata: ttk.Data = data
        self.setup: dict = setup

        winids = []
        self.left_win = self.create_left_window(winids)
        self.bottom_win = self.create_bottom_window(winids)
        self.main_win = wx.Panel(self, style=wx.SUNKEN_BORDER)

        self.treepanel = TreePanel(self.left_win)
        self.refresh_tree()
        self.book = wx.Simplebook(self.main_win)

        self.Bind(wx.adv.EVT_SASH_DRAGGED_RANGE, self.on_sash_drag, id=min(winids), id2=max(winids))
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(dv.EVT_DATAVIEW_SELECTION_CHANGED, self.on_tree_select)

        fcmult = self.treedata.get([0]).get_data('fc_mult')
        page = Page(self.book, self.setup)
        rootpage = RootPage(self.book, self.setup, self.refresh_tree)
        itempage = ItemPage(self.book, self.setup, fcmult, self.refresh_tree)
        childpage = ChildPage(self.book, self.setup, self.refresh_tree)

        self.book.AddPage(page, "page", True)
        self.book.AddPage(rootpage, "rootpage")
        self.book.AddPage(itempage, "itempage")
        self.book.AddPage(childpage, "childpage")

        # self.Bind(wx.EVT_BOOKCTRL_PAGE_CHANGING, self.on_book_pagechanged, self.book)
        sizer_book = wx.BoxSizer(wx.HORIZONTAL)
        sizer_book.Add(self.book, 1, wx.EXPAND)
        self.main_win.SetSizer(sizer_book)

    def create_left_window(self, winids):
        leftwin = wx.adv.SashLayoutWindow(
            self, size=LEFTWIN_SIZE
        )
        leftwin.SetDefaultSize(LEFTWIN_SIZE)
        leftwin.SetOrientation(wx.adv.LAYOUT_VERTICAL)
        leftwin.SetAlignment(wx.adv.LAYOUT_LEFT)
        leftwin.SetBackgroundColour(wx.Colour(255, 200, 200))
        leftwin.SetSashVisible(wx.adv.SASH_RIGHT, True)
        winids.append(leftwin.GetId())
        return leftwin

    def create_bottom_window(self, winids):
        botwin = wx.adv.SashLayoutWindow(
            self, size=BOTWIN_SIZE
        )
        botwin.SetDefaultSize(BOTWIN_SIZE)
        botwin.SetOrientation(wx.adv.LAYOUT_HORIZONTAL)
        botwin.SetAlignment(wx.adv.LAYOUT_BOTTOM)
        botwin.SetBackgroundColour(wx.Colour(200, 200, 255))
        botwin.SetSashVisible(wx.adv.SASH_TOP, True)
        winids.append(botwin.GetId())
        return botwin

    def on_sash_drag(self, evt):
        if evt.GetDragStatus() == wx.adv.SASH_STATUS_OUT_OF_RANGE:
            print("Drag is out of range.")
            return

        eobj = evt.GetEventObject()

        if eobj is self.left_win:
            self.left_win.SetDefaultSize(( evt.GetDragRect().width, LEFTWIN_SIZE[1]))
        elif eobj is self.bottom_win:
            self.bottom_win.SetDefaultSize((BOTWIN_SIZE[0], evt.GetDragRect().height))
        
        wx.adv.LayoutAlgorithm().LayoutWindow(self, self.main_win)
        self.main_win.Refresh()
    
    def on_size(self, evt):
        wx.adv.LayoutAlgorithm().LayoutWindow(self, self.main_win)

    def on_tree_select(self, evt):
        """Change and update page on tree selection."""
        link = evt.GetEventObject().GetItemData(evt.GetItem())  # tree.get_link(treeitem)
        selection_old = self.book.GetSelection()
        selection_new = len(link)
        print(f"Panel.on_tree_select - Selected link: {link}")

        self.treedata.set_active(link)

        # Change page
        if selection_old != selection_new:
            self.book.SetSelection(selection_new)

        # Refresh page
        page = self.book.GetPage(selection_new)
        active_data = self.treedata.get_active()
        if selection_new == 2:
            fcmult = self.treedata.get([0]).get_data('fc_mult')
            page.change_data(active_data, fcmult)
        else:
            page.change_data(active_data)
        evt.Skip()

    def refresh_tree(self):
        """Handle refreshing the tree."""
        datatree = self.treedata.get_tree()
        self.treepanel.fill(datatree)
