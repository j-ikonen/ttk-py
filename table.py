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

sql_create_fcmults_table = """
    CREATE TABLE IF NOT EXISTS fcmults (
        id      TEXT PRIMARY KEY,
        unit    TEXT DEFAULT '',
        mult    REAL DEFAULT 0.0
    )
"""
fcmults_labels = ["ID", "Yksikkö", "Kerroin"]
fcmults_types = ["string", "string", "double:6,2"]
fcmults_keys = ["id", "unit", "mult"]

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
sql_create_predefs_table = """
    CREATE TABLE IF NOT EXISTS predefs (
        offer_id    TEXT NOT NULL,
        group_id    TEXT NOT NULL,
        id          TEXT NOT NULL,
        part        TEXT DEFAULT '',
        material    TEXT DEFAULT '',
        PRIMARY KEY (id, group_id, offer_id),
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
        id          TEXT NOT NULL,
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
        PRIMARY KEY (id, group_id, offer_id),
        FOREIGN KEY (offer_id) REFERENCES offers (id)
            ON DELETE CASCADE
            ON UPDATE CASCADE,
        FOREIGN KEY (group_id) REFERENCES groups (id)
            ON DELETE CASCADE
            ON UPDATE CASCADE
    );
"""
sql_create_products_table = """
    CREATE TABLE IF NOT EXISTS products (
        offer_id    TEXT NOT NULL,
        group_id    TEXT NOT NULL,
        id          TEXT NOT NULL
        code        TEXT DEFAULT '',
        desc        TEXT DEFAULT '',
        prod        TEXT DEFAULT '',
        count       INTEGER DEFAULT 1,
        inst_unit   TEXT DEFAULT '',
        PRIMARY KEY (id, group_id, offer_id),
        FOREIGN KEY (offer_id) REFERENCES offers (id)
            ON DELETE CASCADE
            ON UPDATE CASCADE,
        FOREIGN KEY (group_id) REFERENCES groups (id)
            ON DELETE CASCADE
            ON UPDATE CASCADE,
        FOREIGN KEY (inst_unit) REFERENCES fcmults (unit)
    )
"""
sql_count_units = """
    SELECT inst_unit, SUM(count), mult, SUM(count)*mult
    FROM products
    LEFT JOIN fcmults ON fcmults.unit = products.inst_unit
    GROUP BY inst_unit
"""
sql_insert_default = {
    "offers": """INSERT INTO offers (id) VALUES (?)""",
    "fcmults": """INSERT INTO fcmults (id) VALUES (?)""",
    "groups": """INSERT INTO groups (id, offer_id) VALUES (?, ?)""",
    "predefs": """INSERT INTO predefs (id, group_id, offer_id) VALUES (?, ?, ?)""",
    "materials": """INSERT INTO materials (id, group_id, offer_id) VALUES (?, ?, ?)""",
    "products": """INSERT INTO products (id, group_id, offer_id) VALUES (?, ?, ?)"""
}

sql_select_groups = """
    SELECT offer_id, name, id
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
sql_select_offer_page = """
    SELECT 
        name,
        client_firstname,
        client_lastname,
        client_company,
        client_phone,
        client_email,
        client_address,
        client_postcode,
        client_postarea,
        client_info
    FROM offers
    WHERE id=?
"""
offer_labels = [
        "ID",
        "Tarjouksen nimi",
        "Etunimi",
        "Sukunimi",
        "Yritys",
        "Puh.",
        "Sähköposti",
        "Lähiosoite",
        "Postinumero",
        "Postitoimipaikka",
        "Lisätiedot"
]
offer_keys = [
    "id",
    "name",
    "client_firstname",
    "client_lastname",
    "client_company",
    "client_phone",
    "client_email",
    "client_address",
    "client_postcode",
    "client_postarea",
    "client_info"
]
offer_types = ["string"] * len(offer_labels)

table_labels = {
    "offers.name": offer_labels[1],
    "offers.client": offer_labels[2:],
}
table_types = {
    "offers.name": offer_types[1],
    "offers.client": offer_types[2:]
}
table_keys = {
    "offers.name": offer_keys[1],
    "offers.client": offer_keys[2:]
}
sql_select_fcmults = """
    SELECT unit, mult
    FROM fcmults
    WHERE unit IN ({})
    ORDER BY unit DESC
"""
sql_update_one_offers = """
    UPDATE offers 
    SET {col} = ?
    WHERE id = ?
"""
sql_update_one_groups = """
    UPDATE groups
    SET {col} = ?
    WHERE id = ? AND offer_id = ?
"""
sql_update_one = {
    "offers": sql_update_one_offers,
    "groups": sql_update_one_groups
}
sql_insert = {
    "fcmults": """INSERT INTO fcmults (id, unit, mult) VALUES (?,?,?)"""
}

class OfferTables:
    con = None
    cur = None

    def __init__(self) -> None:
        """."""
        cur = self.create_connection("ttk.db")

        cur.execute("""DROP TABLE IF EXISTS offers;""")
        cur.execute("""DROP TABLE IF EXISTS groups;""")
        cur.execute("""DROP TABLE IF EXISTS fcmults;""")
        cur.execute("""DROP TABLE IF EXISTS clients;""")
        cur.execute("""DROP TABLE IF EXISTS predefs;""")
        cur.execute("""DROP TABLE IF EXISTS materials;""")
        self.con.commit()

        self.create_table(sql_create_offers_table)
        self.create_table(sql_create_groups_table)
        self.create_table(sql_create_predefs_table)
        self.create_table(sql_create_materials_table)
        self.create_table(sql_create_fcmults_table)
        

        # offer_id = self.insert_offer()
        # if offer_id is not None:
        #     self.insert_group(offer_id)
        #     self.insert_group(offer_id)
        #     self.insert_group(offer_id)

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

    def execute(self, sql, values=None):
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

    def get_unitcount(self,):
        """."""


    def get_offer_page(self, offer_id):
        """Return the relevant data for offer page as a list."""
        try:
            res = self.cur.execute(sql_select_offer_page, (offer_id,)).fetchone()
        except sqlite3.Error as e:
            print(e)
            return None

        print(res)
        return res

    def get_labels(self, key):
        """Return the list of labels matching get_offer_page return tuple indexes."""
        return table_labels[key]

    def get_types(self, key):
        """Return the list of types matching get_offer_page return tuple indexes."""
        return table_types[key]

    def get_treelist(self, offers: list):
        """Return a list of offer group tuples.

        offer: (offer_id, name), group: (offer_id, name, group_id) tuples in name order.

        Args:
        - offers (list): List of open offer id's.
        """
        treelist = []
        seq = ','.join(['?']*len(offers))
        offers = self.cur.execute(sql_select_offers_by_list.format(seq), offers).fetchall()
        for oid in offers:
            # print(f"get_treelist - type: {type(oid)}")
            groups = self.cur.execute(sql_select_groups, (oid[0],)).fetchall()
            treelist += ([oid] + groups)
        
        for item in treelist:
            print(item)
        return treelist

    def get_unit_count(self, offer_id):
        """Return the install unit count of products in the offer.
        
        Return (unit, count, mult)
        """
        self.execute(sql_count_units)

    def update_one(self, table, primary_key, name, col, value):
        """Update a value at given table.
        
        Args:
        - table (str): Name of the table.
        - primary_key (tuple): Tuple to match with tables primary key.
        - name (str): Name to match col to key.
        - col (int): Column index or None.
        - value (Any): New value.
        """
        key = table_keys[name] if col is None else table_keys[name][col]
        sql = sql_update_one[table].format(col=key)
        self.execute(sql, (value,) + primary_key)

    def update_one_offers(self, offer_id, name, col, value):
        """Update a value in offers table."""
        key = table_keys[name] if col is None else table_keys[name][col]
        sql = sql_update_one_offers.format(col=key)
        self.execute(sql, (value, offer_id))

    def update_one_groups(self, ids, name, col, value):
        """Update a value in groups table. (offer_id, group_id) = ids"""
        (offer_id, group_id) = ids
        pass
    
    def insert(self, name, ids):
        """."""
        oid = ObjectId()
        if self.execute(sql_insert[name], (oid,) + ids):
            return oid
        return None

    def insert_default(self, table, ids):
        """
        sql_insert_default = {
            "offers": INSERT INTO offers (id) VALUES (?),
            "groups": INSERT INTO groups (id, offer_id) VALUES (?, ?),
            "predefs": INSERT INTO predefs (id, group_id, offer_id) VALUES (?, ?, ?),
            "materials": INSERT INTO materials (id, group_id, offer_id) VALUES (?, ?, ?)
        """
        oid = ObjectId()
        if self.execute(sql_insert_default[table], (oid,) + ids):
            return oid
        return None

    def insert_offer(self):
        """Insert a new offer. Return id of inserted offer or None if not successful."""
        oid = str(ObjectId())
        if self.execute(sql_insert_default["offers"], (oid,)):
            return oid
        return None

    def insert_group(self, offer_id: str):
        """Insert a new group. Return id of inserted group or None if not successful."""
        oid = str(ObjectId())
        if self.execute(sql_insert_default["groups"], (oid, offer_id)):
            return oid
        return None


if __name__ == '__main__':

    db = OfferTables()
    db.close()

