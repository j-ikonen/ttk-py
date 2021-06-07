from decimal import Decimal
import unittest
import sqlite3

import tablebase as tb


class TestOffersTable(unittest.TestCase):
    """Test that SQLTableBase functions work as intended on a simplest SQL table."""
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
                self.table_keys = [
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

        cls.con = tb.connect(":memory:")
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

    def test_insert_or_replace(self):
        values = [
            1,
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
        rowid = self.table.insert(values, include_rowid=True, upsert=True)
        self.assertEqual(rowid, 1)
        values[1] = "Tarjouksen nimi"
        rowid = self.table.insert(values, include_rowid=True, upsert=True)
        result = self.table.execute_dql(
            "SELECT name FROM offers WHERE offer_id=(?)", (rowid,)
        )
        self.assertEqual(result[0][0], "Tarjouksen nimi")

    def test_get_column_setup_value(self):
        result = self.table.get_column_setup("key", 2)
        self.assertEqual(result, "firstname")

    def test_get_column_setup_list(self):
        result = self.table.get_column_setup("key")
        self.assertEqual(len(result), len(self.table.table_keys))
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


class TestRegisteredFunctions(unittest.TestCase):
    """Test if functions, types and aggregates registered to sqlite3 work as intented."""
    def setUp(self) -> None:
        """Setup a SQLite database in memory for testing."""
        class TestDecimal(tb.SQLTableBase):
            """Class for testing tb.SQLTableBase functions."""
            def __init__(self, connection):
                super().__init__(connection)
                self.name = "decimals"
                self.sql_create_table = """
                    CREATE TABLE IF NOT EXISTS decimals (
                        rowid       INTEGER PRIMARY KEY,
                        col_a pydecimal,
                        col_b pydecimal,
                        col_c pydecimal,
                        col_sum pydecimal
                            GENERATED ALWAYS AS (
                                dec_add(col_a, col_b, col_c)
                            )
                    )
                """
                self.indexes = [
                ]
                self.primary_key = "rowid"
                self.foreign_key = None
                self.read_only = ["rowid"]
                self.default_columns = [
                    ("decimals", "rowid", "ID", "string"),
                    ("decimals", "col_a", "A", "string"),
                    ("decimals", "col_b", "B", "string"),
                    ("decimals", "col_c", "C", "string")
                ]
                self.table_keys = [
                    "rowid",
                    "col_a",
                    "col_b",
                    "col_c"
                ]

        self.con = tb.connect(":memory:")
        self.con.execute("PRAGMA foreign_keys = OFF")
        self.table = TestDecimal(self.con)
        self.table.create()

    def tearDown(self) -> None:
        self.con.close()

    def test_decimal(self):
        self.table.execute_dml(
            "INSERT INTO decimals(col_a, col_b, col_c) VALUES(?,?,?)",
            [Decimal('1.01'), Decimal('12.78'), Decimal('14.51')]
        )
        values = self.table.execute_dql("SELECT col_a as 'col_a [pydecimal]' FROM decimals")
        self.assertEqual(values[0][0], Decimal('1.01'))

    def test_decimal_add(self):
        a = '0.10'.encode('ascii')
        sum = tb.decimal_add(a, a, a)
        self.assertEqual(sum, '0.30'.encode('ascii'))

    def test_decimal_add_query(self):
        self.table.execute_dml(
            "INSERT INTO decimals(col_a, col_b, col_c) VALUES(?,?,?)",
            [Decimal('1.01'), Decimal('12.78'), Decimal('14.51')]
        )
        values = self.table.execute_dql("SELECT col_sum as 'col_sum [pydecimal]' FROM decimals")
        self.assertEqual(values[0][0], Decimal('1.01') + Decimal('12.78') + Decimal('14.51'))

    def test_decimal_sum(self):
        success = self.table.execute_dml(
            "INSERT INTO decimals(col_a, col_b, col_c) VALUES(?,?,?)",
            [
                [Decimal('0.1'), Decimal('12.78'), Decimal('14.51')],
                [Decimal('0.1'), Decimal('12.78'), Decimal('14.51')],
                [Decimal('0.1'), Decimal('12.78'), Decimal('14.51')]
            ],
            True
        )
        self.assertTrue(success)
        values = self.table.execute_dql("SELECT dec_sum(col_a) 's [pydecimal]' FROM decimals")
        self.assertEqual(values[0][0], Decimal('0.3'))

    def test_material_cost(self):
        success = self.table.execute_dml(
            "INSERT INTO decimals(col_a, col_b, col_c) VALUES(?,?,?)",
            [Decimal('5.1'), Decimal('12.78'), Decimal('0.15')]
        )
        self.assertTrue(success)
        values = self.table.execute_dql(
            """
            SELECT material_cost(col_b, col_a, col_a, col_c, col_c) AS 'tot_cost [pydecimal]'
            FROM decimals
            """)
        tot_cost = (Decimal('12.78') * (Decimal('1.00') + Decimal('0.15')) + 
                    Decimal('5.1') + Decimal('5.1')) * (Decimal('1.00') - Decimal('0.15'))
        self.assertEqual(values[0][0], tot_cost)


class TestMaterialsTable(unittest.TestCase):
    """Test if member functions work with a generated column in table."""
    def setUp(self) -> None:
        """Setup a SQLite database in memory for testing."""
        self.con = tb.connect(":memory:")
        self.con.execute("PRAGMA foreign_keys = OFF")
        self.table = tb.GroupMaterialsTable(self.con)
        self.table.create()

    def tearDown(self) -> None:
        self.con.close()

    def test_materials_create(self):
        self.assertIsInstance(self.con, sqlite3.Connection)

    def test_insert_empty_on_generated_column(self):
        # values = [None * len(self.table.table_keys)]
        rowid = self.table.insert_empty(12)
        result = self.table.select(filter={0: ["=", rowid]})
        self.assertEqual(result[0][1], 12)

    def test_insert_on_generated_column(self):
        values = [None] * len(self.table.get_insert_keys())
        values[0] = 12
        rowid = self.table.insert(values)
        result = self.table.select(filter={0: ["=", rowid]})
        self.assertEqual(result[0][1], 12)

    def test_update_fail_on_generated_column(self):
        rowid = self.table.insert_empty(12)
        result = self.table.update(rowid, len(self.table.table_keys) - 1, Decimal('0.1'))
        self.assertFalse(result)

    def test_select_generated_column(self):
        rowid = self.table.insert_empty(12)
        self.table.update(rowid, len(self.table.table_keys) - 6, Decimal('0.1'))
        self.table.update(rowid, len(self.table.table_keys) - 5, Decimal('0.1'))
        self.table.update(rowid, len(self.table.table_keys) - 4, Decimal('0.1'))
        result = self.table.select(filter={0: ["=", rowid]})
        tot_cost_col = len(self.table.table_keys) - 1
        self.assertEqual(result[0][tot_cost_col], Decimal('0.3'))


class TestPartsTable(unittest.TestCase):
    """Test if overridden functions work for group_parts table."""
    def setUp(self) -> None:
        """Setup a SQLite database in memory for testing."""
        self.con = tb.connect(":memory:")
        self.con.execute("PRAGMA foreign_keys = OFF")
        self.table = tb.GroupPartsTable(self.con)
        self.products_table = tb.GroupProductsTable(self.con)
        self.predefs_table = tb.GroupPredefsTable(self.con)
        self.materials_table = tb.GroupMaterialsTable(self.con)
        self.predefs_table.create()
        self.materials_table.create()
        self.products_table.create()
        self.table.create()

    def tearDown(self) -> None:
        self.con.close()

    def test_materials_create(self):
        self.assertIsInstance(self.con, sqlite3.Connection)

    def test_insert_and_select(self):
        # Parts select uses INNER JOIN with products.
        # SELECT of parts requires an existing product.
        pr_rowid = self.products_table.insert_empty(12)
        rowid = self.table.insert_empty(pr_rowid)
        result = self.table.select()
        self.assertEqual(result[0][0], rowid)

    def test_update(self):
        pr_rowid = self.products_table.insert_empty(12)
        rowid = self.table.insert_empty(pr_rowid)
        self.table.update(rowid, 13, "=määrä * 11.12")
        result = self.table.select()
        self.assertEqual(result[0][13], "=määrä * 11.12")

    def test_code_parse(self):
        pr_rowid = self.products_table.insert_empty(12)
        rowid = self.table.insert_empty(pr_rowid)
        self.table.update(rowid, 13, "=määrä * 11.12")
        self.table.update(rowid, 3, 4)
        result = self.table.select()
        self.assertEqual(result[0][10], Decimal('4') * Decimal('11.12'))


if __name__ == '__main__':
    unittest.main()