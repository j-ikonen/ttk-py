import wx
import wx.dataview as dv


# BTN_ADD_GROUP = "+Ryhmä"
# BTN_ADD_OFFER = "+Tarjous"
# BORDER = 5


class TreePanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)

        self.tree = dv.DataViewTreeCtrl(self)
        # self.btn_group = wx.Button(self, label=BTN_ADD_GROUP)
        # self.btn_offer = wx.Button(self, label=BTN_ADD_OFFER)
        self.expanded = {}
        # self.selected = []

        # self.Bind(dv.EVT_DATAVIEW_SELECTION_CHANGED, self.on_select, self.tree)
        self.Bind(dv.EVT_DATAVIEW_ITEM_START_EDITING, self.on_edit, self.tree)
        self.Bind(dv.EVT_DATAVIEW_ITEM_COLLAPSING, self.on_collapsing, self.tree)
        self.Bind(dv.EVT_DATAVIEW_ITEM_EXPANDING, self.on_expanding, self.tree)

        sizer = wx.BoxSizer(wx.VERTICAL)
        # sizer_btn = wx.BoxSizer(wx.HORIZONTAL)
        # sizer_btn.Add(self.btn_group, 0, wx.EXPAND|wx.RIGHT, BORDER)
        # sizer_btn.Add(self.btn_offer, 0, wx.EXPAND)
        # sizer.Add(sizer_btn, 0, wx.EXPAND|wx.ALL, BORDER)
        sizer.Add(self.tree, 1, wx.EXPAND)

        self.SetSizer(sizer)

    # def btn_add_group(self):
    #     return self.btn_group

    # def btn_add_offer(self):
    #     return self.btn_offer

    def refresh(self, treelist):
        """Refresh the content of the treelist with new items from treelist.

        Attach (offer_id, group_id) tuple to list item data.

        Parameters
        ----------
        treelist : list
            List of tuples (Name, offer_id, group_id)
        """
        self.tree.DeleteAllItems()
        item = dv.NullDataViewItem

        for tup in treelist:
            if len(tup) == 2:
                expanded = self.get_expanded(tup[1])
                item = self.tree.AppendContainer(
                    dv.NullDataViewItem,
                    tup[0],
                    data=tup[1:]
                )
                if expanded:
                    self.tree.Expand(item)
            elif len(tup) == 3:
                self.tree.AppendItem(
                    item,
                    tup[0],
                    data=tup[1:]
                )
            else:
                pass

    def get_expanded(self, key):
        """Return True if expanded, False otherwise. Init as True if not defined."""
        if key not in self.expanded:
            self.expanded[key] = True
        return self.expanded[key]

    def get_selected(self):
        """Return attached data of the selected list item.

        Return
        ------
            Attached data of selected item.
            None if nothing is selected.
        """
        item = self.tree.GetSelection()
        if item.IsOk():
            return self.tree.GetItemData(item)
        else:
            return None

    def on_collapsing(self, evt):
        """Save collapsed status for refresh."""
        data = self.tree.GetItemData(evt.GetItem())
        self.expanded[data[-1]] = False
        evt.Skip()

    def on_edit(self, evt):
        """Prevent editing."""
        evt.Veto()

    def on_expanding(self, evt):
        """Save expanded status for refresh."""
        data = self.tree.GetItemData(evt.GetItem())
        self.expanded[data[-1]] = True
        evt.Skip()

    # def on_select(self, evt):
    #     # tree = evt.GetEventObject()
    #     self.selected = self.tree.GetItemData(evt.GetItem())
    #     evt.Skip()
