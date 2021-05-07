from copy import deepcopy
import json


TYPES = {
    'string': str,
    'long': int,
    'double': float,
    'choice': str,
    'object': dict,
    'array': list,
    'bool': bool,
    'DataGrid': list
}
FIELD_KEY = 0
FIELD_LABEL = 1
FIELD_TYPE = 2
FIELD_READONLY = 3
FIELD_DEF = 4


def read_file(path, file) -> dict:
    if path is None:
        filepath = file
    else:
        filepath = path + '\\' + file
    try:
        with open(filepath, 'r') as rf:
            return json.load(rf)
    except FileNotFoundError as e:
        print(f"{e}")
        return None
    except json.decoder.JSONDecodeError as e:
        print(f"{filepath}\n\tFile is not a valid json.")
        return None

def write_file(path, file, data):
    if path is None:
        filepath = file
    else:
        filepath = path + '\\' + file
    with open(filepath, 'w') as wf:
        json.dump(data, wf, indent=4)

def split_path(filepath: str):
    """Split the full filepath into path and file strings (path, file)."""
    file_start = filepath.rfind('\\') + 1
    file = filepath[file_start:]
    path = filepath[:file_start-1]
    return (path, file)

def type_default(typestring: str):
    return TYPES[typestring.split(':')[0]]()

def str2type(typestring: str, value: str):
    """Convert the given valuestring to given type by typestring."""
    split = typestring.split(':')
    if split[0] == "double":
        mod_value = value.replace(',', '.')
    else:
        mod_value = value
    return TYPES[split[0]](mod_value)

def type2str(value):
    """Convert the give value to a string for wx.grid.Grid."""
    strvalue = str(value)
    if isinstance(value, float):
        return strvalue.replace('.', ',')
    return strvalue

class Setup:
    default_file = "test_setup.json"
    root = None

    def __init__(self, link=None):
        if Setup.root is None:
            Setup.root = read_file(None, Setup.default_file)

        self.link = link
        self.local = self.get_from_root(link)

    def __get__(self, key):
        return self.local[key]

    def __set__(self, key, value):
        self.local[key] = value

    def get_default_object(self):
        """Return the local defined default object. Dictionary or a row in a list."""
        object = {}
        if "fields" in self.local:
            for key, value in self.local["fields"].items():
                if isinstance(value["default"], (dict, list)):
                    object[key] = deepcopy(value["default"])
                else:
                    object[key] = value["default"]

            if "child_data" in self.local:
                for child_key, value in self.local["child_data"]:
                    if value["ui_type"] == "ArrayOfObjectsGrid":
                        object[child_key] = []
                    elif value["ui_type"] == "SetupGrid":
                        object[child_key] = {}
        return object
    
    def get_page_init_data(self):
        data = {}
        for key, value in self.local["data"].items():
            if "link" in value:
                value = self.get_from_root(value["link"])
            if value["ui_type"] == "TextCtrl":
                # data[key] = str2type(value["type"], value["value"])
                data[key] = value
            elif value["ui_type"] == "SetupGrid":
                data[key] = self.get_default_object()
            elif value["ui_type"] == "ArrayOfObjectsGrid":
                data[key] = []
            elif value["ui_type"] == "3StateCheckBox":
                data[key] = value


    def get_parent(self):
        return Setup(self.link[:-1])

    def get_grandparent(self):
        return Setup(self.link[:-2])

    def get_page_setup(self):
        return Setup(self.link[:2])

    def get_child(self, key):
        link_copy = [n for n in self.link]
        link_copy.append(key)
        return Setup(link_copy)
    
    def get_link(self):
        return [n for n in self.link]
    
    def get_from_root(self, link):
        link_copy = [n for n in link]
        if link is not None:
            node = Setup.root[link_copy.pop(0)]
            while link_copy != []:
                node = node[link_copy.pop(0)]
        else:
            node = Setup.root
        return node