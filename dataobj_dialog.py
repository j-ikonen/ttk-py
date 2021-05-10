from copy import deepcopy
from table import OfferTables
import wx

from setup_grid import SetupGrid


BORDER = 5
DOD_COL_SIZE = 360
DOD_MSG = "Muokkaa taulukon '{}' riviä."
DOD_CAP = "Muokkaa"


class DataObjectDialog(wx.Dialog):
    def __init__(self, parent, obj, setup):
        """### Open dialog for editing an object.

        Editing happends in place in given obj arg or a copy can be retrieved with dlg.get_result()
        ### Args:
        - parent: Parent wx.Window
        - obj (dict): Object to edit.
        - setup (dict): Setup information for object. Must contain keys 'label' and 'fields'.
        """
        super().__init__(parent, title=DOD_CAP)

        self.obj = obj
        self.setup = setup
        self.tables = OfferTables()

        # wx.Windows
        txt_msg = wx.StaticText(self, label=DOD_MSG.format(setup['label']))
        grid = SetupGrid(self, self.tables, "", "")
        btn_ok = wx.Button(self, wx.ID_OK)
        btn_cancel = wx.Button(self, wx.ID_CANCEL)

        # Event Bindings

        # Setup
        self.CenterOnParent()
        grid.SetColSize(0, DOD_COL_SIZE)
        grid.change_data(obj, ("",))
        btn_ok.SetDefault()

        # Sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer_btn = wx.StdDialogButtonSizer()

        sizer_btn.AddButton(btn_ok)
        sizer_btn.AddButton(btn_cancel)
        sizer_btn.Realize()

        sizer.Add(txt_msg, 0, wx.EXPAND|wx.ALL, BORDER)
        sizer.Add(grid, 1, wx.EXPAND|wx.ALL, BORDER)
        sizer.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.LEFT|wx.RIGHT, BORDER)
        sizer.Add(sizer_btn, 0, wx.EXPAND|wx.ALL, BORDER)

        self.SetSizer(sizer)
        sizer.Fit(self)

    def get_result(self) -> dict:
        """Return copy of the edited object."""
        return deepcopy(self.obj)