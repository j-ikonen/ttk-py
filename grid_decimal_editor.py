"""Custom wx.grid.Grid editor for Decimal class."""
from decimal import Decimal

import wx
import wx.grid as wxg


class GridDecimalEditor(wxg.GridCellEditor):
    SEPARATOR = 46

    @classmethod
    def set_separator(cls, char: str):
        """Set the separator character used in grid for decimals."""
        if char == '.':
            cls.SEPARATOR = 46
        elif char == ',':
            cls.SEPARATOR = 44
    
    @classmethod
    def get_separator(cls):
        """Return the separator as str."""
        if cls.SEPARATOR == 46:
            return '.'
        elif cls.SEPARATOR == 44:
            return ','

    def __init__(self):
        super().__init__()

    def Create(self, parent, id, evtHandler):
        """Create the textctrl.
        
        Must override.
        """
        self._tc = wx.TextCtrl(parent, id, "")
        self._tc.SetInsertionPoint(0)
        self._tc.Bind(wx.EVT_CHAR, self.on_char, self._tc)
        self.SetControl(self._tc)

        if evtHandler:
            self._tc.PushEventHandler(evtHandler)

    def on_char(self, evt):
        print("Pressed key {}".format(evt.GetKeyCode()))
        key = evt.GetKeyCode()
        mod = evt.GetModifiers()
        sel = self._tc.GetSelection()
        val: str = self._tc.GetValue()
        if key == self.SEPARATOR and mod == wx.MOD_NONE and self.get_separator() not in val:
            evt.Skip()
        elif key > 47 and key < 58 and mod == wx.MOD_NONE:
            evt.Skip()
        elif evt.GetUnicodeKey() == wx.WXK_NONE:
            evt.Skip()
        elif key == 8 and sel is not None:
            if sel[0] == sel[1]:
                self._tc.SetValue(val[0:sel[0]-1] + val[sel[1]:])
                self._tc.SetInsertionPoint(sel[0]-1)
            else:
                self._tc.SetValue(val[0:sel[0]] + val[sel[1]:])
                self._tc.SetInsertionPoint(sel[0])
        elif key == 8:
            pos = self._tc.GetInsertionPoint()
            if pos > 0:
                self._tc.SetValue(val[0:pos-1] + val[pos:])
                self._tc.SetInsertionPoint(pos-1)

    def BeginEdit(self, row, col, grid):
        """Fetch the value from table for text ctrl and begin editing.

        Set focus on the ctrl.        
        Must override.
        """
        val = grid.GetTable().GetValue(row, col)
        if val is None:
            self.startvalue = ""
        else:
            self.startvalue = str(val)

        self._tc.SetValue(self.startvalue)
        self._tc.SetInsertionPointEnd()
        self._tc.SetFocus()
        self._tc.SelectAll()

    def EndEdit(self, row, col, grid, oldval):
        """End edit. Check for a valid and different value.
        
        Must override.
        """
        val = self._tc.GetValue()
        try:
            dec = Decimal(val)
        except:
            return None

        if val != oldval:
            return val
        else:
            return None

    def ApplyEdit(self, row, col, grid):
        """Apply the edit to the table after EndEdit returns a non-None value.
        
        Must override.
        """
        val = self._tc.GetValue()
        grid.GetTable().SetValue(row, col, Decimal(val))
        self.startvalue = ''
        self._tc.SetValue('')

    def Reset(self):
        """Reset the control back to starting value.
        
        Must override.
        """
        self._tc.SetValue(self.startvalue)
        self._tc.SetInsertionPointEnd()

    def IsAcceptedKey(self, evt):
        """Check that the given key is accepted to start the edit.
        
        Only accept editing when first key is [0-9]"""
        key = evt.GetKeyCode()
        if key == 8:
            return True
        return key > 47 and key < 58 and evt.GetModifiers() == wx.MOD_NONE

    def StartingKey(self, evt):
        """Enter the starting key to the control."""
        key = evt.GetKeyCode()
        if key == 8:
            self._tc.SetValue("")

        elif self.IsAcceptedKey(evt):
            self._tc.SetValue(chr(key))
            self._tc.SetInsertionPointEnd()
        else:
            evt.Skip()

    def Clone(self):
        """Create a new object by copying this one.
        
        Must override.
        """
        return GridDecimalEditor()

    def Destroy(self):
        super(GridDecimalEditor, self).Destroy()


if __name__ == '__main__':
    """
    This test uses default table so the Decimal values
    are not retained after setting them.
    """
    app = wx.App()

    frame = wx.Frame(None, size=(1200, 600), title="GridTest")
    grid = wxg.Grid(frame)
    grid.CreateGrid(5,3)
    # grid.RegisterDataType("decimal", wxg.GridCellFloatRenderer, GridDecimalEditor)
    attr = wxg.GridCellAttr()
    attr.SetEditor(GridDecimalEditor())
    grid.SetColAttr(0, attr)
    grid.SetColAttr(1, attr)
    frame.Show()
    app.MainLoop()
