from copy import deepcopy
import json
from os import write


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

        with open(filepath, 'r', encoding='utf-8') as fh:
            return json.load(fh)

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

    with open(filepath, 'w', encoding='utf-8') as fh:
        json.dump(data, fh, indent=4)

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
    savefile = "savedsetup.json"
    root = None

    def __init__(self, link):
        if Setup.root is None:
            Setup.root = read_file(None, Setup.default_file)

        self.link = link
        self.local = self.get_from_root(link)

    def __getitem__(self, key):
        return self.local[key]

    def __setitem__(self, key, value):
        self.local[key] = value

    def close(self):
        write_file(None, Setup.savefile, Setup.root)

    def get_default_object(self, objkey) -> dict:
        """Return the local defined default object. Dictionary or a row in a list.
        
        Args:
        - key (str): Key of the object.
        """
        object = {}
        try:
            obj_setup = self.local["data"][objkey]
        except KeyError:
            obj_setup = self.local

        if "fields" in obj_setup:
            # print("Setup.get_default_object")
            for key, value in obj_setup["fields"].items():
                # print(f"\t{key}: {value}")
                if isinstance(value["default"], (dict, list)):
                    object[key] = deepcopy(value["default"])
                else:
                    object[key] = value["default"]

            if "child_data" in obj_setup:
                for child_key, value in obj_setup["child_data"].items():
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
                data[key] = value["value"]

            elif value["ui_type"] == "SetupGrid":
                data[key] = self.get_default_object(key)

            elif value["ui_type"] == "ArrayOfObjectsGrid":
                data[key] = []

            elif value["ui_type"] == "3StateCheckBox":
                data[key] = value["value"]

            else:
                print(f"Setup.get_page_init_data - ui_type '{value['ui_type']}'" +
                       " not defined.")
        return data

    def get_parent(self):
        return Setup(self.link[:-1])

    def get_grandchild(self, key, ckey):
        link_copy = [n for n in self.link]
        link_copy.append(key)
        link_copy.append(ckey)
        return Setup(link_copy)

    def get_grandparent(self):
        return Setup(self.link[:-2])

    def get_pages_setup(self):
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
    
    def get(self, key, objkey):
        obj = self.local[key][objkey]
        if "link" in obj:
            obj = self.get_from_root(obj["link"])
        return obj