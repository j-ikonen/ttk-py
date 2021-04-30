"""
TODO:
    Is Asennusyksikkö choice or string?

    Create dialog with Treebook for settings / global values.
    Add predefined column widths.
    Add remove from database functionality.
    Add part editing in database dialogs.
    Add code editor.
    Add ctrl arrow key scrolling to choice cells.
    Add FoldPanelBar to fold grids hidden.
    Change use_predef column in parts to bool.
    Change Info into something closer to GridData.

    DONE:
    Add field count multiplier global and local editing.
    Add field count list title and a check box for global/local multiplier
    Add inst_unit variables and multipliers to offer.info.
    Add Installunit count with multiplier and a total costs on offer page.
    Make refresh on gridpage check for edited status.
    Format edited columns as a colored cell.
    Test Database dialogs with new column additions.
    Change DbDialog to append items to grids in gridpage.
    Fix adding parts to database.

BUGS:
    Possibly linking same groups list object across different offers on some unknown condition.
        No way to reproduce found. Only happened once. Possibly fixed.

Fields:
    edited:
        'P' 'Puuttuu' for no mathcing document found with 'code'.
        'K' 'Kyllä' for edited document found with 'code'.
        'E' 'Ei' for same document found with 'code'

Part:
    In coded value calculations of Part material used is Part.use_material. 
    Part.use_material is Part.material_code if predef does not exist or
    Part.use_predef is ""|"n"|"no"|"e"|"ei"|"False"|"false" otherwise
    Part.use_material is a Predef.materialcode of a matching Predef.partcode

Codes:
    VALUES:
        osd:    Outside Data
            osd['predefs']      - GridData
            osd['materials']    - GridData
            osd['parts']        - GridData
            osd['parent']       - Dictionary
        self:   GridData where the code is.
        obj:    self[row] - Dictionary where the code is.
        db:     Database(self.name)

    FUNCTIONS:
        GridData.find(target_key, target_value, value_key):
            Find a value in another grid.
            Args:
                target_key: Key for matching.
                target_value: Value for matching.
                value_key:  Key for return value.
        GridData.is_true(value):
            Return False if value is ""|"n"|"no"|"e"|"ei"|"False"|"false" else True
        GridData.sum(key):
            Return sum of values in all rows at key in grid.
        db.has(filter)
            Return True if database has a document matching the filter, else return False.
"""
import wx
import wx.grid

from data import Data
from frame import AppFrame
from database import Database


def main():
    app = wx.App(useBestVisual=True)

    data = Data()

    indexes = Database('materials').get_indexes()
    if 'code' not in indexes:
        Database('materials').index('code', True)
    
    indexes = Database('products').get_indexes()
    if 'code' not in indexes:
        Database('products').index('code', True)

    frame = AppFrame(data)
    frame.Show()
    frame.Layout()

    app.MainLoop()


if __name__ == '__main__':
    main()