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
import csv


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

def cond2str(condition):
    """Parse condition dict to a sql string.

    Return tuple with sql string and values for bindings.

    Parameters
    ----------
    condition : dict
        Search conditions in form {key: [op, val]}

    Returns
    -------
    tuple(str, list)
        (sql_conditions_string, value_list)
    """
    s = ""
    values = []
    for n, (key, val) in enumerate(condition.items()):
        s += key + " " + val[0] + " (?)"
        values.append(val[1])
        if n != len(condition) - 1:
            s += " AND "
    return (s, values)

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
pk_variables = ["key"]
fk_variables = []
keys_variables = ["key", "val"]
sql_create_table_columns = """
    CREATE TABLE IF NOT EXISTS columns (
        columns_id  INTEGER PRIMARY KEY,
        tablename   TEXT,
        key         TEXT,
        label       TEXT,
        type        TEXT,
        col_idx     INTEGER,
        width       INTEGER DEFAULT 55,
        is_unique   INTEGER DEFAULT 0,
        ro          INTEGER DEFAULT 0,
        visible     INTEGER DEFAULT 1,
        order       INTEGER DEFAULT 0,
        UNIQUE (tablename, key),
        UNIQUE (tablename, col_idx)
    )
"""
pk_columns = ["columns_id"]
fk_columns = []
keys_columns = [
    "columns_id",
    "tablename",
    "key",
    "label",
    "type",
    "col_idx",
    "width",
    "is_unique",
    "ro",
    "visible"
]
TABLE = 0
KEY = 1
LABEL = 2
TYPE = 3
INDEX = 4
WIDTH = 5
UNIQUE = 6
READ_ONLY = 7
VISIBLE = 7

sql_create_table_offers = """
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
pk_offers = ["offer_id"]
fk_offers = []
columns_offers = [
    ("offers", "offer_id", "ID", "string", 0, 45, 1, 1),
    ("offers", "name", "Tarjouksen nimi", "string", 1, 55, 0, 0),
    ("offers", "firstname", "Etunimi", "string", 2, 55, 0, 0),
    ("offers", "lastname", "Sukunimi", "string", 3, 55, 0, 0),
    ("offers", "company", "Yritys.", "string", 4, 55, 0, 0),
    ("offers", "phone", "Puh", "string", 5, 55, 0, 0),
    ("offers", "email", "Sähköposti", "string", 6, 55, 0, 0),
    ("offers", "address", "Lähiosoite", "string", 7, 55, 0, 0),
    ("offers", "postcode", "Postinumero", "string", 8, 55, 0, 0),
    ("offers", "postarea", "Postitoimipaikka", "string", 9, 55, 0, 0),
    ("offers", "info", "Lisätiedot", "string", 10, 55, 0, 0)
]
keys_offers = [
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
sql_create_table_offer_groups = """
    CREATE TABLE IF NOT EXISTS groups (
        group_id    INTEGER PRIMARY KEY,
        offer_id    INTEGER NOT NULL,
        name        TEXT,

        FOREIGN KEY (offer_id)
            REFERENCES offers (offer_id)
            ON DELETE CASCADE
            ON UPDATE CASCADE,
        UNIQUE (offer_id, name)
    )
"""
pk_groups = ["group_id"]
fk_groups = ["offer_id"]
keys_groups = ["group_id", "offer_id", "name"]
columns_groups = [
    ("groups", "group_id", "RyhmäID", "long", 0, 25, 1, 1, 0),
    ("groups", "offer_id", "TarjousID", "long", 0, 25, 1, 1, 0),
    ("groups", "name", "Ryhmän nimi", "string", 0, 80, 1, 0, 1)
]
sql_create_table_group_predefs = """
    CREATE TABLE IF NOT EXISTS group_predefs (
        gpd_id      INTEGER PRIMARY KEY,
        group_id    INTEGER NOT NULL,
        part        TEXT,
        material    TEXT,

        FOREIGN KEY (group_id)
            REFERENCES offer_groups (id)
            ON DELETE CASCADE
            ON UPDATE CASCADE,
        UNIQUE(group_id, part)
    )
"""
pk_gpd = ["gpd_id"]
fk_gpd = ["offer_id"]
keys_gpd = [
    "gpd_id",
    "group_id",
    "part",
    "material"
]
columns_gpd = [
    ("group_predefs", "gpd_id", "ID", "long", 0, 25, 1, 1),
    ("group_predefs", "group_id", "RyhmäID", "long", 1, 25, 1, 1),
    ("group_predefs", "part", "Osa", "string", 2, 60, 0, 0),
    ("group_predefs", "material", "Materiaali", "string", 3, 60, 0, 0)
]
sql_temp_group_predefs = """
    CREATE TEMP TABLE group_predefs (
        temp_id     INTEGER PRIMARY KEY,
        stack_id    INTEGER,

        gpd_id      INTEGER,
        group_id    INTEGER NOT NULL,
        part        TEXT,
        material    TEXT,

        UNIQUE(group_id, part)
    )
"""
sql_create_table_group_materials = """
    CREATE TABLE IF NOT EXISTS group_materials (
        gm_id       INTEGER PRIMARY KEY,
        group_id    INTEGER NOT NULL,
        category    TEXT,
        code        TEXT,
        desc        TEXT,
        prod        TEXT,
        thickness   INTEGER,
        is_stock    TEXT DEFAULT 'varasto',
        unit        TEXT,
        cost        REAL,
        add_cost    REAL DEFAULT 0.0,
        edg_cost    REAL DEFAULT 0.0,
        loss        REAL DEFAULT 0.0,
        discount    REAL DEFAULT 0.0,
        tot_cost    REAL
            GENERATED ALWAYS AS
            ((cost * (1 + loss) + edg_cost + add_cost) * (1 - discount))
            STORED,

        FOREIGN KEY (group_id) REFERENCES offer_groups (id)
            ON DELETE CASCADE
            ON UPDATE CASCADE,
        UNIQUE(group_id, code)
    )
"""
pk_gm = ["gm_id"]
fk_gm = ["group_id"]
keys_gm = [
    "gm_id",        
    "group_id",  
    "category",  
    "code",      
    "desc",      
    "prod",      
    "thickness", 
    "is_stock",  
    "unit",      
    "cost",      
    "add_cost",  
    "edg_cost",  
    "loss",      
    "discount",
    "tot_cost"
]
columns_gm = [
    ("group_materials", "gm_id", "MateriaaliID", "long", 0, 80, 1, 1),
    ("group_materials", "group_id", "RyhmäID", "long", 1, 80, 1, 1),
    ("group_materials", "category", "Tuoteryhmä", "string", 2, 60, 0, 0),
    ("group_materials", "code", "Koodi", "string", 3, 60, 0, 0),
    ("group_materials", "desc", "Kuvaus", "string", 4, 80, 0, 0),
    ("group_materials", "prod", "Valmistaja", "string", 5, 60, 0, 0),
    ("group_materials", "thickness", "Paksuus", "long", 6, 60, 0, 0),
    ("group_materials", "is_stock", "Onko varasto", "choice:varasto,tilaus,tarkista", 7, 45, 0, 0),
    ("group_materials", "unit", "Hintayksikkö", "choice:€/m2,€/kpl", 8, 60, 0, 0),
    ("group_materials", "cost", "Hinta", "double:6,2", 9, 60, 0, 0),
    ("group_materials", "add_cost", "Lisähinta", "double:6,2", 10, 60, 0, 0),
    ("group_materials", "edg_cost", "R.Nauhan hinta", "double:6,2", 11, 60, 0, 0),
    ("group_materials", "loss", "Hukka", "double:6,2", 12, 60, 0, 0),
    ("group_materials", "discount", "Alennus", "double:6,2", 13, 60, 0, 0),
    ("group_materials", "tot_cost", "Kokonaishinta", "double:6,2", 14, 60, 0, 1)
]
# select_omaterials = """SELECT {} FROM group_materials WHERE group_id=(?)""".format(",".join(omaterials_keys_select))
sql_create_table_group_products = """
    CREATE TABLE IF NOT EXISTS group_products (
        gp_id       INTEGER PRIMARY KEY,
        group_id    INTEGER NOT NULL,
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
            ON UPDATE CASCADE,
        UNIQUE(group_id, code)
    )
"""
pk_gp = ["gp_id"]
fk_gp = ["group_id"]
keys_gp = [
    "gp_id",      
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
    "work_time"
]
columns_gp = [
    ("group_products", "gp_id", "TuoteID", "long", 0, 80, 1, 1),
    ("group_products", "group_id", "RyhmäID", "long", 1, 80, 1, 1),
    ("group_products", "category", "Tuoteryhmä", "string", 2, 60, 0, 0),
    ("group_products", "code", "Koodi", "string", 3, 60, 0, 0),
    ("group_products", "count", "Määrä", "long", 4, 45, 0, 0),
    ("group_products", "desc", "Kuvaus", "string", 5, 80, 0, 0),
    ("group_products", "prod", "Valmistaja", "string", 6, 60, 0, 0),
    ("group_products", "inst_unit", "As.Yksikkö", "double:6,2", 7, 45, 0, 0),
    ("group_products", "width", "Leveys", "long", 8, 45, 0, 0),
    ("group_products", "height", "Korkeus", "long", 9, 45, 0, 0),
    ("group_products", "depth", "Syvyys", "long", 10, 45, 0, 0),
    ("group_products", "work_time", "Työaika", "double:6,2", 11, 45, 0, 0),
    ("group_products", "part_cost", "Osahinta", "double:6,2", 12, 45, 0, 1),
    ("group_products", "tot_cost", "Kokonaishinta", "double:6,2", 13, 45, 0, 1),
]
select_gp = """
    SELECT
        pr.gp_id,
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
    FROM group_products AS pr
    LEFT JOIN (
        SELECT pa.gp_id, SUM(pa.cost) AS part_cost
        FROM group_parts AS pa
        GROUP BY pa.gp_id) pa ON pr.id=pa.gp_id
    WHERE pr.group_id=(?)
    """
sql_create_table_group_parts = """
    CREATE TABLE IF NOT EXISTS group_parts (
        gpa_id      INTEGER PRIMARY KEY,
        gp_id       INTEGER NOT NULL,
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

        FOREIGN KEY (gp_id)
            REFERENCES group_products (id)
            ON DELETE CASCADE
            ON UPDATE CASCADE,
        UNIQUE(gp_id, part)
    )
"""
pk_gpa = ["gpa_id"]
fk_gpa = ["gp_id"]
columns_gpa = [
    ("group_parts", "gpa_id", "OsaID", "string", 0, 80, 1, 1),
    ("group_parts", "gp_id", "TuoteID", "string", 1, 80, 1, 1),
    ("group_parts", "part", "Osa", "string", 2, 60, 0, 0),
    ("group_parts", "code", "Koodi", "string", 3, 60, 0, 0),
    ("group_parts", "count", "Määrä", "long", 4, 45, 0, 0),
    ("group_parts", "desc", "Kuvaus", "string", 5, 80, 0, 0),
    ("group_parts", "use_predef", "Käytä esimääritystä", "bool", 6, 45, 0, 0),
    ("group_parts", "default_mat", "Oletus materiaali", "string", 7, 45, 0, 0),
    ("group_parts", "width", "Leveys", "long", 8, 45, 0, 1),
    ("group_parts", "length", "Pituus", "long", 9, 45, 0, 1),
    ("group_parts", "cost", "Hinta", "double:6,2", 10, 45, 0, 1),
    ("group_parts", "code_width", "Koodi Leveys", "string", 11, 120, 0, 0),
    ("group_parts", "code_length", "Koodi Pituus", "string", 12, 120, 0, 0),
    ("group_parts", "code_cost", "Koodi Hinta", "string", 13, 120, 0, 0),
    ("group_parts", "used_mat", "Käyt. Mat.", "string", 14, 55, 0, 1),
    ("group_parts", "m.thickness", "Paksuus", "long", 15, 35, 0, 1),
    ("group_parts", "m.tot_cost", "Mat. Hinta", "double:6,2", 16, 35, 0, 1),
    ("group_parts", "pr.width", "Tuote leveys", "long", 17, 35, 0, 1),
    ("group_parts", "pr.height", "Tuote korkeus", "long", 18, 35, 0, 1),
    ("group_parts", "pr.depth", "Tuote syvyys", "long", 19, 35, 0, 1),
    ("group_parts", "product_code", "Tuote Koodi", "string", 20, 35, 0, 1),
]
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
keys_gpa = [
    "gpa_id",          
    "gp_id",  
    "part",        
    "code",        
    "count",       
    "desc",        
    "use_predef",  
    "default_mat", 
    "width",       
    "length",      
    "cost",        
    "code_width",  
    "code_length", 
    "code_cost"
]
select_gpa = """
    SELECT
        pa.gpa_id,
        pa.gp_id,
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
        pr.depth,
        pr.code as product_code

    FROM group_parts pa
        INNER JOIN group_products pr
            ON pa.gp_id=pr.id

        LEFT JOIN group_predefs d
            ON pr.group_id=d.group_id AND pa.part=d.part

        LEFT JOIN group_materials m
            ON (
                CASE
                    WHEN pa.use_predef=0 THEN
                        pa.default_mat
                    ELSE
                        d.material
                    END
                ) = m.code

    WHERE pa.gp_id=(?)
"""
sql_create_table_materials = """
    CREATE TABLE IF NOT EXISTS materials (
        material_id INTEGER PRIMARY KEY,
        code        TEXT UNIQUE,
        category    TEXT,
        desc        TEXT,
        prod        TEXT,
        thickness   INTEGER,
        unit        TEXT,
        cost        REAL,
        add_cost    REAL,
        edg_cost    REAL,
        loss        REAL,
        discount    REAL
    )
"""
pk_materials = ["material_id"]
fk_materials = []
columns_mats = [
    ("materials", "material_id", "MateriaaliID", "long", 0, 60, 1, 1),
    ("materials", "code", "Koodi", "string", 1, 60, 0, 0),
    ("materials", "category", "Tuoteryhmä", "string", 2, 60, 0, 0),
    ("materials", "desc", "Kuvaus", "string", 3, 80, 0, 0),
    ("materials", "prod", "Valmistaja", "string", 4, 60, 0, 0),
    ("materials", "thickness", "Paksuus", "long", 5, 60, 0, 0),
    ("materials", "unit", "Hintayksikkö", "choice:€/m2,€/kpl", 6, 60, 0, 0),
    ("materials", "cost", "Hinta", "double:6,2", 7, 60, 0, 0),
    ("materials", "add_cost", "Lisähinta", "double:6,2", 8, 60, 0, 0),
    ("materials", "edg_cost", "R.Nauhan hinta", "double:6,2", 9, 60, 0, 0),
    ("materials", "loss", "Hukka", "double:6,2", 10, 60, 0, 0),
    ("materials", "discount", "Alennus", "double:6,2", 11, 60, 0, 0),
    ("materials", "is_stock", "Onko varasto", "choice:varasto,tilaus,tarkista", 12, 45, 0, 0)
]
keys_materials = [
    "material_id",
    "code",      
    "category",  
    "desc",      
    "prod",      
    "thickness", 
    "unit",      
    "cost",      
    "add_cost",  
    "edg_cost",  
    "loss",      
    "discount",
    "is_stock"
]

sql_create_table_products = """
    CREATE TABLE IF NOT EXISTS products (
        product_id  INTEGER PRIMARY KEY,
        code        TEXT UNIQUE,
        category    TEXT,
        desc        TEXT,
        prod        TEXT,
        inst_unit   TEXT,
        width       INTEGER,
        height      INTEGER,
        depth       INTEGER,
        work_time   REAL
    )
"""
pk_products = ["product_id"]
fk_products = []
columns_products = [
    ("products", "product_id", "TuoteID", "long", 0, 60, 0, 0),
    ("products", "code", "Koodi", "string", 1, 60, 0, 0),
    ("products", "category", "Tuoteryhmä", "string", 2, 60, 0, 0),
    ("products", "desc", "Kuvaus", "string", 3, 80, 0, 0),
    ("products", "prod", "Valmistaja", "string", 4, 60, 0, 0),
    ("products", "inst_unit", "As.Yksikkö", "double:6,2", 5, 45, 0, 0),
    ("products", "width", "Leveys", "long", 6, 45, 0, 0),
    ("products", "height", "Korkeus", "long", 7, 45, 0, 0),
    ("products", "depth", "Syvyys", "long", 8, 45, 0, 0),
    ("products", "work_time", "Työaika", "double:6,2", 9, 45, 0, 0)
]
keys_products = [
    "code",        
    "category",    
    "desc",        
    "prod",        
    "inst_unit",   
    "width",       
    "height",      
    "depth",       
    "work_time"
]
sql_create_table_parts = """
    CREATE TABLE IF NOT EXISTS parts (
        part_id         INTEGER PRIMARY KEY,
        product_id      INTEGER,
        part            TEXT,
        code            TEXT,
        count           INTEGER DEFAULT 1,
        desc            TEXT,
        default_mat     TEXT,
        code_width      TEXT,
        code_length     TEXT,
        code_cost       TEXT,

        UNIQUE (part, product_id),
        FOREIGN KEY (product_id)
            REFERENCES products (product_id)
            ON DELETE CASCADE
            ON UPDATE CASCADE
    )
"""
pk_parts = ["part_id"]
fk_parts = ["product_id"]
columns_parts = [
    ("parts", "part_id", "OsaID", "long", 0, 60, 0, 1),
    ("parts", "product_id", "TuoteID", "long", 1, 60, 0, 1),
    ("parts", "part", "Osa", "string", 2, 60, 0, 0),
    ("parts", "code", "Koodi", "string", 3, 60, 0, 0),
    ("parts", "count", "Määrä", "long", 4, 45, 0, 0),
    ("parts", "desc", "Kuvaus", "string", 5, 80, 0, 0),
    ("parts", "default_mat", "Oletus materiaali", "string", 6, 45, 0, 0),
    ("parts", "code_width", "Koodi Leveys", "string", 7, 120, 0, 0),
    ("parts", "code_length", "Koodi Pituus", "string", 8, 120, 0, 0),
    ("parts", "code_cost", "Koodi Hinta", "string", 9, 120, 0, 0)
]
keys_parts = [
    "part",
    "code",
    "product_code",
    "count",
    "desc",
    "default_mat",
    "code_width",
    "code_length",
    "code_cost"
]
sql_create_table = {
    "variables": sql_create_table_variables,
    "columns": sql_create_table_columns,
    "offers": sql_create_table_offers,
    "groups": sql_create_table_offer_groups,
    "group_predefs": sql_create_table_group_predefs,
    "group_materials": sql_create_table_group_materials,
    "group_products": sql_create_table_group_products,
    "group_parts": sql_create_table_group_parts,
    "materials": sql_create_table_materials,
    "products": sql_create_table_products,
    "parts": sql_create_table_parts
}
sql_insert_general = """INSERT{replace}INTO {table} ({columns}) VALUES ({qm})"""
sql_insert_fk = """INSERT INTO {table} ({fk}) VALUES (?)"""

sql_select_general = """SELECT {columns} FROM {table} WHERE {cond}"""
sql_update_general = """UPDATE {table} SET {key}=(?) WHERE {pk}=(?)"""
sql_delete_general = """DELETE FROM {table} WHERE {key}=(?)"""

primary_keys = {
    "offers": pk_offers,
    "groups": pk_groups,
    "group_predefs": pk_gpd,
    "group_materials": pk_gm,
    "group_products": pk_gp,
    "group_parts": pk_gpa,
    "materials": pk_materials,
    "products": pk_products,
    "parts": pk_parts,
    "columns": pk_columns,
    "variables": pk_variables
}
foreign_keys = {
    "offers": fk_offers,
    "groups": fk_groups,
    "group_predefs": fk_gpd,
    "group_materials": fk_gm,
    "group_products": fk_gp,
    "group_parts": fk_gpa,
    "materials": fk_materials,
    "products": fk_products,
    "parts": fk_parts,
    "columns": fk_columns,
    "variables": fk_variables
}
keys = {
    "offers": keys_offers,
    "groups": keys_groups,
    "group_predefs": keys_gpd,
    "group_materials": keys_gm,
    "group_products": keys_gp,
    "group_parts": keys_gpa,
    "materials": keys_materials,
    "products": keys_products,
    "parts": keys_parts,
    "columns": keys_columns,
    "variables": keys_variables
}
insert_keys = {
    "offers": keys_offers,
    "groups": keys_groups,
    "group_predefs": keys_gpd,
    "group_materials": keys_gm[:-1],
    "group_products": keys_gp,
    "group_parts": keys_gpa,
    "materials": keys_materials,
    "products": keys_products,
    "parts": keys_parts,
    "columns": keys_columns,
    "variables": keys_variables
}
database_tables = {
    "group_materials": "materials",
    "group_products": "products",
    "group_parts": "parts"
}
temp_tables = {
    "group_predefs": "temp_gpdefs",
    "group_materials": "temp_gmats",
    "group_products": "temp_gproducts",
    "group_parts": "temp_gparts"
}
# select_all = {
#     "offers": sql_select_general.format(
#         table="offers",
#         columns=", ".join(keys_groups)),
#     "groups": sql_select_general.format(
#         table="groups",
#         columns=", ".join(keys_groups)),
#     "group_predefs": sql_select_general.format(
#         table="group_predefs",
#         columns=", ".join(keys_gpd)),
#     "group_materials": sql_select_general.format(
#         table="group_materials",
#         columns=", ".join(keys_gm)),
#     "group_products": select_gp,
#     "group_parts": select_gpa,
#     "materials": sql_select_general.format(
#         table="materials",
#         columns=", ".join(keys_groups)),
#     "products": keys_products,
#     "parts": keys_parts,
#     "columns": keys_columns,
#     "variables": keys_variables
# }
# ****************************************************************
#  Get Treelist Queries
# ****************************************************************
sql_select_offernames_sorted = """
    SELECT name, offer_id FROM offers
    WHERE offer_id=?
"""
sql_select_groupnames_sorted = """
    SELECT name, offer_id, group_id FROM groups
    WHERE offer_id=?
    ORDER BY name ASC
"""

def get_pk_column(table: str) -> int:
    """Return the primary key column for table."""
    return keys[table].index(primary_keys[table][0])

def has_fk(table: str) -> bool:
    """Return True if the table requires a foreign key."""
    return len(foreign_keys[table]) > 0

class OfferTables:
    con = None
    cur = None

    table_setup = read_json("table.json")

    def __init__(self) -> None:
        """."""
        self.create_connection("ttk.db")
        # for table, sql in sql_create_table.items():
            # OfferTables.cur.execute("""DROP TABLE IF EXISTS {};""".format(table))
            # self.create_table(sql)
        self.create_table(sql_temp_group_materials)
        # tables = self.select("SELECT name FROM sqlite_master WHERE type=(?)", ("table",))
        # print(tables)
        # totcost = self.select("SELECT tot_cost FROM group_materials WHERE group_id=(?)", ("1",))
        # print(totcost)
        # cur.execute("""DROP TABLE IF EXISTS parts;""")
        # self.create_table(sql_create_table_parts)

        # self.insert("columns", insert_keys["columns"], columns_gm, True)
        # self.insert("columns", insert_keys["columns"], columns_gp, True)
        # self.insert("columns", insert_keys["columns"], columns_gpa, True)
        # self.insert("columns", insert_keys["columns"], columns_gpd, True)
        # self.insert("columns", insert_keys["columns"], columns_parts, True, True)
        # self.insert("columns", insert_keys["columns"], columns_mats, True, True)
        # self.insert("columns", insert_keys["columns"], columns_products, True, True)
        # self.insert("columns", insert_keys["columns"], columns_offers, True, True)
        self.con.commit()

    def has_database_table(self, table):
        """Return true if the table has a related database table."""
        return table in database_tables

    def column_count(self, table):
        """Return the number of columns defined for given table in 'columns' table."""
        return self.select("SELECT COUNT(*) FROM columns WHERE tablename=(?)", (table,))[0][0]

    def get_col_order(self, table) -> list:
        """Return a list of column orders in table."""
        sql = """
            SELECT col_order, col_idx FROM columns WHERE tablename=(?) ORDER BY col_order ASC
        """
        order = self.select(sql, (table,))
        return [c[1] for c in order]

    def get_read_only(self, table) -> list:
        """Return a list of read only columns."""
        sql = """
            SELECT col_idx FROM columns WHERE tablename=(?) AND ro=(?)
        """
        rolist = self.select(sql, (table, 1))
        return [row[0] for row in rolist]

    def set_column_value(self, table: str, key: str, col: int, value: int):
        """Set the value of a column in columns table."""
        sql = """
            UPDATE columns SET {}=(?) WHERE col_idx=(?) AND tablename=(?)
        """.format(key)
        return self.update(sql, (value, col, table))

    def set_column_values(self, key: str, values: list):
        """Set the values of a column in columns table.
        
        values = [(value, col, table), ...]
        """
        sql = """
            UPDATE columns SET {}=(?) WHERE col_idx=(?) AND tablename=(?)
        """.format(key)
        return self.update(sql, values, True)

    def get_column_value(self, table: str, key: str, col: int):
        """Return value from columns table at key."""
        sql = """
            SELECT {}
            FROM columns
            WHERE tablename=(?) AND col_idx=(?)""".format(key)
        return self.select(sql, (table, col))[0][0]

    def delete_row(self, table: str, pk: int) -> bool:
        """Delete a row matching given primary key in table."""
        sql = """
            DELETE FROM {} WHERE {}=(?)
        """.format(table, primary_keys[table][0])
        return self.update(sql, (pk,))

    def update_cell(self, table: str, col: int, pk_value: int, value) -> bool:
        """Update a value in the table.

        Return True on success.
        """
        pk = primary_keys[table]
        if len(pk) != 1:
            print("OfferTables.update_cell update of table with multiple " +
                  "primary keys is not supported. Tried to update table: '{}'".format(table)
            )
            return False
        sql = """UPDATE {} SET {}=(?) WHERE {}=(?)""".format(
            table, keys[table][col], pk[0]
        )
        return self.update(sql, (value, pk_value))

    def insert_with_fk(self, table: str, fk_value: int) -> int:
        """Insert a new row with possible foreign key.

        Return inserted row id if successful.
        """
        sql_ins = """INSERT INTO {} {}"""
        sql_fk = """({}) VALUES (?)"""
        if fk_value is None:
            sql = sql_ins.format(table, "DEFAULT VALUES")
        else:
            sql = sql_ins.format(table, sql_fk.format(foreign_keys[table][0]))

        try:
            if fk_value is None:
                self.cur.execute(sql)
            else:
                self.cur.execute(sql, (fk_value,))
            self.con.commit()
        except (sqlite3.Error, ValueError) as e:
            print("OfferTables.insert_with_fk\n\t{}".format(e))
            print("\tsql: {}".format(sql))
            print("\ttable: {}".format(table))
            print("\tfk_value: {}".format(fk_value))
            return None

        return self.cur.lastrowid

    def insert_rows(self, table: str, data: list) -> int:
        """Insert a row with given values."""
        values = []
        keys = []
        ins_keys = insert_keys[table][1:]
        # print(ins_keys)
        # print(rowdata)
        # for col, key in enumerate(insert_keys[table]):
        #     # key = self.get_column_value(table, "key", col)
        #     if key in ins_keys:
        #         # values.append(rowdata[col])
        #         keys.append(key)
        for dr in data:
            values.append(dr[1:len(ins_keys)+1])
        return self.insert(table, ins_keys, values, True)

    def delete_with_fk(self, table, value):
        """Delete all rows with a foreign key."""
        sql = """
            DELETE FROM {t} WHERE group_id=(?)
        """.format(t=table)
        self.update(sql, (value,))

    def select_with(self, table, fk_value=None, condition: dict=None):
        """Return all results with fkvalue or condition from table."""
        if table == "group_materials":
            columns = ", ".join(keys[table])
            # columns = "*"
            fk = foreign_keys[table][0]
            # sql = sql_select_general

        if fk_value is not None and condition is None:
            (cond_str, values) = cond2str({fk: ["=", fk_value]})
        elif condition is not None and fk_value is None:
            (cond_str, values) = cond2str(condition)
        elif condition is None and fk_value is None:
            cond_str = "1"
            values = []
        else:
            condition.update({fk: ["=", fk_value]})
            (cond_str, values) = cond2str(condition)
        pk = primary_keys[table][0]
        cond_str += " ORDER BY {} ASC".format(pk)
        sql = sql_select_general.format(columns=columns, table=table, cond=cond_str)
        data = self.select(sql, values)
        # print(sql)
        # print(values)
        # print(data)
        return data

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

    def insert(self, table: str, columns: Iterable, values: Iterable, many: bool=False, replace: bool=False):
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
        replace : bool
            True if this should replace existing entry.

        Returns
        -------
        bool
            True if successful, False otherwise. Prints error to console.
        """
        cols = ','.join(columns)
        qms = ','.join(['?'] * len(columns))
        replace_str = " OR REPLACE " if replace else " "
        sql = sql_insert_general.format(replace=replace_str, table=table, columns=cols, qm=qms)
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
            conditions += col + " " + operator + " (?)"
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
        except (sqlite3.Error, ValueError) as e:
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

    def get_with_conditions(self, table, keys, conditions):
        """Return rows found with given conditions.

        Parameters
        ----------
        table : str
            Name of the table.
        keys : Iterable
            List of column keys to get.
        conditions : dict
            Condtions in format: {key: [operator, value]}
        """
        values = []
        s = ""
        for n, (key, val) in enumerate(conditions.items()):
            s += key + " " + val[0] + " (?)"
            values.append(val[1])
            if n != len(conditions) - 1:
                s += " AND "
        sql = sql_select_general.format(columns=','.join(keys), table=table, cond=s)
        print(sql)
        return self.select(sql, values)

    # def get_omaterials(self, group_id: str):
    #     try:
    #         self.cur.execute(select_omaterials, (group_id,))
    #         self.con.commit()
    #     except sqlite3.Error as e:
    #         print("OfferTables.get_omaterials\n\t{}".format(e))
    #         return []

    #     return self.cur.fetchall()

    # def get_oproducts(self, group_id: str):
    #     self.update_parts(group_id)
    #     try:
    #         self.cur.execute(select_oproducts, (group_id,))
    #         self.con.commit()
    #     except sqlite3.Error as e:
    #         print("OfferTables.get_oproducts\n\t{}".format(e))
    #         return []
    #     # print("select oproducts")
    #     return self.cur.fetchall()

    def select(self, sql, values):
        """General function for sql that returns values."""
        try:
            self.cur.execute(sql, values)
            self.con.commit()
        except sqlite3.Error as e:
            print("OfferTables.select\n\tsql: {}\n\t{}".format(sql, e))
            return []

        return self.cur.fetchall()

    def update(self, sql, values, many=False):
        """General function for sql that does not return values."""
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
            UPDATE group_parts
            SET width = (?),
                length = (?),
                cost = (?)

            WHERE gpa_id = (?)
        """
        select_oproduct_ids = """
            SELECT gp_id
            FROM group_products
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

    # def get_opredefs(self, group_id: str):
    #     try:
    #         self.cur.execute(select_gpd, (group_id,))
    #         self.con.commit()
    #     except sqlite3.Error as e:
    #         print("OfferTables.get_oparts\n\t{}".format(e))
    #         return []

    #     return self.cur.fetchall()

    # def get_parts(self, keys, product_code: str):
    #     """Return the parts with given product code."""
    #     sql = """SELECT {} FROM parts WHERE product_code=(?)""".format(",".join(keys))
    #     return self.select(sql, (product_code,))

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

    # def get_column_setup(self, table, keys):
    #     """Return a dictionary with column setup for keys from table."""
    #     cols = self.table_setup["columns"][table]
    #     return {k: cols[k] for k in keys}

    # def get_display_setup(self, display_key):
    #     """Return the display setup."""
    #     return self.table_setup["display"][display_key]

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

    sql_delete_general = """DELETE FROM {table} WHERE {match}"""
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
        match = ""
        for col in match_columns:
            match += col + "=(?)"
            if col != match_columns[-1]:
                match += " AND "
        
        sql = self.sql_delete_general.format(
            table=table,
            match=match
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
        """Return list booleans signifying visibility of the columns.

        Parameters
        ----------
        table : str
            Name of table.
        """
        sql = """
            SELECT col_idx, visible
            FROM columns
            WHERE tablename = (?)
            ORDER BY col_idx ASC
        """
        data = self.select(sql, (table,))
        return [False if r[1] == 0 else True for r in data]

    def copy_parts(self, table: str, old_id: str, new_id: str):
        """Copy parts of given product id to a new product id."""
        if table == "group_parts":
            keys = keys_gpa
            mcol = "gp_id"
            replace_id = True
        elif table == "parts":
            keys = keys_parts
            mcol = "product_id"
            replace_id = False
        else:
            print("OfferTables.copy_oparts - Invalid table '{}'".format(table))
            return False
        sql_select = """
            SELECT {}
            FROM {}
            WHERE {} = (?)
        """
        sql_insert = """
            INSERT OR REPLACE INTO {} ({}) VALUES ({})
        """

        keystr = ", ".join(keys)
        sql = sql_select.format(keystr, table, mcol)
        sel_values = (old_id,)

        data = self.select(sql, sel_values)
        ins_values = []
        for row in data:
            newrow = list(row)
            if replace_id:
                newrow[0] = str(ObjectId())
            idx = keys.index(mcol)
            newrow[idx] = new_id
            ins_values.append(newrow)
            # print(newrow)

        sql = sql_insert.format(table, keystr, ",".join(["(?)"] * len(keys)))
        return self.update(sql, ins_values, True)


if __name__ == '__main__':
    db = OfferTables()
    db.close()

