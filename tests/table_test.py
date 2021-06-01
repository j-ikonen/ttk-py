import sqlite3
import unittest
import sqlite3
import tablebase as tb


class TestOffersTable(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.con = sqlite3.connect(":memory:")
        cls.con.execute("PRAGMA foreign_keys = OFF")
        cls.table = tb.OffersTable(cls.con)
        cls.table.create()

    @classmethod
    def tearDownClass(cls):
        cls.con.execute("DROP TABLE IF EXISTS columns")
        cls.con.execute("DROP TABLE IF EXISTS offers")
        cls.con.close()

    def test_create(self):
        sql = "SELECT name FROM sqlite_master WHERE type=(?) AND name=(?)"
        result = self.table.execute_dql(
            sql, ("table", "offers")
        )
        self.assertEqual(len(result), 1)

    def test_insert_empty(self):
        rowid = self.table.insert_empty(None)
        self.assertIsNotNone(rowid)

    def test_update(self):
        rowid = self.table.insert_empty(None)
        result = self.table.update(rowid, 2, "Nimi")
        self.assertTrue(result)

    def test_delete(self):
        self.assertTrue(self.table.delete(1))

    def test_execute_dql(self):
        rowid = self.table.insert_empty(None)
        result = self.table.update(rowid, 1, "Nimi")
        result = self.table.execute_dql(
            "SELECT name FROM offers WHERE offer_id=(?)", (rowid,)
        )
        self.assertEqual(result[0][0], "Nimi")

    def test_insert(self):
        values = (
            "name",      
            "firstname", 
            "lastname",  
            "company",   
            "phone",     
            "email",     
            "address",   
            "postcode",  
            "postarea",  
            "info"
        )
        result = self.table.insert(values)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, int)
        self.assertNotEqual(result, -1)

    def test_get_column_setup_value(self):
        result = self.table.get_column_setup("key", 2)
        self.assertEqual(result, "firstname")

    def test_get_column_setup_list(self):
        result = self.table.get_column_setup("key")
        self.assertEqual(len(result), len(self.table.keys_select))
        self.assertEqual(result[2], "firstname")

    def test_set_column_setup(self):
        success = self.table.set_column_setup("width", 2, 122)
        self.assertTrue(success)
        result = self.table.get_column_setup("width", 2)
        self.assertEqual(result, 122)


if __name__ == '__main__':
    unittest.main()