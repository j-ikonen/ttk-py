import unittest
import sqlite3

import tablebase as tb


class TestOffersTable(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """Setup a SQLite database in memory for testing."""
        class TestOffersTables(tb.SQLTableBase):
            """Class for testing tb.SQLTableBase functions."""
            def __init__(self, connection):
                super().__init__(connection)
                self.name = "offers"
                self.sql_create_table = """
                    CREATE TABLE IF NOT EXISTS offers (
                        offer_id    INTEGER PRIMARY KEY,
                        name        TEXT UNIQUE,
                        firstname   TEXT,
                        lastname    TEXT,
                        company     TEXT,
                        phone       TEXT,
                        email       TEXT,
                        address     TEXT,
                        postcode    TEXT,
                        postarea    TEXT,
                        info        TEXT
                    )
                """
                self.indexes = [
                    """CREATE INDEX IF NOT EXISTS idx_offers_name ON offers(name)"""
                ]
                self.primary_key = "offer_id"
                self.foreign_key = None
                self.read_only = ["offer_id"]
                self.default_columns = [
                    ("offers", "offer_id", "ID", "string"),
                    ("offers", "name", "Tarjouksen nimi", "string"),
                    ("offers", "firstname", "Etunimi", "string"),
                    ("offers", "lastname", "Sukunimi", "string"),
                    ("offers", "company", "Yritys.", "string"),
                    ("offers", "phone", "Puh", "string"),
                    ("offers", "email", "Sähköposti", "string"),
                    ("offers", "address", "Lähiosoite", "string"),
                    ("offers", "postcode", "Postinumero", "string"),
                    ("offers", "postarea", "Postitoimipaikka", "string"),
                    ("offers", "info", "Lisätiedot", "string")
                ]
                self.keys_insert = [
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
                ]
                self.keys_select = [
                    "offer_id",
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
                ]

        cls.con = sqlite3.connect(":memory:")
        cls.con.execute("PRAGMA foreign_keys = OFF")
        cls.table = TestOffersTables(cls.con)
        cls.table.create()

    @classmethod
    def tearDownClass(cls):
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

    def test_select_with_filter(self):
        rowid = self.table.insert_empty(None)
        self.table.update(rowid, 3, "SukuNimi")
        result = self.table.select(None, {3: ["like", "suku%"]})
        self.assertEqual(result[0][3], "SukuNimi")

    def test_select_with_fk(self):
        rowid = self.table.insert_empty(None)
        self.table.update(rowid, 3, "SukuNimi")

        self.table.foreign_key = "lastname"
        result = self.table.select("SukuNimi", None)
        self.table.foreign_key = None

        self.assertEqual(result[0][3], "SukuNimi")

    def test_select_with_fk_and_filter(self):
        rowid = self.table.insert_empty(None)
        self.table.update(rowid, 2, "EtuNimi")
        self.table.update(rowid, 3, "SukuNimi")

        self.table.foreign_key = "lastname"
        result = self.table.select("SukuNimi", {2: ["like", "etu%"]})
        self.table.foreign_key = None

        self.assertEqual(result[0][2], "EtuNimi")


if __name__ == '__main__':
    unittest.main()