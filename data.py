
NEW_OFFER_NAME = "Uusi tarjous"
NEW_GROUP_NAME = "Uusi ryhmä"
NO_PREDEF_FOUND = "No predef found for part '{}'"

PART_DEFAULT = {
    'code': '',
    'desc': '',
    'use_predef': '',
    'mat': '',
    'use_mat': '',
    'x': 0,
    'y': 0,
    'z': 0,
    'cost': 0.0,
    'code_use_mat':
        "osd['predefs'].find('part', obj['code'], 'mat') "+
        "if self.is_true(obj['use_predef']) else obj['mat']",
    'code_x': "0",
    'code_y': "0",
    'code_z': "0",
    'code_cost':
        "obj['x'] * obj['y'] * "+
        "osd['materials'].find('mat', obj['use_mat'], 'cost')"
}
PREDEF_DEFAULT = {
    'part': "",
    'mat': ""
}
MATERIAL_DEFAULT = {
    'code': '',
    'desc': '',
    'thck': 0,
    'prod': '',
    'cost': 0.0,
    'unit': ''
}
PRODUCT_DEFAULT = {
    'code': '',
    'desc': '',
    'prod': '',
    'x': 0,
    'y': 0,
    'z': 0,
    'cost': 0.0,
    'code_cost': "obj['parts'].sum('cost')",
    'parts': [PART_DEFAULT],
}
DATA_DEFAULT = {
    'predefs': [PREDEF_DEFAULT],
    'materials': [MATERIAL_DEFAULT],
    'products': [PRODUCT_DEFAULT],
    'parts': [PART_DEFAULT]
}

class GridData:
    DEFAULT = 0
    TYPE = 1
    LABEL = 2
    READONLY = 3

    def __init__(
        self,
        name="",
        data=[],
        fields={},
        child=None,
        parent=None,
        columns=[],
        tab_to=[],
        codes={}
    ):
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
        self.name = name
        self.data = data
        self.fields = fields
        self.child=child
        self.parent=parent
        self.columns = columns
        self.tab_to = tab_to
        self.codes = codes

    def get(self, row, col=None):
        if col is None:
            try:
                return self.data[row]
            except IndexError as e:
                print(f"{e}\n    row: {row}, len(self.data): {len(self.data)}")

        elif isinstance(col, int):
            try:
                return self.data[row][self.columns[col]]
            except (IndexError, KeyError) as e:
                print(f"{e}\n    row: {row}, col: {col}, len(self.data): {len(self.data)},"+
                      f" len(self.col_keys): {len(self.columns)}")
        elif isinstance(col, str):
            try:
                return self.data[row][col]
            except (KeyError, IndexError) as e:
                print(f"{e}\n    row: {row}, col: {col}, len(self.data): {len(self.data)},"+
                      f" len(self.col_keys): {len(self.columns)}")

    def set(self, row, col, value) -> bool:
        """Return True if value was successfully set.
        
        Args:
            row (int): Row in grid.
            col (int|str): Column index OR dictionary key for the value.
            value (Any): Value to set.
        """
        if isinstance(col, int):
            try:
                self.data[row][self.columns[col]] = value
                return True
            except (IndexError, KeyError) as e:
                print(f"{e}\n    row: {row}, col: {col}, len(self.data): {len(self.data)},"+
                      f" len(self.col_keys): {len(self.columns)}")
                return False
        elif isinstance(col, str):
            try:
                self.data[row][col] = value
                return True
            except (IndexError, KeyError) as e:
                print(f"{e}\n    row: {row}, col: {col}, len(self.data): {len(self.data)},"+
                      f" len(self.col_keys): {len(self.columns)}")
                return False

    def process_codes(self, osd):
        print(f"GridData.process_codes - type(self.data): {type(self.data)}")
        for obj in self.data:
            for target_key, code_key in self.codes.items():
                obj[target_key] = eval(obj[code_key])

    def get_codes(self, row) -> dict:
        codes = {}
        for code_key in self.codes.values():
            codes[code_key] = self.data[row][code_key]
        return codes

    def set_codes(self, row, codes: dict):
        for key, value in codes.items():
            self.data[row][key] = value

    def find(self, target_key, target_value, return_key):
        """Find a value matching the given keys.
                
        Attributes:
            target_key (str): Key to the value used to check for correct row.
            target_value (Any): Value used to check for correct row.
            return_key (str): Key to the return value.
        Return:
            Value or None if no value is found.
        """
        for rowdata in self.data:
            try:
                if rowdata[target_key] == target_value:
                    return rowdata[return_key]
            except KeyError as e:
                print(f"There is no field with key: {target_key} or {return_key} in"+
                      f" GridData.name={self.name} - {e}")
        return self.fields[return_key][GridData.DEFAULT]

    def append(self, dic=None) -> int:
        """Return the index of the appended item.
        
        Args:
            dic (dict): Must match with self.data.keys().
        """
        if dic is None:
            self.data.append({k: v[self.DEFAULT] for k, v in self.fields.items()})
        else:
            if self.fields.keys() == dic.keys():
                self.data.append(dic)
            else:
                return None
        return len(self.data) - 1
    
    def delete(self, pos=0, num_rows=1) -> int:
        """Return number of deleted rows."""
        deleted = 0
        for n in range(num_rows):
            try:
                del self.data[pos]
                deleted += 1
            except IndexError as e:
                print(f"{e}\n    pos:{pos}, num_rows:{num_rows}, n:{n},"+
                      f" len: {len(self.data)}")
        if len(self.data) == 0:
            self.data = DATA_DEFAULT[self.name]
        return deleted


    def get_label(self, col) -> str:
        return self.fields[self.columns[col]][self.LABEL]

    def get_type(self, col) -> str:
        return self.fields[self.columns[col]][self.TYPE]

    def sum(self, key: str):
        s = 0
        for obj in self.data:
            s += obj[key]
        return s

    def is_true(self, value: str) -> bool:
        false_keys = [
            "",
            'n',
            'N',
            'no',
            'NO',
            'e',
            'E',
            'ei',
            'EI',
            'false',
            'False',
            'FALSE'
        ]
        return False if value in false_keys else True

    def is_readonly(self, col) -> bool:
        """Return True if column is specified as read only."""
        return self.fields[self.columns[col]][GridData.READONLY]

    def to_dict(self) -> dict:
        if self.child is None:
            return self.data
        else:
            data = []
            for obj in self.data:
                new_obj = {}
                for key, value in obj.items():
                    if key == self.child:
                        new_obj[key] = value.to_dict()
                    else:
                        new_obj[key] = value
                data.append(new_obj)
            return data
    
    @classmethod
    def from_dict(cls, name, data):
        griddata = cls.new(name)
        if griddata.child is None:
            griddata.data = data
        else:
            child_data = cls.from_dict(griddata.child, data[griddata.child])
            data[griddata.child] = child_data
            griddata.data = data
        return griddata

    @classmethod
    def new(cls, name):
        if name == 'predefs':
            return cls.predefs()
        elif name == 'materials':
            return cls.materials()
        elif name == 'products':
            return cls.products()
        elif name == 'parts':
            return cls.parts()

    @classmethod
    def predefs(cls, data=[PREDEF_DEFAULT]):
        return cls(
            name="predefs",
            data=data,
            fields={
                'part': ['', 'string', 'Osa', False],
                'mat': ['', 'string', 'Materiaali', False]
            },
            child=None,
            parent=None,
            columns=['part', 'mat'],
            tab_to=[1, 0],
            codes={}
        )
    @classmethod
    def materials(cls, data=[MATERIAL_DEFAULT]):
        return cls(
            name="materials",
            data=data,
            fields={
                'code': ['', 'string', 'Koodi', False],
                'desc': ['', 'string', 'Kuvaus', False],
                'thck': [0, 'long', 'Paksuus (mm)', False],
                'prod': ['', 'string', 'Valmistaja', False],
                'cost': [0.0, 'double', 'Hinta', False],
                'unit': ['', 'string', 'Hintayksikkö', False]
            },
            child=None,
            parent=None,
            columns=['code', 'desc', 'thck', 'prod', 'cost', 'unit'],
            tab_to=[1, 2, 3, 4, 5],
            codes={}
        )
    @classmethod
    def products(cls, data=[PRODUCT_DEFAULT]):
        for obj in data:
            if isinstance(obj['parts'], GridData):
                parts = GridData.parts(obj['parts'].data)
            else:
                parts = GridData.parts(obj['parts'])
            obj['parts'] = parts

        return cls(
            name="products",
            data=data,
            fields={
                'code': ['', 'string', 'Koodi', False],
                'desc': ['', 'string', 'Kuvaus', False],
                'prod': ['', 'string', 'Valmistaja', False],
                'x': [0, 'long', 'Leveys', True],
                'y': [0, 'long', 'Korkeus', True],
                'z': [0, 'long', 'Syvyys', True],
                'cost': [0.0, 'double', 'Hinta', True],
                'code_cost': ["obj['parts'].sum('cost')", 'string', 'Hinta koodi', False],
                'parts': [GridData.parts(), 'griddata', 'Osat', True]
            },
            child="parts",
            parent=None,
            columns=['code', 'desc', 'prod', 'x', 'y', 'z', 'cost'],
            tab_to=[1, 2, 3, 4],
            codes={'cost': 'code_cost'}
        )
    @classmethod
    def parts(cls, data=[PART_DEFAULT]):
        if isinstance(data, GridData):
            raise TypeError("GridData.parts(data), data can not be class GridData")
        return cls(
            name="parts",
            data=data,
            fields={
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
                    "osd['materials'].find('mat', obj['use_mat'], 'cost')",
                    'string', 'Hinta koodi', False
                ]
            },
            child=None,
            parent="products",
            columns=['code', 'desc', 'use_predef', 'mat', 'use_mat', 'x', 'y', 'z', 'cost'],
            tab_to=[1, 2, 3, 4, 5, 6, 7],
            codes=
            {
                'use_mat': "code_use_mat",
                'x': "code_x",
                'y': "code_y",
                'z': "code_z",
                'cost': "code_cost"
            }
        )


class Group:
    def __init__(self, name=NEW_GROUP_NAME) -> None:
        self.name = name
        self.predefs = GridData.predefs()
        self.materials = GridData.materials()
        self.products = GridData.products()

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
        obj.predefs = GridData.predefs(dic["predefs"])
        obj.materials = GridData.materials(dic["materials"])
        obj.products = GridData.products(dic["products"])
        return obj


class Info:
    def __init__(self):
        self.filepath = ""
        self.first_name = ""
        self.last_name = ""
        self.address = ""
    
    def to_dict(self) -> dict:
        return {
            "filepath": self.filepath,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "address": self.address
        }
    @classmethod
    def from_dict(cls, dic: dict):
        obj = cls()
        obj.filepath = dic["filepath"]
        obj.first_name = dic["first_name"]
        obj.last_name = dic["last_name"]
        obj.address = dic["address"]
        return obj


class Offer:
    def __init__(self, name=NEW_OFFER_NAME, groups=[Group()]):
        self.name = name
        self.info = Info()
        self.groups = groups

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "info": self.info.to_dict(),
            "groups": [group.to_dict() for group in self.groups]
        }
    @classmethod
    def from_dict(cls, dic: dict):
        obj = cls()
        obj.name = dic["name"]
        obj.info = Info.from_dict(dic["info"])
        obj.groups = [Group.from_dict(gr) for gr in dic["groups"]]
        return obj

    def get_group_names(self):
        lst = []
        for group in self.groups:
            lst.append(group.name)
        return lst

    def del_groups(self, lst):
        lst.reverse()
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
            name = self.offers[n_offer].name
            treelist.append((link, name))

            for n_group in range(len(self.offers[n_offer].groups)):
                link = Link(Link.GROUP, [n_offer, n_group])
                name = self.offers[n_offer].groups[n_group].name
                treelist.append((link, name))

        return treelist

    def set(self, link, col, value):
        """Set a value to a member at col to a object at link.

        Args:
            link (Link): Link to the object.
            col (int): Column idx to the member which value is to be changed.
            value (Any): Value to be changed.
        """
        try:
            obj = self.get(link)
        except IndexError:
            obj = link.get_new_object()
            arraylink = Link(link.target - 1, link.n[:-1])
            try:
                self.get(arraylink).append(obj)
            except IndexError:
                product_link = Link(Link.PRODUCT, link.n[:-1])
                self.get(product_link).parts.append(obj)

        if (link.target == Link.PREDEF or 
            link.target == Link.MATERIAL or 
            link.target == Link.PRODUCT or 
            link.target == Link.PART):
            obj.set(col, value)
        self.to_print()

    def build_test(self):
        self.offers.append(Offer("Tarjous 1", [
            Group("TestGroup"),
            Group("Group2")
        ]))
        self.offers.append(Offer("Testi tarjous", [
            Group("DefName"),
            Group("One"),
            Group("Two"),
            Group("Three")
        ]))
        self.offers.append(Offer("Matinkatu 15", [
            Group("Kitchen")
        ]))

        self.offers[0].groups[0].predefs.data.append({'part': "ovi", 'mat': "MELVA16"})
        self.offers[0].groups[0].predefs.data.append({'part': "hylly", 'mat': "MELVA16"})

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
        lst.reverse()
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
