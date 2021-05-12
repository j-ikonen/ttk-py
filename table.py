"""Database operations.

TODO
----
    Unittest for get many.
    Add operator format for get.
    Add delete method.
    Add update method.

"""

import sqlite3
from typing import Iterable

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
    return TYPES[split[0]](mod_value)

def type2str(value):
    """Return the value as string."""
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
    "products": TABLE_COLUMNS_PRODUCTS
}
TABLE_LABELS = {
    "fcmults": "Asennusyksikkökertoimet",
    "materials": "Materiaalit",
    "products": "Tuotteet"
}
sql_create_table_fcmults = """
    CREATE TABLE IF NOT EXISTS fcmults (
        unit    TEXT PRIMARY KEY,
        mult    REAL
    )
"""
sql_create_table_offers = """
    CREATE TABLE IF NOT EXISTS offers (
        id                  TEXT PRIMARY KEY,
        name                TEXT DEFAULT 'Uusi Tarjous',
        client_firstname    TEXT,
        client_lastname     TEXT,
        client_company      TEXT,
        client_phone        TEXT,
        client_email        TEXT,
        client_address      TEXT,
        client_postcode     TEXT,
        client_postarea     TEXT,
        client_info         TEXT
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
        code        TEXT UNIQUE,
        desc        TEXT,
        prod        TEXT,
        unit        TEXT,
        thck        INTEGER,
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
        code        TEXT,
        desc        TEXT,
        use_predef  INTEGER,
        default_mat TEXT,
        code_x      TEXT,
        code_y      TEXT,
        code_z      TEXT,

        FOREIGN KEY (product_id)
            REFERENCES offer_products (id)
            ON DELETE CASCADE
            ON UPDATE CASCADE
    )
"""
sql_create_table_materials = """
    CREATE TABLE IF NOT EXISTS materials (
        code        TEXT PRIMARY KEY,
        desc        TEXT,
        prod        TEXT,
        unit        TEXT,
        thck        INTEGER,
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
        code            TEXT PRIMARY KEY,
        product_code    TEXT NOT NULL,
        desc            TEXT,
        default_mat     TEXT,
        code_x          TEXT,
        code_y          TEXT,
        code_z          TEXT,

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

sql_select_general = """SELECT {columns} FROM {table} WHERE {match}{op}{qm}"""
sql_update_general = """UPDATE {table} SET {column} = ? WHERE {pk} = ({qm})"""

# select_parts = """
#     SELECT
#         opa.code,
#         opa.desc,
#         opa.use_predef,
#         opa.default_mat,
#         CASE
#             WHEN opa.use_predef = 0 THEN opa.default_mat
#             WHEN opa.use_predef = 1 
#                 THEN
#                     SELECT opd.material 
#                     FROM offer_predefs opd
#                     WHERE opd.group_id=opa.group_id AND opd.part=opa.code
#             ELSE null
#             END used_mat
#         (offer_products.width - m.thck) width,
#         () length,
#         () thickness,
#         () cost
#     FROM offer_parts opa
#         LEFT JOIN offer_materials m ON p.used_mat=m.code
#         LEFT JOIN offer_products t ON opr.product_id=t.id
#     WHERE id=?
# """
# sql_insert_materials = """
#     INSERT INTO materials (
#         id,
#         code,
#         desc,
#         prod,
#         unit,
#         thck,
#         loss,
#         cost,
#         edg_cost,
#         add_cost,
#         discount
#     ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
# """
# sql_count_units = """
#     SELECT inst_unit, SUM(count), mult, SUM(count)*mult
#     FROM products
#     LEFT JOIN fcmults ON fcmults.unit = products.inst_unit
#     GROUP BY inst_unit
# """
# sql_insert_default = {
#     "offers": """INSERT INTO offers (id) VALUES (?)""",
#     "fcmults": """INSERT INTO fcmults (id) VALUES (?)""",
#     "groups": """INSERT INTO groups (id, offer_id) VALUES (?, ?)""",
#     "predefs": """INSERT INTO predefs (id, group_id, offer_id) VALUES (?, ?, ?)""",
#     "materials": """INSERT INTO materials (id, group_id, offer_id) VALUES (?, ?, ?)""",
#     "products": """INSERT INTO products (id, group_id, offer_id) VALUES (?, ?, ?)"""
# }

# sql_select_groups = """
#     SELECT offer_id, name, id
#     FROM groups
#     WHERE offer_id=?
#     ORDER BY name DESC
# """
# sql_select_offers_by_list = """
#     SELECT id, name
#     FROM offers
#     WHERE id IN ({})
#     ORDER BY name DESC
# """
# sql_select_offer_page = """
#     SELECT 
#         name,
#         client_firstname,
#         client_lastname,
#         client_company,
#         client_phone,
#         client_email,
#         client_address,
#         client_postcode,
#         client_postarea,
#         client_info
#     FROM offers
#     WHERE id=?
# """
# offer_labels = [
#         "ID",
#         "Tarjouksen nimi",
#         "Etunimi",
#         "Sukunimi",
#         "Yritys",
#         "Puh.",
#         "Sähköposti",
#         "Lähiosoite",
#         "Postinumero",
#         "Postitoimipaikka",
#         "Lisätiedot"
# ]
# offer_keys = [
#     "id",
#     "name",
#     "client_firstname",
#     "client_lastname",
#     "client_company",
#     "client_phone",
#     "client_email",
#     "client_address",
#     "client_postcode",
#     "client_postarea",
#     "client_info"
# ]
# offer_types = ["string"] * len(offer_labels)

# table_labels = {
#     "offers.name": offer_labels[1],
#     "offers.client": offer_labels[2:],
# }
# table_types = {
#     "offers.name": offer_types[1],
#     "offers.client": offer_types[2:]
# }
# table_keys = {
#     "offers.name": offer_keys[1],
#     "offers.client": offer_keys[2:]
# }
# sql_select_fcmults = """
#     SELECT unit, mult
#     FROM fcmults
#     WHERE unit IN ({})
#     ORDER BY unit DESC
# """
# sql_update_one_offers = """
#     UPDATE offers 
#     SET {col} = ?
#     WHERE id = ?
# """
# sql_update_one_groups = """
#     UPDATE groups
#     SET {col} = ?
#     WHERE id = ? AND offer_id = ?
# """
# sql_update_one = {
#     "offers": sql_update_one_offers,
#     "groups": sql_update_one_groups
# }

# sql_upsert = {
#     "offer_materials": """
#         INSERT INTO offer_materials (id, group_id, {column})
#         VALUES (?, ?, ?)
#         ON CONFLICT (id) DO UPDATE SET {column}=excluded.{column}
#     """
# }
# sql_select_ids = {
#     "materials": """SELECT id FROM materials WHERE group_id=?"""
# }

sql_select_offer_materials_grid = """
    SELECT
        id,
        code,
        desc,
        prod,
        unit,
        thck,
        loss,
        cost,
        edg_cost,
        add_cost,
        discount,
        ((cost + edg_cost + add_cost) * (1 + loss) * (1 - discount)) tot_cost
    FROM offer_materials
    WHERE group_id=?
"""
sql_select_grid = {
    "offer_materials": sql_select_offer_materials_grid
}



class OfferTables:
    con = None
    cur = None
    keys = {
        "offer_materials": [
            "code",
            "desc",
            "prod",
            "unit",
            "thck",
            "loss",
            "cost",
            "edg_cost",
            "add_cost",
            "discount",
            "tot_cost"
        ]
    }
    labels = {
        "offer_materials": [
            "Koodi",
            "Kuvaus",
            "Valmistaja",
            "Yksikkö",
            "Paksuus",
            "Hukka",
            "Materiaalin hinta",
            "RNauhan hinta",
            "Lisähinta",
            "Alennus",
            "Kokonaishinta"
        ]
    }
    label_sizes = {
        "offer_materials": [
            60,
            100,
            80,
            55,
            45,
            45,
            45,
            45,
            45,
            45,
            45
        ]
    }
    read_only = {
        "offer_materials": [10]
    }
    types = {
        "offer_materials": [
            "string",
            "string",
            "string",
            "choice:€/m2,€/kpl",
            "long",
            "double:6,2",
            "double:6,2",
            "double:6,2",
            "double:6,2",
            "double:6,2",
            "double:6,2"
        ]
    }
    unique = {
        "offer_materials": [0]
    }

    table_columns = TABLE_COLUMNS

    def __init__(self) -> None:
        """."""
        cur = self.create_connection("ttk.db")

        for table, sql in sql_create_table.items():
            cur.execute("""DROP TABLE IF EXISTS {};""".format(table))
            self.create_table(sql)

        self.con.commit()

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

    def get(self, table: str, columns: Iterable,
            match_columns: Iterable, values: Iterable, many=False, operator='='):
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

        Returns
        -------
        List or Tuple
            Row or multiple rows of search results.
        """
        cols = ','.join(columns)
        mcols = ','.join(match_columns)
        qms = ','.join(['?'] * len(match_columns))
        op = operator
        sql = sql_select_general.format(
            table=table,
            columns=cols,
            match=mcols,
            op=op,
            qm=qms
        )
        print(sql)
        try:
            self.cur.execute(sql, values)
            self.con.commit()
        except sqlite3.Error as e:
            print(e)
            return []
        if many:
            return self.cur.fetchall()
        else:
            return self.cur.fetchone()

    def get_grid(self, key, parent_id):
        """Return list of columns by foreign key id.

        [row][0] = id"""
        sql = sql_select_grid[key]
        try:
            self.cur.execute(sql, (parent_id,))
        except sqlite3.Error as e:
            print(e)
            return []
        return self.cur.fetchall()

    def get_column_setup(self, key):
        # cols = self.table_columns[key]
        column_setup = {
            "dbpanel.materials": self.table_columns["materials"],
            "dbpanel.products": self.table_columns["products"],
            "objectgrid.materials": self.table_columns["materials"],
            "objectgrid.products": self.table_columns["products"]
        }
        # column_setup_materials = [key for key in cols[key].keys()] + ["((cost + edg_cost + add_cost) * (1 + loss) * (1 - discount)) tot_cost"]
        return column_setup[key]

    def get_panel_setup(self, panel):
        panel_setup = {
            "dbpanel": {
                "materials": {"label": TABLE_LABELS["materials"], "pk": "code"},
                "products": {"label": TABLE_LABELS["products"], "pk": "code"}
            },
            "objectgrid": {
                "materials": {"label": TABLE_LABELS["materials"], "pk": "code"},
                "products": {"label": TABLE_LABELS["products"], "pk": "code"}
            }
        }
        return panel_setup[panel]

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
        qm = '?' if isinstance(pk, str) else ','.join(['?'] * len(pk))
        sql = sql_update_general.format(
            table=table,
            column=column_key,
            pk=pk,
            qm=qm)
        print(sql)
        try:
            if isinstance(values[0], Iterable):
                self.cur.executemany(sql, values)
            else:
                self.cur.execute(sql, values)
            self.con.commit()
        except sqlite3.Error as e:
            print(e)
            return False
        return True

    # def upsert(self, key, column_key, values):
    #     """
    #     INSERT INTO materials (id, group_id, {column})
    #     VALUES (?, ?, ?)
    #     ON CONFLICT (id) DO UPDATE SET {column}=excluded.{column}
    #     """
    #     sql = sql_upsert[key].format(column=column_key)
        
    #     try:
    #         self.cur.execute(sql, values)
    #     except sqlite3.Error as e:
    #         print(e)
    #         return False
    #     return True

    # def delete(self, key, id):
    #     """Delete a row with id. Return True on success."""
    #     sql = {"materials": """DELETE FROM materials WHERE id=?"""}[key]
    #     return self.execute(sql, (id,))

    # def execute(self, sql, values=None):
    #     """Execute with values. Return True on success."""
    #     try:
    #         if values is None:
    #             self.cur.execute(sql)
    #         else:
    #             self.cur.execute(sql, values)
    #         self.con.commit()
    #     except sqlite3.Error as e:
    #         print(e)
    #         return False
    #     return True

    # def get_unitcount(self,):
    #     """."""

    # def get_ids(self, key, parent_id):
    #     """Return the lists of ids by foreign key id."""
    #     sql = sql_select_ids[key]
    #     res = self.execute(sql, (parent_id,))
    #     if res:
    #         return self.cur.fetchall()
    #     return []


    # def get_by_ids(self, key, ids):
    #     """Return rows where id"""
    #     sql = {"materials": """SELECT """}
    # def get_offer_page(self, offer_id):
    #     """Return the relevant data for offer page as a list."""
    #     try:
    #         res = self.cur.execute(sql_select_offer_page, (offer_id,)).fetchone()
    #     except sqlite3.Error as e:
    #         print(e)
    #         return None

    #     print(res)
    #     return res

    # def get_labels(self, key):
    #     """Return the list of labels matching get_offer_page return tuple indexes."""
    #     return table_labels[key]

    # def get_types(self, key):
    #     """Return the list of types matching get_offer_page return tuple indexes."""
    #     return table_types[key]

    # def get_treelist(self, offers: list):
    #     """Return a list of offer group tuples.

    #     offer: (offer_id, name), group: (offer_id, name, group_id) tuples in name order.

    #     Args:
    #     - offers (list): List of open offer id's.
    #     """
    #     treelist = []
    #     seq = ','.join(['?']*len(offers))
    #     offers = self.cur.execute(sql_select_offers_by_list.format(seq), offers).fetchall()
    #     for oid in offers:
    #         # print(f"get_treelist - type: {type(oid)}")
    #         groups = self.cur.execute(sql_select_groups, (oid[0],)).fetchall()
    #         treelist += ([oid] + groups)
        
    #     for item in treelist:
    #         print(item)
    #     return treelist

    # def get_unit_count(self, offer_id):
    #     """Return the install unit count of products in the offer.
        
    #     Return (unit, count, mult)
    #     """
    #     self.execute(sql_count_units)


    # def update_one_offers(self, offer_id, name, col, value):
    #     """Update a value in offers table."""
    #     key = table_keys[name] if col is None else table_keys[name][col]
    #     sql = sql_update_one_offers.format(col=key)
    #     self.execute(sql, (value, offer_id))

    # def update_one_groups(self, ids, name, col, value):
    #     """Update a value in groups table. (offer_id, group_id) = ids"""
    #     (offer_id, group_id) = ids
    #     pass
    

    # def insert(self, name, ids):
    #     """."""
    #     oid = ObjectId()
    #     if self.execute(sql_insert[name], (oid,) + ids):
    #         return oid
    #     return None

    # def insert_default(self, table, ids):
    #     """
    #     sql_insert_default = {
    #         "offers": INSERT INTO offers (id) VALUES (?),
    #         "groups": INSERT INTO groups (id, offer_id) VALUES (?, ?),
    #         "predefs": INSERT INTO predefs (id, group_id, offer_id) VALUES (?, ?, ?),
    #         "materials": INSERT INTO materials (id, group_id, offer_id) VALUES (?, ?, ?)
    #     """
    #     oid = ObjectId()
    #     if self.execute(sql_insert_default[table], (oid,) + ids):
    #         return oid
    #     return None

    # def insert_offer(self):
    #     """Insert a new offer. Return id of inserted offer or None if not successful."""
    #     oid = str(ObjectId())
    #     if self.execute(sql_insert_default["offers"], (oid,)):
    #         return oid
    #     return None

    # def insert_group(self, offer_id: str):
    #     """Insert a new group. Return id of inserted group or None if not successful."""
    #     oid = str(ObjectId())
    #     if self.execute(sql_insert_default["groups"], (oid, offer_id)):
    #         return oid
    #     return None


if __name__ == '__main__':

    db = OfferTables()
    db.close()

