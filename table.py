"""Database operations.

TODO
----
Do unittests for any functions that do not have them
Add delete unittest
"""

import json
import sqlite3
from typing import Iterable
from operator import itemgetter

from bson.objectid import ObjectId


TYPES = {
    'string': str,
    'long': int,
    'double': float,
    'choice': str,
    'object': dict,
    'array': list,
    'bool': bool,
    'oid': ObjectId
}

def read_json(file):
    try:
        with open(file, 'r', encoding='utf-8') as fh:
            return json.load(fh)
    except FileNotFoundError as e:
        print(f"{e}")
        return None
    except json.decoder.JSONDecodeError as e:
        print(f"{file}\n\tFile is not a valid json.")
        return None

def type2default(typestring: str):
    """Return the default value for the typestring."""
    return TYPES[typestring.split(':')[0]]()

def str2type(typestring: str, value: str):
    """Return the value as type given by typestring."""
    split = typestring.split(':')
    if split[0] == "double":
        mod_value = value.replace(',', '.')
    else:
        mod_value = value
    try:
        return TYPES[split[0]](mod_value)
    except ValueError:
        return None

def type2str(value):
    """Return the value as string."""
    # if value is None:
    #     return None
    strvalue = str(value)
    if isinstance(value, float):
        return strvalue.replace('.', ',')
    return strvalue

code2col = {
    "määrä": 4,
    "leveys": 8,
    "pituus": 9,
    "mpaksuus": 15,
    "mhinta": 16,
    "tleveys": 17,
    "tkorkeus": 18,
    "tsyvyys": 19
}
from asteval import Interpreter
aeval = Interpreter()

def find_row(col, code, data):
    for n, datarow in enumerate(data):
        if datarow[col] == code:
            return n
    return None

def parse_code(code, row, data):
    if code is not None and len(code) > 0 and code[0] == "=":
        parsed_code: str = code[1:] # "=code" -> "code"
        split_code = list(dict.fromkeys(parsed_code.split(" ")))
        for var in split_code:
            # Default values
            src_row = row
            key = var
            # If variable is link to another row in data. "code".key
            # get value from data arg.
            if var[0] == '"':
                try:
                    (source, key) = var.split(".") # ["code", key]
                # Use default values on error.
                except ValueError:
                    print('SyntaxError when parsing "{}"\n'.format(code) +
                          'to refer to another part: "part".key')
                # Find the row containing key given in code.
                else:
                    res = find_row(2, source.strip('"'), data)
                    if res is not None:
                        src_row = res

            # Get the column and value to replace the var substring with.
            if key in code2col:
                col = code2col[key]
                try:
                    value = data[src_row][col]
                except IndexError as e:
                    print("IndexError: {}\n\ttable.parse_code row, col: ".format(e) +
                          "{}, {} not in data arg.".format(src_row, col))
                    return None

                if value is None:
                    return None

                var_value = str(value)
                parsed_code = parsed_code.replace(var, var_value)

        try:
            return aeval(parsed_code)
        except NameError as e:
            print(f"NameError: {e}")
            return None

    # Invalid code
    else:
        return None

sql_create_table_variables = """
    CREATE TABLE IF NOT EXISTS variables (
        key     TEXT PRIMARY KEY,
        val     REAL
    )
"""
sql_create_table_columns = """
    CREATE TABLE IF NOT EXISTS columns (
        tablename   TEXT,
        key         TEXT,
        label       TEXT,
        type        TEXT,
        col_idx     INTEGER,
        width       INTEGER,
        is_unique   INTEGER,
        ro          INTEGER,
        visible     INTEGER DEFAULT 1,
        PRIMARY KEY (tablename, key)
    )
"""
columns_keys = [
    "tablename",
    "key",
    "label",
    "type",
    "col_idx",
    "width",
    "is_unique",
    "ro"
]
TABLE = 0
KEY = 1
LABEL = 2
TYPE = 3
INDEX = 4
WIDTH = 5
UNIQUE = 6
READ_ONLY = 7

sql_create_table_offers = """
    CREATE TABLE IF NOT EXISTS offers (
        id          TEXT PRIMARY KEY,
        name        TEXT DEFAULT 'Uusi Tarjous',
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
sql_create_table_offer_groups = """
    CREATE TABLE IF NOT EXISTS offer_groups (
        id          TEXT PRIMARY KEY,
        offer_id    TEXT NOT NULL,
        name        TEXT DEFAULT 'Uusi Ryhmä',

        FOREIGN KEY (offer_id)
            REFERENCES offers (id)
            ON DELETE CASCADE
            ON UPDATE CASCADE
    )
"""
sql_create_table_offer_predefs = """
    CREATE TABLE IF NOT EXISTS offer_predefs (
        id          TEXT PRIMARY KEY,
        group_id    TEXT NOT NULL,
        part        TEXT,
        material    TEXT,

        FOREIGN KEY (group_id)
            REFERENCES offer_groups (id)
            ON DELETE CASCADE
            ON UPDATE CASCADE
    )
"""
columns_opredefs = [
    ("offer_predefs", "id", "ID", "string", 0, 25, 1, 1),
    ("offer_predefs", "group_id", "RyhmäID", "string", 1, 25, 1, 1),
    ("offer_predefs", "part", "Osa", "string", 2, 60, 0, 0),
    ("offer_predefs", "material", "Materiaali", "string", 3, 60, 0, 0)
]
select_opredefs = """
    SELECT id, group_id, part, material
    FROM offer_predefs
    WHERE group_id=(?)
"""
sql_create_table_offer_materials = """
    CREATE TABLE IF NOT EXISTS offer_materials (
        id          TEXT PRIMARY KEY,
        group_id    TEXT NOT NULL,
        category    TEXT,
        code        TEXT,
        desc        TEXT,
        prod        TEXT,
        thickness   INTEGER,
        unit        TEXT,
        cost        REAL DEFAULT 0.0,
        add_cost    REAL DEFAULT 0.0,
        edg_cost    REAL DEFAULT 0.0,
        loss        REAL DEFAULT 0.0,
        discount    REAL DEFAULT 0.0,
        tot_cost    REAL
            GENERATED ALWAYS AS
            ((cost + edg_cost + add_cost) * (1 + loss) * (1 - discount))
            STORED,

        FOREIGN KEY (group_id) REFERENCES offer_groups (id)
            ON DELETE CASCADE
            ON UPDATE CASCADE
    )
"""
columns_omats = [
    ("offer_materials", "id", "ID", "string", 0, 80, 1, 1),
    ("offer_materials", "group_id", "RyhmäID", "string", 1, 80, 1, 1),
    ("offer_materials", "category", "Tuoteryhmä", "string", 2, 60, 0, 0),
    ("offer_materials", "code", "Koodi", "string", 3, 60, 0, 0),
    ("offer_materials", "desc", "Kuvaus", "string", 4, 80, 0, 0),
    ("offer_materials", "prod", "Valmistaja", "string", 5, 60, 0, 0),
    ("offer_materials", "thickness", "Paksuus", "long", 6, 60, 0, 0),
    ("offer_materials", "unit", "Hintayksikkö", "choice:€/m2,€/kpl", 7, 60, 0, 0),
    ("offer_materials", "cost", "Hinta", "double:6,2", 8, 60, 0, 0),
    ("offer_materials", "add_cost", "Lisähinta", "double:6,2", 9, 60, 0, 0),
    ("offer_materials", "edg_cost", "R.Nauhan hinta", "double:6,2", 10, 60, 0, 0),
    ("offer_materials", "loss", "Hukka", "double:6,2", 11, 60, 0, 0),
    ("offer_materials", "discount", "Alennus", "double:6,2", 12, 60, 0, 0),
    ("offer_materials", "tot_cost", "Kokonaishinta", "double:6,2", 13, 60, 0, 1)
]
select_omaterials = """SELECT * FROM offer_materials WHERE group_id=(?)"""
sql_create_table_offer_products = """
    CREATE TABLE IF NOT EXISTS offer_products (
        id          TEXT PRIMARY KEY,
        group_id    TEXT NOT NULL,
        category    TEXT,
        code        TEXT,
        count       INTEGER DEFAULT 1,
        desc        TEXT,
        prod        TEXT,
        inst_unit   REAL DEFAULT 0.0,
        width       INTEGER DEFAULT 0,
        height      INTEGER DEFAULT 0,
        depth       INTEGER DEFAULT 0,
        work_time   REAL DEFAULT 0.0,

        FOREIGN KEY (group_id)
            REFERENCES offer_groups (id)
            ON DELETE CASCADE
            ON UPDATE CASCADE
    )
"""
columns_oproducts = [
    ("offer_products", "id", "ID", "string", 0, 80, 1, 1),
    ("offer_products", "group_id", "RyhmäID", "string", 1, 80, 1, 1),
    ("offer_products", "category", "Tuoteryhmä", "string", 2, 60, 0, 0),
    ("offer_products", "code", "Koodi", "string", 3, 60, 0, 0),
    ("offer_products", "count", "Määrä", "long", 4, 45, 0, 0),
    ("offer_products", "desc", "Kuvaus", "string", 5, 80, 0, 0),
    ("offer_products", "prod", "Valmistaja", "string", 6, 60, 0, 0),
    ("offer_products", "inst_unit", "As.Yksikkö", "double:6,2", 7, 45, 0, 0),
    ("offer_products", "width", "Leveys", "long", 8, 45, 0, 0),
    ("offer_products", "height", "Korkeus", "long", 9, 45, 0, 0),
    ("offer_products", "depth", "Syvyys", "long", 10, 45, 0, 0),
    ("offer_products", "work_time", "Työaika", "double:6,2", 11, 45, 0, 0),
    ("offer_products", "part_cost", "Osahinta", "double:6,2", 12, 45, 0, 1),
    ("offer_products", "tot_cost", "Kokonaishinta", "double:6,2", 13, 45, 0, 1),
]
select_oproducts = """
    SELECT
        pr.id,
        pr.group_id,
        pr.category,
        pr.code,
        pr.count,
        pr.desc,
        pr.prod,
        pr.inst_unit,
        pr.width,
        pr.height,
        pr.depth,
        pr.work_time,
        pa.part_cost,
        (pa.part_cost + pr.work_time *
            (
                SELECT var.val
                FROM variables AS var
                WHERE key="work_cost"
            )
        ) tot_cost
    FROM offer_products AS pr
    LEFT JOIN (
        SELECT pa.product_id, SUM(pa.cost) AS part_cost
        FROM offer_parts AS pa
        GROUP BY pa.product_id) pa ON pr.id=pa.product_id
    WHERE pr.group_id=(?)
    """
sql_create_table_offer_parts = """
    CREATE TABLE IF NOT EXISTS offer_parts (
        id          TEXT PRIMARY KEY,
        product_id  TEXT NOT NULL,
        part        TEXT,
        code        TEXT,
        count       INTEGER DEFAULt 1,
        desc        TEXT,
        use_predef  INTEGER DEFAULT 0,
        default_mat TEXT,
        width       INTEGER DEFAULT 0,
        length      INTEGER DEFAULT 0,
        cost        REAL DEFAULT 0.0,
        code_width  TEXT,
        code_length TEXT,
        code_cost   TEXT,

        FOREIGN KEY (product_id)
            REFERENCES offer_products (id)
            ON DELETE CASCADE
            ON UPDATE CASCADE
    )
"""
columns_oparts = [
    ("offer_parts", "id", "ID", "string", 0, 80, 1, 1),
    ("offer_parts", "product_id", "TuoteID", "string", 1, 80, 1, 1),
    ("offer_parts", "part", "Osa", "string", 2, 60, 0, 0),
    ("offer_parts", "code", "Koodi", "string", 3, 60, 0, 0),
    ("offer_parts", "count", "Määrä", "long", 4, 45, 0, 0),
    ("offer_parts", "desc", "Kuvaus", "string", 5, 80, 0, 0),
    ("offer_parts", "use_predef", "Käytä esimääritystä", "bool", 6, 45, 0, 0),
    ("offer_parts", "default_mat", "Oletus materiaali", "string", 7, 45, 0, 0),
    ("offer_parts", "width", "Leveys", "long", 8, 45, 0, 1),
    ("offer_parts", "length", "Pituus", "long", 9, 45, 0, 1),
    ("offer_parts", "cost", "Hinta", "double:6,2", 10, 45, 0, 1),
    ("offer_parts", "code_width", "Koodi Leveys", "string", 11, 120, 0, 0),
    ("offer_parts", "code_length", "Koodi Pituus", "string", 12, 120, 0, 0),
    ("offer_parts", "code_cost", "Koodi Hinta", "string", 13, 120, 0, 0),
    ("offer_parts", "used_mat", "Käyt. Mat.", "string", 14, 55, 0, 1),
    ("offer_parts", "m.thickness", "Paksuus", "long", 15, 35, 0, 1),
    ("offer_parts", "m.tot_cost", "Mat. Hinta", "double:6,2", 16, 35, 0, 1),
    ("offer_parts", "pr.width", "Tuote leveys", "long", 17, 35, 0, 1),
    ("offer_parts", "pr.height", "Tuote korkeus", "long", 18, 35, 0, 1),
    ("offer_parts", "pr.depth", "Tuote syvyys", "long", 19, 35, 0, 1),
]
select_oparts = """
    SELECT
        pa.id,
        pa.product_id,
        pa.part,
        pa.code,
        pa.count,
        pa.desc,
        pa.use_predef,
        pa.default_mat,
        pa.width,
        pa.length,
        pa.cost,
        pa.code_width,
        pa.code_length,
        pa.code_cost,
        CASE
            WHEN pa.use_predef=0 THEN
                pa.default_mat
            ELSE
                d.material
            END used_mat,
        m.thickness,
        m.tot_cost,
        pr.width,
        pr.height,
        pr.depth

    FROM offer_parts pa
        INNER JOIN offer_products pr
            ON pa.product_id=pr.id

        LEFT JOIN offer_predefs d
            ON pr.group_id=d.group_id AND pa.part=d.part

        LEFT JOIN offer_materials m
            ON (
                CASE
                    WHEN pa.use_predef=0 THEN
                        pa.default_mat
                    ELSE
                        d.material
                    END
                ) = m.code

    WHERE pa.product_id=(?)
"""
sql_create_table_materials = """
    CREATE TABLE IF NOT EXISTS materials (
        code        TEXT PRIMARY KEY,
        category    TEXT,
        desc        TEXT,
        prod        TEXT,
        unit        TEXT,
        thickness   INTEGER,
        loss        REAL,
        cost        REAL,
        edg_cost    REAL,
        add_cost    REAL,
        discount    REAL
    )
"""
sql_create_table_products = """
    CREATE TABLE IF NOT EXISTS products (
        code        TEXT PRIMARY KEY,
        category    TEXT,
        desc        TEXT,
        prod        TEXT,
        inst_unit   TEXT,
        width       INTEGER,
        height      INTEGER,
        depth       INTEGER,
        work_time   REAL,
        work_cost   REAL
    )
"""
sql_create_table_parts = """
    CREATE TABLE IF NOT EXISTS parts (
        code            TEXT NOT NULL,
        product_code    TEXT,
        category        TEXT,
        desc            TEXT,
        default_mat     TEXT,
        width           INTEGER,
        length          INTEGER,
        code_width      TEXT,
        code_length     TEXT,
        cost            REAL,

        PRIMARY KEY (code, product_code),
        FOREIGN KEY (product_code)
            REFERENCES offer_products (code)
            ON DELETE CASCADE
            ON UPDATE CASCADE
    )
"""
sql_create_table = {
    "variables": sql_create_table_variables,
    "columns": sql_create_table_columns,
    "offers": sql_create_table_offers,
    "offer_groups": sql_create_table_offer_groups,
    "offer_predefs": sql_create_table_offer_predefs,
    "offer_materials": sql_create_table_offer_materials,
    "offer_products": sql_create_table_offer_products,
    "offer_parts": sql_create_table_offer_parts,
    "materials": sql_create_table_materials,
    "products": sql_create_table_products,
    "parts": sql_create_table_parts
}
sql_insert_general = """INSERT INTO {table} ({columns}) VALUES ({qm})"""

sql_insert_default_fcmults = """INSERT INTO fcmults (unit) VALUES (?)"""
sql_insert_default_offers = """INSERT INTO offers (id) VALUES (?)"""
sql_insert_default_offer_groups = """INSERT INTO offer_groups (id, offer_id) VALUES (?,?)"""
sql_insert_default_offer_predefs = """INSERT INTO offer_predefs (id, group_id) VALUES (?,?)"""
sql_insert_default_offer_materials = """INSERT INTO offer_materials (id, group_id) VALUES (?,?)"""
sql_insert_default_offer_products = """INSERT INTO offer_products (id, group_id) VALUES (?,?)"""
sql_insert_default_offer_parts = """INSERT INTO offer_parts (id, product_id) VALUES (?,?)"""
sql_insert_default_materials = """INSERT INTO materials (code) VALUES (?)"""
sql_insert_default_products = """INSERT INTO products (code) VALUES (?)"""
sql_insert_default_parts = """INSERT INTO parts (code, product_code) VALUES (?,?)"""

sql_insert_default = {
    "fcmults": sql_insert_default_fcmults,
    "offers": sql_insert_default_offers,
    "offer_groups": sql_insert_default_offer_groups,
    "offer_predefs": sql_insert_default_offer_predefs,
    "offer_materials": sql_insert_default_offer_materials,
    "offer_products": sql_insert_default_offer_products,
    "offer_parts": sql_insert_default_offer_parts,
    "materials": sql_insert_default_materials,
    "products": sql_insert_default_products,
    "parts": sql_insert_default_parts
}

sql_select_general = """SELECT {columns} FROM {table} WHERE {cond}"""

# ****************************************************************
#  Get Treelist Queries
# ****************************************************************
sql_select_offernames_sorted = """
    SELECT name, id FROM offers
    WHERE id=?
"""
sql_select_groupnames_sorted = """
    SELECT name, offer_id, id FROM offer_groups
    WHERE offer_id=?
    ORDER BY name ASC
"""


import csv

class OfferTables:
    con = None
    cur = None

    table_setup = read_json("table.json")

    def __init__(self) -> None:
        """."""
        cur = self.create_connection("ttk.db")

        # for table, sql in sql_create_table.items():
            # cur.execute("""DROP TABLE IF EXISTS {};""".format(table))
            # self.create_table(sql)

        # self.insert("columns", columns_keys, columns_omats, True)
        # self.insert("columns", columns_keys, columns_oproducts, True)
        # self.insert("columns", columns_keys, columns_oparts, True)
        # self.insert("columns", columns_keys, columns_opredefs, True)

        self.con.commit()

    def insert_from_csv(self, table, file):
        data_keys = None
        data = []
        with open(file, newline='', encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile, delimiter=",")
            first = True
            types = []
            for row in reader:
                if first:
                    data_keys = row
                    first = False
                    for key in row:
                        typestring = self.table_setup["columns"][table][key]["type"]
                        types.append(typestring)
                else:
                    conv_row = [str2type(types[n], v) for n, v in enumerate(row)]
                    data.append(conv_row)

        self.insert(
            table,
            data_keys,
            data,
            True
        )

    def close(self):
        """Close the connection."""
        self.con.close()

    def create_connection(self, database_file):
        """Create connection if it does not exists and return the cursor.
        
        Sets OfferTables.cur and OfferTables.con
        """
        try:
            if self.con is None:
                OfferTables.con = sqlite3.connect(database_file)

            if self.cur is None:
                OfferTables.cur = OfferTables.con.cursor()
            return OfferTables.cur

        except sqlite3.Error as e:
            print(e)

    def create_table(self, create_table_sql):
        try:
            self.cur.execute(create_table_sql)
        except sqlite3.Error as e:
            print(e)

    def insert(self, table: str, columns: Iterable, values: Iterable, many: bool=False):
        """Insert values into a table.

        Parameters
        ----------
        table : str
            Name of the table.
        columns : Iterable
            The column names where values are inserted.
        values : Iterable
            Values for insertion matching the column names.
        many : bool
            True if inserting multiple rows.

        Returns
        -------
        bool
            True if successful, False otherwise. Prints error to console.
        """
        cols = ','.join(columns)
        qms = ','.join(['?'] * len(columns))
        sql = sql_insert_general.format(table=table, columns=cols, qm=qms)
        try:
            if many:
                self.cur.executemany(sql, values)
            else:
                self.cur.execute(sql, values)
            self.con.commit()
        except sqlite3.Error as e:
            print(e)
            return False
        return True

    def get(self, table: str, columns: Iterable, match_columns: Iterable,
            values: Iterable, many=False, operator='='):
        """Get a row of values.

        Parameters
        ----------
        table : str
            Name of the table.
        columns : Iterable
            List of columns to get.
        match_columns : Iterable
            List of columns used to find results.
        values : Iterable
            Values matching columns used to find results.
        many : bool, optional
            True if returing multiple rows, by default False
        operator : str, optional
            Operator used for matching the select.

        Returns
        -------
        List or Tuple
            Row or multiple rows of search results.
        """
        cols = ','.join(columns)
        conditions = ""
        for col in match_columns:
            conditions += col + operator + "?"
            if col != match_columns[-1]:
                conditions += " AND "

        sql = sql_select_general.format(
            table=table,
            columns=cols,
            cond=conditions
        )
        # print(sql)
        try:
            self.cur.execute(sql, values)
            self.con.commit()
        except sqlite3.Error as e:
            print("OfferTables.get\n\t{}".format(e))
            print("\tsql: {}".format(sql))
            print("\ttable: {}".format(table))
            print("\tcolumns: {}".format(columns))
            print("\tmatch_columns: {}".format(match_columns))
            print("\tvalues: {}".format(values))
            print("\tmany: {}".format(many))
            print("\toperator: {}".format(operator))
            return []
        if many:
            return self.cur.fetchall()
        else:
            return self.cur.fetchone()

    def get_omaterials(self, group_id: str):
        try:
            self.cur.execute(select_omaterials, (group_id,))
            self.con.commit()
        except sqlite3.Error as e:
            print("OfferTables.get_omaterials\n\t{}".format(e))
            return []

        return self.cur.fetchall()
    
    def get_oproducts(self, group_id: str):
        self.update_parts(group_id)
        try:
            self.cur.execute(select_oproducts, (group_id,))
            self.con.commit()
        except sqlite3.Error as e:
            print("OfferTables.get_oproducts\n\t{}".format(e))
            return []
        # print("select oproducts")
        return self.cur.fetchall()

    def select(self, sql, values):
        try:
            self.cur.execute(sql, values)
            self.con.commit()
        except sqlite3.Error as e:
            print("OfferTables.select\n\tsql: {}\n\t{}".format(sql, e))
            return []

        return self.cur.fetchall()

    def update(self, sql, values, many=False):
        try:
            if many:
                self.cur.executemany(sql, values)
            else:
                self.cur.execute(sql, values)
            self.con.commit()
        except sqlite3.Error as e:
            print("OfferTables.update\n\tsql: {}\n\t{}".format(sql, e))
            return False
        return True

    def update_parts(self, group_id: str, products=None):
        """Update the offer parts table to get up to date coded values."""
        update_parts = """
            UPDATE offer_parts
            SET width = (?),
                length = (?),
                cost = (?)

            WHERE id = (?)
        """
        select_oproduct_ids = """
            SELECT id
            FROM offer_products
            WHERE group_id = (?)
        """
        if products is None:
            product_ids = self.select(select_oproduct_ids, (group_id,))
        else:
            product_ids = products

        for pid in product_ids:
            part_list = self.select(select_oparts, (pid[0],))
            new_values_list = []

            for row, part in enumerate(part_list):
                new_values = []
                is_changed = False

                for n in range(8, 11):
                    old_value = part[n]
                    code = part[n + 3]
                    value = parse_code(code, row, part_list)
                    new_values.append(value)
                    if value != old_value:
                        is_changed = True

                if is_changed:
                    new_values.append(part[0])
                    new_values_list.append(new_values)

            self.update(update_parts, new_values_list, True)

    def get_oparts(self, product_id: str):
        self.update_parts("", [(product_id,)])
        return self.select(select_oparts, (product_id,))

    def get_opredefs(self, group_id: str):
        try:
            self.cur.execute(select_opredefs, (group_id,))
            self.con.commit()
        except sqlite3.Error as e:
            print("OfferTables.get_oparts\n\t{}".format(e))
            return []

        return self.cur.fetchall()

    select_get_columns = """SELECT * FROM columns WHERE tablename=(?) ORDER BY col_idx ASC"""
    def get_columns(self, table):
        """Return the column setup for given table.

        Parameters
        ----------
        table : str
            Name of table.

        Returns
        -------
        List of tuples
            Column setup for table. Empty list on error.
        """
        try:
            self.cur.execute(self.select_get_columns, (table,))
            self.con.commit()
        except sqlite3.Error as e:
            print("OfferTables.get_columns\n\t{}".format(e))
            return []
        return self.cur.fetchall()

    def get_column_setup(self, table, keys):
        """Return a dictionary with column setup for keys from table."""
        cols = self.table_setup["columns"][table]
        return {k: cols[k] for k in keys}

    def get_display_setup(self, display_key):
        """Return the display setup."""
        return self.table_setup["display"][display_key]

    sql_update_general = """UPDATE {table} SET {column}=(?) WHERE {cond}"""
    def update_one(self, table: str, column_key: str, pk: Iterable, values: Iterable):
        """Update a single column with values.

        Parameters
        ----------
        table : str
            Name of the table.
        column_key : str
            Column to update.
        pk : Iterable
            Private key to find the row to update.
        values : Iterable
            [NewValue] + Iterable private_key

        Returns
        -------
        bool
            True if successful.
        """
        # qm = '?' if isinstance(pk, str) else ','.join(['?'] * len(pk))
        condition = ""
        for key in pk:
            condition += key + "=(?)"
            if key != pk[-1]:
                condition += " AND "

        sql = self.sql_update_general.format(
            table=table,
            column=column_key,
            cond=condition)
        try:
            self.cur.execute(sql, values)
            self.con.commit()
        except sqlite3.Error as e:
            print("OfferTables.update_one\n\t{}".format(e))
            print("\tsql: {}".format(sql))
            print("\ttable: {}".format(table))
            print("\tcolumn_key: {}".format(column_key))
            print("\tpk: {}".format(pk))
            print("\tvalues: {}".format(values))
            return False
        return True

    sql_delete_general = """DELETE FROM {table} WHERE {match}=({qm})"""
    def delete(self, table, match_columns: Iterable, values: Iterable, many=False):
        """Delete rows matching the columns and values specified.

        Parameters
        ----------
        table : str
            Name of the table.
        match_columns : Iterable
            Columns that are used for matching the deleted rows.
        values : Iterable
            Values for the columns used to match.

        Returns
        -------
        bool
            True on success, False otherwise.
        """
        
        sql = self.sql_delete_general.format(
            table=table,
            match=','.join(match_columns),
            qm=','.join(['?'] * len(match_columns))
        )

        try:
            if many:
                self.cur.executemany(sql, values)
            else:
                self.cur.execute(sql, values)
            self.con.commit()
        except sqlite3.Error as e:
            print("OfferTables.delete\n\t{}".format(e))
            print("\tsql: {}".format(sql))
            print("\ttable: {}".format(table))
            print("\tmatch_columns: {}".format(match_columns))
            print("\tvalues: {}".format(values))
            return False
        return True

    def get_treelist(self, offer_ids: list):
        """Return a list of offer and group names and ids.

        return listitem: (name, offer_id, group_id).
        """
        treelist = []
        offers = []

        for oid in offer_ids:
            try:
                self.cur.execute(sql_select_offernames_sorted, (oid,))
            except sqlite3.Error as e:
                print("ERROR in OfferTables.get_treelist\n\t{}".format(e))
                return []

            # self.con.commit()
            res = self.cur.fetchone()
            offers.append(res)

        offers.sort(key=itemgetter(0))

        for item in offers:
            try:
                self.cur.execute(sql_select_groupnames_sorted, (item[-1],))
            except sqlite3.Error as e:
                print("ERROR in OfferTables.get_treelist\n\t{}".format(e))
                return []

            groups = self.cur.fetchall()

            treelist.append(item)
            for g in groups:
                treelist.append(g)

        return treelist

    def set_visible(self, table, col, is_visible):
        """Set the visibility of a column.

        Parameters
        ----------
        table: str
            Name of the table.
        col : int
            Column index
        is_visible : bool
            True if column is to be set visible. False for hiding.
        """
        sql = """
            UPDATE columns
            SET visible = (?)
            WHERE tablename = (?) AND col_idx = (?)
        """
        val = 1 if is_visible else 0
        return self.update(sql, (val, table, col))

    def get_visible(self, table):
        """Return list of visible column indexes.

        Parameters
        ----------
        table : str
            Name of table.
        """
        sql = """
            SELECT col_idx
            FROM columns
            WHERE tablename = (?) AND visible = 1
            ORDER BY col_idx ASC
        """
        data = self.select(sql, (table,))
        return [c[0] for c in data]


if __name__ == '__main__':
    db = OfferTables()
    db.close()

