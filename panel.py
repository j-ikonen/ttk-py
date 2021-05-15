from grouppage import GroupPage
import wx
import wx.adv
import wx.dataview as dv

from table import OfferTables
from tree_panel import TreePanel
from offerpage import OfferPage


FRAME_SIZE = (1200, 750)
LEFTWIN_SIZE = (270, FRAME_SIZE[1])
BOTWIN_SIZE = (FRAME_SIZE[0], 100)
BORDER = 5


class Panel(wx.Panel):
    def __init__(self, parent, tables):
        """Handle MainPanel windows.
        
        Args:
            - parent: Parent wx.Frame.
            - data (ttk.Data): Data class.
            - setup (dict): The setup information for data.
        """
        super().__init__(parent)

        self.tables: OfferTables = tables
        self.open_offers = [
            self.tables.offer_data[0][0],
            self.tables.offer_data[1][0],
            self.tables.offer_data[2][0],
            self.tables.offer_data[3][0]
        ]
        self.active_offer = None
        self.active_group = None

        winids = []
        self.left_win = self.create_left_window(winids)
        self.bottom_win = self.create_bottom_window(winids)
        self.main_win = wx.Panel(self, style=wx.SUNKEN_BORDER)

        self.treepanel = TreePanel(self.left_win)
        self.refresh_tree()
        self.book = wx.Notebook(self.main_win, style=wx.BK_DEFAULT)

        self.Bind(
            wx.adv.EVT_SASH_DRAGGED_RANGE,
            self.on_sash_drag,
            id=min(winids),
            id2=max(winids))

        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(dv.EVT_DATAVIEW_SELECTION_CHANGED, self.on_tree_select)

        self.page_offer = OfferPage(self.book, self.tables)
        self.page_group = GroupPage(self.book, self.tables)
        self.page_db = wx.Panel(self.book)

        self.page_db.SetBackgroundColour((220, 220, 255))

        PAGE_TITLE_OFFER = "Tarjous"
        PAGE_TITLE_GROUP = "Ryhmä"
        PAGE_TITLE_DB = "Tietokanta"

        self.book.AddPage(self.page_offer, PAGE_TITLE_OFFER)
        self.book.AddPage(self.page_group, PAGE_TITLE_GROUP)
        self.book.AddPage(self.page_db, PAGE_TITLE_DB)

        # self.Bind(wx.EVT_BOOKCTRL_PAGE_CHANGING, self.on_book_pagechanged, self.book)
        sizer_book = wx.BoxSizer(wx.HORIZONTAL)
        sizer_book.Add(self.book, 1, wx.EXPAND)
        self.main_win.SetSizer(sizer_book)

    # def on_btn_add_group(self, evt):
    #     selected_link = self.treepanel.get_selected_link()
    #     if selected_link is None:
    #         return

    #     print(selected_link)
    #     offer_id = selected_link[0]
    #     group_id = self.tables.insert_group(offer_id)
    #     if group_id is not None:
    #         self.refresh_tree()
    #     else:
    #         print("panel.on_btn_add_offer - failed to add offer")

    # def on_btn_add_offer(self, evt):
    #     offer_id = self.tables.insert_offer()
    #     if offer_id is not None:
    #         self.offers.append(offer_id)
    #         self.refresh_tree()
    #     else:
    #         print("panel.on_btn_add_offer - failed to add offer")

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
        data = evt.GetEventObject().GetItemData(evt.GetItem())
        # selection_old = self.book.GetSelection()
        if data is None:
            evt.Skip()
        else:
            # selection_new = len(data) - 1

            # # Change page
            # if selection_old != selection_new:
            #     self.book.SetSelection(selection_new)

            # Refresh page
            # page = self.book.GetPage(selection_new)
            if self.page_offer.pk_val != data[0]:
                self.page_offer.set_pk(data[0])

            if len(data) > 1 and self.page_group.pk_val != data[1]:
                self.page_group.set_pk(data[1])

            # self.page_db.set_pk(data)
            # page.set_pk(data[-1])
            evt.Skip()

    def refresh_tree(self):
        """Handle refreshing the tree."""
        treelist = self.tables.get_treelist(self.open_offers)
        self.treepanel.refresh(treelist)