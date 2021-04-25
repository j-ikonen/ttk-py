import wx
import wx.adv
import wx.dataview as dv

from data import Link, GridData, Group, Info
from grid import CustomGrid
from database import Database


FRAME_SIZE = (1200, 750)
LEFTWIN_SIZE = (270, FRAME_SIZE[1])
BOTWIN_SIZE = (FRAME_SIZE[0], 100)
TREE_ROOT_TITLE = "Tarjoukset"
GP_NAMELABEL = "Ryhmän nimi: "
GP_NAMECTRL_SIZE = (125, -1)
IP_TEXTCTRL_SIZE = (400,-1)
IP_LABEL_SIZE = (150, -1)
BORDER = 5
GP_BTN_REFRESH = "Päivitä"
GP_PREDEFS_LABEL = "Osien esimääritellyt materiaalit"
GP_MATERIALS_LABEL = "Materiaalit"
GP_PRODUCTS_LABEL = "Tuotteet"
GP_PARTS_LABEL = "Tuotteen '{}' osat"
GP_NO_PRODUCT_SELECTED = "Tuotetta ei ole valittu."
NO_OFFER_SELECTED = "Tarjousta ei ole valittu."
BTN_NEW_GROUP = "Lisää ryhmä"
BTN_DEL_GROUP = "Poista ryhmiä"
BTN_NEW_OFFER = "Uusi tarjous"
BTN_CLOSE_OFFER = "Sulje tarjous"
DLG_CLOSE_OFFERS_MSG = "Valitse suljettavat tarjoukset."
DLG_CLOSE_OFFERS_CAP = "Sulje tarjouksia"
DLG_DEL_GROUPS_MSG = "Valitse poistettavat ryhmät tarjouksesta '{}'."
DLG_DEL_GROUPS_CAP = "Poista ryhmiä"
REFRESH_TIMES = 3


class Panel(wx.Panel):
    def __init__(self, parent, data):
        """Handle MainPanel windows.
        
        Args:
            parent: Parent wx.Frame.
            data (data.Data): Data class.
        """
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
        self.gp_btn_refresh = wx.Button(gridpage, label=GP_BTN_REFRESH)
        
        self.Bind(wx.EVT_TEXT, self.on_gp_namectrl_text, self.gp_namectrl)
        self.Bind(wx.EVT_BUTTON, self.on_gp_btn_refresh, self.gp_btn_refresh)

        gp_label_sizer = wx.BoxSizer(wx.HORIZONTAL)
        gp_label_sizer.Add(self.gp_namelabel, 0, wx.ALL, BORDER)
        gp_label_sizer.Add(self.gp_namectrl, 0, wx.ALL, BORDER)
        gp_label_sizer.Add(self.gp_btn_refresh, 0, wx.ALL, BORDER)

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
        info_sizer = wx.BoxSizer(wx.VERTICAL)
        infopanel = wx.Panel(infopage)

        # Buttons
        btn_new_group = wx.Button(infopanel, label=BTN_NEW_GROUP)
        btn_del_group = wx.Button(infopanel, label=BTN_DEL_GROUP)

        self.Bind(wx.EVT_BUTTON, self.on_btn_new_group, btn_new_group)
        self.Bind(wx.EVT_BUTTON, self.on_btn_del_group, btn_del_group)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.Add(btn_new_group, 0, wx.ALL, BORDER)
        btn_sizer.Add(btn_del_group, 0, wx.ALL, BORDER)

        info_sizer.Add(btn_sizer, 0, wx.EXPAND)
        info_sizer.Add((400, 20))

        # Info() edits.
        info_labels = {}
        self.info_textctrls = {}
        biggest_width = 0
        test_text = wx.StaticText(infopanel)
        init_info = Info.get_labels()

        for label in init_info.values():
            size = test_text.GetTextExtent(label)
            if biggest_width < size.GetWidth():
                biggest_width = size.GetWidth()

        for key, label in init_info.items():
            info_labels[key] = wx.StaticText(
                infopanel,
                label=label,
                size=(biggest_width, -1),
                style=wx.ALIGN_RIGHT
            )
            self.info_textctrls[key] = wx.TextCtrl(
                infopanel,
                value="",
                size=IP_TEXTCTRL_SIZE
            )
            size = info_labels[key].GetSizeFromText(label)
            if size.GetWidth() > biggest_width:
                biggest_width = size.GetWidth()

            info_row_sizer = wx.BoxSizer(wx.HORIZONTAL)
            info_row_sizer.Add(info_labels[key], 0, wx.ALL, BORDER)
            info_row_sizer.Add(self.info_textctrls[key], 0, wx.ALL, BORDER)
            info_sizer.Add(info_row_sizer, 0, wx.EXPAND)

            self.Bind(wx.EVT_TEXT, self.on_info_text, self.info_textctrls[key])

        infopanel.SetSizer(info_sizer)
        infopage_sizer = wx.BoxSizer(wx.HORIZONTAL)
        infopage_sizer.Add(infopanel, 1, wx.EXPAND)
        infopage.SetSizer(infopage_sizer)


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
                elif link.target == Link.OFFER:
                    self.update_infopage_content()
                    # print("Panel.on_treeitem_activate CHANGE TO INFOPAGE")

            elif self.pagesel_link.n != link.n:
                # Change content of the page to obj.
                self.pagesel_link = link
                if link.target == Link.GROUP:
                    self.update_gridpage_content(link)
                elif link.target == Link.OFFER:
                    self.update_infopage_content()
                    # print("Panel.on_treeitem_activate CHANGE CONTENT OF INFOPAGE")

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
        product_code = self.grid_products.data.get(row, 'code')

        # Update parts grid label.
        if product_code is None:
            print("Product selection in a row without any initialized data." +
                  " Using previous row for part grid.")
            self.gp_parts_label.SetLabel(GP_NO_PRODUCT_SELECTED)
        else:   
            self.gp_parts_label.SetLabel(GP_PARTS_LABEL.format(product_code))

        # Update part codes
        parts = self.grid_products.data.get(row, 'parts')
        if parts:
            print(f"Panel.on_select_product - parts type: {type(parts)}")
            outside_data = {
                self.grid_predefs.data.name: self.grid_predefs.data,
                self.grid_materials.data.name: self.grid_materials.data,
                self.grid_parts.data.name: self.grid_products.data.get(
                    row, self.grid_parts.data.name),
                'parent': self.grid_products.data.get(row)
            }
            parts.process_codes(outside_data)
            self.grid_parts.update_data(parts.data, True)
        else:
            self.grid_parts.update_data([], True)

    def on_cell_changed(self, evt):
        print(f"Panel.on_cell_changed")

    def on_gp_btn_refresh(self, evt):
        """Handle refresh button event for GridData.process_codes()."""
        print(f"Panel.on_gp_btn_refresh")
        def inner_refresh():
            outside_data = {
                self.grid_predefs.data.name: self.grid_predefs.data,
                self.grid_materials.data.name: self.grid_materials.data,
                self.grid_products.data.name: self.grid_products.data
            }
            self.grid_predefs.data.process_codes(outside_data)
            self.grid_materials.data.process_codes(outside_data)
            self.grid_products.data.process_codes(outside_data)
            self.grid_predefs.Refresh()
            self.grid_materials.Refresh()
            self.grid_products.Refresh()
            for row in range(self.grid_products.GetNumberRows() - 1):
                parent = self.grid_products.data.get(row)
                parts = self.grid_products.data.get(row, 'parts')
                outside_data['parent'] = parent
                parts.process_codes(outside_data)

            self.grid_parts.Refresh()
        for n in range(REFRESH_TIMES):
            inner_refresh()

    # def on_btn_materials_insert(self, evt):
    #     self.insert_to_db('materials')

    # def on_btn_products_insert(self, evt):
    #     self.insert_to_db('products')

    # def insert_to_db(self, collection):
    #     """Insert selected data to database.

    #     Args:
    #         collection (str): Name of collection where insert happens.
    #     """
    #     print("Panel.insert_to_db")
    #     # Find the grid from which we add to database.
    #     if collection == 'materials':
    #         grid = self.grid_materials
    #     elif collection == 'products':
    #         grid = self.grid_products

    #     # Create list of objects for database insert.
    #     data = grid.data.to_dict()
    #     to_db = []
    #     for row in grid.GetSelectedRows():
    #         to_db.append(data[row])
        
    #     # Insert to database.
    #     ids = Database(collection).insert(to_db)
    #     print(f"\tInserted ids: {ids}")

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
                DLG_DEL_GROUPS_MSG.format(offer.info.offer_name),
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

    def on_info_text(self, evt):
        """Handle event for infopage textctrls."""
        eobj = None
        key = ""
        # Find the key for edited ctrl.
        for k, ctrl in self.info_textctrls.items():
            if ctrl == evt.GetEventObject():
                eobj = ctrl
                key = k
                break

        # Update data with new value.
        info = self.get_selected_offer().info.to_dict()
        info[key] = eobj.GetValue()
        self.get_selected_offer().info = Info.from_dict(info)

        # Update tree with new name.
        if key == "offer_name":
            self.create_tree()

    def update_infopage_content(self):
        """Get values from selected offer to TextCtrls."""
        print("Panel.update_infopage_content")
        info_dict = self.get_selected_offer().info.to_dict()
        for key, ctrl in self.info_textctrls.items():
            ctrl.ChangeValue(info_dict[key])

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
