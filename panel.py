from database_panel import DatabasePanel
from offer_dialog import OfferDialog
from bson.objectid import ObjectId
from wx.core import TextEntryDialog
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
        self.Bind(dv.EVT_DATAVIEW_ITEM_CONTEXT_MENU, self.on_tree_context_menu)

        self.page_offer = OfferPage(self.book, self.tables)
        self.page_group = GroupPage(self.book, self.tables)
        self.page_db = DatabasePanel(self.book, self.tables)

        self.page_db.SetBackgroundColour((220, 220, 255))

        PAGE_TITLE_OFFER = "Tarjous"
        PAGE_TITLE_GROUP = "Ryhmä"
        PAGE_TITLE_DB = "Tietokanta"

        self.book.AddPage(self.page_offer, PAGE_TITLE_OFFER)
        self.book.AddPage(self.page_group, PAGE_TITLE_GROUP)
        self.book.AddPage(self.page_db, PAGE_TITLE_DB)

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

            # Selection changed offer.
            if self.page_offer.pk_val != data[0]:
                self.page_offer.set_pk(data[0])

                # No group selected with offer.
                if len(data) == 1:
                    self.page_group.set_pk(None)

            # Selection changed group.
            if len(data) > 1 and self.page_group.pk_val != data[1]:
                self.page_group.set_pk(data[1])

            # self.page_db.set_pk(data)
            # page.set_pk(data[-1])
            evt.Skip()

    def on_tree_context_menu(self, evt):
        """Open context menu for the tree."""
        item = evt.GetItem()

        if not hasattr(self, "id_new_offer"):
            self.id_new_offer = wx.NewIdRef()
            self.id_open_offer = wx.NewIdRef()
            self.close_offer = wx.NewIdRef()
            self.id_edit_name = wx.NewIdRef()
            self.id_delete = wx.NewIdRef()
            self.id_new_group = wx.NewIdRef()

            self.Bind(wx.EVT_MENU, self.on_new_offer, self.id_new_offer)
            self.Bind(wx.EVT_MENU, self.on_open_offer, self.id_open_offer)
            self.Bind(wx.EVT_MENU, self.on_close_offer, self.close_offer)
            self.Bind(wx.EVT_MENU, self.on_edit_name, self.id_edit_name)
            self.Bind(wx.EVT_MENU, self.on_new_group, self.id_new_group)
            self.Bind(wx.EVT_MENU, self.on_delete, self.id_delete)

        menu = wx.Menu()
        menu.Append(self.id_new_offer, "Uusi tarjous", "Avaa uusi tarjous.")
        menu.Append(self.id_open_offer, "Avaa tarjous", "Avaa tallennettu tarjous.")
        if item.IsOk():
            menu.Append(self.close_offer, "Sulje tarjous", "Sulje valittu tarjous.")
            menu.AppendSeparator()
            menu.Append(self.id_edit_name, "Muuta nimeä", "Muuta valitun tarjouksen tai ryhmän nimi.")
            menu.AppendSeparator()
            menu.Append(self.id_new_group, "Uusi ryhmä", "Lisää uusi ryhmä valittuun tarjoukseen.")
            if len(self.treepanel.tree.GetItemData(item)) == 2:
                menu.Append(self.id_delete, "Poista ryhmä", "Poista valittu ryhmä.")

        self.PopupMenu(menu)
        menu.Destroy()

    def on_open_offer(self, evt):
        """Open an existing offer."""
        with OfferDialog(self, self.tables, self.open_offers) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                offer_id = dlg.selected_id
                self.open_offers.append(offer_id)
                self.refresh_tree()

    def on_new_offer(self, evt):
        """Create a new offer."""
        with TextEntryDialog(self, "Uuden tarjouksen nimi", "Uusi tarjous") as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                oid = str(ObjectId())
                if self.tables.insert(
                    "offers",
                    ["id", "name"],
                    [oid, dlg.GetValue()]):

                    self.open_offers.append(oid)
                    self.refresh_tree()


    def on_new_group(self, evt):
        """Open a new group to selected offer."""
        item = self.treepanel.tree.GetSelection()
        if item.IsOk():
            data = self.treepanel.tree.GetItemData(item)
            with TextEntryDialog(self, "Uuden ryhmän nimi", "Uusi ryhmä") as dlg:
                if dlg.ShowModal() == wx.ID_OK:
                    if self.tables.insert(
                        "offer_groups",
                        ["id", "offer_id", "name"],
                        [str(ObjectId()), data[0], dlg.GetValue()]):

                        self.refresh_tree()

    def on_edit_name(self, evt):
        print("EDIT NAME TO BE IMPLEMENTED")
        # item = evt.GetItem()
        item = self.treepanel.tree.GetSelection()
        if item.IsOk():
            data = self.treepanel.tree.GetItemData(item)

            # Offer selected.
            if len(data) == 1:
                self.page_offer.change_name()

            # Group selected.
            elif len(data) == 2:
                self.page_group.change_name()

    def on_delete(self, evt):
        """Delete the selected group."""
        item = self.treepanel.tree.GetSelection()
        if item.IsOk():
            data = self.treepanel.tree.GetItemData(item)
            # Group selected.
            if len(data) == 2:
                group_id = data[-1]
                if self.tables.delete("offer_groups", ["id"], [group_id]):
                    self.page_group.set_pk(None)
                    self.refresh_tree()

    def on_close_offer(self, evt):
        """Close the selected offer."""
        item = self.treepanel.tree.GetSelection()
        if item.IsOk():
            data = self.treepanel.tree.GetItemData(item)

            # Find the selected offer.
            for n, offer in enumerate(self.open_offers):
                if offer == data[0]:
                    del self.open_offers[n]
                    self.page_offer.set_pk(None)
                    self.page_group.set_pk(None)
                    self.refresh_tree()
                    return

    def refresh_tree(self):
        """Handle refreshing the tree."""
        treelist = self.tables.get_treelist(self.open_offers)
        self.treepanel.refresh(treelist)