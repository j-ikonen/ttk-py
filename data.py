NEW_OFFER_NAME = "Uusi tarjous"
NEW_GROUP_NAME = "Uusi ryhmä"
NO_PREDEF_FOUND = "No predef found for part '{}'"


class GridData:
    def __init__(self) -> None:
        pass
    def get(self, col):
        return None
    def set(self, col, value):
        pass
    def new(self):
        return type(self)()
    def get_labels(self):
        return []
    def get_types(self):
        return []
    def get_list(self):
        return []
    def get_readonly(self): # [4, 5] columns 4 and 5 are readonly
        return []
    def get_tab(self): # [1, 0]
        return []
    def __getitem__(self, col):
        return self.get(col)
    def __setitem__(self, col, value):
        self.set(col, value)
    def get_codes(self):
        return None

class Predef(GridData):
    def __init__(self, partcode="", materialcode="") -> None:
        super().__init__()
        self.partcode = partcode
        self.materialcode = materialcode
    def to_dict(self) -> dict:
        return {
            "partcode": self.partcode,
            "materialcode": self.materialcode
        }
    def get(self, col):
        if col == 0: return self.partcode
        elif col == 1: return self.materialcode
    def set(self, col, value):
        if col == 0: self.partcode = value
        elif col == 1: self.materialcode = value
    def new(self):
        return Predef()
    def get_labels(self):
        return ['Osa koodi', 'Materiaali koodi']
    def get_types(self):
        return ['string', 'string']
    def get_list(self):
        return [self.partcode, self.materialcode]
    def get_readonly(self): 
        return []
    def get_tab(self):
        return [1, 0]
    def __getitem__(self, col):
        return self.get(col)
    def __setitem__(self, col, value):
        self.set(col, value)
    
    @classmethod
    def from_dict(cls, dic: dict):
        obj = cls()
        obj.partcode = dic["partcode"]
        obj.materialcode = dic["materialcode"]
        return obj

class Material(GridData):
    def __init__(self, code="", desc="") -> None:
        super().__init__()
        self.code = code
        self.desc = desc
        self.thickness = 10
    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "desc": self.desc,
            "thickness": self.thickness
        }
    @classmethod
    def from_dict(cls, dic: dict):
        obj = cls()
        obj.code = dic["code"]
        obj.desc = dic["desc"]
        obj.thickness = dic["thickness"]
        return obj

    def get(self, col):
        if col == 0: return self.code
        elif col == 1: return self.desc
        elif col == 2: return self.thickness
    def set(self, col, value):
        if col == 0: self.code = value
        elif col == 1: self.desc = value
        elif col == 2: self.thickness = value
    def new(self):
        return Material()
    def get_labels(self):
        return ['Koodi', 'Kuvaus', 'Paksuus']
    def get_types(self):
        return ['string', 'string', 'long']
    def get_list(self):
        return [self.code, self.desc, self.thickness]
    def get_readonly(self): 
        return []
    def get_tab(self):
        return [1, 0]
    def __getitem__(self, col):
        return self.get(col)
    def __setitem__(self, col, value):
        self.set(col, value)

class Product(GridData):
    def __init__(self, code="", desc="", w=0, h=0, d=0) -> None:
        super().__init__()
        self.code = code
        self.desc = desc
        self.w = w
        self.h = h
        self.d = d
        self.parts = []
    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "desc": self.desc,
            "w": self.w,
            "h": self.h,
            "d": self.d,
            "parts": [p.to_dict() for p in self.parts]
        }
    @classmethod
    def from_dict(cls, dic: dict):
        obj = cls()
        obj.code = dic["code"]
        obj.desc = dic["desc"]
        obj.w = dic["w"]
        obj.h = dic["h"]
        obj.d = dic["d"]
        obj.parts = [Part.from_dict(part) for part in dic["parts"]]
        return obj

    def get(self, col):
        if col == 0: return self.code
        elif col == 1: return self.desc
        elif col == 2: return self.w
        elif col == 3: return self.h
        elif col == 4: return self.d
    def set(self, col, value):
        if col == 0: self.code = value
        elif col == 1: self.desc = value
        elif col == 2: self.w = value
        elif col == 3: self.h = value
        elif col == 4: self.d = value
    def new(self):
        return Product()
    def get_labels(self):
        return ['Koodi', 'Kuvaus', 'Leveys', 'Korkeys', 'Syvyys']
    def get_types(self):
        return ['string', 'string', 'long', 'long', 'long']
    def get_list(self):
        return [self.code, self.desc, self.w, self.h, self.d]
    def get_readonly(self): 
        return []
    def get_tab(self):
        return [1, 2, 3, 4, 0]
    def __getitem__(self, col):
        return self.get(col)
    def __setitem__(self, col, value):
        self.set(col, value)
    def part(self, code):
        for n in range(len(self.parts)):
            if self.parts[n].code == code:
                return self.parts[n]
        raise ValueError(f"Part with code '{code}' was not found.")

class Part(GridData):
    def __init__(self, code="", desc="") -> None:
        super().__init__()
        self.code = code
        self.desc = desc
        self.use_predef = ""
        self.material_code = ""
        self.use_material = ""
        self.x = 0
        self.y = 0
        self.z = 0
        self.code_x = "product_w - (2 * thickness['sivu'])"
        self.code_y = "thickness['sivu']"
        self.code_z = "product_d - thickness['tausta']"
    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "desc": self.desc,
            "use_predef": self.use_predef,
            "material_code": self.material_code,
            "use_material": self.use_material,
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "code_x": self.code_x,
            "code_y": self.code_y,
            "code_z": self.code_z
        }
    @classmethod
    def from_dict(cls, dic: dict):
        obj = cls()
        obj.code = dic["code"]
        obj.desc = dic["desc"]
        obj.use_predef = dic["use_predef"]
        obj.material_code = dic["material_code"]
        obj.use_material = dic["use_material"]
        obj.x = dic["x"]
        obj.y = dic["y"]
        obj.z = dic["z"]
        obj.code_x = dic["code_x"]
        obj.code_y = dic["code_y"]
        obj.code_z = dic["code_z"]
        return obj

    def get(self, col):
        if col == 0: return self.code
        elif col == 1: return self.desc
        elif col == 2: return self.use_predef
        elif col == 3: return self.material_code
        elif col == 4: return self.use_material
        elif col == 5: return self.x
        elif col == 6: return self.y
        elif col == 7: return self.z
    def set(self, col, value):
        if col == 0: self.code = value
        elif col == 1: self.desc = value
        elif col == 2: self.use_predef = value
        elif col == 3: self.material_code = value
    def new(self):
        return Part()
    def get_labels(self):
        return ['Koodi', 'Kuvaus', 'Käytä Esiasetusta', 'Materiaali', 'Materiaali käytössä', 'Leveys', 'Korkeus', 'Syvyys']
    def get_types(self):
        return ['string', 'string', 'string', 'string', 'string', 'long', 'long', 'long']
    def get_list(self):
        return [self.code, self.desc, self.use_predef, self.material_code, self.use_material, self.x, self.y, self.z]
    def get_readonly(self):
        return [4, 5, 6, 7]
    def get_tab(self):
        return [1, 2, 3, 4, 5, 6, 7, 0]
    def __getitem__(self, col):
        return self.get(col)
    def __setitem__(self, col, value):
        self.set(col, value)
    def process_codes(self, product, materials, predefs):
        print(f"Processing coded values of product: '{product.code}', part: '{self.code}'.")
        if (self.use_predef != ""
            and self.use_predef != "n"
            and self.use_predef != "no"
            and self.use_predef != "e"
            and self.use_predef != "ei"
            and self.use_predef != "False"
            and self.use_predef != "false"):
            predef_found = False
            for predef in predefs:
                print(f"Check if predef == part: {predef.partcode} == {self.code}")
                if predef.partcode == self.code:
                    self.use_material = predef.materialcode
                    predef_found = True
                    break
            if not predef_found:
                self.use_material = self.material_code
                print(NO_PREDEF_FOUND.format(self.code))
                # print(f"    from predefs of len: {len(predefs)}")
        else:
            self.use_material = self.material_code

        material_found = False
        material_dict = {}

        for n in range(len(materials)):
            material_dict[materials[n].code] = materials[n].thickness
            if materials[n].code == self.use_material:
                material_found = True

        if not material_found:
            print(f"Material with code '{self.use_material}' not found")

        product_w = int(product.w)
        product_h = int(product.h)
        product_d = int(product.d)
        thickness = {}
        for part in product.parts:
            try:
                thickness[part.code] = int(material_dict[part.use_material])
            except KeyError:
                thickness[part.code] = 0
        try:
            self.x = eval(self.code_x)
        except ValueError as e:
            print(f"Could not evaluate code_x: '{self.code_x}' of part '{self.code}' - {e}")
            self.x = 0
        except KeyError as e:
            print(f"Could not find part or material with code: {e}")
            self.x = 0

        try:
            self.y = eval(self.code_y)
        except ValueError as e:
            print(f"Could not evaluate code_y: '{self.code_y}' of part '{self.code}' - {e}")
            self.y = 0
        except KeyError as e:
            print(f"Could not find part or material with code: {e}")
            self.y = 0

        try:
            self.z = eval(self.code_z)
        except ValueError as e:
            print(f"Could not evaluate code_z: '{self.code_z}' of part '{self.code}' - {e}")
            self.z = 0
        except KeyError as e:
            print(f"Could not find part or material with code: {e}")
            self.z = 0

    def get_codes(self):
        return {
            'Leveys': self.code_x,
            'Korkeus': self.code_y,
            'Syvyys': self.code_z
        }
    def set_codes(self, codes):
        self.code_x = codes['Leveys']
        self.code_y = codes['Korkeus']
        self.code_z = codes['Syvyys']


class GridData:
    def __init__(
        self,
        name="",
        data=[],
        defaults={},
        child=None,
        parent=None,
        col_keys=[],
        col_labels=[],
        col_types=[],
        col_readonly=[],
        tab_to=[],
        codes=[]
    ):
        self.name = name
        self.data = data
        self.defaults = defaults
        child=child
        parent=parent
        self.col_keys = col_keys
        self.col_labels = col_labels
        self.col_types = col_types
        self.col_readonly = col_readonly
        self.tab_to = tab_to
        self.codes = codes

    def get(self, row, col):
        if isinstance(col, int):
            try:
                return self.data[row][self.col_keys[col]]
            except (IndexError, KeyError) as e:
                print(f"{e}\n    row: {row}, col: {col}, len(self.data): {len(self.data)},"+
                      f" len(self.col_keys): {len(self.col_keys)}")
        elif isinstance(col, str):
            try:
                return self.data[row][col]
            except (KeyError, IndexError) as e:
                print(f"{e}\n    row: {row}, col: {col}, len(self.data): {len(self.data)},"+
                      f" len(self.col_keys): {len(self.col_keys)}")

    def set(self, row, col, value):
        if isinstance(col, int):
            try:
                self.data[row][self.col_keys[col]] = value
            except (IndexError, KeyError) as e:
                print(f"{e}\n    row: {row}, col: {col}, len(self.data): {len(self.data)},"+
                      f" len(self.col_keys): {len(self.col_keys)}")

        elif isinstance(col, str):
            try:
                self.data[row][col] = value
            except (IndexError, KeyError) as e:
                print(f"{e}\n    row: {row}, col: {col}, len(self.data): {len(self.data)},"+
                       " len(self.col_keys): {len(self.col_keys)}")
    
    def process_codes(self, osd):
        for rowdata in self.data:
            for target_key, code_key in self.codes.items():
                rowdata[target_key] = eval(rowdata[code_key])

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
        return None

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
        if value in false_keys:
            return False
        else:
            return True

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
    def predefs(cls) -> GridData:
        return cls(
            name="predefs",
            data=[],
            defaults={'part': "", 'mat': ""},
            child=None,
            parent=None,
            col_keys=['part', 'mat'],
            col_labels=['Osa', 'Materiaali'],
            col_types=['string', 'string'],
            col_readonly=[],
            tab_to=[1, 0],
            codes={}
        )
    @classmethod
    def materials(cls) -> GridData:
        return cls(
            name="materials",
            data=[],
            defaults={'code': "", 'desc': "", 'thck': 0, 'prod': "", 'cost': 0.0, 'unit': ""},
            child=None,
            parent=None,
            col_keys=['code', 'desc', 'thck', 'prod', 'cost', 'unit'],
            col_labels=['Osa', 'Kuvaus', 'Paksuus (mm)', 'Valmistaja', 'Hinta', 'Hintayksikkö'],
            col_types=['string', 'string', 'long', 'string', 'double', 'string'],
            col_readonly=[],
            tab_to=[1, 2, 3, 4, 5],
            codes={}
        )
    @classmethod
    def products(cls) -> GridData:
        return cls(
            name="products",
            data=[],
            defaults={'code': "", 'desc': "", 'prod': "", 'x': 0, 'y': 0, 'z': 0, 'cost': 0.0, 'code_cost': "self.parts.sum('cost')"},
            child="parts",
            parent=None,
            col_keys=['code', 'desc', 'prod', 'x', 'y', 'z', 'cost'],
            col_labels=['Osa', 'Kuvaus', 'Valmistaja', 'Leveys', 'Korkeus', 'Syvyys', 'Hinta (€)'],
            col_types=['string', 'string', 'string', 'long', 'long', 'long', 'double'],
            col_readonly=[],
            tab_to=[1, 2, 3, 4],
            codes={}
        )
    @classmethod
    def parts(cls) -> GridData:
        return cls(
            name="parts",
            data=[],
            defaults={
                'code': "",
                'desc': "",
                'use_predef': "",
                'mat': "",
                'use_mat': "",
                'x': 0,
                'y': 0,
                'z': 0,
                'cost': 0.0,
                'code_use_mat': "osd['predef'].find('part', rowdata['code'], 'mat') if self.is_true(rowdata['use_predef']) else rowdata['mat'])",
                'code_x': "0",
                'code_y': "0",
                'code_z': "0",
                'code_cost': "rowdata['x'] * rowdata['y'] * osd['materials'].find('mat', 'rowdata['use_mat']', 'cost')"
            },
            child="parts",
            parent="products",
            col_keys=['code', 'desc', 'use_predef', 'mat', 'use_mat', 'x', 'y', 'z', 'cost'],
            col_labels=['Osa', 'Kuvaus', 'Käytä Esimääritystä', 'Materiaali', 'Käytettävä Materiaali', 'Leveys', 'Korkeus', 'Syvyys', 'Hinta (€)'],
            col_types=['string', 'string', 'string', 'string', 'string', 'long', 'long', 'long', 'double'],
            col_readonly=[4, 5, 6, 7, 8],
            tab_to=[1, 2, 3, 4, 5, 6, 7],
            codes={'use_mat': "code_use_mat", 'x': "code_x", 'y': "code_y", 'z': "code_z", 'cost': "code_cost"}
        )


class Data:
    def __init__(self) -> None:
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
            return self.offers[link.n[0]].groups[link.n[1]].products[link.n[2]]
        elif link.target == Link.PARTS:
            return self.offers[link.n[0]].groups[link.n[1]].products[link.n[2]].parts
        elif link.target == Link.PREDEF:
            return self.offers[link.n[0]].groups[link.n[1]].predefs[link.n[2]]
        elif link.target == Link.MATERIAL:
            return self.offers[link.n[0]].groups[link.n[1]].materials[link.n[2]]
        elif link.target == Link.PRODUCT:
            return self.offers[link.n[0]].groups[link.n[1]].products[link.n[2]]
        elif link.target == Link.PART:
            return self.offers[link.n[0]].groups[link.n[1]].products[link.n[2]].parts[link.n[3]]
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

        self.offers[0].groups[0].predefs.append(Predef("ovi", "MELVA16"))
        self.offers[0].groups[0].predefs.append(Predef("hylly", "MELVA16"))

    def to_print(self):
        print("")
        for offer in self.offers:
            print(f"offer: {offer.name}")
            for group in offer.groups:
                print(f"    group: {group.name}")
                for predef in group.predefs:
                    print(f"        predef: {predef.get_data()}")
                for material in group.materials:
                    print(f"        material: {material.get_data()}")
                for product in group.products:
                    print(f"        product: {product.get_data()}")
                    for part in product.parts:
                        print(f"            part: {part.get_data()}")
        print("")

    def new_offer(self):
        self.offers.append(Offer(NEW_OFFER_NAME, groups=[Group(NEW_GROUP_NAME)]))

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

class Offer:
    def __init__(self, name="", groups=[]):
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


class Group:
    def __init__(self, name="") -> None:
        self.name = name
        self.predefs = []
        self.materials = []
        self.products = []

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "predefs": [pd.to_dict() for pd in self.predefs],
            "materials": [mat.to_dict() for mat in self.materials],
            "products": [pr.to_dict() for pr in self.products]
        }
    @classmethod
    def from_dict(cls, dic: dict):
        obj = cls()
        obj.name = dic["name"]
        obj.predefs = [Predef.from_dict(gr) for gr in dic["predefs"]]
        obj.materials = [Material.from_dict(gr) for gr in dic["materials"]]
        obj.products = [Product.from_dict(gr) for gr in dic["products"]]
        return obj


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

    def get_new_object(self):
        if self.target == Link.PREDEF:
            return Predef()
        elif self.target == Link.MATERIAL:
            return Material()
        elif self.target == Link.PRODUCT:
            return Product()
        elif self.target == Link.PART:
            return Part()
