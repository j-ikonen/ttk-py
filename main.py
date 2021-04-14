import wx
import wx.adv
import wx.dataview as dv
import wx.grid


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
        self.selected_product = Link(Link.PRODUCT, [0, 0, 0])
        self.gp_namelabel = wx.StaticText(gridpage, label=GP_NAMELABEL)
        self.gp_predefs_label = wx.StaticText(gridpage, label=GP_PREDEFS_LABEL)
        self.gp_materials_label = wx.StaticText(gridpage, label=GP_MATERIALS_LABEL)
        self.gp_products_label = wx.StaticText(gridpage, label=GP_PRODUCTS_LABEL)
        self.gp_parts_label = wx.StaticText(
            gridpage,
            label=GP_PARTS_LABEL.format(self.data.get(self.selected_product).code)
        )
        self.gp_namectrl = wx.TextCtrl(gridpage, size=GP_NAMECTRL_SIZE)

        self.Bind(wx.EVT_TEXT, self.on_gp_namectrl_text, self.gp_namectrl)

        gp_label_sizer = wx.BoxSizer(wx.HORIZONTAL)
        gp_label_sizer.Add(self.gp_namelabel, 0, wx.ALL, BORDER)
        gp_label_sizer.Add(self.gp_namectrl, 0, wx.ALL, BORDER)

        self.grid_predefs = self.init_grid(gridpage, Link(Link.PREDEFS, [0, 0]))
        self.grid_materials = self.init_grid(gridpage, Link(Link.MATERIALS, [0, 0]))
        self.grid_products = self.init_grid(gridpage, Link(Link.PRODUCTS, [0, 0]))
        self.grid_parts = self.init_grid(gridpage, Link(Link.PARTS, [i for i in self.selected_product.n]))

        self.Bind(wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.on_grid_cell_left_dclick)

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
                    self.update_gridpage_content(obj)

            elif self.pagesel_link.n != link.n:
                # Change content of the page to obj.
                self.pagesel_link = link
                self.update_gridpage_content(obj)

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

    def update_gridpage_content(self, obj):
        """Update the content of the gridpage.

        Args:
            obj (Group): Group with the new data.
        """
        if isinstance(obj, Group):
            self.gp_namectrl.ChangeValue(obj.name)
            print(f"Panel.on_treeitem_activate: Change page content to {obj}")
        else:
            print(f"Panel.update_gridpage_content given object '{obj}' is not a Group class.")

    def init_grid(self, parent, link):
        """Initialize a grid

        Args:
            parent (wx.Panel): Parent window.
            link (Link): Link to the list of data of this grid.

        Returns:
            wx.Grid: The initialized grid object.
        """
        grid = wx.grid.Grid(parent)
        table = CustomDataTable(self.data.get(link))
        grid.SetTable(table, True)
        grid.SetRowLabelSize(0)
        grid.SetMargins(0, 0)
        grid.AutoSizeColumns(False)
        return grid

    def on_grid_cell_left_dclick(self, evt):
        """Change default behaviour so that left doubleclick enables cell editing."""
        if self.grid.CanEnableCellControl():
            self.grid.EnableCellEditControl()

class Link:
    DATA = 0
    OFFERS = 1
    OFFER = 2
    INFO = 3
    GROUPS = 4
    GROUP = 5
    PREDEFS = 6
    MATERIALS = 7
    PRODUCTS = 8
    PARTS = 9
    PREDEF = 10
    MATERIAL = 11
    PRODUCT = 12
    PART = 13

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


class Data:
    def __init__(self) -> None:
        self.offers = []
    
    def get(self, link: Link):
        if link.target == Link.OFFER:
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
        self.predefs = [Predef()]
        self.materials = [Material()]
        self.products = [Product()]


class Predef:
    def __init__(self) -> None:
        self.part = ""
        self.material = ""

    def get_labels(self) -> list:
        return ['Nimi', 'Materiaalikoodi']
        
    def get_types(self) -> list:
        return [
            wx.grid.GRID_VALUE_STRING,
            wx.grid.GRID_VALUE_STRING
        ]
        
    def get_data(self) -> list:
        return [self.part, self.material]
        
class Material:
    def __init__(self) -> None:
        self.code = ""
        self.description = ""

    def get_labels(self) -> list:
        return ['Koodi', 'Kuvaus']
        
    def get_types(self) -> list:
        return [
            wx.grid.GRID_VALUE_STRING,
            wx.grid.GRID_VALUE_STRING
        ]
        
    def get_data(self) -> list:
        return [self.code, self.description]

class Product:
    def __init__(self) -> None:
        self.code = ""
        self.description = ""
        self.parts = [Part()]

    def get_labels(self) -> list:
        return ['Koodi', 'Kuvaus']

    def get_types(self) -> list:
        return [
            wx.grid.GRID_VALUE_STRING,
            wx.grid.GRID_VALUE_STRING
        ]
        
    def get_data(self) -> list:
        return [self.code, self.description]

class Part:
    def __init__(self) -> None:
        self.code = ""

    def get_labels(self) -> list:
        return ['Koodi']

    def get_types(self) -> list:
        return [
            wx.grid.GRID_VALUE_STRING
        ]

    def get_data(self) -> list:
        return [self.code]


class CustomDataTable(wx.grid.GridTableBase):
    def __init__(self, objlist):
        """Custom table for lists of Predef, Material, Product or Part objects.

        Args:
            objlist (list): list with atleast one object.
        """
        super().__init__()
        if isinstance(objlist[0], (Predef, Material, Product, Part)):
            self.column_labels = objlist[0].get_labels()
            self.data_types = objlist[0].get_types()
            self.data = []
            for n in range(len(objlist)):
                self.data.append(objlist[n].get_data())
        else:
            raise TypeError(f"Tried to create a CustomDataTable for obj: {objlist[0]}")

    def GetNumberRows(self):
        return len(self.data) + 1
    
    def GetNumberCols(self):
        return len(self.data[0])
    
    def IsEmptyCell(self, row, col):
        try:
            return not self.data[row][col]
        except IndexError:
            return True
    
    def GetValue(self, row, col):
        try:
            return self.data[row][col]
        except IndexError:
            return ''
    
    def SetValue(self, row, col, value):
        def innerSetValue(row, col, value):
            try:
                self.data[row][col] = value
            except IndexError:
                # Add a new row.
                self.data.append([''] * self.GetNumberCols())
                innerSetValue(row, col, value)

                # Tell the grid a row was added.
                msg = wx.grid.GridTableMessage(self, wx.grid.GRIDTABLE_NOTIFY_ROWS_APPENDED, 1)
                self.GetView().ProcessTableMessage(msg)
        innerSetValue(row, col, value)

    def GetColLabelValue(self, col):
        return self.column_labels[col]

    def GetTypeName(self, row, col):
        return self.data_types[col]


if __name__ == '__main__':
    app = wx.App(useBestVisual=True)

    data = Data()
    data.build_test()

    frame = AppFrame(data)
    frame.Show()
    frame.Layout()

    app.MainLoop()