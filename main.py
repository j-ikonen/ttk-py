"""
TODO:
    Implement filling Parts grid on product row selection.
    Add Saving/Loading an offer to/from a file.
    Add Dialog for uploading selected objects to a database.
    Add Windows to handle loading objects from a database.
"""

import wx
import wx.adv
import wx.dataview as dv
import wx.grid

import grid
import data as dt


FRAME_TITLE = "Ttk-py"
FRAME_SIZE = (1200, 750)
LEFTWIN_SIZE = (200, FRAME_SIZE[1])
BOTWIN_SIZE = (FRAME_SIZE[0], 100)
TREE_ROOT_TITLE = "Tarjoukset"
GP_NAMELABEL = "Ryhmän nimi: "
GP_NAMECTRL_SIZE = (125, -1)
BORDER = 5
GP_PREDEFS_LABEL = "Osien esimääritellyt materiaalit"
GP_MATERIALS_LABEL = "Materiaalit"
GP_PRODUCTS_LABEL = "Tuotteet"
GP_PARTS_LABEL = "Tuotteen '{}' osat"


class AppFrame(wx.Frame):
    def __init__(self, data):
        super().__init__(
            None,
            title=FRAME_TITLE,
            size=FRAME_SIZE,
            style=wx.DEFAULT_FRAME_STYLE|wx.FULL_REPAINT_ON_RESIZE
        )

        self.panel = Panel(self, data)

        self.Bind(wx.EVT_CLOSE, self.on_close_window)
    
    def on_close_window(self, evt):
        self.Destroy()


class Panel(wx.Panel):
    def __init__(self, parent, data):
        super().__init__(parent)

        self.data: Data = data

        #------------------------------------------------------------------------------------------
        # SashWindows
        #------------------------------------------------------------------------------------------
        winids = []
        self.left_win = self.create_left_window(winids)
        self.bottom_win = self.create_bottom_window(winids)
        self.main_win = wx.Panel(self, style=wx.SUNKEN_BORDER)

        self.Bind(wx.adv.EVT_SASH_DRAGGED_RANGE, self.on_sash_drag, id=min(winids), id2=max(winids))
        self.Bind(wx.EVT_SIZE, self.on_size)

        #------------------------------------------------------------------------------------------
        # DVC_TreeCtrl
        #------------------------------------------------------------------------------------------
        self.tree_ctrl = dv.DataViewTreeCtrl(self.left_win)
        self.tree_root = self.tree_ctrl.AppendContainer(
            dv.NullDataViewItem,
            TREE_ROOT_TITLE,
            data=Link(Link.DATA, [])
        )
        self.is_treeitem_expanded = {TREE_ROOT_TITLE: True}
        self.create_tree()

        # Fill the left window with tree_ctrl
        self.left_win.Sizer = wx.BoxSizer()
        self.left_win.Sizer.Add(self.tree_ctrl, 1, wx.EXPAND)

        self.Bind(dv.EVT_DATAVIEW_ITEM_ACTIVATED, self.on_treeitem_activate)
        self.Bind(dv.EVT_DATAVIEW_ITEM_START_EDITING, self.on_treeitem_edit)
        self.Bind(dv.EVT_DATAVIEW_ITEM_COLLAPSING, self.on_treeitem_collapsing)
        self.Bind(dv.EVT_DATAVIEW_ITEM_EXPANDING, self.on_treeitem_expanding)

        #------------------------------------------------------------------------------------------
        # Simplebook
        #------------------------------------------------------------------------------------------
        self.book = wx.Simplebook(self.main_win)
        gridpage = wx.Panel(self.book)
        infopage = wx.Panel(self.book)
        rootpage = wx.Panel(self.book)
        gridpage.SetBackgroundColour((255, 200, 200))   # For testing
        infopage.SetBackgroundColour((200, 255, 200))   # For testing
        rootpage.SetBackgroundColour((200, 200, 255))   # For testing

        self.book.AddPage(gridpage, "gridpage")
        self.book.AddPage(infopage, "infopage")
        self.book.AddPage(rootpage, "rootpage")
        self.pageidx = {Link.GROUP: 0, Link.OFFER: 1, Link.DATA: 2}
        self.pagesel_link = Link(Link.DATA, [])
        self.book.SetSelection(2)

        # self.Bind(wx.EVT_BOOKCTRL_PAGE_CHANGING, self.on_book_pagechanged, self.book)
        self.main_win.Sizer = wx.BoxSizer()
        self.main_win.Sizer.Add(self.book, 1, wx.EXPAND)

        #------------------------------------------------------------------------------------------
        # Simplebook - gridpage
        #------------------------------------------------------------------------------------------
        self.selected_product = None
        self.gp_namelabel = wx.StaticText(gridpage, label=GP_NAMELABEL)
        self.gp_predefs_label = wx.StaticText(gridpage, label=GP_PREDEFS_LABEL)
        self.gp_materials_label = wx.StaticText(gridpage, label=GP_MATERIALS_LABEL)
        self.gp_products_label = wx.StaticText(gridpage, label=GP_PRODUCTS_LABEL)
        try:
            part_label = self.data.get(self.selected_product).code
        except (IndexError, AttributeError):
            part_label = ""

        self.gp_parts_label = wx.StaticText(gridpage,label=GP_PARTS_LABEL.format(part_label))
        self.gp_namectrl = wx.TextCtrl(gridpage, size=GP_NAMECTRL_SIZE)

        self.Bind(wx.EVT_TEXT, self.on_gp_namectrl_text, self.gp_namectrl)

        gp_label_sizer = wx.BoxSizer(wx.HORIZONTAL)
        gp_label_sizer.Add(self.gp_namelabel, 0, wx.ALL, BORDER)
        gp_label_sizer.Add(self.gp_namectrl, 0, wx.ALL, BORDER)

        self.grid_predefs = grid.CustomGrid(gridpage, dt.Predef())
        self.grid_materials = grid.CustomGrid(gridpage, dt.Material())
        self.grid_products = grid.CustomGrid(gridpage, dt.Product())
        self.grid_parts = grid.CustomGrid(gridpage, dt.Part(), None)

        self.Bind(wx.grid.EVT_GRID_SELECT_CELL, self.on_select_product, self.grid_products)

        gp_sizer = wx.BoxSizer(wx.VERTICAL)
        gp_sizer.Add(gp_label_sizer)
        gp_sizer.Add(self.gp_predefs_label, 0, wx.EXPAND|wx.LEFT|wx.TOP, BORDER)
        gp_sizer.Add(self.grid_predefs, 1, wx.EXPAND|wx.ALL, BORDER)

        gp_sizer.Add(self.gp_materials_label, 0, wx.EXPAND|wx.LEFT|wx.TOP, BORDER)
        gp_sizer.Add(self.grid_materials, 1, wx.EXPAND|wx.ALL, BORDER)

        gp_sizer.Add(self.gp_products_label, 0, wx.EXPAND|wx.LEFT|wx.TOP, BORDER)
        gp_sizer.Add(self.grid_products, 1, wx.EXPAND|wx.ALL, BORDER)

        gp_sizer.Add(self.gp_parts_label, 0, wx.EXPAND|wx.LEFT|wx.TOP, BORDER)
        gp_sizer.Add(self.grid_parts, 1, wx.EXPAND|wx.ALL, BORDER)
        gridpage.Sizer = gp_sizer

        #------------------------------------------------------------------------------------------
        # Simplebook - infopage
        #------------------------------------------------------------------------------------------

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

    #----------------------------------------------------------------------------------------------
    # DVC_TreeCtrl functions
    #----------------------------------------------------------------------------------------------
    def create_tree(self):
        """Add items from data to dv_treectrl."""

        self.tree_ctrl.DeleteChildren(self.tree_root)
        list = self.data.get_treelist()

        last = None
        for n in range(len(list)):
            if list[n][0].target == Link.OFFER:
                last = self.tree_ctrl.AppendContainer(self.tree_root, list[n][1], data=list[n][0])
                is_expanded = self.is_treeitem_expanded.get(list[n][1])
                if is_expanded:
                    self.tree_ctrl.Expand(last)
                elif is_expanded is None:
                    self.is_treeitem_expanded[list[n][1]] = True
                    self.tree_ctrl.Expand(last)

            elif list[n][0].target == Link.GROUP:
                if last:
                    self.tree_ctrl.AppendItem(last, list[n][1], data=list[n][0])

    def on_treeitem_activate(self, evt):
        """Change the page or it's content based on treeitem activation event."""

        link = self.tree_ctrl.GetItemData(evt.GetItem())
        obj = self.data.get(link)

        if link.target in self.pageidx: # if link is a valid page

            if self.pagesel_link.target != link.target:
                # Change page.
                self.book.ChangeSelection(self.pageidx[link.target])
                self.pagesel_link = link
                print(f"Panel.on_treeitem_activate: Change page to {obj}")

                if link.target == Link.GROUP:
                    self.update_gridpage_content(link)

            elif self.pagesel_link.n != link.n:
                # Change content of the page to obj.
                self.pagesel_link = link
                if link.target == Link.GROUP:
                    self.update_gridpage_content(link)

            else:
                print(f"Panel.on_treeitem_activate: Page already activated {obj}")

        else:
            print(f"Panel.on_treeitem_activate: Page not changed - obj: {obj}")

    def on_treeitem_edit(self, evt):
        """Prevent editing."""
        evt.Veto()

    def on_treeitem_expanding(self, evt):
        text = self.tree_ctrl.GetItemText(evt.GetItem())
        self.is_treeitem_expanded[text] = True
        # print(f"Panel.on_treeitem_expanded: Set {text} to True")

    def on_treeitem_collapsing(self, evt):
        text = self.tree_ctrl.GetItemText(evt.GetItem())
        self.is_treeitem_expanded[text] = False
        # print(f"Panel.on_treeitem_collapsed: Set {text} to False")

    #------------------------------------------------------------------------------------------
    # Simplebook
    #------------------------------------------------------------------------------------------
    # def on_book_pagechanged(self, evt):
    #     """Update the page to new data. Covers Group1 -> Offer -> Group2 change."""
    #     print(f"Panel.on_book_pagechanged: {evt}")

    #------------------------------------------------------------------------------------------
    # Simplebook - gridpage
    #------------------------------------------------------------------------------------------
    def on_gp_namectrl_text(self, evt):
        """Update the group name with content of textctrl."""
        group = self.data.get(self.pagesel_link)
        if self.pagesel_link.target == Link.GROUP:
            group.name = evt.GetString()
            self.create_tree()
            print(f"Panel.on_gp_namectrl_text: {evt.GetString()}")
        else:
            print(f"Panel.on_gp_namectrl_text: Selected page '{self.pagesel_link}' is not a grouppage")

    def update_gridpage_content(self, link):
        """Update the content of the gridpage.

        Args:
            link (Link): Link to the new Group.
        """
        obj = self.data.get(link)
        # self.selected_product = Link(Link.PRODUCT, link.n + [0])
        if isinstance(obj, Group):
            self.gp_namectrl.ChangeValue(obj.name)
            print(f"Panel.on_treeitem_activate: Change page content to {obj}")
            self.grid_predefs.update_data(obj.predefs, True)
            self.grid_materials.update_data(obj.materials, True)
            self.grid_products.update_data(obj.products, True)
            self.grid_parts.update_data(None, True)
        else:
            print(f"Panel.update_gridpage_content given object '{obj}' is not a Group class.")

    def on_select_product(self, evt):
        print(f"Panel.on_select_grid_cell")


class Link:
    DATA = 0
    OFFERS = 1
    OFFER = 2
    INFO = 3
    GROUPS = 1000
    GROUP = 1001
    PREDEFS = 2000
    PREDEF = 2001
    MATERIALS = 2012
    MATERIAL = 2013
    PRODUCTS = 2014
    PRODUCT = 2015
    PARTS = 2016
    PART = 2017

    def __init__(self, tar, n: list):
        """Link referring to an object in Data class.

        Args:
            tar (int): Target to which class/object this link refers to. (self.tar = Link.GROUP)
            n (list): A list of indexes for each array on path to target.
        """
        self.target = tar
        self.n = n

    def is_valid(self):
        if self.target == Link.DATA:
            return len(self.n) == 0
        elif self.target == Link.OFFERS:
            return len(self.n) == 0
        elif self.target == Link.OFFER:
            return len(self.n) == 1
        elif self.target == Link.INFO:
            return len(self.n) == 1
        elif self.target == Link.GROUPS:
            return len(self.n) == 1
        elif self.target == Link.GROUP:
            return len(self.n) == 2
        elif self.target == Link.PREDEFS:
            return len(self.n) == 2
        elif self.target == Link.MATERIALS:
            return len(self.n) == 2
        elif self.target == Link.PRODUCTS:
            return len(self.n) == 2
        elif self.target == Link.PARTS:
            return len(self.n) == 3
        elif self.target == Link.PREDEF:
            return len(self.n) == 3
        elif self.target == Link.MATERIAL:
            return len(self.n) == 3
        elif self.target == Link.PRODUCT:
            return len(self.n) == 3
        elif self.target == Link.PART:
            return len(self.n) == 4

    def get_new_object(self):
        if self.target == Link.PREDEF:
            return dt.Predef()
        elif self.target == Link.MATERIAL:
            return dt.Material()
        elif self.target == Link.PRODUCT:
            return dt.Product()
        elif self.target == Link.PART:
            return dt.Part()


class Data:
    def __init__(self) -> None:
        self.offers = []
    
    def get(self, link: Link):
        if link is None:
            return []
        elif link.target == Link.OFFER:
            return self.offers[link.n[0]]
        elif link.target == Link.GROUP:
            return self.offers[link.n[0]].groups[link.n[1]]
        elif link.target == Link.PREDEFS:
            return self.offers[link.n[0]].groups[link.n[1]].predefs
        elif link.target == Link.MATERIALS:
            return self.offers[link.n[0]].groups[link.n[1]].materials
        elif link.target == Link.PRODUCTS:
            return self.offers[link.n[0]].groups[link.n[1]].products
        elif link.target == Link.PRODUCT:
            return self.offers[link.n[0]].groups[link.n[1]].products[link.n[2]]
        elif link.target == Link.PARTS:
            return self.offers[link.n[0]].groups[link.n[1]].products[link.n[2]].parts
        elif link.target == Link.PREDEF:
            return self.offers[link.n[0]].groups[link.n[1]].predefs[link.n[2]]
        elif link.target == Link.MATERIAL:
            return self.offers[link.n[0]].groups[link.n[1]].materials[link.n[2]]
        elif link.target == Link.PRODUCT:
            return self.offers[link.n[0]].groups[link.n[1]].products[link.n[2]]
        elif link.target == Link.PART:
            return self.offers[link.n[0]].groups[link.n[1]].products[link.n[2]].parts[link.n[3]]
        elif link.target == Link.DATA:
            return self
        else:
            print(f"Data.get: Link.target '{link.target}' is not defined.")

    def get_treelist(self) -> list:
        treelist = []
        for n_offer in range(len(self.offers)):
            link = Link(Link.OFFER, [n_offer])
            name = self.offers[n_offer].name
            treelist.append((link, name))

            for n_group in range(len(self.offers[n_offer].groups)):
                link = Link(Link.GROUP, [n_offer, n_group])
                name = self.offers[n_offer].groups[n_group].name
                treelist.append((link, name))

        return treelist

    def set(self, link, col, value):
        """Set a value to a member at col to a object at link.

        Args:
            link (Link): Link to the object.
            col (int): Column idx to the member which value is to be changed.
            value (Any): Value to be changed.
        """
        try:
            obj = self.get(link)
        except IndexError:
            obj = link.get_new_object()
            arraylink = Link(link.target - 1, link.n[:-1])
            try:
                self.get(arraylink).append(obj)
            except IndexError:
                product_link = Link(Link.PRODUCT, link.n[:-1])
                self.get(product_link).parts.append(obj)

        if (link.target == Link.PREDEF or 
            link.target == Link.MATERIAL or 
            link.target == Link.PRODUCT or 
            link.target == Link.PART):
            obj.set(col, value)
        self.to_print()

    def build_test(self):
        self.offers.append(Offer("Tarjous 1"))
        self.offers.append(Offer("Testi tarjous"))
        self.offers.append(Offer("Matinkatu 15"))

        self.offers[0].groups.append(Group("TestGroup"))
        self.offers[0].groups.append(Group("Group2"))
        self.offers[1].groups.append(Group("DefName"))
        self.offers[1].groups.append(Group("One"))
        self.offers[1].groups.append(Group("Two"))
        self.offers[1].groups.append(Group("Three"))
        self.offers[2].groups.append(Group("Kitchen"))

        self.offers[0].groups[0].predefs.append(dt.Predef("ovi", "MELVA16"))
        self.offers[0].groups[0].predefs.append(dt.Predef("hylly", "MELVA16"))
    
    def to_print(self):
        print("")
        for offer in self.offers:
            print(f"offer: {offer.name}")
            for group in offer.groups:
                print(f"    group: {group.name}")
                for predef in group.predefs:
                    print(f"        predef: {predef.get_data()}")
                for material in group.materials:
                    print(f"        material: {material.get_data()}")
                for product in group.products:
                    print(f"        product: {product.get_data()}")
                    for part in product.parts:
                        print(f"            part: {part.get_data()}")
        print("")


class Offer:
    def __init__(self, name="") -> None:
        self.name = name
        self.info = ""
        self.groups = []


class Info:
    def __init__(self) -> None:
        self.first_name = ""
        self.last_name = ""
        self.address = ""


class Group:
    def __init__(self, name="") -> None:
        self.name = name
        self.predefs = []
        self.materials = []
        self.products = []


if __name__ == '__main__':
    app = wx.App(useBestVisual=True)

    data = Data()
    data.build_test()

    frame = AppFrame(data)
    frame.Show()
    frame.Layout()

    app.MainLoop()