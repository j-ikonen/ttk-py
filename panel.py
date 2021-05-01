import wx
import wx.adv
import wx.dataview as dv

from data import FC_GLOBAL, Link, GridData, Group, Info, Data
from grid import CustomGrid
from dialog import DbDialog


FRAME_SIZE = (1200, 750)
LEFTWIN_SIZE = (270, FRAME_SIZE[1])
BOTWIN_SIZE = (FRAME_SIZE[0], 100)
IP_TEXTCTRL_SIZE = (400,-1)     # InfoPage
IP_LABEL_SIZE = (150, -1)
GP_NAMECTRL_SIZE = (125, -1)
BORDER = 5
REFRESH_TIMES = 3

TREE_ROOT_TITLE = "Tarjoukset"
GP_NAMELABEL = "Ryhmän nimi: "  # GridPage
GP_BTN_REFRESH = "Päivitä"
GP_PREDEFS_LABEL = "Osien esimääritellyt materiaalit"
GP_MATERIALS_LABEL = "Materiaalit"
GP_PRODUCTS_LABEL = "Tuotteet"
GP_PARTS_LABEL = "Tuotteen '{}' osat"
GP_NO_PRODUCT_SELECTED = "Tuotetta ei ole valittu."
GP_BTN_DB = "Tietokanta"
NO_OFFER_SELECTED = "Tarjousta ei ole valittu."
BTN_NEW_GROUP = "Lisää ryhmä"
BTN_DEL_GROUP = "Poista ryhmiä"
BTN_NEW_OFFER = "Uusi tarjous"
BTN_CLOSE_OFFER = "Sulje tarjous"
DLG_CLOSE_OFFERS_MSG = "Valitse suljettavat tarjoukset."    # Dialog
DLG_CLOSE_OFFERS_CAP = "Sulje tarjouksia"
DLG_DEL_GROUPS_MSG = "Valitse poistettavat ryhmät tarjouksesta '{}'."
DLG_DEL_GROUPS_CAP = "Poista ryhmiä"
FCL_LABEL_UNIT = "Asennusyksikkö"   # Field Count List
FCL_LABEL_MULT = "Hintakerroin"
FCL_LABEL_N = "Määrä"
FCL_LABEL_COST = "Hinta"
FC_COUNT_KEY = "count"
FC_DLG_MSG = "Yksikön '{}' hintakerroin"
FC_UNIT_COL = 0
FC_MULT_COL = 1
FC_COUNT_COL = 2
FC_TOT_COL = 3


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
        gridpage.SetBackgroundColour((250, 220, 220))   # For testing
        infopage.SetBackgroundColour((200, 240, 230))   # For testing
        rootpage.SetBackgroundColour((220, 210, 240))   # For testing

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
        self.gb_btn_db = wx.Button(gridpage, label=GP_BTN_DB)

        self.Bind(wx.EVT_TEXT, self.on_gp_namectrl_text, self.gp_namectrl)
        self.Bind(wx.EVT_BUTTON, self.on_gp_btn_refresh, self.gp_btn_refresh)
        self.Bind(wx.EVT_BUTTON, self.on_gp_btn_db, self.gb_btn_db)

        gp_label_sizer = wx.BoxSizer(wx.HORIZONTAL)
        gp_label_sizer.Add(self.gp_namelabel, 0, wx.ALL, BORDER)
        gp_label_sizer.Add(self.gp_namectrl, 0, wx.ALL, BORDER)
        gp_label_sizer.Add(self.gp_btn_refresh, 0, wx.ALL, BORDER)
        gp_label_sizer.Add(self.gb_btn_db, 0, wx.ALL, BORDER)

        self.grid_predefs = CustomGrid(gridpage, GridData("predefs"))
        self.grid_materials = CustomGrid(gridpage, GridData("materials"))
        self.grid_products = CustomGrid(gridpage, GridData("products"))
        self.grid_parts = CustomGrid(gridpage, GridData("parts"))

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
        btn_new_group = wx.Button(infopage, label=BTN_NEW_GROUP)
        btn_del_group = wx.Button(infopage, label=BTN_DEL_GROUP)

        self.Bind(wx.EVT_BUTTON, self.on_btn_new_group, btn_new_group)
        self.Bind(wx.EVT_BUTTON, self.on_btn_del_group, btn_del_group)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.Add(btn_new_group, 0, wx.ALL, BORDER)
        btn_sizer.Add(btn_del_group, 0, wx.ALL, BORDER)

        # info_sizer.Add(btn_sizer, 0)
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

        # InstallUnit counter.
        # self.list_data = []
        # field_count_panel = wx.Panel(infopage)
        # TXT_FC_LABEL = "Asennusyksiköt"
        # TXT_FC_MULT = "{} kerroin:"
        # TXT_FC_MULT_NOSEL = "Yksikköä ei ole valittu"
        # self.txt_fc = wx.StaticText(infopage, label=TXT_FC_LABEL)
        # self.txt_fc_mult = wx.StaticText(infopage, label=TXT_FC_MULT_NOSEL)
        # self.txtc_fc = wx.TextCtrl(infopage)
        FC_CHK_LABEL = "Käytä yleisiä kertoimia"
        self.chk_fc_globals = wx.CheckBox(infopage, label=FC_CHK_LABEL)

        self.field_count_list = dv.DataViewListCtrl(infopage)
        self.field_count_list.AppendTextColumn(FCL_LABEL_UNIT)
        self.field_count_list.AppendTextColumn(FCL_LABEL_MULT, dv.DATAVIEW_CELL_EDITABLE)
        self.field_count_list.AppendTextColumn(FCL_LABEL_N)
        self.field_count_list.AppendTextColumn(FCL_LABEL_COST)

        self.Bind(dv.EVT_DATAVIEW_SELECTION_CHANGED, self.on_fc_selection, self.field_count_list)
        self.Bind(dv.EVT_DATAVIEW_ITEM_ACTIVATED, self.on_fc_activate, self.field_count_list)
        self.Bind(wx.EVT_CHECKBOX, self.on_fc_use_global, self.chk_fc_globals)
        # sizer_fc_label = wx.BoxSizer(wx.HORIZONTAL)
        # sizer_fc_label.Add(self.txt_fc_mult, 0, wx.EXPAND|wx.LEFT, BORDER)
        # sizer_fc_label.Add(self.txtc_fc, 0, wx.EXPAND|wx.LEFT, BORDER)

        sizer_fc = wx.BoxSizer(wx.VERTICAL)
        # sizer_fc.Add(self.txt_fc, 0, wx.EXPAND|wx.ALL, BORDER)
        sizer_fc.Add(self.chk_fc_globals, 0, wx.ALL, BORDER)
        sizer_fc.Add(self.field_count_list, 1, wx.EXPAND)

        infopage_sizer = wx.BoxSizer(wx.HORIZONTAL)
        infopage_sizer.Add(infopanel, 3, wx.EXPAND)
        infopage_sizer.Add(sizer_fc, 2, wx.EXPAND)

        sizer_page = wx.BoxSizer(wx.VERTICAL)
        sizer_page.Add(btn_sizer, 0)
        sizer_page.Add(infopage_sizer, 1, wx.EXPAND)

        # infopage_sizer.Add(self.field_count_list, 2, wx.EXPAND)
        infopanel.SetSizer(info_sizer)
        infopage.SetSizer(sizer_page)

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

        root_sizer = wx.BoxSizer(wx.VERTICAL)
        root_sizer.Add(btn_sizer)
        rootpage.SetSizer(root_sizer)

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
        print(f"Panel.on_treeitem_activate: \n\t" +
              f"link: {link.target}, {link.n}, {link}")

        if isinstance(obj, Group):
            print(f"Panel.on_treeitem_activate: Change page content to {obj}")
            self.gp_namectrl.ChangeValue(obj.name)
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
        print(f"\nPanel.on_select_product row: {row}")
        self.grid_products.selected_row = row
        product_code = self.grid_products.data.get(row, 'code')

        # Update parts grid label.
        if product_code is None:
            print("\tProduct selection in a row without any initialized data.")
            self.gp_parts_label.SetLabel(GP_NO_PRODUCT_SELECTED)
        else:   
            self.gp_parts_label.SetLabel(GP_PARTS_LABEL.format(product_code))

        # Update part codes
        parts = self.grid_products.data.get(row, 'parts')
        # print(f"\n\tPARTS - {parts}")
        # try:
        #     printparts = [{k: v for k, v in part.items() if k == 'code'} for part in parts.data]
        #     pprint(printparts)
        # except:
        #     pass
        # print("\n\tPARTS END")
        if parts is not None:
            print(f"\tPanel.on_select_product - parts type: {type(parts)}")
            outside_data = {
                self.grid_predefs.data.name: self.grid_predefs.data,
                self.grid_materials.data.name: self.grid_materials.data,
                self.grid_parts.data.name: self.grid_products.data.get(
                    row, self.grid_parts.data.name),
                'parent': self.grid_products.data.get(row)
            }
            parts.process_codes(outside_data)
            self.grid_parts.update_data(parts, True)
        else:
            self.grid_parts.update_data(None, True)

    def on_cell_changed(self, evt):
        print(f"Panel.on_cell_changed")

    def on_gp_btn_refresh(self, evt):
        """Handle refresh button event for GridData.process_codes()."""
        print(f"Panel.on_gp_btn_refresh")
        def inner_refresh(n):
            outside_data = {
                self.grid_predefs.data.name: self.grid_predefs.data,
                self.grid_materials.data.name: self.grid_materials.data,
                self.grid_products.data.name: self.grid_products.data
            }
            self.grid_predefs.data.process_codes(outside_data)
            self.grid_materials.data.process_codes(outside_data)
            self.grid_products.data.process_codes(outside_data)

            for row in range(self.grid_products.GetNumberRows() - 1):
                parent = self.grid_products.data.get(row)
                parts = self.grid_products.data.get(row, 'parts')
                outside_data['parent'] = parent
                parts.process_codes(outside_data)

            # Do stuff that does not require repeats.
            if n == REFRESH_TIMES - 1:
                # Repaint the cells that require it.
                for row in range(len(self.grid_materials.data)):
                    self.grid_materials.set_edited_cell(row)

                for row in range(len(self.grid_products.data)):
                    self.grid_products.set_edited_cell(row)

                self.grid_predefs.Refresh()
                self.grid_materials.Refresh()
                self.grid_products.Refresh()
                self.grid_parts.Refresh()

        # Repeat to make sure all dependend codes are updated.
        for n in range(REFRESH_TIMES):
            inner_refresh(n)

    def on_gp_btn_db(self, evt):
        """Handle event for db dialog button."""
        with DbDialog(self, 'materials') as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self.add_items_to_offer(dlg.to_offer)

    def add_items_to_offer(self, to_offer):
        """Add items received from dialog to the open offer."""
        print("Panel.add_items_to_offer")
        for collection, obj_list in to_offer.items():
            if collection == 'materials':
                grid = self.grid_materials
            elif collection == 'products':
                grid = self.grid_products
            else:
                print(f"\tP.AITO - Collection '{collection}' is not defined.")
                continue
            for obj in obj_list:
                grid.append(obj)
                print(f"\tP.AITO - parts type: {type(obj['parts'])} should be list")

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
        offer = self.get_selected_offer()
        info: Info = offer.info
        info_dict = info.to_dict()
        for key, ctrl in self.info_textctrls.items():
            ctrl.ChangeValue(info_dict[key])

        use_globals = info.get(FC_GLOBAL)
        self.chk_fc_globals.SetValue(use_globals)
        info.update_fieldcount_data(offer.groups)
        self.update_fcl(info.get_fc_liststrings())

    def update_fcl(self, data: list):
        """Update the Field Count List with new data."""
        self.field_count_list.DeleteAllItems()
        for list_row in data:
            self.field_count_list.AppendItem(list_row)

    def on_fc_selection(self, evt):
        """Handle event for selecting a row. 
        
        Implementing this stopped a crash from happening when left clicking a row.
        """
        pass
        # item = evt.GetItem()
        # row = self.field_count_list.ItemToRow(item)
        # print(f"Panel.on_fc_selection - row: {row}")

    def on_fc_activate(self, evt):
        """Handle field count list activation event. Opens dialog to edit multiplier."""
        item = evt.GetItem()
        row = self.field_count_list.ItemToRow(item)
        unit = self.field_count_list.GetValue(row, FC_UNIT_COL)
        mult = self.field_count_list.GetValue(row, FC_MULT_COL)
        print(f"Panel.on_fc_activate - row: {row}, unit: {unit}")
        with wx.TextEntryDialog(self, FC_DLG_MSG.format(unit), value=mult) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                value: str = dlg.GetValue()
                try:
                    new_mult = float(value.replace(',', '.'))
                except:
                    new_mult = mult
                    print(f"Panel.on_fc_activate - Value '{value}' " +
                           "could not be converted to decimal number. ")
                info: Info = self.get_selected_offer().info
                total = info.set_fc_mult(new_mult, unit)
                if info.get(FC_GLOBAL):
                    self.field_count_list.SetValue(str(Info.fc_mult[unit]), row, FC_MULT_COL)
                else:
                    self.field_count_list.SetValue(str(new_mult), row, FC_MULT_COL)
                self.field_count_list.SetValue(str(total), row, FC_TOT_COL)

        evt.Skip()

    def on_fc_use_global(self, evt):
        """Handle event for fc use global check box."""
        info: Info = self.get_selected_offer().info
        if evt.IsChecked():
            info.set_fc_global(True)
        else:
            info.set_fc_global(False)

        list_data = info.get_fc_liststrings()
        self.update_fcl(list_data)

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
