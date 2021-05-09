import sqlite3

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


sql_create_offers_table = """
    CREATE TABLE IF NOT EXISTS offers (
        id      TEXT PRIMARY KEY,
        name    TEXT NOT NULL DEFAULT 'Uusi tarjous',
        client_firstname   TEXT DEFAULT '',
        client_lastname    TEXT DEFAULT '',
        client_company     TEXT DEFAULT '',
        client_phone       TEXT DEFAULT '',
        client_email       TEXT DEFAULT '',
        client_address     TEXT DEFAULT '',
        client_postcode    TEXT DEFAULT '',
        client_postarea    TEXT DEFAULT '',
        client_info        TEXT DEFAULT ''
    );
"""

sql_create_groups_table = """
    CREATE TABLE IF NOT EXISTS groups (
        id          TEXT NOT NULL,
        name        TEXT NOT NULL DEFAULT 'Uusi ryhmä',
        offer_id    TEXT NOT NULL,
        PRIMARY KEY (id, offer_id),
        FOREIGN KEY (offer_id)
            REFERENCES offers (id)
            ON DELETE CASCADE
            ON UPDATE CASCADE
    );
"""

sql_create_unitmults_table = """
    CREATE TABLE IF NOT EXISTS unitmults (
        offer_id    TEXT NOT NULL,
        unit        TEXT NOT NULL,
        mult        REAL NOT NULL DEFAULT 0.00,
        PRIMARY KEY (unit, offer_id),
        FOREIGN KEY (offer_id) REFERENCES offers (id)
            ON DELETE CASCADE
            ON UPDATE CASCADE
    );
"""
sql_create_predefs_table = """
    CREATE TABLE IF NOT EXISTS predefs (
        offer_id    TEXT NOT NULL,
        group_id    TEXT NOT NULL,
        part        TEXT DEFAULT '',
        material    TEXT DEFAULT '',
        PRIMARY KEY (part, group_id, offer_id),
        FOREIGN KEY (offer_id) REFERENCES offers (id)
            ON DELETE CASCADE
            ON UPDATE CASCADE,
        FOREIGN KEY (group_id) REFERENCES groups (id)
            ON DELETE CASCADE
            ON UPDATE CASCADE
    );
"""
sql_create_materials_table = """
    CREATE TABLE IF NOT EXISTS materials (
        offer_id    TEXT NOT NULL,
        group_id    TEXT NOT NULL,
        code        TEXT DEFAULT '',
        desc        TEXT DEFAULT '',
        prod        TEXT DEFAULT '',
        unit        TEXT DEFAULT '',
        thck        INTEGER DEFAULT 0,
        loss        REAL DEFAULT 0.0,
        cost        REAL DEFAULT 0.0,
        edg_cost    REAL DEFAULT 0.0,
        add_cost    REAL DEFAULT 0.0,
        discount    REAL DEFAULT 0.0,
        PRIMARY KEY (code, group_id, offer_id),
        FOREIGN KEY (offer_id) REFERENCES offers (id)
            ON DELETE CASCADE
            ON UPDATE CASCADE,
        FOREIGN KEY (group_id) REFERENCES groups (id)
            ON DELETE CASCADE
            ON UPDATE CASCADE
    );
"""
sql_insert_default = {
    "offers": """INSERT INTO offers (id) VALUES (?)""",
    "groups": """INSERT INTO groups (id, offer_id) VALUES (?, ?)""",
    "unitmults": """INSERT INTO unitmults (unit, mult, offer_id) VALUES (?, ?, ?)""",
    "predefs": """INSERT INTO predefs (part, group_id, offer_id) VALUES (?, ?, ?)""",
    "materials": """INSERT INTO materials (code, group_id, offer_id) VALUES (?, ?, ?)"""
}

sql_select_groups = """
    SELECT id, name, offer_id
    FROM groups
    WHERE offer_id=?
    ORDER BY name DESC
"""
sql_select_offers_by_list = """
    SELECT id, name
    FROM offers
    WHERE id IN ({})
    ORDER BY name DESC
"""

class OfferTables:
    con = None
    cur = None

    def __init__(self) -> None:
        """."""
        cur = self.create_connection("ttk.db")

        cur.execute("""DROP TABLE IF EXISTS offers;""")
        cur.execute("""DROP TABLE IF EXISTS groups;""")
        cur.execute("""DROP TABLE IF EXISTS unitmults;""")
        cur.execute("""DROP TABLE IF EXISTS clients;""")
        cur.execute("""DROP TABLE IF EXISTS predefs;""")
        cur.execute("""DROP TABLE IF EXISTS materials;""")
        self.con.commit()

        self.create_table(sql_create_offers_table)
        self.create_table(sql_create_groups_table)
        self.create_table(sql_create_unitmults_table)
        self.create_table(sql_create_predefs_table)
        self.create_table(sql_create_materials_table)

        offer_id = self.insert_offer()
        if offer_id is not None:
            self.insert_group(offer_id)
            self.insert_group(offer_id)
            self.insert_group(offer_id)

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

    def excecute(self, sql, values=None):
        """Execute with values. Return True on success."""
        try:
            if values is None:
                self.cur.execute(sql)
            else:
                self.cur.execute(sql, values)
            self.con.commit()
        except sqlite3.Error as e:
            print(e)
            return False
        return True

    def get_treelist(self, offers: list):
        """Return a list of offer (id, name) and group (id, name, offer_id) tuples in name order.

        Args:
        - offers (list): List of open offer id's.
        """
        treelist = []
        seq = ','.join(['?']*len(offers))
        offers = self.cur.execute(sql_select_offers_by_list.format(seq), offers).fetchall()
        for oid in offers:
            groups = self.cur.execute(sql_select_groups, (oid,)).fetchall()
            treelist += ([oid] + groups)
        return treelist

    def insert_offer(self):
        """Insert a new offer. Return id of inserted offer or None if not successful."""
        oid = str(ObjectId())
        if self.excecute(sql_insert_default["offers"], (oid,)):
            return oid
        return None

    def insert_group(self, offer_id: str):
        """Insert a new group. Return id of inserted group or None if not successful."""
        oid = str(ObjectId())
        if self.excecute(sql_insert_default["groups"], (oid, offer_id)):
            return oid
        return None


if __name__ == '__main__':

    db = OfferTables()
    db.close()

