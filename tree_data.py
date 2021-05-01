"""Data classes for TreeCtrl display and selections."""


IDX_TYPE = 0
FK_FCG_MULT = 'fcg_mult'    # FieldKey FieldCountGlobal
FK_OFFER_INFO = 'offer_info'
FK_PREDEFS = 'predefs'
FK_MATERIALS = 'materials'
FK_PRODUCTS = 'products'
FK_PARTS = 'parts'

class SetupData:
    def __init__(self, name, setup):
        self.name = name
        self.data = {}
        self.setup = setup

    def values(self) -> list:
        return list(self.data.values())
    
    def set(self, key, value):
        try:
            self.data[key] = value
        except KeyError:
            for n, k in enumerate(self.data.keys()):
                if n == key:
                    self.data[k] = value
                    break

class GridData:
    def __init__(self, name, setup):
        self.name = name
        self.data = []
        self.setup = setup


GD_CHILD_SETUP = {
    'parts': {
        'fields': {
            'code': ['', 'string', 'Koodi', False]
        },
        'columns': [
            'code',
            'count'
        ],
        'db': True,
        'tab_to': [1],
        'codes': {},
        'children': []
    }
}

GD_SETUP = {
    'predefs': {},
    'materials': {},
    'products': {
        'fields': {
            'code': ['', 'string', 'Koodi', False],
            'count': [0, 'long', 'Määrä', False],
            'parts': [None, 'griddata', 'Osat', False]
        },
        'columns': [
            'code',
            'count'
        ],
        'db': True,
        'tab_to': [1],
        'codes': {},
        'children': ['parts']
    },
    FK_FCG_MULT: {},
    FK_OFFER_INFO: {
        'fields': {
            'file': ['', 'string', 'Tiedosto'],
            'client.firstname': ['', 'string', 'Etunimi'],
            'client.lastname': ['', 'string', 'Sukunimi'],
            'client.email': ['', 'string', 'Sähköposti'],
            'client.phone': ['', 'string', 'Puh.'],
            'client.address': ['', 'string', 'Osoite'],
            'client.add_info': ['', 'string', 'Lisätiedot']
        }
    },
}


class TreeData:
    """Data class that is a selectable item in TreeCtrl.

    Opens a SimpleBook page on selection. Has multiple instances in the tree.
    May have child items of TreeData or other container types.

    Instance Attributes:
        - name (str): Name of the instance.
        - selected (int): Index of the selected child.
        - children (list): List of child objects.
        - data (dict): Data for this instance. Defined by Class variables.
    """
    name = "ClassDefaultName"

    def __init__(self, data):
        self.name = "InstanceDefaultName"
        self.selected = None
        self.children = []
        try:
            self.data = {k: v[IDX_TYPE](k, GD_SETUP[k]) for k, v in self.fields.items()}

            if data:
                for key in self.data.keys():
                    self.data[key] = data[key]
        except AttributeError:
            self.data = {}

    def append_child(self, data=None):
        try:
            child = self.child_type(data)
        except AttributeError as e:
            print(f"AttributeError - {e} - TreeData with name '{self.name}'")
            return None

        idx = len(self.children)
        self.children.append(child)
        return idx

    def get(self, link: list):
        """Get the TreeRoot or it's child TreeData item matching the link."""
        if len(link) == 0:
            return self
        index = link.pop()
        return self.children[index].get(link)

    def get_data(self, key):
        try:
            return self.data[key]
        except AttributeError as e:
            print(f"\nError in TreeData with name '{self.name}'\n\t-" +
                   " Necessary Class Attribute for " +
                   "inherited method get_data() has not been initiated.")
            raise e

    def get_name(self):
        return self.name

    def get_selected(self):
        return self.selected

    def set(self, key, subkey, value):
        self.data[key][subkey] = value

    def set_name(self, value):
        self.name = value

    def set_selected(self, link):
        self.selected = self.get(link)




class TreeChild(TreeData):
    fields = {
        FK_PREDEFS: [GridData],
        FK_MATERIALS: [GridData],
        FK_PRODUCTS: [GridData]
        # FK_PARTS: [GridData]
    }

    def __init__(self, data=None):
        super().__init__(data)


class TreeItem(TreeData):
    fields = {
        FK_OFFER_INFO: [SetupData]
    }
    child_type = TreeChild

    def __init__(self, data=None):
        super().__init__(data)


class TreeRoot(TreeData):
    fields = {
        FK_FCG_MULT: [SetupData]
    }
    child_type = TreeItem

    def __init__(self, data=None):
        super().__init__(data)

    def get_treelist(self):
        """Return a list for displaying the tree.

        List is made of tuples (name, link).
        Link is list of indexes to get the TreeData object.
        """
        treelist = []
        treelist.append((self.get_name(), []))
        for ni, item in enumerate(self.children):
            treelist.append((item.get_name(), [ni]))

            for nc, child in enumerate(item.children):
                treelist.append((child.get_name(), [nc, ni]))
        return treelist


if __name__ == '__main__':

    treedata = TreeRoot()
    print(f"{treedata.get_data(FK_FCG_MULT)}")
