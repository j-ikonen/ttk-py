"""
TODO:
    Is Asennusyksikkö choice or string?

    Fix database dialog to work with new stuff.
    testtestestesttestesttesttesttest

    Create dialog with Treebook for settings / global values.
    Add predefined column widths.
    Add remove from database functionality.
    Add part editing in database dialogs.
    Add code editor.
    Add ctrl arrow key scrolling to choice cells.
    Add FoldPanelBar to fold grids hidden.
    Change use_predef column in parts to bool.
    Change Info into something closer to GridData.
    Change TtkData.init_data to select the data on something other than isinstance(v, dict)

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

# from data import Data
from frame import AppFrame
from database import Database
from ttk_data import Data, DataRoot, DataItem, DataChild


DEFAULT_SETUP = {
    str(Data): {},
    str(DataRoot): {
        "__name": "Tarjoukset",
        "fc_mult": {
            "type": "DataGrid",
            "fields": {
                "unit": ["", "Asennusyksikkö", "string", False],
                "mult": [0.0, "Kerroin (€/n)", "double:6,2", False]
            },
            "columns": ["unit", "mult"],
        }
    },
    str(DataItem): {
        "__name": "Tarjous",
        "__default_instance_name": "Uusi tarjous",
        "file": {
            "type": "SetupGrid",
            "fields": {
                "file": ["", "Tiedosto", "string", False],
                "path": ["", "Polku", "string", False]
            }
        },
        "info": {
            "type": "SetupGrid",
            "fields": {
                "firstname": ["", "Etunimi", "string", False],
                "lastname": ["", "Sukunimi", "string", False],
                "phone": ["", "Puh.", "string", False],
                "email": ["", "Sähköposti", "string", False],
                "address": ["", "Osoite", "string", False],
                "info": ["", "Lisätiedot", "string", False],
            }
        },
        "fieldcount": {
            "type": "DataGrid",
            "fields": {
                "unit": ["", "Asennusyksikkö", "string", True],
                "mult": [0.0 , "Kerroin (€/n)", "double:6,2", True],
                "count": [0, "Määrä (n)", "long", True],
                "cost": [0.0, "Hinta (€)", "double:6,2", True]
            },
            "columns": ["unit", "mult", "count", "cost"],
            "prevent_new_row": True,
            "read_only": True
        },
        "fc_mult": {
            "type": "DataGrid",
            "fields": {
                "unit": ["", "Asennusyksikkö", "string", False],
                "mult": [0.0, "Kerroin (€/n)", "double:6,2", False]
            },
            "columns": ["unit", "mult"],
        },
        "use_global": {
            "type": 'bool',
            "fields": {"use_global": [False, "Käytä yleisiä arvoja", "bool", False]}
        }
    },
    str(DataChild): {
        "__name": "Ryhmä",
        "__default_instance_name": "Uusi ryhmä",
        "__refresh_n": 3,
        "predefs": {
            "type": "DataGrid",
            "label": "Esimääritykset",
            "name": "Esimääritykset",
            "fields": {
                "part": ["", "Osa", "string", False],
                "material": ["", "Materiaali", "string", False]
            },
            "columns": ["part", "material"]
        },
        "materials": {
            "type": "DataGrid",
            "label": "Materiaalit",
            "name": "Materiaalit",
            "db": "materials",
            "fields": {
                'code': ['', 'Koodi', 'string', False],
                'edited': ['', 'Muokattu', 'string', True],
                'desc': ['', 'Kuvaus', 'string', False],
                'thck': [0, 'Paksuus (mm)', 'long', False],
                'prod': ['', 'Valmistaja', 'string', False],
                'loss': [0.0, 'Hukka', 'double:6,2', False],
                'unit': ['€/m2', 'Hintayksikkö', 'choice:€/m2,€/kpl', False],
                'cost': [0.0, 'Hinta', 'double:6,2', False],
                'edg_cost': [0.0, 'Reunanauhan hinta', 'double:6,2', False],
                'add_cost': [0.0, 'Lisähinta', 'double:6,2', False],
                'discount': [0.0, 'Alennus', 'double:6,2', False],
                'tot_cost': [0.0, 'Kok. Hinta', 'double:6,2', True],
                'code_tot_cost': [
                    "(obj['cost'] + obj['edg_cost'] + obj['add_cost']) * obj['discount'] * obj['loss']",
                    'Kokonaishinnan koodi', 'string', False
                ],
                'code_edited': [
                    "db.get_edited(flt(obj))",
                    'Muokattu koodi', 'string', False
                ],
            },
            "columns": [
                'code',
                'edited',
                'desc',
                'thck',
                'prod',
                'loss',
                'unit',
                'cost',
                'edg_cost',
                'add_cost',
                'discount',
                'tot_cost'
            ],
            "codes": {
                'tot_cost': 'code_tot_cost',
                'edited': 'code_edited'
            }
        },
        "products": {
            "type": "DataGrid",
            "label": "Tuotteet",
            "name": "Tuotteet",
            "db": "products",
            "child": "parts",
            "eq_keys": ['code', 'group', 'desc', 'prod', 'x', 'y', 'z'],
            "child_eq_keys": ['code', 'desc', 'code_x', 'code_y', 'code_z'],
            "fields": {
                'code': ['', 'Koodi', 'string', False],
                'edited': ['E', 'Muokattu', 'string', True],
                'count': [1, 'Määrä', 'long', False],
                'group': ['', 'Tuoteryhmä', 'string', False],
                'desc': ['', 'Kuvaus', 'string', False],
                'prod': ['', 'Valmistaja', 'string', False],
                'x': [0, 'Leveys', 'long', False],
                'y': [0, 'Korkeus', 'long', False],
                'z': [0, 'Syvyys', 'long', False],
                'work_time': [0.0, 'Työaika', 'double:6,2', False],
                'work_cost': [0.0, 'Työhinta', 'double:6,2', False],
                'part_cost': [0.0, 'Osahinta', 'double:6,2', True],
                'tot_cost': [0.0, 'Kok. Hinta', 'double:6,2', True],
                'inst_unit': ['', 'Asennusyksikkö', 'string', False],
                'code_edited':
                [
                    "db.get_edited(flt(obj))",
                    'Muokattu koodi', 'string', True
                ],
                'code_part_cost':
                [
                    "sum(obj['parts'], 'cost')", 'Osahinnan koodi', 'string', False
                ],
                'code_tot_cost':
                [
                    "(obj['work_time'] * obj['work_cost']) + obj['part_cost']",
                    'Kokonaishinnan koodi', 'string', False
                ],
                'parts': [None, 'Osat', 'DataGrid', False]
            },
            "columns": [
                "code",
                "edited",
                "count",
                "group",
                "desc",
                "prod",
                "x",
                "y",
                "z",
                "inst_unit",
                "work_time",
                "work_cost",
                "part_cost",
                "tot_cost",
            ],
            "codes": {
                'part_cost': 'code_part_cost',
                'tot_cost': 'code_tot_cost',
                'edited': 'code_edited'
            }
        },
        "parts": {
            "type": "DataGrid",
            "label": "Osat",
            "name": "Tuotetta ei ole valittu",
            "name_on_parent_selection": "Tuotteen '{}' osat",
            "parent_name_key": "code",
            "fields": {
                'code': ['', 'Koodi', 'string', False],
                'desc': ['', 'Kuvaus', 'string', False],
                'use_predef': ['', 'Esimääritys', 'string', False],
                'mat': ['', 'Materiaali', 'string', False],
                'use_mat': ['', 'Käyt. Mat.', 'string', True],
                'x': [0, 'Leveys', 'long', True],
                'y': [0, 'Korkeus', 'long', True],
                'z': [0, 'Syvyys', 'long', True],
                'cost': [0.0, 'Hinta', 'double:6,2', True],
                'code_use_mat': 
                [
                    "find('predefs', 'material', 'part', obj['code']) "+
                    "if is_true(obj['use_predef']) else obj['mat']",
                    'Käyttö Mat. koodi', 'string', False
                ],
                'code_x': ["parent['x']", 'Leveys koodi', 'string', False],
                'code_y': ["parent['y']", 'Korkeus koodi', 'string', False],
                'code_z': ["parent['z']", 'Syvyys koodi', 'string', False],
                'code_cost': 
                [
                    "obj['x'] * obj['y'] * "+
                    "find('materials', 'cost', 'code', obj['use_mat']) / 1000000",
                    'Hinta koodi', 'string', False
                ]
            },
            "columns": [
                'code', 'desc', 'use_predef', 'mat',
                'use_mat', 'x', 'y', 'z', 'cost'
            ],
            "codes": {
                'use_mat': "code_use_mat",
                'x': "code_x",
                'y': "code_y",
                'z': "code_z",
                'cost': "code_cost"
            }
        }
    },
}

def main():
    app = wx.App(useBestVisual=True)

    setup = DEFAULT_SETUP
    data = Data('ttk-py', setup)
    data.push('Tarjoukset', setup)

    indexes = Database('materials').get_indexes()
    if 'code' not in indexes:
        Database('materials').index('code', True)

    indexes = Database('products').get_indexes()
    if 'code' not in indexes:
        Database('products').index('code', True)

    frame = AppFrame(data, setup)
    frame.Show()
    frame.Layout()

    app.MainLoop()


if __name__ == '__main__':
    main()