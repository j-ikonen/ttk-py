from setupgrid import SetupGrid
import wx
import wx.adv
import wx.dataview as dv


from tree_data import TreeRoot, GD_SETUP


FRAME_SIZE = (1200, 700)
BOTWIN_SIZE = (150, 150)
LEFTWIN_SIZE = (230, 230)
BORDER_BTN = 5
BTN_ADD_ITEM = "Uusi Tarjous"
BTN_ADD_CHILD = "Uusi ryhmä"


class RootPage(wx.Panel):
    def __init__(self, parent, treedata):
        super().__init__(parent)

        self.treedata: TreeRoot = treedata
        self.btn_add_item = wx.Button(self, label=BTN_ADD_ITEM)

        sizer_btn = wx.BoxSizer(wx.HORIZONTAL)
        sizer = wx.BoxSizer(wx.VERTICAL)

        sizer_btn.Add(self.btn_add_item, 0, wx.RIGHT, BORDER_BTN)

        sizer.Add(sizer_btn, 0, wx.EXPAND|wx.ALL, BORDER_BTN)

        self.SetSizer(sizer)

    def update(self, treedata):
        print(f"RootPage.update")



class ItemPage(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)

        setup = GD_SETUP['offer_info']
        self.btn_add_child = wx.Button(self, label=BTN_ADD_CHILD)
        self.infogrid = SetupGrid(self, setup)

        sizer_btn = wx.BoxSizer(wx.HORIZONTAL)
        sizer = wx.BoxSizer(wx.VERTICAL)

        sizer_btn.Add(self.btn_add_child, 0, wx.RIGHT, BORDER_BTN)

        sizer.Add(sizer_btn, 0, wx.EXPAND|wx.ALL, BORDER_BTN)
        sizer.Add(self.infogrid, 1, wx.EXPAND)

        self.SetSizer(sizer)


    def update(self, treedata):
        print(f"ItemPage.update")
        self.infogrid.update(treedata.get_data('offer_info').values())


class ChildPage(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
    
    def update(self, treedata):
        print(f"ChildPage.update")


class TreePanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)

        self.tree = dv.DataViewTreeCtrl(self)
        self.expanded = {}
        self.selected = []

        self.Bind(dv.EVT_DATAVIEW_SELECTION_CHANGED, self.on_select, self.tree)
        self.Bind(dv.EVT_DATAVIEW_ITEM_START_EDITING, self.on_edit, self.tree)
        self.Bind(dv.EVT_DATAVIEW_ITEM_COLLAPSING, self.on_collapsing, self.tree)
        self.Bind(dv.EVT_DATAVIEW_ITEM_EXPANDING, self.on_expanding, self.tree)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.tree, 1, wx.EXPAND)

        self.SetSizer(sizer)

    def fill(self, treelist):
        """Fill the tree with given treelist data.
        
        Args:
            - treelist (list): List of tuples where (name, link).
        """
        self.tree.DeleteAllItems()
        root = dv.NullDataViewItem
        item = dv.NullDataViewItem

        for (name, link) in treelist:
            try:
                expanded = self.expanded[str(link)]
            except KeyError:
                if len(link) < 2:
                    self.expanded[str(link)] = True
                    expanded = True

            if len(link) == 0:      # TreeRoot
                root = self.tree.AppendContainer(
                    dv.NullDataViewItem,
                    name,
                    expanded=expanded,
                    data=link
                )
                if expanded:
                    self.tree.Expand(root)
            elif len(link) == 1:    # TreeItem
                item = self.tree.AppendContainer(
                    root,
                    name,
                    expanded=expanded,
                    data=link
                )
                if expanded:
                    self.tree.Expand(item)
            elif len(link) == 2:    # TreeChild
                self.tree.AppendItem(item, name, data=link)

    def on_collapsing(self, evt):
        link = self.tree.GetItemData(evt.GetItem())
        self.expanded[str(link)] = False

    def on_edit(self, evt):
        """Prevent editing."""
        evt.Veto()

    def on_expanding(self, evt):
        link = self.tree.GetItemData(evt.GetItem())
        self.expanded[str(link)] = True

    def on_select(self, evt):
        tree = evt.GetEventObject()
        self.selected = tree.GetItemData(evt.GetItem())
        # print("TreePanel.on_select: {}".format(str(self.selected)))
        evt.Skip()


class BasePanel(wx.Panel):
    def __init__(self, parent, treedata):
        super().__init__(parent)
        
        self.treedata: TreeRoot = treedata
        self.treedata.set_selected([])  # Select TreeRoot

        #------------------------------------------------------------------------------------------
        # SashWindows
        #------------------------------------------------------------------------------------------
        winids = []
        self.left_win = self.create_left_window(winids)
        self.bottom_win = self.create_bottom_window(winids)
        self.main_win = wx.Panel(self, style=wx.SUNKEN_BORDER)

        self.Bind(
            wx.adv.EVT_SASH_DRAGGED_RANGE,
            self.on_sash_drag,
            id=min(winids),
            id2=max(winids)
        )
        self.Bind(wx.EVT_SIZE, self.on_size)
        
        #------------------------------------------------------------------------------------------
        # TreePanel
        #------------------------------------------------------------------------------------------
        self.treepanel = TreePanel(self.left_win)
        self.treepanel.fill(self.treedata.get_treelist())

        self.Bind(
            dv.EVT_DATAVIEW_SELECTION_CHANGED,
            self.on_tree_select,
            self.treepanel.tree
        )

        #------------------------------------------------------------------------------------------
        # Simplebook
        #------------------------------------------------------------------------------------------
        self.book = wx.Simplebook(self.main_win)
        page_root = RootPage(self.book, self.treedata)
        page_item = ItemPage(self.book)
        page_child = ChildPage(self.book)

        page_root.SetBackgroundColour((250, 220, 220))   # For testing
        page_item.SetBackgroundColour((200, 240, 230))   # For testing
        page_child.SetBackgroundColour((220, 210, 240))   # For testing

        self.book.AddPage(page_root, "rootpage")
        self.book.AddPage(page_item, "itempage")
        self.book.AddPage(page_child, "childpage")

        self.book.SetSelection(0)   # BookPageIndex == len(TreeData.selection)

        import wx.grid as wxg
        self.Bind(wx.EVT_BUTTON, self.on_add_item, page_root.btn_add_item)
        self.Bind(wx.EVT_BUTTON, self.on_add_child, page_item.btn_add_child)
        self.Bind(wxg.EVT_GRID_CELL_CHANGED, self.on_edit_item_data, page_item.infogrid)
        #------------------------------------------------------------------------------------------
        # Sizers
        #------------------------------------------------------------------------------------------
        sizer_main = wx.BoxSizer(wx.VERTICAL)
        sizer_main.Add(self.book, 1, wx.EXPAND)
        self.main_win.SetSizer(sizer_main)

    #----------------------------------------------------------------------------------------------
    # TreePanel functions
    #----------------------------------------------------------------------------------------------
    def on_tree_select(self, evt):
        link: list = self.treepanel.tree.GetItemData(evt.GetItem())
        page_selection = self.book.GetSelection()
        new_selection = len(link)
        self.treedata.set_selected([i for i in link])
        print("BasePanel.on_tree_select: {}".format(str(link)))

        # Change page
        if page_selection != new_selection:
            self.book.ChangeSelection(new_selection)

        # Refresh page
        page = self.book.GetPage(new_selection)
        page.update(self.treedata.get_selected())

    #----------------------------------------------------------------------------------------------
    # Page functions
    #----------------------------------------------------------------------------------------------
    def on_add_item(self, evt):
        print("BasePanel.on_add_item")
        self.treedata.append_child()
        self.treepanel.fill(self.treedata.get_treelist())

    def on_add_child(self, evt):
        print("BasePanel.on_add_child")
        self.treedata.get_selected().append_child()
        self.treepanel.fill(self.treedata.get_treelist())

    def on_edit_item_data(self, evt):
        print("BasePanel.on_edit_item_data")
        item = self.treedata.get_selected()
        # for n, key in item.data['offer_info']:
        #     if n == evt.GetRow():
        #         item.set('offer_info', key, self.book.GetPage())

    #----------------------------------------------------------------------------------------------
    # SashWindows functions
    #----------------------------------------------------------------------------------------------
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


if __name__ == '__main__':
    
    app = wx.App(useBestVisual=True)

    frame = wx.Frame(None, size=FRAME_SIZE)
    treedata = TreeRoot(None)
    panel = BasePanel(frame, treedata)

    frame.Show()
    frame.Layout()

    app.MainLoop()