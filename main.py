"""
TODO:
    Create CustomGrid Class for handling all grid stuff.
    Add Saving/Loading an offer to/from a file.
    Add Dialog for uploading selected objects to a database.
    Add Windows to handle loading objects from a database.
"""
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

        self.grid_predefs = self.init_grid(gridpage, Link(Link.PREDEFS, [0, 0]))
        self.grid_materials = self.init_grid(gridpage, Link(Link.MATERIALS, [0, 0]))
        self.grid_products = self.init_grid(gridpage, Link(Link.PRODUCTS, [0, 0]))
        self.grid_parts = self.init_grid(gridpage, None)

        self.Bind(wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.on_grid_cell_left_dclick)
        self.Bind(wx.grid.EVT_GRID_SELECT_CELL, self.on_grid_product_selected_cell, self.grid_products)

        self.Bind(wx.grid.EVT_GRID_TABBING, self.on_grid_predefs_tab, self.grid_predefs)
        self.Bind(wx.grid.EVT_GRID_TABBING, self.on_grid_materials_tab, self.grid_materials)
        self.Bind(wx.grid.EVT_GRID_TABBING, self.on_grid_products_tab, self.grid_products)
        self.Bind(wx.grid.EVT_GRID_TABBING, self.on_grid_parts_tab, self.grid_parts)

        self.Bind(wx.grid.EVT_GRID_CELL_CHANGED, self.on_grid_predefs_cell_changed, self.grid_predefs)
        self.Bind(wx.grid.EVT_GRID_CELL_CHANGED, self.on_grid_materials_cell_changed, self.grid_materials)
        self.Bind(wx.grid.EVT_GRID_CELL_CHANGED, self.on_grid_products_cell_changed, self.grid_products)
        self.Bind(wx.grid.EVT_GRID_CELL_CHANGED, self.on_grid_parts_cell_changed, self.grid_parts)


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
            self.update_grid(Link(Link.PREDEFS, link.n))
            self.update_grid(Link(Link.MATERIALS, link.n))
            self.update_grid(Link(Link.PRODUCTS, link.n))
            self.update_grid(None)
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
        table = CustomDataTable(self.data.get(link), link)
        grid.SetTable(table, True)
        grid.SetRowLabelSize(0)
        grid.SetMargins(0, 0)
        grid.AutoSizeColumns(False)
        return grid

    def update_grid(self, link):
        """Update the content of a grid matching the type of obj in the given list.

        Args:
            objlist (list): A list of Predef|Material|Product|Part objects.
        """
        grid = None
        if link is None:
            table = CustomDataTable(None, link)
            self.grid_parts.SetTable(table, True)
            self.grid_parts.Refresh()
            return
        elif link.target == Link.PARTS:
            grid = self.grid_parts
        elif link.target == Link.PREDEFS:
            grid = self.grid_predefs
        elif link.target == Link.MATERIALS:
            grid = self.grid_materials
        elif link.target == Link.PRODUCTS:
            grid = self.grid_products

        else:
            raise TypeError(f"Panel.update_grid: No grid exists for link target: {link.tar}")

        array = self.data.get(link)
        print(f"Panel.update_grid: Update an array with {array}")
        table = CustomDataTable(array, link)
        grid.SetTable(table, True)
        grid.Refresh()

    def on_grid_cell_left_dclick(self, evt):
        """Change default behaviour so that left doubleclick enables cell editing."""
        if evt.GetEventObject().CanEnableCellControl():
            evt.GetEventObject().EnableCellEditControl()

    def on_grid_predefs_tab(self, evt):
        print("Event grid predefs tab")
    def on_grid_materials_tab(self, evt):
        print("Event grid materials tab")
    def on_grid_products_tab(self, evt):
        print("Event grid products tab")
    def on_grid_parts_tab(self, evt):
        print("Event grid parts tab")

    def on_grid_predefs_cell_changed(self, evt):
        link = Link(Link.PREDEF, self.pagesel_link.n + [evt.GetRow()])
        grid = self.grid_predefs
        self.grid_cell_changed(evt, grid, link)

    def on_grid_materials_cell_changed(self, evt):
        link = Link(Link.MATERIAL, self.pagesel_link.n + [evt.GetRow()])
        self.grid_cell_changed(evt, self.grid_materials, link)

    def on_grid_products_cell_changed(self, evt):
        link = Link(Link.PRODUCT, self.pagesel_link.n + [evt.GetRow()])
        self.grid_cell_changed(evt, self.grid_products, link)

    def on_grid_parts_cell_changed(self, evt):
        link = Link(Link.PART, self.pagesel_link.n + [evt.GetRow()])
        self.grid_cell_changed(evt, self.grid_parts, link)

    def grid_cell_changed(self, evt, grid, link):
        row = evt.GetRow()
        col = evt.GetCol()
        value = grid.GetCellValue(row, col)
        print(f"Panel.grid_cell_changed: col: {col}, link.tar: {link.target}, row: {link.n[-1]}, value: {value}")
        self.data.set(link, col, value)

    def on_grid_product_selected_cell(self, evt):
        row = evt.GetRow()
        n = self.pagesel_link.n + [row]
        self.selected_product = Link(Link.PRODUCT, [i for i in n])
        self.update_grid(Link(Link.PARTS, [i for i in n]))

        try:
            part_label = self.data.get(self.selected_product).code
        except (IndexError, AttributeError):
            part_label = ""

        self.gp_parts_label.SetLabel(GP_PARTS_LABEL.format(part_label))

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
            return Predef()
        elif self.target == Link.MATERIAL:
            return Material()
        elif self.target == Link.PRODUCT:
            return Product()
        elif self.target == Link.PART:
            return Part()


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

        self.offers[0].groups[0].predefs.append(Predef("ovi", "MELVA16"))
        self.offers[0].groups[0].predefs.append(Predef("hylly", "MELVA16"))
    
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


class Predef:
    def __init__(self, part="", material="") -> None:
        self.part = part
        self.material = material

    def get_labels(self) -> list:
        return ['Nimi', 'Materiaalikoodi']
        
    def get_types(self) -> list:
        return [
            wx.grid.GRID_VALUE_STRING,
            wx.grid.GRID_VALUE_STRING
        ]
        
    def get_data(self) -> list:
        return [self.part, self.material]
    
    def set(self, col, value):
        if col == 0:
            self.part = value
        elif col == 1:
            self.material = value

class Material:
    def __init__(self, code="", desc="") -> None:
        self.code = code
        self.description = desc

    def get_labels(self) -> list:
        return ['Koodi', 'Kuvaus']
        
    def get_types(self) -> list:
        return [
            wx.grid.GRID_VALUE_STRING,
            wx.grid.GRID_VALUE_STRING
        ]
        
    def get_data(self) -> list:
        return [self.code, self.description]
    
    def set(self, col, value):
        if col == 0:
            self.code = value
        elif col == 1:
            self.description = value

class Product:
    def __init__(self, code="", desc="") -> None:
        self.code = code
        self.description = desc
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
 
    def set(self, col, value):
        if col == 0:
            self.code = value
        elif col == 1:
            self.description = value

class Part:
    def __init__(self, code="") -> None:
        self.code = code

    def get_labels(self) -> list:
        return ['Koodi']

    def get_types(self) -> list:
        return [
            wx.grid.GRID_VALUE_STRING
        ]

    def get_data(self) -> list:
        return [self.code]
 
    def set(self, col, value):
        if col == 0:
            self.code = value



if __name__ == '__main__':
    app = wx.App(useBestVisual=True)

    data = Data()
    data.build_test()

    frame = AppFrame(data)
    frame.Show()
    frame.Layout()

    app.MainLoop()