import wx
import wx.dataview as dv


class TreePanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)

        self.tree = dv.DataViewTreeCtrl(self)
        self.expanded = {}
        self.selected = []

        self.Bind(dv.EVT_DATAVIEW_SELECTION_CHANGED, self.on_select, self.tree)
        self.Bind(dv.EVT_DATAVIEW_ITEM_START_EDITING, self.on_edit, self.tree)
        self.Bind(dv.EVT_DATAVIEW_ITEM_COLLAPSING, self.on_collapsing, self.tree)
        self.Bind(dv.EVT_DATAVIEW_ITEM_EXPANDING, self.on_expanding, self.tree)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.tree, 1, wx.EXPAND)

        self.SetSizer(sizer)

    def fill(self, treelist):
        """Fill the tree with given treelist data.
        
        Args:
            - treelist (list): List of tuples where (name, link).
        """
        self.tree.DeleteAllItems()
        root = dv.NullDataViewItem
        item = dv.NullDataViewItem

        for (link, name) in treelist:
            try:
                expanded = self.expanded[str(link)]
            except KeyError:
                if len(link) < 2:
                    self.expanded[str(link)] = True
                    expanded = True

            if len(link) == 1:      # TreeRoot
                root = self.tree.AppendContainer(
                    dv.NullDataViewItem,
                    name,
                    expanded=expanded,
                    data=link
                )
                if expanded:
                    self.tree.Expand(root)
            elif len(link) == 2:    # TreeItem
                item = self.tree.AppendContainer(
                    root,
                    name,
                    expanded=expanded,
                    data=link
                )
                if expanded:
                    self.tree.Expand(item)
            elif len(link) == 3:    # TreeChild
                self.tree.AppendItem(item, name, data=link)
        # self.Refresh()

    def get_selected_link(self):
        """Return link to selected item."""
        link = self.tree.GetItemData(self.tree.GetSelection())
        return [n for n in link]

    def on_collapsing(self, evt):
        link = self.tree.GetItemData(evt.GetItem())
        self.expanded[str(link)] = False

    def on_edit(self, evt):
        """Prevent editing."""
        evt.Veto()

    def on_expanding(self, evt):
        link = self.tree.GetItemData(evt.GetItem())
        self.expanded[str(link)] = True

    def on_select(self, evt):
        tree = evt.GetEventObject()
        self.selected = tree.GetItemData(evt.GetItem())
        evt.Skip()
