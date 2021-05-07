from copy import deepcopy


from database import Database
from setup import Setup


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
        self.setup: Setup = setup.get_child(self.key)

        self.child = child
        self.children = None if child is None else []
        self.data = self.setup.get_page_init_data()

        # self.init_data()

    def __len__(self):
        return len(self.children)

    def push_from_dict(self, data, setup):
        """Push a new child created from dictionary data."""
        self.children.append(self.child.from_dict(data, setup))

    def delete_child(self, idx: int):
        """Delete a child at idx."""
        del self.children[idx]

    def delete_all_children(self):
        """Delete all the children."""
        self.children = None if self.child is None else []

    @classmethod
    def from_dict(cls, data: dict, setup):
        """Return a Data object created from dictionary data."""
        obj = cls(data['name'], setup)
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
        link_copy = [n for n in link]
        if len(link_copy) == 0:
            return self
        elif self.children:
            return self.children[link_copy.pop()].get(link_copy)

        elif self.children is None:
            print(f"{type(self)}.get(link) - Link {str(link_copy)} is not valid. " +
                f"'{self.name} does not define children.'")
            return None
        
        print(f"{type(self)}.get(link) - Link {str(link_copy)} is not valid. " +
            f"'{self.name} has no children.'")
        return None

    def get_setup(self):
        return self.setup

    def get_child(self, idx):
        return self.children(idx)

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

    # def init_data(self):
    #     """Initialize the data."""
    #     for k, v in self.setup.items():
    #         if isinstance(v, dict):
    #             if v['type'] == "SetupGrid":
    #                 fs = v['fields'].items()
    #                 self.data[k] = {k: type_default(f[FIELD_TYPE]) for k, f in fs}

    #             else:
    #                 self.data[k] = type_default(v['type'])

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
        child = self.children[-1]
        return child

    def set_data(self, key, value):
        self.data[key] = value

    def set_name(self, name):
        self.name = name

    def sum(self, objkey, fieldkey):
        """Return the sum of all values at fieldkey in list of objects at objkey.
        
        Args:
        - objkey (str|list): Key to objectlist or the objectlist itself.
        - fieldkey (str): Key to the field in object.
        """
        if isinstance(objkey, str):
            objlist = self.get_data[objkey]
        else:
            objlist = objkey
        total = 0
        if objlist is not None:
            for item in objlist:
                total += item[fieldkey]
        return total


class Data(TtkData):
    key = "app"
    def __init__(self, name, setup):
        super().__init__(name, 0, setup, DataRoot)
        self.active = self

    def delete(self, link: list):
        """Delete the object at link where link[0] is deleted object."""
        parent = self.get(link[1:])
        del parent.children[link[0]]

    def get_active(self):
        """Return the active Data object."""
        return self.active
    
    def set_active(self, link):
        """Set the object at link as active."""
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
    key = "root"
    def __init__(self, name, setup):
        super().__init__(name, 1, setup, DataItem)

    def file_open(self, folder, file):
        """Return True if the child is already opened."""
        for child in self.children:
            if (folder == child.get_data('file')['path'] and
                file == child.get_data('file')['file']):
                return True
        return False


class DataItem(TtkData):
    key = "item"
    def __init__(self, name, setup):
        super().__init__(name, 2, setup, DataChild)


class DataChild(TtkData):
    key = "child"
    def __init__(self, name, setup):
        super().__init__(name, 3, setup, None)

    def process_codes(self):
        """Process the coded fields in data."""
        # print("DataChild.process_codes")
        sum = self.sum
        flt = self.get_edited_filter
        grd = self.data
        find = self.find
        is_true = self.is_true
        # Iterate over grids.
        for data_key, value in self.data.items():
            if data_key in self.setup["codes"]:
                codes = self.setup["codes"][data_key]
                db = Database(data_key)
                # for field_key, value in self.setup["data"][data_key]["fields"].items():
                for obj in value:
                    for field_key, code in codes.items():
                        if code[0] == "$":
                            code = obj[code[1:]]
                        try:
                            obj[field_key] = eval(code)
                        except:
                            print(f"Error in eval: \n\tfield_key: {field_key}\t\ncode: {code}")

                        if "child_data" in self.setup["data"][data_key]:
                            child_setup = self.setup["data"][data_key]['child_data']
                            parent = obj
                            for child_key, child_value in child_setup.items():
                                child_codes = self.setup["codes"][child_key]
                                for cf_key, c_code in child_codes.items():
                                    for obj in parent[child_key]:
                                        if code[0] == "$":
                                            code = obj[code[1:]]
                                        try:
                                            obj[cf_key] = eval(c_code)
                                        except:
                                            print(f"Error in eval: \n\tfield_key: {cf_key}\t\ncode: {code}")
                            obj = parent

    def find(self, datakey, returnkey, matchkey, matchvalue):
        """Find a value in another grid.

        Args:
            datakey (str):    Key of the grid where value is found.
            returnkey (str):  Key for the value to be returned.
            matchkey (str):   Key of field to use for matching correct object in list.
            matchvalue (Any): Value that needs to be at target_key field for a match.
        """
        for item in self.get_data(datakey):
            if item[matchkey] == matchvalue:
                return item[returnkey]

    def is_true(self, strvalue: str):
        """Return False if value is ""|"n"|"e"|"False"|"false" else True."""
        false_strings = [
            "", "n", "e", "false", "False"
        ]
        return False if strvalue in false_strings else True

    def get_edited_filter(self, obj, key):
        """Return the filter for database to check if obj exists in it.
        
        Using this in codes that are in object that does not have a database collection will
        result in undefined behaviour.
        """
        flt = {}
        if "database" not in self.setup or key not in self.setup["database"]:
            return None

        db_setup = self.setup["database"][key]
        eq_keys = db_setup['eq_keys']

        for key in eq_keys:
            flt[key] = obj[key]
        
        if "children" in db_setup:
            for child_key, value in db_setup["children"].items():
                child_eq_keys = value["child_eq_keys"]
                for n, cobj in enumerate(obj[child_key]):
                    for key in child_eq_keys:
                        key = child_key + "." + str(n) + key
                        flt[key] = cobj[key]
        return flt
