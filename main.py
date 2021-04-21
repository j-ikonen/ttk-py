"""
TODO:
    Add saved file path/name to Offer.info.
    Add check for already opened file to menu_open event.
    Add workspace to data for remembering opened filepaths.
    Add checkbox to automatically add predefs to parts when adding them.
    Add Dialog for uploading selected objects to a database.
    Add Windows to handle loading objects from a database.
"""
import os
import json

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
GP_NO_PRODUCT_SELECTED = "Tuotetta ei ole valittu."
NO_OFFER_SELECTED = "Tarjousta ei ole valittu."
SAVE_FILE_MESSAGE = "Tallenna nimellä ..."
SAVING_TO = "Tallennetaan tarjous tiedostoon {}"
SAVEAS_CANCEL = "Tallennus peruttu."
WILDCARD = "JSON file (*.json) |*.json"
OPEN_FILE_MESSAGE = "Valitse tiedosto."
OPENING_FILE = "Avataan tiedosto {}"


class AppFrame(wx.Frame):
    def __init__(self, data):
        super().__init__(
            None,
            title=FRAME_TITLE,
            size=FRAME_SIZE,
            style=wx.DEFAULT_FRAME_STYLE|wx.FULL_REPAINT_ON_RESIZE
        )
        self.CenterOnScreen()
        self.create_menubar()

        self.panel = Panel(self, data)

        self.Bind(wx.EVT_CLOSE, self.on_close_window)
    
    def on_close_window(self, evt):
        print("Closing frame.")
        self.Destroy()

    def create_menubar(self):
        menu_bar = wx.MenuBar()
        menu_file = wx.Menu()

        menu_file.Append(wx.ID_NEW)
        menu_file.Append(wx.ID_OPEN)
        # menu_file.Append(wx.ID_SAVE)
        menu_file.Append(wx.ID_SAVEAS)
        menu_file.Append(wx.ID_SEPARATOR)
        menu_file.Append(wx.ID_EXIT)

        menu_bar.Append(menu_file, wx.GetStockLabel(wx.ID_FILE))

        self.SetMenuBar(menu_bar)

        self.Bind(wx.EVT_MENU, self.menu_new, id=wx.ID_NEW)
        self.Bind(wx.EVT_MENU, self.menu_open, id=wx.ID_OPEN)
        # self.Bind(wx.EVT_MENU, self.menu_save, id=wx.ID_SAVE)
        self.Bind(wx.EVT_MENU, self.menu_saveas, id=wx.ID_SAVEAS)
        self.Bind(wx.EVT_MENU, self.menu_exit, id=wx.ID_EXIT)

    def menu_new(self, evt):
        print(f"menu_new event - ")
        self.panel.data.new_offer()
        self.panel.create_tree()

    def menu_open(self, evt):
        """Handle event for opening an offer from a file."""
        dlg = wx.FileDialog(
            self,
            message=OPEN_FILE_MESSAGE,
            defaultDir=os.getcwd(),
            defaultFile="",
            wildcard=WILDCARD,
            style=wx.FD_OPEN | wx.FD_MULTIPLE | wx.FD_CHANGE_DIR |
                  wx.FD_FILE_MUST_EXIST | wx.FD_PREVIEW
        )

        # Get return code from dialog.
        if dlg.ShowModal() == wx.ID_OK:
            paths = dlg.GetPaths()
            for path in paths:
                
                # Open and read the file at path.
                print(OPENING_FILE.format(path))
                with open(path, 'r') as rf:
                    offer_dict = json.load(rf)

                # Create offer object from dictionary
                offer = dt.Offer.from_dict(offer_dict)
                self.panel.data.offers.append(offer)

            # Refresh TreeList with new offers.
            self.panel.create_tree()
        dlg.Destroy()

    def menu_save(self, evt):
        print(f"menu_save event - NOT IMPLEMENTED")

    def menu_saveas(self, evt):
        """Handle event for saving an offer with name."""
        # Get the Link to selected offer.
        offer_link = dt.Link(dt.Link.OFFER, n=[0])
        link = self.panel.pagesel_link
        if link.target == dt.Link.DATA:
            print(NO_OFFER_SELECTED)
            return
        elif link.target == dt.Link.GROUP:
            offer_link.n = [i for i in link.n[:-1]]
        elif link.target == dt.Link.OFFER:
            offer_link.n = [i for i in link.n]

        # Get dictionary of selected offer.
        offer = self.panel.data.get(offer_link).to_dict()
        print(f"Saving '{offer['name']}'")

        # Open FileDialog for Saving.
        dlg = wx.FileDialog(
            self,
            message=SAVE_FILE_MESSAGE,
            defaultDir=os.getcwd(),
            defaultFile=offer['name'],
            wildcard=WILDCARD,
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        )
        # dlg.SetFilterIndex(1)     # For default WILDCARD

        # Get return code from dialog.
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            print(SAVING_TO.format(path))

            # Save offer dictionary to selected file.
            with open(path, 'w') as fp:
                json.dump(offer, fp, indent=4)
        else:
            print(SAVEAS_CANCEL)

        dlg.Destroy()

    def menu_exit(self, evt):
        self.Close()


class Panel(wx.Panel):
    def __init__(self, parent, data):
        super().__init__(parent)

        self.data: dt.Data = data

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
            data=dt.Link(dt.Link.DATA, [])
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
        self.pageidx = {dt.Link.GROUP: 0, dt.Link.OFFER: 1, dt.Link.DATA: 2}
        self.pagesel_link = dt.Link(dt.Link.DATA, [])
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
        self.Bind(wx.grid.EVT_GRID_CELL_CHANGED, self.on_cell_changed, self.grid_parts)
        self.Bind(wx.grid.EVT_GRID_CELL_CHANGED, self.on_cell_changed, self.grid_materials)
        self.Bind(wx.grid.EVT_GRID_CELL_CHANGED, self.on_cell_changed, self.grid_products)

        gp_sizer = wx.BoxSizer(wx.VERTICAL)
        horgrids_sizer = wx.BoxSizer(wx.HORIZONTAL)
        predef_sizer = wx.BoxSizer(wx.VERTICAL)
        mat_sizer = wx.BoxSizer(wx.VERTICAL)

        gp_sizer.Add(gp_label_sizer)
        predef_sizer.Add(self.gp_predefs_label, 0, wx.EXPAND|wx.LEFT|wx.TOP, BORDER)
        predef_sizer.Add(self.grid_predefs, 1, wx.EXPAND|wx.ALL, BORDER)
        horgrids_sizer.Add(predef_sizer, 0, wx.EXPAND)

        mat_sizer.Add(self.gp_materials_label, 0, wx.EXPAND|wx.LEFT|wx.TOP, BORDER)
        mat_sizer.Add(self.grid_materials, 1, wx.EXPAND|wx.ALL, BORDER)
        horgrids_sizer.Add(mat_sizer, 1, wx.EXPAND)

        gp_sizer.Add(horgrids_sizer, 1, wx.EXPAND)
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
            if list[n][0].target == dt.Link.OFFER:
                last = self.tree_ctrl.AppendContainer(self.tree_root, list[n][1], data=list[n][0])
                is_expanded = self.is_treeitem_expanded.get(list[n][1])
                if is_expanded:
                    self.tree_ctrl.Expand(last)
                elif is_expanded is None:
                    self.is_treeitem_expanded[list[n][1]] = True
                    self.tree_ctrl.Expand(last)

            elif list[n][0].target == dt.Link.GROUP:
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

                if link.target == dt.Link.GROUP:
                    self.update_gridpage_content(link)

            elif self.pagesel_link.n != link.n:
                # Change content of the page to obj.
                self.pagesel_link = link
                if link.target == dt.Link.GROUP:
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
        if self.pagesel_link.target == dt.Link.GROUP:
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

        if isinstance(obj, dt.Group):
            self.gp_namectrl.ChangeValue(obj.name)
            print(f"Panel.on_treeitem_activate: Change page content to {obj}")
            self.grid_predefs.update_data(obj.predefs, True)
            self.grid_materials.update_data(obj.materials, True)
            self.grid_products.update_data(obj.products, True)
            self.grid_parts.update_data(None, True)
            self.gp_parts_label.SetLabel(GP_NO_PRODUCT_SELECTED)

        else:
            print(f"Panel.update_gridpage_content given object '{obj}' is not a Group class.")

    def on_select_product(self, evt):
        """Update parts grid and it's label."""
        row = evt.GetRow()
        # print(f"Panel.on_select_grid_cell row: {row}")
        self.grid_products.selected_row = row
        try:
            product_code = self.grid_products.data[row].code
        except IndexError:
            print("Product selection in a row without any initialized data." +
                  " Using previous row for part grid.")
        else:
            # Update part codes
            product = self.grid_products.data[row]
            parts = product.parts
            materials = self.grid_materials.data
            for part in parts:
                part.process_codes(product, materials)
            self.gp_parts_label.SetLabel(GP_PARTS_LABEL.format(product_code))
            self.grid_parts.update_data(parts, True)

    def on_cell_changed(self, evt):
        # print(f"Panel.on_cell_changed")
        # Get selected product, return if no products are initiated.
        product_row = self.grid_products.selected_row
        if product_row is None:
            return

        # Get Product and materials data.
        try:
            product = self.grid_products.data[product_row]
        except IndexError:
            print("Product selection in a row without any initialized data." +
                  " Using previous row for part grid.")
            product = self.grid_products.data[product_row - 1]
        materials = self.grid_materials.data

        # Process part codes and update part data to the grid.
        for part in product.parts:
            # print(f"Processing part {part.code}")
            part.process_codes(product, materials)
        self.grid_parts.update_data(product.parts)
        self.grid_parts.Refresh()


if __name__ == '__main__':
    app = wx.App(useBestVisual=True)

    data = dt.Data()
    data.build_test()

    frame = AppFrame(data)
    frame.Show()
    frame.Layout()

    app.MainLoop()