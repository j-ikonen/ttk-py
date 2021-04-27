"""
TODO:
    Fix DbDialog
    Materiaaleille hukka, hintayksikkö enum €/m2, €/kpl Reunanauha, Lisähinta, Alennus
    Add Tuoteryhmä Työaika Työhinta Osahinta Kokohinta Asennusyksikkö to products.
    Price to two decimals.
    IsEdited as a colored cell

    Add FoldPanelBar to fold grids hidden.

Part:
    In coded value calculations of Part material used is Part.use_material. 
    Part.use_material is Part.material_code if predef does not exist or
    Part.use_predef is ""|"n"|"no"|"e"|"ei"|"False"|"false" otherwise
    Part.use_material is a Predef.materialcode of a matching Predef.partcode

Codes:
    VALUES:
        osd: Outside Data
            osd['predefs']      - GridData
            osd['materials']    - GridData
            osd['parts']        - GridData
            osd['parent']       - Dictionary
        self: GridData where the code is.
        obj: self[row] - Dictionary where the code is.

    FUNCTIONS:
        GridData.find(target_key, target_key, value_key):
            Find a value in another grid.
            Args:
                target_key: Key for matching.
                target_key: Value for matching.
                value_key:  Key for return value.
        GridData.is_true(value):
            Return False if value is ""|"n"|"no"|"e"|"ei"|"False"|"false" else True
        GridData.sum(key):
            Return sum of values in all rows at key in grid.
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