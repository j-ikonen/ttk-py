import wx
import wx.dataview as dv


BTN_ADD_GROUP = "+Ryhmä"
BTN_ADD_OFFER = "+Tarjous"
BORDER = 5


class TreePanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)

        self.tree = dv.DataViewTreeCtrl(self)
        self.btn_group = wx.Button(self, label=BTN_ADD_GROUP)
        self.btn_offer = wx.Button(self, label=BTN_ADD_OFFER)
        self.expanded = {}
        self.selected = []

        self.Bind(dv.EVT_DATAVIEW_SELECTION_CHANGED, self.on_select, self.tree)
        self.Bind(dv.EVT_DATAVIEW_ITEM_START_EDITING, self.on_edit, self.tree)
        self.Bind(dv.EVT_DATAVIEW_ITEM_COLLAPSING, self.on_collapsing, self.tree)
        self.Bind(dv.EVT_DATAVIEW_ITEM_EXPANDING, self.on_expanding, self.tree)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer_btn = wx.BoxSizer(wx.HORIZONTAL)
        sizer_btn.Add(self.btn_group, 0, wx.EXPAND|wx.RIGHT, BORDER)
        sizer_btn.Add(self.btn_offer, 0, wx.EXPAND)
        sizer.Add(sizer_btn, 0, wx.EXPAND|wx.ALL, BORDER)
        sizer.Add(self.tree, 1, wx.EXPAND)

        self.SetSizer(sizer)

    def btn_add_group(self):
        return self.btn_group

    def btn_add_offer(self):
        return self.btn_offer

    # def fill(self, treelist):
    #     """Fill the tree with given treelist data.
        
    #     Args:
    #         - treelist (list): List of tuples where (name, link).
    #     """
    #     self.tree.DeleteAllItems()
    #     root = dv.NullDataViewItem
    #     item = dv.NullDataViewItem

    #     for (link, name) in treelist:
    #         try:
    #             expanded = self.expanded[str(link)]
    #         except KeyError:
    #             if len(link) < 2:
    #                 self.expanded[str(link)] = True
    #                 expanded = True

    #         if len(link) == 1:      # TreeRoot
    #             root = self.tree.AppendContainer(
    #                 dv.NullDataViewItem,
    #                 name,
    #                 expanded=expanded,
    #                 data=link
    #             )
    #             if expanded:
    #                 self.tree.Expand(root)
    #         elif len(link) == 2:    # TreeItem
    #             item = self.tree.AppendContainer(
    #                 root,
    #                 name,
    #                 expanded=expanded,
    #                 data=link
    #             )
    #             if expanded:
    #                 self.tree.Expand(item)
    #         elif len(link) == 3:    # TreeChild
    #             self.tree.AppendItem(item, name, data=link)
    #     # self.Refresh()

    def refresh(self, treelist):
        """Refresh the content of the tree with new data."""
        self.tree.DeleteAllItems()
        item = dv.NullDataViewItem

        for tup in treelist:
            if len(tup) == 2:
                expanded = self.get_expanded(tup[0])
                item = self.tree.AppendContainer(
                    dv.NullDataViewItem,
                    tup[1],
                    data=tup
                )
                if expanded:
                    self.tree.Expand(item)
            elif len(tup) == 3:
                self.tree.AppendItem(
                    item,
                    tup[1],
                    data=tup
                )
            else:
                pass

    def get_expanded(self, key):
        """Return True if expanded or init if not set before."""
        if key in self.expanded:
            expanded = self.expanded[key]
        else:
            self.expanded[key] = True
            expanded = True
        print(f"key: {key}, expanded: {expanded}")
        return expanded

    def get_selected_link(self):
        """Return link to selected item."""
        link = self.tree.GetItemData(self.tree.GetSelection())
        if link is None:
            return None
        else:
            return [n for n in link]

    def get_expanded_key(self, link):
        if len(link) == 3:
            return link[2]
        else:
            return link[0]

    def on_collapsing(self, evt):
        link = self.tree.GetItemData(evt.GetItem())
        self.expanded[self.get_expanded_key(link)] = False
        evt.Skip()

    def on_edit(self, evt):
        """Prevent editing."""
        evt.Veto()

    def on_expanding(self, evt):
        link = self.tree.GetItemData(evt.GetItem())
        self.expanded[self.get_expanded_key(link)] = True
        evt.Skip()

    def on_select(self, evt):
        tree = evt.GetEventObject()
        self.selected = tree.GetItemData(evt.GetItem())
        evt.Skip()
