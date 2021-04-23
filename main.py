"""
TODO:
    Find why rows are multiplied when saving and maybe loading from file.
    Add Dialog for uploading selected objects to a database.
    Add Windows to handle loading objects from a database.
    Add FoldPanelBar to fold grids hidden.

Part:
    In coded value calculations of Part material used is Part.use_material. 
    Part.use_material is Part.material_code if predef does not exist or
    Part.use_predef is ""|"n"|"no"|"e"|"ei"|"False"|"false" otherwise
    Part.use_material is a Predef.materialcode of a matching Predef.partcode
"""
import os
import json

import wx
import wx.adv
import wx.dataview as dv
import wx.grid

from grid import CustomGrid
from data import GridData, Link, Info, Group, Offer, Data


FRAME_TITLE = "Ttk-py"
FRAME_SIZE = (1200, 750)
WORKSPACE_FILE = "workspace.json"
LEFTWIN_SIZE = (270, FRAME_SIZE[1])
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
SAVE_NO_PATH = ("Tarjoukselle ei ole määritetty tallenus tiedostoa." +
                " Avataan Tallenna nimellä ...")
BTN_NEW_GROUP = "Lisää ryhmä"
BTN_DEL_GROUP = "Poista ryhmiä"
BTN_NEW_OFFER = "Uusi tarjous"
BTN_CLOSE_OFFER = "Sulje tarjous"
DLG_CLOSE_OFFERS_MSG = "Valitse suljettavat tarjoukset."
DLG_CLOSE_OFFERS_CAP = "Sulje tarjouksia"
DLG_DEL_GROUPS_MSG = "Valitse poistettavat ryhmät tarjouksesta '{}'."
DLG_DEL_GROUPS_CAP = "Poista ryhmiä"


class AppFrame(wx.Frame):
    def __init__(self, data):
        super().__init__(
            None,
            title=FRAME_TITLE,
            size=FRAME_SIZE,
            style=wx.DEFAULT_FRAME_STYLE|wx.FULL_REPAINT_ON_RESIZE
        )
        self.workspace = {
            "open_offers": []
        }
        
        # Load workspace info from file.
        try:
            with open(WORKSPACE_FILE, 'r') as rf:
                self.workspace = json.load(rf)
        except FileNotFoundError as e:
            print(f"No workspace file found: {e}")
        else:
            # Load offers open in last session.
            for path in self.workspace['open_offers']:
                try:
                    with open(path, 'r') as rf:
                        offer = Offer.from_dict(json.load(rf))
                        data.offers.append(offer)
                except FileNotFoundError as e:
                    print(f"{e}")
                except json.decoder.JSONDecodeError as e:
                    print(f"{path}\n\tFile is not a valid json.")

        self.CenterOnScreen()
        self.create_menubar()

        self.panel = Panel(self, data)

        self.Bind(wx.EVT_CLOSE, self.on_close_window)

    def on_close_window(self, evt):
        print("Closing frame.")
        # Save open offers to session workspace file.
        self.workspace['open_offers'] = []
        for offer in self.panel.data.offers:
            if offer.info.filepath != "":
                self.workspace['open_offers'].append(offer.info.filepath)

        # Save offer dictionary to selected file.
        with open(WORKSPACE_FILE, 'w') as fp:
            json.dump(self.workspace, fp, indent=4)

        self.Destroy()

    def create_menubar(self):
        menu_bar = wx.MenuBar()
        menu_file = wx.Menu()

        menu_file.Append(wx.ID_NEW)
        menu_file.Append(wx.ID_OPEN)
        menu_file.Append(wx.ID_SAVE)
        menu_file.Append(wx.ID_SAVEAS)
        menu_file.Append(wx.ID_SEPARATOR)
        menu_file.Append(wx.ID_EXIT)

        menu_bar.Append(menu_file, wx.GetStockLabel(wx.ID_FILE))

        self.SetMenuBar(menu_bar)

        self.Bind(wx.EVT_MENU, self.menu_new, id=wx.ID_NEW)
        self.Bind(wx.EVT_MENU, self.menu_open, id=wx.ID_OPEN)
        self.Bind(wx.EVT_MENU, self.menu_save, id=wx.ID_SAVE)
        self.Bind(wx.EVT_MENU, self.menu_saveas, id=wx.ID_SAVEAS)
        self.Bind(wx.EVT_MENU, self.menu_exit, id=wx.ID_EXIT)

    def menu_new(self, evt):
        """Create new offer."""
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

            for path in dlg.GetPaths():
                # Check if an offer with 'path' is already open.
                if self.panel.data.file_opened(path):
                    print(f"Selected offer is already opened from path {path}.")
                    dlg.Destroy()
                    return

                # Open and read the file at path.
                print(OPENING_FILE.format(path))
                with open(path, 'r') as rf:
                    offer_dict = json.load(rf)

                # Create offer object from dictionary
                offer = Offer.from_dict(offer_dict)
                offer.info.filepath = path
                self.panel.data.offers.append(offer)

            # Refresh TreeList with new offers.
            self.panel.create_tree()
        dlg.Destroy()

    def menu_save(self, evt):
        """Save selected offer to info.filepath if not empty."""
        # Get dictionary of selected offer.
        offer = self.panel.get_selected_offer()
        path = offer.info.filepath
        if path != "":
            print(f"Saving '{offer.name}' to '{path}'")
            
            # Save offer dictionary to selected file.
            with open(path, 'w') as fp:
                json.dump(offer.to_dict(), fp, indent=4)
        else:
            print(SAVE_NO_PATH)
            self.menu_saveas(self, evt)

    def menu_saveas(self, evt):
        """Handle event for 'save as'."""
        # Get selected offer.
        offer = self.panel.get_selected_offer()
        print(f"Saving '{offer.name}'")

        # Open FileDialog for Saving.
        dlg = wx.FileDialog(
            self,
            message=SAVE_FILE_MESSAGE,
            defaultDir=os.getcwd(),
            defaultFile=offer.name,
            wildcard=WILDCARD,
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        )
        # dlg.SetFilterIndex(1)     # For default WILDCARD

        # Get return code from dialog.
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            offer.info.filepath = path
            print(SAVING_TO.format(path))

            # Save offer dictionary to selected file.
            with open(path, 'w') as fp:
                json.dump(offer.to_dict(), fp, indent=4)

        else:
            print(SAVEAS_CANCEL)

        dlg.Destroy()

    def menu_exit(self, evt):
        self.Close()


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
        
        tree_panel = wx.Panel(self.left_win)
        self.tree_ctrl = dv.DataViewTreeCtrl(tree_panel)
        self.tree_root = self.tree_ctrl.AppendContainer(
            dv.NullDataViewItem,
            TREE_ROOT_TITLE,
            data=Link(Link.DATA, [])
        )
        # Save expanded status for refreshing the tree.
        self.is_treeitem_expanded = {TREE_ROOT_TITLE: True}
        self.create_tree()

        # Fill the left window with tree_ctrl
        lwin_sizer = wx.BoxSizer(wx.VERTICAL)
        lwin_sizer.Add(self.tree_ctrl, 1, wx.EXPAND)

        tree_panel.SetSizer(lwin_sizer)

        self.Bind(dv.EVT_DATAVIEW_SELECTION_CHANGED, self.on_treeitem_activate)
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

        self.grid_predefs = CustomGrid(gridpage, GridData.predefs())
        self.grid_materials = CustomGrid(gridpage, GridData.materials())
        self.grid_products = CustomGrid(gridpage, GridData.products())
        self.grid_parts = CustomGrid(gridpage, GridData.parts())

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
        btn_new_group = wx.Button(infopage, label=BTN_NEW_GROUP)
        btn_del_group = wx.Button(infopage, label=BTN_DEL_GROUP)

        self.Bind(wx.EVT_BUTTON, self.on_btn_new_group, btn_new_group)
        self.Bind(wx.EVT_BUTTON, self.on_btn_del_group, btn_del_group)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.Add(btn_new_group, 0, wx.ALL, BORDER)
        btn_sizer.Add(btn_del_group, 0, wx.ALL, BORDER)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(btn_sizer)
        infopage.Sizer = sizer

        #------------------------------------------------------------------------------------------
        # Simplebook - rootpage
        #------------------------------------------------------------------------------------------
        # btn_new_offer = wx.Button(rootpage, label=BTN_NEW_OFFER)
        btn_close_offer = wx.Button(rootpage, label=BTN_CLOSE_OFFER)
        
        # self.Bind(wx.EVT_BUTTON, self.on_btn_new_offer, btn_new_offer)
        self.Bind(wx.EVT_BUTTON, self.on_btn_close_offer, btn_close_offer)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        # btn_sizer.Add(btn_new_offer, 0, wx.ALL, BORDER)
        btn_sizer.Add(btn_close_offer, 0, wx.ALL, BORDER)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(btn_sizer)
        rootpage.Sizer = sizer

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

        # Clear the tree.
        self.tree_ctrl.DeleteChildren(self.tree_root)
        list = self.data.get_treelist()

        last = None
        for n in range(len(list)):
            # Attach offers to rootitem
            if list[n][0].target == Link.OFFER:
                last = self.tree_ctrl.AppendContainer(
                    self.tree_root,
                    list[n][1],
                    data=list[n][0]
                )
                
                # Set expanded status from saved.
                is_expanded = self.is_treeitem_expanded.get(list[n][1])
                if is_expanded:
                    self.tree_ctrl.Expand(last)
                elif is_expanded is None:
                    self.is_treeitem_expanded[list[n][1]] = True
                    self.tree_ctrl.Expand(last)

            # Attach Groups to previous offer.
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

    def get_selected_offer(self):
        """Return the offer selected or whose child is selected in treelist."""
        offer_link = Link(Link.OFFER, n=[0])
        link = self.pagesel_link

        # Check if offer or it's child is selected.
        if link.target == Link.DATA:
            print(NO_OFFER_SELECTED)
            return
        elif link.target == Link.GROUP:
            offer_link.n = [i for i in link.n[:-1]]
        elif link.target == Link.OFFER:
            offer_link.n = [i for i in link.n]

        # Return the selected offer.
        return self.data.get(offer_link)

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

        if isinstance(obj, Group):
            print(f"Panel.on_treeitem_activate: Change page content to {obj}")
            self.gp_namectrl.ChangeValue(obj.name)
            self.grid_predefs.update_data(obj.predefs.data, True)
            self.grid_materials.update_data(obj.materials.data, True)
            self.grid_products.update_data(obj.products.data, True)
            self.grid_parts.update_data([], True)
            self.gp_parts_label.SetLabel(GP_NO_PRODUCT_SELECTED)

        else:
            print(f"Panel.update_gridpage_content given object '{obj}' is not a Group class.")

    def on_select_product(self, evt):
        """Update parts grid and it's label."""
        row = evt.GetRow()
        # print(f"Panel.on_select_grid_cell row: {row}")
        self.grid_products.selected_row = row
        try:
            product_code = self.grid_products.data.get(row, 'code')
        except IndexError:
            print("Product selection in a row without any initialized data." +
                  " Using previous row for part grid.")
        else:
            # Update part codes
            product = self.grid_products.data.get(row)
            parts = product['parts']
            print(f"Panel.on_select_product - parts type: {type(parts)}")
            outside_data = {
                self.grid_predefs.data.name: self.grid_predefs.data,
                self.grid_materials.data.name: self.grid_materials.data,
                self.grid_parts.data.name: product['parts'],
                'parent': product
            }
            parts.process_codes(outside_data)
            self.gp_parts_label.SetLabel(GP_PARTS_LABEL.format(product_code))
            self.grid_parts.update_data(parts.data, True)

    def on_cell_changed(self, evt):
        print(f"Panel.on_cell_changed")
        # Get selected product, return if no products are initiated.
        # product_row = self.grid_products.selected_row
        # if product_row is None:
        #     return

        # # Get Product and materials data.
        # try:
        #     product = self.grid_products.data.get(product_row)
        # except IndexError:
        #     print("Product selection in a row without any initialized data." +
        #           " Using previous row for part grid.")
        #     product = self.grid_products.data.get(product_row - 1)
        # materials = self.grid_materials.data
        # predefs = self.grid_predefs.data

        # # Process part codes and update part data to the grid.
        # for part in product.parts:
        #     # print(f"Processing part {part.code}")
        #     part.process_codes(product, materials, predefs)
        # self.grid_parts.update_data(product.parts)
        # self.grid_parts.Refresh()

    #------------------------------------------------------------------------------------------
    # Simplebook - infpage
    #------------------------------------------------------------------------------------------
    def on_btn_new_group(self, evt):
        """Add a new group to selected offer."""
        offer = self.get_selected_offer()
        if offer is not None:
            offer.groups.append(Group())
            self.create_tree()
        else:
            print(NO_OFFER_SELECTED)

    def on_btn_del_group(self, evt):
        """Delete a group from selected offer."""
        offer = self.get_selected_offer()
        if offer is not None:
            lst = offer.get_group_names()
            dlg = wx.MultiChoiceDialog(
                self,
                DLG_DEL_GROUPS_MSG.format(offer.name),
                DLG_DEL_GROUPS_CAP,
                lst
            )
            if dlg.ShowModal() == wx.ID_OK:
                selections = dlg.GetSelections()
                # Move selection to parent if a deleted group is selected.
                if (self.pagesel_link.target == Link.GROUP and
                    self.pagesel_link.n[1] in selections):
                    cur_sel = self.tree_ctrl.GetSelection()
                    parent = self.tree_ctrl.GetModel().GetParent(cur_sel)
                    self.tree_ctrl.Select(parent)
                    self.tree_ctrl.Refresh()

                offer.del_groups(selections)
                self.create_tree()

        else:
            print(NO_OFFER_SELECTED)

    #------------------------------------------------------------------------------------------
    # Simplebook - rootpage
    #------------------------------------------------------------------------------------------
    def on_btn_new_offer(self, evt):
        print("Panel.on_btn_new_offer")

    def on_btn_close_offer(self, evt):
        print("Panel.on_btn_close_offer")
        lst = self.data.get_offer_names()
        dlg = wx.MultiChoiceDialog(
            self,
            DLG_CLOSE_OFFERS_MSG,
            DLG_CLOSE_OFFERS_CAP,
            lst
        )
        if dlg.ShowModal() == wx.ID_OK:
            selections = dlg.GetSelections()
            self.data.del_offers(selections)
            self.create_tree()

        dlg.Destroy()


if __name__ == '__main__':
    app = wx.App(useBestVisual=True)

    data = Data()
    # data.build_test()

    frame = AppFrame(data)
    frame.Show()
    frame.Layout()

    app.MainLoop()