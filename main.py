"""
TODO:
    Do part dimensions differ in a way that requires cost code for each part?

    Add coloring code cell based on database existance.
    Add part editing in database dialogs.
    Add code editor.
    Add ctrl arrow key scrolling to choice cells.
    Create dialog with Treebook for settings / global values.
    Add FoldPanelBar to fold grids hidden.
    Change use_predef column in parts to bool.


BUGS:


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
        grd:    TtkData.data    - Dictionary of data in this TtkData
            grd['predefs']      - List of dictionaries
            grd['materials']    - List of dictionaries
            grd['parts']        - List of dictionaries
            grd['products']     - List of dictionaries

        self:   TtkData where the code is.
        obj:    Dictionary where the code is.
        db:     Database(self.name)
        parent: Parent dicionary.

    FUNCTIONS:
        find(datakey, returnkey, matchkey, matchvalue):
            Find a value in another grid.
            Args:
                datakey (str):    Key of the grid where value is found.
                returnkey (str):  Key for the field of value to be returned.
                matchkey (str):   Key of field to use for matching correct object in list.
                matchvalue (Any): Value that needs to be at target_key field for a match.

        is_true(value: str):
            Return False if value is ""|"n"|"e"|"False"|"false" else True

        sum(objkey, fieldkey):
            Return the sum of all values at fieldkey in list of objects at objkey.
            Args:
            - objkey (str|list): Key to objectlist or the objectlist itself.
            - fieldkey (str): Key to the field in object.

        db.get_edited(filter)
            Return 'E' for full match found.
            Return 'K' for match with 'code' found with differing eq_fields.
            Return 'P' for not match with 'code' field found.

        flt(obj):
            Return the filter created from obj for db.get_edited function.
"""
import wx
import wx.grid

from frame import AppFrame
from database import Database
from ttk_data import Data
from setup import Setup
from table import OfferTables

def main():
    app = wx.App(useBestVisual=True)

    setup = Setup(['pages'])
    data = Data(setup)
    data.push(setup)
    tables = OfferTables()

    indexes = Database('materials').get_indexes()
    if 'code' not in indexes:
        Database('materials').index('code', True)

    indexes = Database('products').get_indexes()
    if 'code' not in indexes:
        Database('products').index('code', True)

    frame = AppFrame(tables, data, setup)
    frame.Show()
    frame.Layout()

    app.MainLoop()


if __name__ == '__main__':
    main()