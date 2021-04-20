import ast


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

class Predef(GridData):
    def __init__(self, partcode="", materialcode="") -> None:
        super().__init__()
        self.partcode = partcode
        self.materialcode = materialcode
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

class Material(GridData):
    def __init__(self, code="", desc="") -> None:
        super().__init__()
        self.code = code
        self.desc = desc
        self.thickness = 10
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
        self.material_code = ""
        self.material_thickness = 0
        self.x = 0
        self.y = 0
        self.z = 0
        self.code_x = "product_w - (2 * thickness['sivu'])"
        self.code_y = "thickness['sivu']"
        self.code_z = "product_d - thickness['tausta']"

    def get(self, col):
        if col == 0: return self.code
        elif col == 1: return self.desc
        elif col == 2: return self.material_code
        elif col == 3: return self.material_thickness
        elif col == 4: return self.x
        elif col == 5: return self.y
        elif col == 6: return self.z
    def set(self, col, value):
        if col == 0: self.code = value
        elif col == 1: self.desc = value
        elif col == 2: self.material_code = value
        # elif col == 3: self.material_thickness = value
        # elif col == 4: self.x = value
        # elif col == 5: self.y = value
        # elif col == 6: self.z = value
    def new(self):
        return Part()
    def get_labels(self):
        return ['Koodi', 'Kuvaus', 'Materiaali', 'Mat. Paksuus', 'Leveys', 'Korkeus', 'Syvyys']
    def get_types(self):
        return ['string', 'string', 'string', 'long', 'long', 'long', 'long']
    def get_list(self):
        return [self.code, self.desc, self.material_code, self.x, self.y, self.z]
    def get_readonly(self): 
        return [3, 4, 5, 6]
    def get_tab(self):
        return [1, 2, 3, 4, 5, 0]
    def __getitem__(self, col):
        return self.get(col)
    def __setitem__(self, col, value):
        self.set(col, value)
    def process_codes(self, product, materials):
        print(f"Processing coded values of product: '{product.code}', part: '{self.code}'.")
        material_found = False
        for n in range(len(materials)):
            if materials[n].code == self.material_code:
                self.material_thickness = materials[n].thickness
                material_found = True
        if material_found:
            print(f"Found thickness {self.material_thickness} for material '{self.material_code}'")
        else:
            print(f"Material with code '{self.material_code}' not found")

        product_w = int(product.w)
        product_h = int(product.h)
        product_d = int(product.d)
        thickness = {}
        for part in product.parts:
            thickness[part.code] = int(part.material_thickness)

        try:
            self.x = eval(self.code_x)
        except ValueError as e:
            self.x = 0
        try:
            self.y = eval(self.code_y)
        except ValueError as e:
            self.y = 0
        try:
            self.z = eval(self.code_z)
        except ValueError as e:
            self.z = 0


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
        self.offers.append(Offer("Tarjous 1"))
        self.offers.append(Offer("Testi tarjous"))
        self.offers.append(Offer("Matinkatu 15"))

        self.offers[0].groups.append(Group("TestGroup"))
        self.offers[0].groups.append(Group("Group2"))
        self.offers[1].groups.append(Group("DefName"))
        self.offers[1].groups.append(Group("One"))
        self.offers[1].groups.append(Group("Two"))
        self.offers[1].groups.append(Group("Three"))
        self.offers[2].groups.append(Group("Kitchen"))

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


class Offer:
    def __init__(self, name="") -> None:
        self.name = name
        self.info = ""
        self.groups = []


class Info:
    def __init__(self) -> None:
        self.first_name = ""
        self.last_name = ""
        self.address = ""


class Group:
    def __init__(self, name="") -> None:
        self.name = name
        self.predefs = []
        self.materials = []
        self.products = []


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
