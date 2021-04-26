import collections
from pprint import pprint

from wx.core import DragNone


NEW_OFFER_NAME = "Uusi tarjous"
NEW_GROUP_NAME = "Uusi ryhmä"
NO_PREDEF_FOUND = "Esimääritystä ei löytynyt osalle: '{}'"
GD_TO_DICT = "Muodosta (dict) kopio '{}' sisällötä, jonka pituus on: {}"

FIELDS_PARTS = {
    'code': ['', 'string', 'Koodi', False],
    'desc': ['', 'string', 'Kuvaus', False],
    'use_predef': ['', 'string', 'Esimääritys', False],
    'mat': ['', 'string', 'Materiaali', False],
    'use_mat': ['', 'string', 'Käyt. Mat.', True],
    'x': [0, 'long', 'Leveys', True],
    'y': [0, 'long', 'Korkeus', True],
    'z': [0, 'long', 'Syvyys', True],
    'cost': [0.0, 'double', 'Hinta', True],
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
    'desc': ['', 'string', 'Kuvaus', False],
    'prod': ['', 'string', 'Valmistaja', False],
    'x': [0, 'long', 'Leveys', False],
    'y': [0, 'long', 'Korkeus', False],
    'z': [0, 'long', 'Syvyys', False],
    'cost': [0.0, 'double', 'Hinta', True],
    'code_cost': ["obj['parts'].sum('cost')", 'string', 'Hinta koodi', False],
    'parts': [None, 'griddata', 'Osat', False]
}

FIELDS_MATERIALS = {
    'code': ['', 'string', 'Koodi', False],
    'desc': ['', 'string', 'Kuvaus', False],
    'thck': [0, 'long', 'Paksuus (mm)', False],
    'prod': ['', 'string', 'Valmistaja', False],
    'cost': [0.0, 'double', 'Hinta', False],
    'unit': ['', 'string', 'Hintayksikkö', False]
}

FIELDS_PREDEFS = {
    'part': ['', 'string', 'Osa', False],
    'mat': ['', 'string', 'Materiaali', False]
}

COL_PREDEFS = [
    'part', 'mat'
]
COL_MATERIALS = [
    'code', 'desc', 'thck', 'prod', 'cost', 'unit'
]
COL_PRODUCTS = [
    'code', 'desc', 'prod', 'x', 'y', 'z', 'cost'
]
COL_PARTS = [
    'code', 'desc', 'use_predef', 'mat',
    'use_mat', 'x', 'y', 'z', 'cost'
]
TABTO_PREDEFS = [1]
TABTO_MATERIALS = [1, 2, 3, 4, 5]
TABTO_PRODUCTS = [1, 2, 3, 4, 5, 6]
TABTO_PARTS = [1, 2, 3]

CODES_PREDEFS = {}
CODES_MATERIALS = {}
CODES_PRODUCTS = {
    'cost': 'code_cost'
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
    DEFAULT = 0
    TYPE = 1
    LABEL = 2
    READONLY = 3

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
            self.data = data
        else:
            raise ValueError(f"GridData.__init__ name '{name}' is not defined.")

    def __len__(self):
        return len(self.data)

    def append(self, data=None) -> int:
        """Return the index of the appended item.

        Field in dictionary that is list or dict that is not specified in self.child
        must not have subcontainers.

        Args:
            data (dict): Append copy of this data.
        """
        row = len(self.data)
        default = self.get_default()
        print(f"GridData.append - row: {row}")

        # Add data to default dictionary.
        for k, v in data.items():
            if k in GridData.child[self.name]:
                for child_obj in v:
                    default[k].append(child_obj)

            elif k in default and isinstance(k, dict):
                default[k] = {key: value for key, value in v.items()}

            elif k in default and isinstance(k, list):
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
        griddata = cls.new(name)
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

    def get_codes(self, row) -> dict:
        """Return dictionary of codes at row. {label: code}."""
        codes = {}
        for label, code_key in GridData.codes[self.name].items():
            codes[label] = self.get(row, code_key)
        return codes

    def get_default(self) -> dict:
        """Return a new dictionary with default values."""
        default = {
            k: v[self.DEFAULT]
            for k, v in self.fields[self.name].items()
        }
        for child_key in self.child[self.name]:
            default[child_key] = GridData.new(child_key)

    def get_keys(self):
        """Return a list of keys defined in GridData.fields."""
        return list(GridData.fields[self.name].keys())

    def get_label(self, col) -> str:
        """Return the label string for for column at index 'col'.
        
        Args:
            col (int|str): Column index or key.
        """
        if isinstance(col, int):
            return GridData.fields[self.name][self.columns[col]][self.LABEL]
        elif isinstance(col, str):
            return GridData.fields[self.name][col][self.LABEL]
        else:
            raise IndexError(
                f"GridData.get_label - Label is not defined for col: {col}")

    def get_type(self, col) -> str:
        """Return type string for column at index 'col'.
        
        Args:
            col (int|str): Column index or key.
        """
        if isinstance(col, int):
            return GridData.fields[self.name][self.columns[col]][self.TYPE]
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
        return GridData.fields[self.name][self.columns[col]][GridData.READONLY]

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


class Info:
    def __init__(self, name=NEW_OFFER_NAME):
        self.offer_name = name
        self.filepath = ""
        self.first_name = ""
        self.last_name = ""
        self.address = ""

    def to_dict(self) -> dict:
        return {
            "offer_name": self.offer_name,
            "filepath": self.filepath,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "address": self.address
        }

    @classmethod
    def from_dict(cls, dic: dict):
        obj = cls()
        obj.offer_name = dic["offer_name"]
        obj.filepath = dic["filepath"]
        obj.first_name = dic["first_name"]
        obj.last_name = dic["last_name"]
        obj.address = dic["address"]
        return obj

    @classmethod
    def get_labels(cls) -> dict:
        return {
            "offer_name": "Tarjouksen nimi",
            "filepath": "Tiedosto",
            "first_name": "Etunimi",
            "last_name": "Sukunimi",
            "address": "Osoite"
        }

class Offer:
    def __init__(self, groups=[Group()]):
        self.info = Info()
        self.groups = groups

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
        lst = []
        for group in self.groups:
            lst.append(group.name)
        return lst

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
        lst = []
        for offer in self.offers:
            lst.append(offer.name)
        return lst

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
