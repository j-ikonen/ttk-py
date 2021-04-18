
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
    def get(self, col):
        if col == 0: return self.code
        elif col == 1: return self.desc
    def set(self, col, value):
        if col == 0: self.code = value
        elif col == 1: self.desc = value
    def new(self):
        return Material()
    def get_labels(self):
        return ['Koodi', 'Kuvaus']
    def get_types(self):
        return ['string', 'string']
    def get_list(self):
        return [self.code, self.desc]
    def get_readonly(self): 
        return []
    def get_tab(self):
        return [1, 0]
    def __getitem__(self, col):
        return self.get(col)
    def __setitem__(self, col, value):
        self.set(col, value)

class Product(GridData):
    def __init__(self, code="", desc="") -> None:
        super().__init__()
        self.code = code
        self.desc = desc
    def get(self, col):
        if col == 0: return self.code
        elif col == 1: return self.desc
    def set(self, col, value):
        if col == 0: self.code = value
        elif col == 1: self.desc = value
    def new(self):
        return Product()
    def get_labels(self):
        return ['Koodi', 'Kuvaus']
    def get_types(self):
        return ['string', 'string']
    def get_list(self):
        return [self.code, self.desc]
    def get_readonly(self): 
        return []
    def get_tab(self):
        return [1, 0]
    def __getitem__(self, col):
        return self.get(col)
    def __setitem__(self, col, value):
        self.set(col, value)

class Part(GridData):
    def __init__(self, code="", desc="") -> None:
        super().__init__()
        self.code = code
        self.desc = desc
    def get(self, col):
        if col == 0: return self.code
        elif col == 1: return self.desc
    def set(self, col, value):
        if col == 0: self.code = value
        elif col == 1: self.desc = value
    def new(self):
        return Part()
    def get_labels(self):
        return ['Koodi', 'Kuvaus']
    def get_types(self):
        return ['string', 'string']
    def get_list(self):
        return [self.code, self.desc]
    def get_readonly(self): 
        return []
    def get_tab(self):
        return [1, 0]
    def __getitem__(self, col):
        return self.get(col)
    def __setitem__(self, col, value):
        self.set(col, value)