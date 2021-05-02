from copy import deepcopy

TYPES = {
    'string': str,
    'long': int,
    'double': float,
    'choice': str,
    'object': dict,
    'array': list,
    'DataGrid': list
}
FIELD_KEY = 0
FIELD_TYPE = 1
FIELD_READONLY = 2
FIELD_DEF = 3


class TtkData:
    def __init__(self, name, page, setup, child):
        """### Initiate the TtkData super class.

        ### Args:
        - name (str): Name of instance.
        - page (int): Page index. Length of link index lists.
        - setup (dict): Setup dictionary for self.data formatting etc.
        - children (bool): Does this instance have children. Default False.
        """
        self.name = name
        self.page = page
        self.setup = setup
        self.child = child
        self.children = None if child is None else []
        self.data = {}

    def __len__(self):
        return len(self.children)

    def delete(self, link: list):
        """Delete the object at link where link[0] is deleted object."""
        parent = self.get(link[1:])
        del parent.children[link[0]]

    @classmethod
    def from_dict(cls, data: dict, setup: dict):
        obj = cls(data['name'], setup[str(type(cls))])
        obj.data = deepcopy(data['data'])
        if obj.child is not None:
            for child in data['ttkdata_children']:
                new_child = obj.child.from_dict(child, setup)
                obj.children.append(new_child)
        return obj

    def get(self, link: list):
        """Return an object that inherits TtkData class at link.
        
        Return None if no children exist or are defined.
        
        Args:
        - link (list): Link index list to object. [child, item, root]"""
        if len(link) == 0:
            return self
        elif self.children:
            return self.children[link.pop()].get(link)

        elif self.children is None:
            print(f"{type(self)}.get(link) - Link {str(link)} is not valid. " +
                f"'{self.name} does not define children.'")
            return None
        
        print(f"{type(self)}.get(link) - Link {str(link)} is not valid. " +
            f"'{self.name} has no children.'")
        return None

    def get_setup(self, key):
        return self.setup[key]

    def get_children(self) -> list:
        return self.children

    def get_data(self, key):
        return self.data[key]

    def get_dict(self) -> dict:
        obj = {}
        obj['name'] = self.name
        obj['data'] = deepcopy(self.data)

        if self.child is not None:
            obj['ttkdata_children'] = []
            for child in self.get_children():
                obj['ttkdata_children'].append(child.get_dict())

        return obj

    def get_name(self) -> str:
        return self.name
    
    def get_page(self) -> int:
        return self.page

    def init_data(self):
        for k, v in self.setup:
            if v['type'] == 'SetupGrid':
                self.data[k] = {
                    field[FIELD_KEY]: field[FIELD_DEF]
                        for field in v['fields']
                }
            else:
                self.data[k] = TYPES[v['type']]()

    def push(self, name, setup):
        """Add a new child to end of list. Return the new child.
        
        Args:
        - name (str): Name of new child.
        - setup (dict): Setup dictionary for the new child.
        """
        if self.child is None:
            raise AttributeError(f"{type(self)} with name '{self.name}' does " +
                                  "not have children.")
        self.children.append(self.child(name, setup))
        return self.children[-1]

    def set_name(self, name):
        self.name = name


class Data(TtkData):
    def __init__(self, name, setup):
        super().__init__(name, 0, setup, DataRoot)
        self.active = self


    def get_active(self):
        return self.active
    
    def set_active(self, link):
        self.active = self.get(link)

    def get_tree(self):
        """Return a list of tuples for TreeCtrl window.
        
        ListItem: ([child, item, root], self.name)
        """
        tree = [([], self.get_name())]
        for n_r, root in enumerate(self.get_children()):
            tree.append(([n_r], root.get_name()))
            for n_i, item in enumerate(root.get_children()):
                tree.append(([n_i, n_r], item.get_name()))
                for n_c, child in enumerate(item.get_children()):
                    tree.append(([n_c, n_i, n_r], child.get_name()))
        return tree

class DataRoot(TtkData):
    def __init__(self, name, setup):
        super().__init__(name, 1, setup, DataItem)

class DataItem(TtkData):
    def __init__(self, name, setup):
        super().__init__(name, 2, setup, DataChild)

class DataChild(TtkData):
    def __init__(self, name, setup):
        super().__init__(name, 3, setup, None)

    def process_codes(self):
        """Process the coded fields in data."""
        print("DataChild.process_codes")