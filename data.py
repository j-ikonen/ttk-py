"""Data classes for TTK."""
from copy import deepcopy

from bson import ObjectId

from database import Database


NEW_OFFER_NAME = "Uusi tarjous"
NEW_GROUP_NAME = "Uusi ryhmä"
NO_PREDEF_FOUND = "Esimääritystä ei löytynyt osalle: '{}'"
GD_TO_DICT = "Muodosta (dict) kopio '{}' sisällötä, jonka pituus on: {}"

GD_NAMES = {
    "predefs": "Esimääritykset",
    "materials": "Materiaalit",
    "products": "Tuotteet",
    "parts": "Osat",
}

GD_DATABASE = ["materials", "products"]

EQ_KEYS = {
    "predefs": ['part', 'mat'],
    "materials": [
        'code',
        'desc',
        'thck',
        'prod',
        'loss',
        'unit',
        'cost'
    ],
    "products": [
        'code',
        'group',
        'desc',
        'prod',
        'x',
        'y',
        'z'
    ],
    "parts": [
        'code',
        'desc',
        'code_x',
        'code_y',
        'code_z'
    ]
}

FIELDS_PARTS = {
    'code': ['', 'string', 'Koodi', False],
    'desc': ['', 'string', 'Kuvaus', False],
    'use_predef': ['', 'string', 'Esimääritys', False],
    'mat': ['', 'string', 'Materiaali', False],
    'use_mat': ['', 'string', 'Käyt. Mat.', True],
    'x': [0, 'long', 'Leveys', True],
    'y': [0, 'long', 'Korkeus', True],
    'z': [0, 'long', 'Syvyys', True],
    'cost': [0.0, 'double:6,2', 'Hinta', True],
    'code_use_mat': 
    [
        "osd['predefs'].find('part', obj['code'], 'mat') "+
        "if self.is_true(obj['use_predef']) else obj['mat']",
        'string', 'Leveys koodi', False
    ],
    'code_x': ["0", 'string', 'Leveys koodi', False],
    'code_y': ["0", 'string', 'Korkeus koodi', False],
    'code_z': ["0", 'string', 'Syvyys koodi', False],
    'code_cost': 
    [
        "obj['x'] * obj['y'] * "+
        "osd['materials'].find('code', obj['use_mat'], 'cost')",
        'string', 'Hinta koodi', False
    ]
}

FIELDS_PRODUCTS = {
    'code': ['', 'string', 'Koodi', False],
    'edited': ['E', 'string', 'Muokattu', True],
    'count': [1, 'long', 'Määrä', False],
    'group': ['', 'string', 'Tuoteryhmä', False],
    'desc': ['', 'string', 'Kuvaus', False],
    'prod': ['', 'string', 'Valmistaja', False],
    'x': [0, 'long', 'Leveys', False],
    'y': [0, 'long', 'Korkeus', False],
    'z': [0, 'long', 'Syvyys', False],
    'work_time': [0.0, 'double:6,2', 'Työaika', False],
    'work_cost': [0.0, 'double:6,2', 'Työhinta', False],
    'part_cost': [0.0, 'double:6,2', 'Osahinta', True],
    'tot_cost': [0.0, 'double:6,2', 'Kok. Hinta', True],
    'inst_unit': ['', 'string', 'Asennusyksikkö', False],
    'code_edited': ["db.get_edited(self.get_edited_filter(obj))", 'string', 'Muokattu koodi', True],
    'code_part_cost': ["obj['parts'].sum('cost')", 'string', 'Osahinnan koodi', False],
    'code_tot_cost': 
    [
        "(obj['work_time'] * obj['work_cost']) + obj['part_cost']",
        'string', 'Kokonaishinnan koodi', False
    ],
    'parts': [None, 'griddata', 'Osat', False]
}

FIELDS_MATERIALS = {
    'code': ['', 'string', 'Koodi', False],
    'edited': ['E', 'string', 'Muokattu', True],
    'desc': ['', 'string', 'Kuvaus', False],
    'thck': [0, 'long', 'Paksuus (mm)', False],
    'prod': ['', 'string', 'Valmistaja', False],
    'loss': [0.0, 'double:6,2', 'Hukka', False],
    'unit': ['€/m2', 'choice:€/m2,€/kpl', 'Hintayksikkö', False],
    'cost': [0.0, 'double:6,2', 'Hinta', False],
    'edg_cost': [0.0, 'double:6,2', 'Reunanauhan hinta', False],
    'add_cost': [0.0, 'double:6,2', 'Lisähinta', False],
    'discount': [0.0, 'double:6,2', 'Alennus', False],
    'tot_cost': [0.0, 'double:6,2', 'Kok. Hinta', True],
    'code_tot_cost': [
        "(obj['cost'] + obj['edg_cost'] + obj['add_cost']) * obj['discount'] * obj['loss']",
        'string', 'Kokonaishinnan koodi', False
    ],
    'code_edited': [
        "db.get_edited(self.get_edited_filter(obj))",
        'string', 'Muokattu koodi', False
    ],
}

FIELDS_PREDEFS = {
    'part': ['', 'string', 'Osa', False],
    'mat': ['', 'string', 'Materiaali', False]
}

COL_PREDEFS = [
    'part', 'mat'
]
COL_MATERIALS = [
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
]
COL_PRODUCTS = [
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
]
COL_PARTS = [
    'code', 'desc', 'use_predef', 'mat',
    'use_mat', 'x', 'y', 'z', 'cost'
]
TABTO_PREDEFS = [1]
TABTO_MATERIALS = [2, 2, 3, 4, 5, 6, 7, 8, 9, 10]
TABTO_PRODUCTS = [2, 2, 3, 4, 5, 6, 7, 8, 9, 10]
TABTO_PARTS = [1, 2, 3]

CODES_PREDEFS = {}
CODES_MATERIALS = {
    'tot_cost': 'code_tot_cost',
    'edited': 'code_edited'
}
CODES_PRODUCTS = {
    'part_cost': 'code_part_cost',
    'tot_cost': 'code_tot_cost',
    'edited': 'code_edited'
}
CODES_PARTS = {
    'use_mat': "code_use_mat",
    'x': "code_x",
    'y': "code_y",
    'z': "code_z",
    'cost': "code_cost"
}

CHILD_PREDEFS = []
CHILD_MATERIALS = []
CHILD_PRODUCTS = ['parts']
CHILD_PARTS = []

PARENT_PREDEFS = []
PARENT_MATERIALS = []
PARENT_PRODUCTS = []
PARENT_PARTS = ['products']


class GridData:
    """Class for data storage and it's various formatting information.

    Class Constants:
        - DEFAULT, TYPE, LABEL, READONLY (int): The index of each information in
        fields Class Variable.

    Class Variables:
        - grid_names (dict): The defined names as key and their labels as values.
        - db (list): The name keys that have a database collection with same name.
        - eq_keys (dict): A list of keys used to check equality for each grid.
        - fields (dict): Field information for each grid.
        - child (dict): Child keys in a list for each grid.
        - parent (dict): Parent keys in a list for each grid.
        - columns (dict): Column keys visible in grid for each grid.
        - tab_to (dict): Each index in list has the index of column to jump to on tab.
        - codes (dict): {The key that receives value from code: The key for code}
    
    Instance Variables:
        - data (list): List of dictionaries containing grid data.
        - name (str): Name key for this GridData.
    """
    DEFAULT = 0
    TYPE = 1
    LABEL = 2
    READONLY = 3

    grid_names = GD_NAMES
    db = GD_DATABASE
    eq_keys = EQ_KEYS
    fields = {
        "predefs": FIELDS_PREDEFS,
        "materials": FIELDS_MATERIALS,
        "products": FIELDS_PRODUCTS,
        "parts": FIELDS_PARTS,
    }
    child = {
        "predefs": CHILD_PREDEFS,
        "materials": CHILD_MATERIALS,
        "products": CHILD_PRODUCTS,
        "parts": CHILD_PARTS,
    }
    parent = {
        "predefs": PARENT_PREDEFS,
        "materials": PARENT_MATERIALS,
        "products": PARENT_PRODUCTS,
        "parts": PARENT_PARTS,
    }
    columns = {
        "predefs": COL_PREDEFS,
        "materials": COL_MATERIALS,
        "products": COL_PRODUCTS,
        "parts": COL_PARTS,
    }
    tab_to = {
        "predefs": TABTO_PREDEFS,
        "materials": TABTO_MATERIALS,
        "products": TABTO_PRODUCTS,
        "parts": TABTO_PARTS,
    }
    codes = {
        "predefs": CODES_PREDEFS,
        "materials": CODES_MATERIALS,
        "products": CODES_PRODUCTS,
        "parts": CODES_PARTS,
    }

    def __init__(self, name, data=[]):
        """GridData class for containing and formatting data for grid windows.
        
        Args:
            name (str): Name string of this GridData object.
            data (list): Contained data as list of dictionaries.
            fields (dict): All field definitions {key: [DEFAULT, TYPE, LABEL, READONLY]}
            child (str|None): GridData.name of child.
            parent (str|None): GridData.name of parent.
            columns (list): Keys that will be shown in grid.
            tab_to (list): Column index for the target column for tab.
            codes (dict): target_key: code_key i.e. 'price': 'code_price'
        """
        if name in self.fields:
            self.name = name
            self.data = []
            if isinstance(data, list):
                for obj in data:
                    self.append(obj)
            else:
                raise TypeError(f"GridData.__init__ data type '{type(data)}' is not a list.")
        else:
            raise ValueError(f"GridData.__init__ name '{name}' is not defined.")

    def __len__(self):
        return len(self.data)

    def append(self, data={}) -> int:
        """Return the index of the appended item.

        Field in dictionary that is list or dict that is not specified in self.child
        must not have subcontainers. Leaving 'data' to default results in an appended
        empty default row.

        Args:
            data (dict): Append copy of this data.
        """
        row = len(self.data)
        default = self.get_default()
        # print(f"GridData.append - name: {self.name} row: {row}, len(data): {len(data)}, " +
        #       f"len(default): {len(default)}")

        # Add data to default dictionary.
        for k, v in data.items():
            if k in GridData.child[self.name]:
                child_list = []
                if isinstance(v, GridData):
                    child_list = v.data
                elif isinstance(v, list):
                    child_list = v

                print(f"GridData.append\n\tdefault[childkey]: {default[k]}" +
                      f"\n\tlen: {len(default[k])}\n")

                for child_obj in child_list:
                    default[k].append(child_obj)

            elif k in default and isinstance(v, dict):
                default[k] = {key: value for key, value in v.items()}

            elif k in default and isinstance(v, list):
                default[k] = [value for value in v]

            elif k in default:
                default[k] = v

            else:
                print(f"Key '{k}' is not defined in GridData.fields[{self.name}]")

        # Append to data.
        self.data.append(default)

        return row

    def delete(self, pos=0, num_rows=1) -> int:
        """Delete 'num_rows' at list index 'pos'
        
        Return: 
            (int) Number of deleted rows.
        """
        deleted = 0
        for n in range(num_rows):
            try:
                del self.data[pos]
                deleted += 1
            except IndexError as e:
                print(f"GridData.delete - {e}\n\tpos: {pos},\n\t" +
                      f"num_rows: {num_rows},\n\tn: {n},\n\t" +
                      f"len: {len(self.data)}\n")

        # # Add empty row if all rows are deleted.
        # if len(self.data) == 0:
        #     self.data = DATA_DEFAULT[self.name]
        return deleted

    def find(self, target_key, target_value, return_key):
        """Find a value matching the given keys.
                
        Attributes:
            target_key (str): Key to the value used to check for correct row.
            target_value (Any): Value used to check for correct row.
            return_key (str): Key to the return value.
        Return:
            Any or GridData.DEFAULT if no value is found.
        """
        for rowdata in self.data:
            try:
                if rowdata[target_key] == target_value:
                    return rowdata[return_key]
            except KeyError as e:
                print(f"GridData.find - There is no field with key:" +
                      f" '{e}' in GridData obj with name={self.name}")
        return GridData.fields[self.name][return_key][GridData.DEFAULT]

    @classmethod
    def from_dict(cls, name, data):
        """Return a new GridData object built from a list of dictionaries.
        
        Args:
            name (str): Name for GridData.name.
            data (list): List of dictionaries for GridData.data
        """
        griddata = GridData(name)
        for obj in data:
            griddata.append(obj)

        # if griddata.child is None:
        #     griddata.data = data
        # else:
        #     for item in data:
        #         child_data = cls.from_dict(griddata.child, item[griddata.child])
        #         item[griddata.child] = child_data
        #         griddata.data.append(item)
        return griddata

    def get(self, row, col=None):
        """Return a value at (row, col) or None.
        
        Args:
            row (int): Row index.
            col (int|str): Column index or dictionary key of value.
        Return:
            Value or None if no value exists at (row, col).
        """
        if col is None:
            try:
                return self.data[row]
            except IndexError:
                return None

        elif isinstance(col, int):
            try:
                return self.data[row][GridData.columns[self.name][col]]
            except (IndexError, KeyError):
                return None

        elif isinstance(col, str):
            try:
                return self.data[row][col]
            except (KeyError, IndexError):
                return None

    def get_children(self) -> list:
        """Return a list of children."""
        return [child for child in GridData.child[self.name]]

    def get_codes(self, row) -> dict:
        """Return dictionary of codes at row. {label: code}."""
        codes = {}
        for label, code_key in GridData.codes[self.name].items():
            codes[label] = self.get(row, code_key)
        return codes

    def get_columns(self) -> list:
        """Return a copy of the list of column keys."""
        return [key for key in GridData.columns[self.name]]

    @classmethod
    def get_db_keys(cls) -> list:
        """Return a copy of grid keys that have a database collection."""
        return [key for key in cls.db]

    def get_default(self) -> dict:
        """Return a new dictionary with default values."""
        default = {
            k: v[self.DEFAULT]
            for k, v in self.fields[self.name].items()
        }

        for child_key in self.child[self.name]:
            default[child_key] = GridData(child_key)

        return default

    def get_default_dict(self) -> dict:
        """Return a new dictionary with default values and any child as dictionary."""
        default = {
            k: v[self.DEFAULT]
            for k, v in self.fields[self.name].items()
        }

        for child_key in self.child[self.name]:
            default[child_key] = GridData(child_key).get_default_dict()

        return default

    def get_edited_filter(self, obj):
        """Return the filter for checking if database has the same item."""
        # print("GridData.get_edited_filter")
        if self.name in GridData.get_db_keys():
            flt = {}
            children = self.get_children()
            for key in GridData.eq_keys[self.name]:
                if key in children:
                    # List of child objects.
                    for n, child_obj in enumerate(obj[key].data):
                        # EqKeys in child object.
                        for child_key in GridData.eq_keys[key]:
                            # Dot notation for MongoDb query of embedded documents.
                            dotkey = "{}.{}.{}".format(key, n, child_key)
                            flt[dotkey] = child_obj[child_key]
                else:
                    flt[key] = obj[key]
                    # print(f"\nAdd {flt[key]}: {obj[key]}")
            return flt

        print(f"\nGridData.get_edited_filter: self.name: {self.name} - " +
              f"Tried to get filter for checking edited cell in a grid with no database.\n")
        return None

    def get_keys(self):
        """Return a list of keys defined in GridData.fields."""
        return list(GridData.fields[self.name].keys())

    def get_key(self, col):
        """Return the key at col index."""
        return GridData.columns[self.name][col]

    def get_label(self, col, grid=False) -> str:
        """Return the label for the column or grid at given index or key.

        Args:
            - col (int|str): Column index or key OR Grid key.
            - grid (bool): True if return label is for the grid, Default False for column.
            For grid label col can only be str key.
        """
        if grid:
            return GridData.grid_names[col]
        else:
            if isinstance(col, int):
                return GridData.fields[self.name][GridData.columns[self.name][col]][self.LABEL]
            elif isinstance(col, str):
                return GridData.fields[self.name][col][self.LABEL]
            else:
                raise IndexError(
                    f"GridData.get_label - Label is not defined for col: {col}")

    def get_n_columns(self) -> int:
        """Return the number of columns to display."""
        return len(GridData.columns[self.name])

    def get_type(self, col) -> str:
        """Return type string for column at index 'col'.
        
        Args:
            col (int|str): Column index or key.
        """
        if isinstance(col, int):
            # try:
            return GridData.fields[self.name][GridData.columns[self.name][col]][self.TYPE]
            # except IndexError as e:
            #     print(f"GridData.get_type - IndexError: {e}\n\tself.name: " +
            #           f"{self.name}\n\tcol: {col}\n\t" +
            #           f"self.TYPE: {self.TYPE}\n")

        elif isinstance(col, str):
            return GridData.fields[self.name][col][self.TYPE]
        else:
            raise IndexError(
                f"GridData.get_type - Type is not defined for col: {col}")

    def is_readonly(self, col) -> bool:
        """Return True if column is specified as read only.
        
        Args:
            col (int): Column index.
        """
        return GridData.fields[self.name][GridData.columns[self.name][col]][GridData.READONLY]

    def is_true(self, value: str) -> bool:
        """Return True if value string is not one of:

        "",'n','N','no','NO','e','E','ei','EI','false','False','FALSE'
        """
        false_keys = [
            "", 'n', 'N', 'no', 'NO',
            'e','E','ei','EI',
            'false', 'False', 'FALSE'
        ]
        return False if value in false_keys else True

    def process_codes(self, osd):
        """Process the codes.

        Args:
            osd (dict): Outside data. Data of other grids.
        """
        # print(f"GridData.process_codes - type(self.data): {type(self.data)}")
        if self.name in GridData.get_db_keys():
            db = Database(self.name)
        else:
            db = None

        for obj in self.data:
            for target_key, code_key in GridData.codes[self.name].items():
                obj[target_key] = eval(obj[code_key])

    def set(self, row, col, value) -> bool:
        """Return True if value was successfully set.

        Args:
            - row (int): Row in grid.
            - col (int|str): Column index OR dictionary key for the value.
            - value (Any): Value to set.

        Return:
            - True: if value is set.
            - False: if not.
        """
        if isinstance(col, int):
            try:
                self.data[row][GridData.columns[self.name][col]] = value
                return True
            except (IndexError, KeyError) as e:
                print(f"{e}\n\trow: {row}, col: {col}, len(self.data): {len(self.data)},"+
                      f" len(self.col_keys): {len(GridData.columns[self.name])}")
                return False
        elif isinstance(col, str):
            try:
                self.data[row][col] = value
                return True
            except (IndexError, KeyError) as e:
                print(f"{e}\n\trow: {row}, col: {col}, len(self.data): {len(self.data)},"+
                      f" len(self.col_keys): {len(GridData.columns[self.name])}")
                return False
        else:
            raise TypeError(f"GridData.set - col: {col} is not int or str")

    def set_codes(self, row, codes: dict):
        """Set the codes.

        Args:
            row (int): Index of row for codes.
            codes (dict): Dictionary in form {label: code}.
        """
        for key, value in codes.items():
            self.data[row][GridData.codes[key]] = value

    def set_row(self, row, value):
        """Set a dictionary to row. 
        
        Row needs to be initiated. Use GridData.append if it is not.

        Args:
            row (int): Row where value is set.
            value (dict): Dictionary of data.
        """
        for key, val in value.items():
            if key in GridData.child[self.name]:
                for child_obj in val:
                    if isinstance(child_obj, GridData):
                        self.data[key].append(child_obj)
                    else:
                        raise TypeError(
                            "GridData.set_row - " +
                            f"Child '{key}' of type {type(child_obj)} " +
                            "is not GridData object.")
                # self.set(row, key, child)
            elif isinstance(val, dict):
                self.set(row, key, {k: v for k, v in val.items()})

            elif isinstance(val, list):
                self.set(row, key, [n for n in val])

            else:
                self.set(row, key, val)

    def sum(self, key: str):
        """Return sum of values at key."""
        s = 0
        for obj in self.data:
            s += obj[key]
        return s

    def to_dict(self) -> list:
        """Return a list of dictionaries of self.data."""
        return [
            {k: (v.to_dict() 
            if k in GridData.child[self.name]
            else [item for item in v]
                if isinstance(v, list)
                else {key: value for key, value in v.items()}
                    if isinstance(v, dict)
                    else v)
                        for k, v in dic.items()}
                            for dic in self.data
        ]

    # @classmethod
    # def new(cls, name):
    #     if name == 'predefs':
    #         return cls.predefs()
    #     elif name == 'materials':
    #         return cls.materials()
    #     elif name == 'products':
    #         return cls.products()
    #     elif name == 'parts':
    #         return cls.parts()

    # @classmethod
    # def predefs(cls, data=[]):
    #     return cls(
    #         name="predefs",
    #         data=data,
    #         fields={
    #             'part': ['', 'string', 'Osa', False],
    #             'mat': ['', 'string', 'Materiaali', False]
    #         },
    #         child=None,
    #         parent=None,
    #         columns=['part', 'mat'],
    #         tab_to=[1, 0],
    #         codes={}
    #     )
    # @classmethod
    # def materials(cls, data=[]):
    #     return cls(
    #         name="materials",
    #         data=data,
    #         fields={
    #             'code': ['', 'string', 'Koodi', False],
    #             'desc': ['', 'string', 'Kuvaus', False],
    #             'thck': [0, 'long', 'Paksuus (mm)', False],
    #             'prod': ['', 'string', 'Valmistaja', False],
    #             'cost': [0.0, 'double', 'Hinta', False],
    #             'unit': ['', 'string', 'Hintayksikkö', False]
    #         },
    #         child=None,
    #         parent=None,
    #         columns=['code', 'desc', 'thck', 'prod', 'cost', 'unit'],
    #         tab_to=[1, 2, 3, 4, 5],
    #         codes={}
    #     )
    # @classmethod
    # def products(cls, data=[]):
    #     for obj in data:
    #         if isinstance(obj['parts'], GridData):
    #             parts = GridData.parts(obj['parts'].data)
    #         else:
    #             parts = GridData.parts(obj['parts'])
    #         obj['parts'] = parts

    #     return cls(
    #         name="products",
    #         data=data,
    #         fields={
    #             'code': ['', 'string', 'Koodi', False],
    #             'desc': ['', 'string', 'Kuvaus', False],
    #             'prod': ['', 'string', 'Valmistaja', False],
    #             'x': [0, 'long', 'Leveys', False],
    #             'y': [0, 'long', 'Korkeus', False],
    #             'z': [0, 'long', 'Syvyys', False],
    #             'cost': [0.0, 'double', 'Hinta', True],
    #             'code_cost': ["obj['parts'].sum('cost')", 'string', 'Hinta koodi', False],
    #             'parts': [GridData.parts(), 'griddata', 'Osat', False]
    #         },
    #         child="parts",
    #         parent=None,
    #         columns=['code', 'desc', 'prod', 'x', 'y', 'z', 'cost'],
    #         tab_to=[1, 2, 3, 4],
    #         codes={'cost': 'code_cost'}
    #     )
    # @classmethod
    # def parts(cls, data=[]):
    #     if isinstance(data, GridData):
    #         raise TypeError("GridData.parts(data), data can not be class GridData")
    #     return cls(
    #         name="parts",
    #         data=data,
    #         fields={
    #             'code': ['', 'string', 'Koodi', False],
    #             'desc': ['', 'string', 'Kuvaus', False],
    #             'use_predef': ['', 'string', 'Esimääritys', False],
    #             'mat': ['', 'string', 'Materiaali', False],
    #             'use_mat': ['', 'string', 'Käyt. Mat.', True],
    #             'x': [0, 'long', 'Leveys', True],
    #             'y': [0, 'long', 'Korkeus', True],
    #             'z': [0, 'long', 'Syvyys', True],
    #             'cost': [0.0, 'double', 'Hinta', True],
    #             'code_use_mat': 
    #             [
    #                 "osd['predefs'].find('part', obj['code'], 'mat') "+
    #                 "if self.is_true(obj['use_predef']) else obj['mat']",
    #                 'string', 'Leveys koodi', False
    #             ],
    #             'code_x': ["0", 'string', 'Leveys koodi', False],
    #             'code_y': ["0", 'string', 'Korkeus koodi', False],
    #             'code_z': ["0", 'string', 'Syvyys koodi', False],
    #             'code_cost': 
    #             [
    #                 "obj['x'] * obj['y'] * "+
    #                 "osd['materials'].find('code', obj['use_mat'], 'cost')",
    #                 'string', 'Hinta koodi', False
    #             ]
    #         },
    #         child=None,
    #         parent="products",
    #         columns=['code', 'desc', 'use_predef', 'mat', 'use_mat', 'x', 'y', 'z', 'cost'],
    #         tab_to=[1, 2, 3, 4, 5, 6, 7],
    #         codes=
    #         {
    #             'use_mat': "code_use_mat",
    #             'x': "code_x",
    #             'y': "code_y",
    #             'z': "code_z",
    #             'cost': "code_cost"
    #         }
    #     )


class Group:
    def __init__(self, name=NEW_GROUP_NAME):
        self.name = name
        self.predefs = GridData('predefs')
        self.materials = GridData('materials')
        self.products = GridData('products')

    def get(self, key):
        if key == 'products':
            return self.products
        elif key == 'materials':
            return self.materials
        elif key == 'predefs':
            return self.predefs
        else:
            raise KeyError(f"Key '{key}' is not defined in Group.get.")

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "predefs": self.predefs.to_dict(),
            "materials": self.materials.to_dict(),
            "products": self.products.to_dict()
        }

    @classmethod
    def from_dict(cls, dic: dict):
        obj = cls()
        obj.name = dic["name"]
        obj.predefs = GridData("predefs", dic["predefs"])
        obj.materials = GridData("materials", dic["materials"])
        obj.products = GridData("products", dic["products"])
        return obj


FILE_KEY = 'filepath'
CLIENT_KEY = 'client'
ADDR_KEY = 'address'
NAME_KEY = 'offer_name'
FC_TEST_KEY = 'Kaappi'
FC_TEST2_KEY = 'Testiyksikkö'
FC_KEY = 'field_count'
FC_MULT = 'mult'
FC_COUNT = 'count'
FC_TOTAL = 'total'
FC_GLOBAL = 'use_global'


class Info:
    # Must be initialized with all possible keys.
    fc_mult = {
        FC_TEST_KEY: 6.5,
        FC_TEST2_KEY: 12.2
    }
    # GridData.name: Field key in GridData
    fc_keys = {'products': 'inst_unit'}
    fc_count_key = 'count'

    def __init__(self, name=NEW_OFFER_NAME):
        self.offer_name = name
        self.filepath = ""
        self.first_name = ""
        self.last_name = ""
        self.address = ""
        self.data = {
            FC_KEY: {
                k: {
                    FC_MULT: mult,
                    FC_COUNT: 0,
                    FC_TOTAL: 0
                } for k, mult in Info.fc_mult.items()
            },
            FC_GLOBAL: True
        }

    def to_dict(self) -> dict:
        return {
            "offer_name": self.offer_name,
            "filepath": self.filepath,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "address": self.address,
            "data": deepcopy(self.data)
        }

    @classmethod
    def from_dict(cls, dic: dict):
        obj = cls()
        obj.offer_name = dic["offer_name"]
        obj.filepath = dic["filepath"]
        obj.first_name = dic["first_name"]
        obj.last_name = dic["last_name"]
        obj.address = dic["address"]
        obj.data = deepcopy(dic["data"])
        return obj
    
    def get(self, key):
        return self.data[key]

    def update_fieldcount_data(self, groups) -> dict:
        """Update the fieldcount data.

        Args:
            group (dict): Group containing GridData objects with field count data.
        """
        # Get multipliers and reset rest to zero.
        fc_data = self.data[FC_KEY]
        for fc_unit in fc_data.keys():
            fc_data[fc_unit][FC_COUNT] = 0
            fc_data[fc_unit][FC_TOTAL] = 0

        # Iterate over all groups.
        for group in groups:
            # Iterate through relevant GridData objects from group.
            for gd_key, field_key in Info.fc_keys.items():
                # Go through the dictionaries in a list.
                for object in group.get(gd_key).data:
                    unit = object[field_key]
                    # Test if object has key for multiples.
                    try:
                        n = object[Info.fc_count_key]
                    except KeyError:
                        n = 1
                    # Update count if the unit is predefined.
                    try:
                        fc_data[unit][FC_COUNT] += 1 * n
                    except KeyError:
                        print(f"Info.get_fieldcount_data\n" +
                            f"\t{unit} is not a predefined fc_unit.")

        # Update the totals.
        for fc_unit in fc_data.keys():
            if self.data[FC_GLOBAL]:
                fc_data[fc_unit][FC_TOTAL] = (Info.fc_mult[fc_unit] *
                                                fc_data[fc_unit][FC_COUNT])
            else:
                fc_data[fc_unit][FC_TOTAL] = (fc_data[fc_unit][FC_MULT] *
                                                fc_data[fc_unit][FC_COUNT])

        # Assign instance Field Count so Class does not overwrite Instance.
        self.data[FC_KEY] = fc_data


    @classmethod
    def get_labels(cls) -> dict:
        return {
            "offer_name": "Tarjouksen nimi",
            "filepath": "Tiedosto",
            "first_name": "Etunimi",
            "last_name": "Sukunimi",
            "address": "Osoite"
        }

    def get_fc_liststrings(self) -> list:
        """Return field count data in listctrl ready format."""
        list_data = []
        for unit in self.data[FC_KEY]:
            unit_data = self.data[FC_KEY][unit]
            mult = Info.fc_mult[unit] if self.data[FC_GLOBAL] else unit_data[FC_MULT]
            list_data.append([
                str(unit),
                str(mult),
                str(unit_data[FC_COUNT]),
                str(unit_data[FC_TOTAL])
            ])
        return list_data

    def set_fc_mult(self, mult, unit):
        """Set the field count multiplier for 'unit'.

        Return the new total using new mult if Info fc use global is set to True.
        """
        if isinstance(mult, float):
            self.data[FC_KEY][unit][FC_MULT] = mult
            return self.update_fc_total(unit)
        return None

    def set_fc_global(self, use_global):
        """Set a new value for fc global and calculate new totals."""
        self.data[FC_GLOBAL] = use_global
        for unit in self.data[FC_KEY].keys():
            self.update_fc_total(unit)

    def update_fc_total(self, unit) -> float:
        """Updated a new total value to a single FC unit. Return the total."""
        if self.data[FC_GLOBAL]:
            total = Info.fc_mult[unit] * self.data[FC_KEY][unit][FC_COUNT]
        else:
            total = self.data[FC_KEY][unit][FC_MULT] * self.data[FC_KEY][unit][FC_COUNT]
        self.data[FC_KEY][unit][FC_TOTAL] = total
        return total

class Offer:
    def __init__(self):
        self.info = Info()
        self.groups = [Group()]

    def to_dict(self) -> dict:
        return {
            "info": self.info.to_dict(),
            "groups": [group.to_dict() for group in self.groups]
        }

    @classmethod
    def from_dict(cls, dic: dict):
        obj = cls()
        obj.info = Info.from_dict(dic["info"])
        obj.groups = [Group.from_dict(gr) for gr in dic["groups"]]
        return obj

    def get_group_names(self):
        return [group.name for group in self.groups]

    def del_groups(self, lst: list):
        lst.sort(reverse=True)
        for idx in lst:
            del self.groups[idx]


class Data:
    def __init__(self):
        self.offers = []
    
    def get(self, link):
        if link is None:
            return []
        elif link.target == Link.OFFER:
            return self.offers[link.n[0]]
        elif link.target == Link.GROUP:
            return self.offers[link.n[0]].groups[link.n[1]]
        elif link.target == Link.PREDEFS:
            return self.offers[link.n[0]].groups[link.n[1]].predefs
        elif link.target == Link.MATERIALS:
            return self.offers[link.n[0]].groups[link.n[1]].materials
        elif link.target == Link.PRODUCTS:
            return self.offers[link.n[0]].groups[link.n[1]].products
        elif link.target == Link.PRODUCT:
            return self.offers[link.n[0]].groups[link.n[1]].products.get(link.n[2])
        elif link.target == Link.PARTS:
            return self.offers[link.n[0]].groups[link.n[1]].products.get(link.n[2], 'parts')
        elif link.target == Link.PREDEF:
            return self.offers[link.n[0]].groups[link.n[1]].predefs.get(link.n[2])
        elif link.target == Link.MATERIAL:
            return self.offers[link.n[0]].groups[link.n[1]].materials.get(link.n[2])
        elif link.target == Link.PRODUCT:
            return self.offers[link.n[0]].groups[link.n[1]].products.get(link.n[2])
        elif link.target == Link.PART:
            return self.offers[link.n[0]].groups[link.n[1]].products.get(link.n[2], 'parts').get(link.n[3])
        elif link.target == Link.DATA:
            return self
        else:
            print(f"Data.get: Link.target '{link.target}' is not defined.")

    def get_treelist(self) -> list:
        treelist = []
        for n_offer in range(len(self.offers)):
            link = Link(Link.OFFER, [n_offer])
            name = self.offers[n_offer].info.offer_name
            treelist.append((link, name))

            for n_group in range(len(self.offers[n_offer].groups)):
                link = Link(Link.GROUP, [n_offer, n_group])
                name = self.offers[n_offer].groups[n_group].name
                treelist.append((link, name))

        return treelist

    # def set(self, link, col, value):
    #     """Set a value to a member at col to a object at link.

    #     Args:
    #         link (Link): Link to the object.
    #         col (int): Column idx to the member which value is to be changed.
    #         value (Any): Value to be changed.
    #     """

    #     obj = self.get(link)

    #     if (link.target == Link.PREDEF or 
    #         link.target == Link.MATERIAL or 
    #         link.target == Link.PRODUCT or 
    #         link.target == Link.PART):
    #         obj.set(col, value)

    #     self.to_print()

    # def build_test(self):
    #     self.offers.append(Offer("Tarjous 1", [
    #         Group("TestGroup"),
    #         Group("Group2")
    #     ]))
    #     self.offers.append(Offer("Testi tarjous", [
    #         Group("DefName"),
    #         Group("One"),
    #         Group("Two"),
    #         Group("Three")
    #     ]))
    #     self.offers.append(Offer("Matinkatu 15", [
    #         Group("Kitchen")
    #     ]))

    #     self.offers[0].groups[0].predefs.data.append({'part': "ovi", 'mat': "MELVA16"})
    #     self.offers[0].groups[0].predefs.data.append({'part': "hylly", 'mat': "MELVA16"})

    def to_print(self):
        print("")
        for offer in self.offers:
            print(f"offer: {offer.name}")
            for group in offer.groups:
                print(f"    group: {group.name}")
                for predef in group.predefs.data:
                    print(f"        predef: {predef}")
                for material in group.materials.data:
                    print(f"        material: {material}")
                for product in group.products.data:
                    print(f"        product: {product}")
                    for part in product['parts'].data:
                        print(f"            part: {part}")
        print("")

    def new_offer(self):
        self.offers.append(Offer())

    def file_opened(self, path: str) -> bool:
        """Return True if an offer with 'path' exists in data."""
        for offer in self.offers:
            if offer.info.filepath == path:
                return True
        return False

    def get_offer_names(self) -> list:
        """Return a list of names of the offers."""
        return [offer.info.offer_name for offer in self.offers]

    def del_offers(self, lst):
        lst.sort(reverse=True)
        for idx in lst:
            del self.offers[idx]


class Link:
    DATA = 0
    OFFERS = 1
    OFFER = 2
    INFO = 3
    GROUPS = 1000
    GROUP = 1001
    PREDEFS = 2000
    PREDEF = 2001
    MATERIALS = 2012
    MATERIAL = 2013
    PRODUCTS = 2014
    PRODUCT = 2015
    PARTS = 2016
    PART = 2017

    def __init__(self, tar, n: list):
        """Link referring to an object in Data class.

        Args:
            tar (int): Target to which class/object this link refers to. (self.tar = Link.GROUP)
            n (list): A list of indexes for each array on path to target.
        """
        self.target = tar
        self.n = n

    def is_valid(self):
        if self.target == Link.DATA:
            return len(self.n) == 0
        elif self.target == Link.OFFERS:
            return len(self.n) == 0
        elif self.target == Link.OFFER:
            return len(self.n) == 1
        elif self.target == Link.INFO:
            return len(self.n) == 1
        elif self.target == Link.GROUPS:
            return len(self.n) == 1
        elif self.target == Link.GROUP:
            return len(self.n) == 2
        elif self.target == Link.PREDEFS:
            return len(self.n) == 2
        elif self.target == Link.MATERIALS:
            return len(self.n) == 2
        elif self.target == Link.PRODUCTS:
            return len(self.n) == 2
        elif self.target == Link.PARTS:
            return len(self.n) == 3
        elif self.target == Link.PREDEF:
            return len(self.n) == 3
        elif self.target == Link.MATERIAL:
            return len(self.n) == 3
        elif self.target == Link.PRODUCT:
            return len(self.n) == 3
        elif self.target == Link.PART:
            return len(self.n) == 4

    # def get_new_object(self):
    #     if self.target == Link.PREDEF:
    #         return Predef()
    #     elif self.target == Link.MATERIAL:
    #         return Material()
    #     elif self.target == Link.PRODUCT:
    #         return Product()
    #     elif self.target == Link.PART:
    #         return Part()


TYPE_STRINGS = {
    "string": str,
    "double": float,
    "long": int,
    "bool": bool,
    "oid": ObjectId,
    "griddata": GridData
}

def convert(typestring: str, valuestring: str):
    st = typestring.split(':')[0]
    if isinstance(valuestring, str):
        if st == "double":
            valuestring = valuestring.replace(',', '.')
        return TYPE_STRINGS[st](valuestring)
    else:
        raise TypeError(f"convert() valuestring is not a string but a {type(valuestring)}")
