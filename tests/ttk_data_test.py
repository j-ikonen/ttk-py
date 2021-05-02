import unittest

from ttk_data import Data, DataRoot, DataItem, DataChild


class Test_TtkData(unittest.TestCase):
    
    setup_data = {}
    setup_root = {
        "fieldcount_mult": {
            "type": "SetupGrid",
            "fields": [
                ["Kaappi", 'double', False, 0.0],
                ["Testiyksikkö", 'double', False, 0.0],
            ]
        }
    }
    setup_item = {
        "fieldcount": {
            "name": "Asennusuksiköt",
            "type": "DataGrid",
            "fields": [
                ["Asennusyksikkö", 'string', False, ""],
                ["Kerroin (€/kpl)", 'double', False, 0.0],
                ["Määrä (kpl)", 'double', False, 0.0],
                ["Hinta (€)", 'double', False, 0.0],
            ]
        },
        "client": {
            "name": "Asiakas",
            "type": "SetupGrid",
            "fields": [
                ["Etunimi", 'string', False, ""],
                ["Sukunimi", 'string', False, ""],
                ["Puh.", 'string', False, ""],
                ["Sähköposti", 'string', False, ""],
                ["Osoite", 'string', False, ""]
            ]
        }
    }
    setup_child = {
        "__name": "Ryhmä",
        "__refresh_n": 3,
        "predefs": {
            "name": "Esimääritykset",
            "type": "DataGrid",
            "fields": [
                ['Osa', 'string', False, ''],
                ['Materiaali', 'string', False, ''],
            ]
        },
        "parts": {
            "name": "Tuotetta ei ole valittu",
            "name_on_parent_selection": "Tuotteen {} osat",
            "parent_name_key": "Koodi",
            "type": "DataGrid",
            "fields": [
                ['Nimi', 'string', False, ''],
                ['Materiaali', 'string', False, ''],
            ]
        }
    }
    setup = {
        str(Data): setup_data,
        str(DataRoot): setup_root,
        str(DataItem): setup_item,
        str(DataChild): setup_child,
    }
    data = Data('Data', setup_data)
    data.push("root0", setup_root)          # [0]
    root1 = data.push("root1", setup_root)  # [1]
    root1.push("item0", setup_item)         # [0, 1]
    root1.push("item1", setup_item)         # [1, 1]

    root2 = data.push("root2", setup_root)  # [2]
    item0 = root2.push("item0", setup_item) # [0, 2]
    child0 = item0.push("child0", setup_child)  # [0, 0, 2]
    child1 = item0.push("child1", setup_child)  # [1, 0, 2]

    item1 = root2.push("item1", setup_item) # [1, 2]


    def test_get_self(self):
        self.assertEqual(self.data, self.data.get([]))

    def test_get_root(self):
        self.assertEqual(self.root1, self.data.get([1]))

    def test_get_item(self):
        self.assertEqual(self.item1, self.data.get([1, 2]))

    def test_get_child(self):
        self.assertEqual(self.child1, self.data.get([1, 0, 2]))

    def test_get_name(self):
        self.assertEqual("child1", self.data.get([1, 0, 2]).get_name())

    def test_get_tree(self):
        self.assertEqual(self.data.get_tree()[3], ([0, 1], 'item0'))

    def test_active(self):
        self.data.set_active([1, 0, 2])
        self.assertEqual(self.data.get_active(), self.child1)

    def test_delete(self):
        self.item0.push("child2", self.setup_child)  # [2, 0, 2]
        self.data.delete([2, 0, 2])
        self.assertEqual(len(self.data.get([0, 2])), 2)

    def test_dict(self):
        dic = self.data.get_dict()
        new_data = Data.from_dict(dic, self.setup)
        self.assertEqual(
            new_data.get([1, 0, 2]).get_name(),
            self.data.get([1, 0, 2]).get_name()
        )

if __name__ == '__main__':
    unittest.main()