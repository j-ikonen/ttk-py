""" The superclass for database classes inherit.

Use Variables and VarID classes to get and set values from variables table.
Use connect function to create a sqlite3 connection object required by
tables. Catalogue tables work as a local database for now.
Could be implemented to connect to remote at a later time.

TODO: Add a paste_row method to SQLTableBase that sets unique columns to None and
inserts.
"""
import sqlite3
from decimal import Decimal
# from asteval import Interpreter

import db.dbtypes as dbt
from db.super import SQLTableBase
from db.offer import OffersTable
from db.group import GroupsTable
from db.predef import GroupPredefsTable
from db.material import GroupMaterialsTable
from db.product import GroupProductsTable
from db.part import GroupPartsTable
from db.vars import VarID


def connect(
    db_name: str,
    fk_on: bool=True,
    cb_trace: bool=False,
    print_err: bool=False
) -> sqlite3.Connection:
    """Create the connection to SQL database.

    Custom types must be declared in data queries to get
    the correct type instead of bytes.
        SELECT column_name AS 'column_name [pydecimal]' FROM table

    Do adapter/converter registering for custom types:
        pydecimal
    Create functions:
        dec_add, dec_sub, dec_mul, dec_div, material_cost, product_cost
    Create aggregates:
        dec_sum
    Create tables for variables and columns if they do not exist.
    Delete and create a new undolog table.

    Parameters
    ----------
    db_name : str
        Name of the database. Use ':memory:' to start an in memory database.
    fk_on : bool, optional
        Set False to turn off foreign keys. Default True
    cb_trace : bool, optional
        Set True to enable callback tracebacks.
        Use for debugging custom SQLite functions and types. Default False.
    print_err : bool, optional
        Set True to print error messages to console.

    Returns
    -------
    sqlite3.Connection
        The connection object needed to init the table classes.
    """
    # Converter and adapter for Decimal type.
    sqlite3.register_adapter(Decimal, dbt.adapter_decimal)
    sqlite3.register_converter("pydecimal", dbt.converter_decimal)

    # Custom type is parsed from table declaration.
    con = sqlite3.connect(db_name, detect_types=sqlite3.PARSE_COLNAMES)
    if fk_on:
        con.execute("PRAGMA foreign_keys = ON")
    else:
        con.execute("PRAGMA foreign_keys = OFF")

    if cb_trace:
        sqlite3.enable_callback_tracebacks(True)

    SQLTableBase.print_errors = print_err

    # Create functions to handle math in queries for custom types.
    con.create_function("dec_add", -1, dbt.decimal_add, deterministic=True)
    con.create_function("dec_sub", 2, dbt.decimal_sub, deterministic=True)
    con.create_function("dec_mul", 2, dbt.decimal_mul, deterministic=True)
    con.create_function("dec_div", 2, dbt.decimal_div, deterministic=True)
    con.create_function("material_cost", 5, dbt.material_cost, deterministic=True)
    con.create_function("product_cost", 3, dbt.product_cost, deterministic=True)
    con.create_aggregate("dec_sum", 1, dbt.DecimalSum)

    try:
        con.execute("DROP TABLE undolog")
    except sqlite3.Error:
        pass

    con.execute("""
        CREATE TABLE undolog (
            seq INTEGER PRIMARY KEY AUTOINCREMENT,
            fk INTEGER,
            tablename TEXT,
            sql TEXT
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS columns (
            columns_id  INTEGER PRIMARY KEY,
            tablename   TEXT,
            key         TEXT,
            label       TEXT,
            type        TEXT,
            col_idx     INTEGER,
            col_order   INTEGER,
            width       INTEGER DEFAULT 55,
            ro          INTEGER DEFAULT 0,
            visible     INTEGER DEFAULT 1,
            UNIQUE (tablename, key),
            UNIQUE (tablename, col_idx)
        )"""
    )
    con.execute("""
        CREATE INDEX IF NOT EXISTS idx_columns
        ON columns(tablename, col_idx)"""
    )
    con.execute("""
        CREATE TABLE IF NOT EXISTS variables (
            variable_id     INTEGER PRIMARY KEY,
            label           TEXT,
            value_decimal   PYDECIMAL,
            value_int       INTEGER,
            value_txt       TEXT,

            CHECK(
                (value_decimal IS NOT NULL AND value_int IS NULL AND value_txt IS NULL)
                OR
                (value_decimal IS NULL AND value_int IS NOT NULL AND value_txt IS NULL)
                OR
                (value_decimal IS NULL AND value_int IS NULL AND value_txt IS NOT NULL)
            )
        )"""
    )
    try:
        con.executemany("""
            INSERT INTO variables(
                variable_id,
                label,
                value_decimal,
                value_int,
                value_txt
            ) VALUES(?,?,?,?,?)
            """,
            [
                [VarID.WORK_COST, "Työn hinta", Decimal('0.0'), None, None],
                [VarID.INSTALL_UNIT_MULT, "Asennusyksikön kerroin", Decimal('0.0'), None, None]
            ]
        )
    except sqlite3.IntegrityError:
        pass

    con.commit()
    return con


class Database:
    """Handler for database table classes."""
    def __init__(self, name=":memory:", fk_on=True, cb_trace=False, print_err=False):
        self.open_offers = []

        self.con = connect(name, fk_on, cb_trace, print_err)
        self.offers = OffersTable(self.con)
        self.groups = GroupsTable(self.con)
        self.group_predefs = GroupPredefsTable(self.con)
        self.group_materials = GroupMaterialsTable(self.con)
        self.group_products = GroupProductsTable(self.con)
        self.group_parts = GroupPartsTable(self.con)

        self.materials = self.group_materials.get_catalogue_table()
        self.products = self.group_products.get_catalogue_table()
        self.parts = self.group_parts.get_catalogue_table()

        self.offers.create()
        self.groups.create()
        self.group_predefs.create()
        self.group_materials.create()
        self.group_products.create()
        self.group_parts.create()

        self.search_tables = {
            "offers": self.offers,
            "groups": self.groups,
            "materials": self.materials,
            "products": self.products,
            "parts": self.parts
        }
        self.catalogue_tables = {
            "materials": self.group_materials,
            "products": self.group_products,
            "parts": self.group_parts,
        }

    def open_offer(self, offer_id):
        """Open the given offer."""
        self.open_offers.append(offer_id)

    def get_cattable(self, key: str):
        """Return the catalogue table"""
        return self.catalogue_tables[key]

    def get_table(self, key: str):
        """Return the table.

        Parameters
        ----------
        key (str): String key for the table, one of:
            offers, groups, materials, products, parts
        """
        return self.search_tables[key]

    def get_table_labels(self):
        """Return the table labels"""
        return [
            "Tarjoukset",
            "Ryhmät",
            "Materiaalit",
            "Tuotteet",
            "Osat"
        ]

    def get_table_keys(self):
        """Return the table keys."""
        return [
            "offers",
            "groups",
            "materials",
            "products",
            "parts"
        ]

    def get_columns_search(self, name):
        """."""
        try:
            table = self.search_tables[name]
        except KeyError as err:
            print(f"No such table is defined for search: {err}")
            raise err
        return table.get_column_search()

    def get_group_costs(self, offer_id: int) -> list:
        """Return the group ids, names and costs."""
        # groups = self.groups.select(offer_id)   # [(group_id, offer_id, name), ...]
        costs = self.group_products.execute_dql(
            """
            SELECT
                group_id,
                name,
                dec_sum(
                    product_cost(
                        a.part_cost,
                        p.work_time,
                        (
                            SELECT value_decimal
                            FROM variables
                            WHERE variable_id=0
                        )
                    )
                ) AS 'tot_cost [PYDECIMAL]'
            FROM
                groups AS g
                LEFT JOIN group_products as p USING(group_id)
                LEFT JOIN (
                    SELECT a.group_product_id, dec_sum(a.cost) AS part_cost
                    FROM group_parts AS a
                    GROUP BY a.group_product_id
                ) a USING(group_product_id)
            WHERE offer_id = (?)
            GROUP BY group_id
            """,
            (offer_id,)
        )
        # print(costs)
        return costs

    def copy_group(self, _group_id: int, _offer_id: int):
        """Copy given group and it's content to an offer."""
        print("UNIMPLEMENTED")

    def get_group_labels(self, offer_id: int):
        """Return a list of (group_id, name) of the given offer."""
        sql = """
            SELECT group_id, name
            FROM groups
            WHERE offer_id = (?)
            ORDER BY group_id ASC
        """
        return self.groups.execute_dql(sql, (offer_id,))

    def get_open_offer_labels(self):
        """Return a list of (offer_id, name) of the open offers."""
        inlist = ",".join(["?"] * len(self.open_offers))
        sql = f"""
            SELECT offer_id, name
            FROM offers
            WHERE offer_id in ({inlist})
            ORDER BY offer_id ASC
        """
        return self.offers.execute_dql(sql, self.open_offers)
