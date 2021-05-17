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

TABLE_COLUMNS_FCMULTS = {
    "unit": {"label": "Asennusyksikkö", "width": 80},
    "mult": {"label": "Kerroin", "width": 80}
}
TABLE_COLUMNS_MATERIALS = {
    "code": {"label": "Koodi", "type": "string", "width": 55},
    "desc": {"label": "Kuvaus", "type": "string", "width": 55},
    "prod": {"label": "Valmistaja", "type": "string", "width": 55},
    "thck": {"label": "Paksuus", "type": "long", "width": 55},
    "unit": {"label": "Hintayksikkö", "type": "string", "width": 55},
    "loss": {"label": "Hukka", "type": "double:6,2", "width": 55},
    "cost": {"label": "Mat. Hinta", "type": "double:6,2", "width": 55},
    "edg_cost": {"label": "R.Nauhan hinta", "type": "double:6,2", "width": 55},
    "add_cost": {"label": "Lisähinta", "type": "double:6,2", "width": 55},
    "discount": {"label": "Alennus", "type": "double:6,2", "width": 55}
}
EXTRA_COLUMNS_MATERIALS = {
    "((cost + edg_cost + add_cost) * (1 + loss) * (1 - discount)) tot_cost": {"label": "Kok. Hinta", "type": "double:6,2", "width": 55}
}
TABLE_COLUMNS_PRODUCTS = {
    "code": {"label": "Koodi", "type": "string", "width": 55},
    "desc": {"label": "Kuvaus", "type": "string", "width": 55},
    "prod": {"label": "Valmistaja", "type": "string", "width": 55},
    "inst_unit": {"label": "Asennusyksikkö", "type": "string", "width": 55},
    "width": {"label": "Leveys", "type": "string", "width": 55},
    "height": {"label": "Korkeus", "type": "string", "width": 55},
    "depth": {"label": "Syvyys", "type": "string", "width": 55},
    "work_time": {"label": "Työaika", "type": "string", "width": 55},
    "work_cost": {"label": "Työn hinta", "type": "string", "width": 55}
}
TABLE_COLUMNS = {
    "fcmults": TABLE_COLUMNS_FCMULTS,
    "materials": TABLE_COLUMNS_MATERIALS,
    "products": TABLE_COLUMNS_PRODUCTS,
}
GRID_COLUMNS = {
    "grouppagegrid.offer_materials": {**TABLE_COLUMNS_MATERIALS, **EXTRA_COLUMNS_MATERIALS}
}
TABLE_LABELS = {
    "offers": "Tarjoukset",
    "offer_groups": "Ryhmät",
    "offer_predefs": "Esimääritykset",
    "offer_materials": "Materiaalit",
    "offer_products": "Tuotteet",
    "offer_parts": "Osat",
    "fcmults": "Asennusyksikkökertoimet",
    "materials": "Materiaalit",
    "products": "Tuotteet",
    "parts": "Osat"
}
sql_create_table_fcmults = """
    CREATE TABLE IF NOT EXISTS fcmults (
        unit    TEXT PRIMARY KEY,
        mult    REAL
    )
"""
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
sql_create_table_offer_materials = """
    CREATE TABLE IF NOT EXISTS offer_materials (
        id          TEXT PRIMARY KEY,
        group_id    TEXT NOT NULL,
        category    TEXT,
        code        TEXT UNIQUE,
        desc        TEXT,
        prod        TEXT,
        unit        TEXT,
        thickness   INTEGER,
        loss        REAL,
        cost        REAL,
        edg_cost    REAL,
        add_cost    REAL,
        discount    REAL,

        FOREIGN KEY (group_id) REFERENCES groups (id)
            ON DELETE CASCADE
            ON UPDATE CASCADE
    )
"""
sql_create_table_offer_products = """
    CREATE TABLE IF NOT EXISTS offer_products (
        id          TEXT PRIMARY KEY,
        group_id    TEXT NOT NULL,
        category    TEXT,
        code        TEXT,
        count       INTEGER,
        desc        TEXT,
        prod        TEXT,
        inst_unit   TEXT,
        width       INTEGER,
        height      INTEGER,
        depth       INTEGER,
        work_time   REAL,
        work_cost   REAL,

        FOREIGN KEY (group_id)
            REFERENCES offer_groups (id)
            ON DELETE CASCADE
            ON UPDATE CASCADE,
        FOREIGN KEY (inst_unit)
            REFERENCES fcmults (unit)
            ON DELETE NO ACTION
            ON UPDATE NO ACTION
    )
"""
sql_create_table_offer_parts = """
    CREATE TABLE IF NOT EXISTS offer_parts (
        id          TEXT PRIMARY KEY,
        product_id  TEXT NOT NULL,
        category    TEXT,
        code        TEXT,
        desc        TEXT,
        use_predef  INTEGER,
        default_mat TEXT,
        width       INTEGER,
        length      INTEGER,
        code_width  TEXT,
        code_length TEXT,
        cost        REAL,

        FOREIGN KEY (product_id)
            REFERENCES offer_products (id)
            ON DELETE CASCADE
            ON UPDATE CASCADE
    )
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
    "fcmults": sql_create_table_fcmults,
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
sql_update_general = """UPDATE {table} SET {column} = (?) WHERE {pk} = (?)"""

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

# sql_select_offer_materials_grid = """
    # SELECT
        # id,
        # code,
        # desc,
        # prod,
        # unit,
        # thck,
        # loss,
        # cost,
        # edg_cost,
        # add_cost,
        # discount,
        # ((cost + edg_cost + add_cost) * (1 + loss) * (1 - discount)) tot_cost
    # FROM offer_materials
    # WHERE group_id=?
# """
# sql_select_grid = {
    # "offer_materials": sql_select_offer_materials_grid
# }

import csv

class OfferTables:
    con = None
    cur = None

    table_setup = read_json("table.json")

    def __init__(self) -> None:
        """."""
        cur = self.create_connection("ttk.db")

        for table, sql in sql_create_table.items():
            cur.execute("""DROP TABLE IF EXISTS {};""".format(table))
            self.create_table(sql)

        self.insert_from_csv("materials", "../../ttk-dbtestdata-materials.csv")
        self.insert_from_csv("products", "../../ttk-dbtestdata-products.csv")
        self.insert_from_csv("parts", "../../ttk-dbtestdata-parts.csv")

        offer_keys = [
            "id",
            "name",
            "firstname",
            "lastname",
            "company",
            "phone",
            "email",
            "address",
            "postcode",
            "postarea",
            "info",
        ]
        self.offer_data = [
            (str(ObjectId()), "Tarjous 1", "Nimi", "Suku", "asd", "012 345", "nimi.suku@mail.net", "Tie 12", "123", "KAUPUNKI", ""),
            (str(ObjectId()), "Tarjous 2", "Etu", "Nimi", "asd", "012 346", "etu.nimi@mail.net", "Tie 13", "1234", "KAUPUNKI2", ""),
            (str(ObjectId()), "Testi tarjous", "Testi", "Nimi", "qwe", "012 347", "testi.nimi@mail.net", "Tie 14", "1236", "KAUPUNKI2", ""),
            (str(ObjectId()), "Uusi tarjous", "Etu", "Suku", "qwe", "012 348", "etu.suku@mail.net", "Tie 15", "1237", "KAUPUNKI", "")
        ]
        group_keys = ["id", "offer_id", "name"]
        self.group_data = [
            (str(ObjectId()), self.offer_data[0][0], "Keittiö"),
            (str(ObjectId()), self.offer_data[0][0], "Kylpyhuone"),
            (str(ObjectId()), self.offer_data[1][0], "Keittiö"),
            (str(ObjectId()), self.offer_data[2][0], "Keittiö"),
            (str(ObjectId()), self.offer_data[3][0], "Keittiö"),
            (str(ObjectId()), self.offer_data[3][0], "...")
        ]
        opredef_keys = ["id", "group_id", "part", "material"]
        opredef_data = [
            (str(ObjectId()), self.group_data[0][0], "sivu", "MAT"),
            (str(ObjectId()), self.group_data[0][0], "hylly", "MAT"),
            (str(ObjectId()), self.group_data[0][0], "tausta", "MAT3"),
        ]

        omaterial_keys = [
            "id",         
            "group_id",   
            "category",   
            "code",       
            "desc",       
            "prod",       
            "unit",       
            "thickness",  
            "loss",       
            "cost",       
            "edg_cost",   
            "add_cost",   
            "discount" 
        ]
        omaterial_data = [
            (str(ObjectId()), self.group_data[0][0], "qwe", "MAT", "Materiaali", "Valmistaja", "€/m^2", 16, 0.15, 12.42, 0.33, 2.45, 0.0),
            (str(ObjectId()), self.group_data[0][0], "qwe", "MAT3", "Materiaali 1", "Valmistaja", "€/m^2", 18, 0.17, 14.42, 0.53, 4.45, 0.0),
            (str(ObjectId()), self.group_data[0][0], "qwe", "MAT8", "Materiaali 2", "Valmistaja", "€/m^2", 8, 0.19, 13.42, 0.31, 2.49, 0.1),
            (str(ObjectId()), self.group_data[0][0], "zxc", "OSA", "OSA", "Valmistaja", "€/kpl", None, 0.10, 22.42, 0.0, 2.85, 0.15)
        ]

        oproduct_keys = [
            "id",          
            "group_id",    
            "category",    
            "code",        
            "count",       
            "desc",        
            "prod",        
            "inst_unit",   
            "width",       
            "height",      
            "depth",       
            "work_time",   
            "work_cost"
        ]
        oproduct_data = [
            (str(ObjectId()), self.group_data[0][0], "tuoteryhmä", "KOODI", 1, "Kuvaus", "Valmistaja", "Asennusyksikkö", 1200, 2300, 620, 0.48, 20.0),
            (str(ObjectId()), self.group_data[1][0], "tuoteryhmä", "KOODI2", 2, "Kuvaus", "Valmistaja", "Asennusyksikkö", 1200, 2300, 620, 0.48, 20.0),
            (str(ObjectId()), self.group_data[0][0], "toinen ryhmä", "TOINEN1", 1, "Kuvaus", "Valmistaja", "Testi yksikkö", 1200, 2300, 620, 0.88, 20.0),
            (str(ObjectId()), self.group_data[0][0], "toinen ryhmä", "TOINEN3", 3, "Uusi Kuvaus", "Valmistaja", "Testi yksikkö", 1200, 2300, 620, 1.18, 20.0)
        ]

        opart_keys = [
            "id",          
            "product_id",  
            "category",    
            "code",        
            "desc",        
            "use_predef",  
            "default_mat", 
            "width",
            "length",
            "cost"
        ]
        opart_data = [
            (str(ObjectId()), oproduct_data[0][0], "sivu", "LEVY01", "Sivulevy", 0, "MAT", 120, 302, 8.2),
            (str(ObjectId()), oproduct_data[0][0], "hylly", "LEVY02", "Kuvaus....", 0, "MAT3", 280, 302, 18.2),
            (str(ObjectId()), oproduct_data[0][0], "tausta", "LEVY01", "Sivulevy", 0, "MAT", 555, 302, 28.2),
            (str(ObjectId()), oproduct_data[0][0], "sivu", "LEVY01", "Toinen Sivulevy", 0, "MAT", 120, 302, 38.2)
        ]

        self.insert("offers", offer_keys, self.offer_data, True)
        self.insert("offer_groups", group_keys,  self.group_data, True)

        self.insert("offer_predefs", opredef_keys, opredef_data, True)
        self.insert("offer_materials", omaterial_keys, omaterial_data, True)
        self.insert("offer_products", oproduct_keys, oproduct_data, True)
        self.insert("offer_parts", opart_keys, opart_data, True)

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

        # print(data_keys)
        # for row in data:
        #     print(row)

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
        """Create connection if it does not exists and return the cursor."""
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

    def insert_many(self, table: str, columns: Iterable, values: Iterable):
        """Insert multiple rows of values into a table.

        Parameters
        ----------
        table : str
            Name of the table.
        columns : Iterable
            The column names where values are inserted.
        values : Iterable
            Values for insertion matching the column names inside an iterable.

        Returns
        -------
        bool
            True if successful, False otherwise. Prints error to console.
        """
        cols = ','.join(columns)
        qms = ','.join(['?'] * len(columns))
        sql = sql_insert_general.format(table=table, columns=cols, qm=qms)
        try:
            self.cur.executemany(sql, values)
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

    sql_select_fieldcount = """
            SELECT pr.inst_unit, IFNULL(fc.mult, 0.0), SUM(pr.count), (IFNULL(fc.mult, 0.0) * SUM(pr.count)) cost
            FROM offer_products pr
                LEFT JOIN fcmults fc ON pr.inst_unit=fc.unit
            WHERE pr.group_id IN (
                SELECT gr.id
                FROM offer_groups gr
                WHERE gr.offer_id=?
            )
            GROUP BY pr.inst_unit
            ORDER BY pr.inst_unit ASC
        """
    def get_fieldcount(self, offer_id):
        """Return the fieldcount data of an offer."""
        try:
            self.cur.execute(self.sql_select_fieldcount, (offer_id,))
            self.con.commit()
        except sqlite3.Error as e:
            print("OfferTables.get_fieldcount\n\t{}".format(e))
            return []

        return self.cur.fetchall()

    sql_select_group_products = """
        SELECT *, (part_cost + wt * wc) FROM
            (SELECT
                pr.id,
                pr.category,
                pr.code,
                pr.count,
                pr.desc,
                pr.prod,
                pr.inst_unit,
                pr.width,
                pr.height,
                pr.depth,
                pr.work_time AS wt,
                pr.work_cost AS wc,
                (
                    SELECT SUM(pa.cost) FROM offer_parts AS pa WHERE pa.product_id=pr.id
                ) part_cost
            FROM offer_products AS pr
            WHERE pr.group_id=?)
        """
    def get_offer_products(self, group_id):
        """Get the group products grid data.

        Parameters
        ----------
        group_id : str
            Id of group whose products will be returned.

        Returns
        -------
        list
            list of tuples containing the grid data.
        """
        try:
            self.cur.execute(self.sql_select_group_products, (group_id,))
            self.con.commit()
        except sqlite3.Error as e:
            print("OfferTables.get_offer_products\n\t{}".format(e))
            return []

        return self.cur.fetchall()

    sql_select_group_parts = """
        SELECT
            p.id,
            p.category,
            p.code,
            p.desc,
            p.use_predef,
            p.default_mat,
            p.width,
            p.length,
            p.cost
        FROM offer_parts AS p
        WHERE product_id=?
        """
    def get_group_parts(self, product_id):
        """Get the group parts grid data.

        Parameters
        ----------
        product_id : str
            Id of products whose parts will be returned.

        Returns
        -------
        list
            list of tuples containing the grid data.
        """
        try:
            self.cur.execute(self.sql_select_group_parts, (product_id,))
            self.con.commit()
        except sqlite3.Error as e:
            print("OfferTables.get_group_parts\n\t{}".format(e))
            return []
        return self.cur.fetchall()

    def get_column_setup(self, table, keys):
        """Return a dictionary with column setup for keys from table."""
        cols = self.table_setup["columns"][table]
        return {k: cols[k] for k in keys}

    def get_display_setup(self, display_key):
        """Return the display setup."""
        return self.table_setup["display"][display_key]

    def update_one(self, table: str, column_key: str, pk: str, values: Iterable):
        """Update a single column with values.

        Parameters
        ----------
        table : str
            Name of the table.
        column_key : str
            Column to update.
        pk : str
            Private key to find the row to update.
        values : Iterable
            (NewValue, private_key, pk_if_multi_part_pk).

        Returns
        -------
        bool
            True if successful.
        """
        # qm = '?' if isinstance(pk, str) else ','.join(['?'] * len(pk))
        sql = sql_update_general.format(
            table=table,
            column=column_key,
            pk=pk)
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
    def delete(self, table, match_columns: Iterable, values: Iterable):
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


if __name__ == '__main__':

    db = OfferTables()
    db.close()

