"""Classes for handling local database operations.

Use Variables and VarID classes to get and set values from variables table.
Use connect function to create a sqlite3 connection object required by
tables. Catalogue tables work as a local database for now.
Could be implemented to connect to remote at a later time.

TODO:
    Setup the grid to handle Decimal types.
"""
import sqlite3
from decimal import Decimal
from asteval import Interpreter


class Database:
    def __init__(self, name=":memory:", fk_on=True, cb_trace=False, print_err=False):
        """Handler for database table classes."""
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
            "materials": self.materials,
            "products": self.products,
            "parts": self.parts
        }

    def get_table_labels(self):
        return [
            "Tarjoukset",
            "Materiaalit",
            "Tuotteet",
            "Osat"
        ]

    def get_table_keys(self):
        return [
            "offers",
            "materials",
            "products",
            "parts"
        ]

    def get_columns_search(self, name):
        try:
            table = self.search_tables[name]
        except KeyError as e:
            print("No such table is defined for search: {}".format(e))
            raise e
        return table.get_column_search()


class VarID:
    """Use as primary key to find the variables in local database table 'variables'."""
    WORK_COST = 0
    INSTALL_UNIT_MULT = 1

    COL = {
        WORK_COST: "value_decimal",
        INSTALL_UNIT_MULT: "value_decimal"
    }

    @classmethod
    def col(cls, id, set=False) -> str:
        """Return the column name used by given 'id'.

        Parameters
        ----------
        id : int
            ID to row of a variable.
        set : bool, default: False
            Set to True to return column name for UPDATE statement instead of
            SELECT statement.
        """
        col_name = cls.COL[id]
        if set:
            return col_name
        else:
            if col_name == "value_decimal":
                col_name = "value_decimal AS 'value_decimal [pydecimal]'"
            return col_name


class Variables:
    """Get and set the local variables table values."""
    PRINT_ERRORS = False

    @classmethod
    def print_errors(cls, value=True):
        cls.PRINT_ERRORS = value

    @classmethod
    def get(cls, con: sqlite3.Connection, var_id: VarID):
        """Return the value for var_id."""
        col_name = VarID.col(var_id)
        sql = """
            SELECT {c}
            FROM variables
            WHERE variable_id = (?)
        """.format(c=col_name)
        try:
            with con:
                cur = con.execute(sql, (var_id,))
                return cur.fetchone()[0]

        except sqlite3.Error as e:
            if cls.print_errors:
                print("\n{}: {}".format(type(e), e))
                print("In SQLTableBase.execute_dql")
                print("Error with sql: {}".format(sql))
                print("using values: {}".format((var_id,)))
            return None

    @classmethod
    def set(cls, con: sqlite3.Connection, var_id: VarID, value):
        """Set the value for var_id."""
        col_name = VarID.col(var_id, True)
        sql = """
            UPDATE variables
            SET {c}=(?)
            WHERE variable_id=(?)
        """.format(c=col_name)
        values = (value, var_id)
        try:
            with con:
                con.execute(sql, values)
                return True

        except sqlite3.Error as e:
            if cls.print_errors:
                print("\n{}: {}".format(type(e), e))
                print("In SQLTableBase.execute_dql")
                print("Error with sql: {}".format(sql))
                print("using values: {}".format(values))
            return False


class DecimalSum:
    """Custom AggregateClass for sqlite3 to sum pydecimal columns."""
    def __init__(self):
        self.sum = Decimal('0.00')
    
    def step(self, value):
        self.sum += converter_decimal(value)
    
    def finalize(self):
        return adapter_decimal(self.sum)

def adapter_decimal(decimal: Decimal):
    """Adapt a decimal to bytes for insert into sqlite table."""
    if decimal is None:
        decimal = Decimal('0.00')
    return str(decimal).encode('ascii')

def converter_decimal(decimal: bytes):
    """Convert bytes from sqlite to Decimal."""
    try:
        return Decimal(decimal.decode('ascii'))
    except AttributeError:
        return Decimal('0.00')

def decimal_add(*args):
    """Define custom function for adding Decimal arguments in sqlite queries."""
    sum = Decimal('0.00')
    for value in args:
        sum += converter_decimal(value)
    return adapter_decimal(sum)

def decimal_sub(a, b):
    """Define custom function for substracting Decimal arguments in sqlite queries."""
    return adapter_decimal(converter_decimal(a) - converter_decimal(b))

def decimal_mul(a, b):
    """Define custom function for multiplying Decimal arguments in sqlite queries."""
    return adapter_decimal(converter_decimal(a) * converter_decimal(b))

def decimal_div(a, b):
    """Define custom function for dividing Decimal arguments in sqlite queries."""
    return adapter_decimal(converter_decimal(a) / converter_decimal(b))

def material_cost(cost, add, edg, loss, discount):
    """Return the total cost per unit for the material row."""
    a = converter_decimal(cost) * (Decimal('1.00') + converter_decimal(loss))
    b = (Decimal('1.00') - converter_decimal(discount))
    c = converter_decimal(edg)
    d = converter_decimal(add)
    return adapter_decimal((a + d + c) * b)

def product_cost(part_cost, work_time, work_cost):
    """Return the products cost."""
    a = converter_decimal(part_cost)
    b = converter_decimal(work_time)
    c = converter_decimal(work_cost)
    return adapter_decimal(a + (b * c))

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
    sqlite3.register_adapter(Decimal, adapter_decimal)
    sqlite3.register_converter("pydecimal", converter_decimal)

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
    con.create_function("dec_add", -1, decimal_add, deterministic=True)
    con.create_function("dec_sub", 2, decimal_sub, deterministic=True)
    con.create_function("dec_mul", 2, decimal_mul, deterministic=True)
    con.create_function("dec_div", 2, decimal_div, deterministic=True)
    con.create_function("material_cost", 5, material_cost, deterministic=True)
    con.create_function("product_cost", 3, product_cost, deterministic=True)
    con.create_aggregate("dec_sum", 1, DecimalSum)

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
    con.commit()
    return con


class SQLTableBase:

    TABLENAME = 0
    KEY = 1
    LABEL = 2
    TYPE = 3
    COL_IDX = 4
    ORDER = 5
    WIDTH = 6
    RO = 7
    VISIBLE = 8

    setup_done = False
    print_errors = False
    _undo = {}
    _undo['freeze'] = -1
    _undo['active'] = True
    _undo['pending'] = []
    _undo['firstlog'] = {}  # {fk: seq}

    def __init__(self, connection):
        self.con: sqlite3.Connection = connection
        self.columns_table_keys = [
            "columns_id", 
            "tablename",  
            "key",        
            "label",      
            "type",       
            "col_idx",    
            "col_order",  
            "width",      
            "ro",         
            "visible"
        ]
        self.variables_table_keys = [
            "variable_id", "label", "value_decimal", "value_int", "value_txt"
        ]
        self.undostack = {}     # {foreign_key: [(begin rowid, end rowid), ...], ...}
        self.redostack = {}

        self.name = None
        self.sql_create_table = None
        self.indexes = None
        self.primary_key = None
        self.foreign_key = None
        self.read_only = None
        self.default_columns = None
        self.table_keys = None

    def create(self):
        """Create the table and it's indexes."""
        
        # print("Existing columns entries: ")
        # coldata = self.con.execute(
        #     "SELECT * FROM columns"
        # )
        # for row in coldata:
        #     print(row)
        
        try:
            with self.con:
                # Create table and indexes.
                self.con.execute(self.sql_create_table)
                for idx in self.indexes:
                    self.con.execute(idx)

                try:
                    self.create_undo_triggers()
                except sqlite3.OperationalError as e:
                    print("Could not create undo triggers: {}".format(e))

                # Insert default columns values if required.
                count = self.con.execute(
                    """SELECT COUNT(*) FROM columns WHERE tablename=(?)""",
                    (self.name,)
                )
                if count != len(self.default_columns):
                    for n, col in enumerate(self.default_columns):
                        ro = 1 if col[self.KEY] in self.read_only else 0
                        try:
                            self.con.execute(
                                "INSERT INTO columns ({k}) VALUES (?,?,?,?,?,?,?,?,?)".format(
                                    k=",".join(self.columns_table_keys[1:])
                                ),
                                list(col) + [n, n, 60, ro, 1]
                            )
                        except sqlite3.IntegrityError:
                            pass

        except sqlite3.OperationalError as e:
            if SQLTableBase.print_errors:
                print("\nsqlite3.OperationalError: {}".format(e))
                print("Could not create table: {}".format(self.name))

    def execute_dml(self, sql: str, values: list=None, many: bool=False, rowid: bool=False) -> bool:
        """Run execute on a data manipulation language string.

        Used for SQL INSERT, REPLACE, UPDATE and DELETE statements.

        Parameters
        ----------
        sql : str
            SQL command string.
        values : list, optional
            Bound values used in the command, by default None. If 'many' is set True
            this must be a list of the values used in each execution.
        many : bool, optional
            Set True if the SQL command is to be executed multiple times.
        rowid : bool, optional
            If set True, return last inserted rowid instead of bool.

        Returns
        -------
        bool
            True on success. False on Errors.
        int
            Last rowid if 'rowid' is set as True.
        """
        try:
            with self.con:
                if many:
                    if values is None:
                        cur = self.con.executemany(sql)
                    else:
                        cur = self.con.executemany(sql, values)
                else:
                    if values is None:
                        cur = self.con.execute(sql)
                    else:
                        cur = self.con.execute(sql, values)

        except sqlite3.Error as e:
            if SQLTableBase.print_errors:
                print("\n{}: {}".format(type(e), e.args[0]))
                print("In SQLTableBase.execute_dml")
                print("Error with sql: {}".format(sql))
                print("using values: {}".format(values))
            return False

        if rowid:
            return cur.lastrowid
        else:
            return True

    def execute_dql(self, sql: str, values: list=None, cursor: bool=False) -> list:
        """Execute a Data Query Language command.
        
        Used for SQL SELECT statements.

        Parameters
        ----------
        sql : str
            SQL statement.
        values : list, optional
            Bound values used in the SQL statement, by default None
        cursor : bool, optional
            Set True to return sqlite3.cursor object instead of a list of results,
            by default False

        Returns
        -------
        list | sqlite3.Cursor
            Return a list of results. On Error return None. If 'cursor' is set True
            returns sqlite3.Cursor object.
        """
        try:
            with self.con:
                if values is None:
                    cur = self.con.execute(sql)
                else:
                    cur = self.con.execute(sql, values)

        except sqlite3.Error as e:
            if SQLTableBase.print_errors:
                print("\n{}: {}".format(type(e), e))
                print("In SQLTableBase.execute_dql")
                print("Error with sql: {}".format(sql))
                print("using values: {}".format(values))
            return None

        if cursor:
            return cur
        else:
            return cur.fetchall()

    def insert(self, values: list, many=False, include_rowid=False, upsert=False):
        """Insert one or many values to database.

        Parameters
        ----------
        values : list
            A list or values or a list of rows.
        many : bool
            Set True if inserting multiple rows in one statement.
        include_rowid : bool
            Set True if rowid / primary key is included in values.

        Returns
        -------
        int
            Last rowid.
        bool
            If many was set True, return true on success and False on Errors.
        """
        keys = self.get_insert_keys(include_rowid)
        keys_str = ",".join(keys)
        binds = ",".join(["?"] * len(keys))

        if upsert:
            rep_str = " OR REPLACE "
        else:
            rep_str = " "
        sql = "INSERT{u}INTO {t}({k}) VALUES ({b})".format(
            u=rep_str, t=self.name, k=keys_str, b=binds
        )

        result = self.execute_dml(sql, values, many, not many)
        return result

    def insert_empty(self, fk: int=None) -> int:
        """Insert an empty row.

        Parameters
        ----------
        fk : int
            A foreign key or None if the table uses no foreign key.

        Returns
        -------
        int
            Last rowid. On error return None.
        """
        sql_ins = "INSERT INTO {t}"
        sql_val = "({k}) VALUES (?)"
        if fk is None:
            sql = sql_ins.format(t=self.name) + " DEFAULT VALUES"
            values = None
        else:
            sql = sql_ins.format(t=self.name) + sql_val.format(k=self.foreign_key)
            values = (fk,)
        rowid = self.execute_dml(sql, values, rowid=True)

        return rowid

    def update(self, pk: int, col: int, value) -> bool:
        """Update a single value in the table.

        Parameters
        ----------
        pk : int
            The primary key used to find the row.
        col : int
            The column index for the value to be updated.
        value : Any
            The new value.

        Returns
        -------
        bool
            True on success. False on Error.
        """
        key = self.col2key(col)
        sql = "UPDATE {t} SET {k}=(?) WHERE {pk}=(?)".format(
            t=self.name,
            k=key,
            pk=self.primary_key
        )
        values = (value, pk)
        result = self.execute_dml(sql, values)
        return result

    def delete(self, pk: int) -> bool:
        sql = "DELETE FROM {t} WHERE {pk}=(?)".format(t=self.name, pk=self.primary_key)
        values = (pk,)
        return self.execute_dml(sql, values)

    def undo(self, fk: int=None) -> bool:
        """Undo the last action.

        Get last statement from undostack. Execute the statement.
        Move the executed statement to redostack.
        Each foreign key in the table has their own undo and redo stacks.
        For tables with no foreign key there are only single undo and redo stacks.

        Parameters
        ----------
        fk : int, optional
            Key to the specific undostack, by default None

        Returns
        -------
        bool
            True on success.
        """
        self.undo_step(fk, True)
        return True
    
    def redo(self, fk: int=None) -> bool:
        self.undo_step(fk, False)
        return True

    def select(self, fk: int=None, filter: dict=None, count: bool=False) -> list:
        """Get list of rows from the table.

        Filters results by using foreign key or filter dictionary.
        If both are set as None or left to default, returns whole table.

        Parameters
        ----------
        fk : int, optional
            Foreign key used for filtering the results, by default None
        filter : dict, optional
            A dictionary as a filter in format {key: [operator, value]}, by default None
        count : bool, optional
            Set true to SELECT count of entries matching given filter and foreign key.

        Returns
        -------
        list
            List of selected values.
        """
        cond = ""
        values = []
        keys = self.table_keys
        sql_sel = self.get_select_query(count)
        table_alias = self.get_table_alias() + "."

        # Add the foreign key to filter for parsing.
        if fk is not None and self.foreign_key is not None:
            fk_idx = keys.index(self.foreign_key)
            if filter is None:
                filter = {fk_idx: ["=", fk]}
            else:
                filter[fk_idx] = ["=", fk]

        if filter is not None and len(filter) > 0:
            # Parse a WHERE string from filter dictionary.
            where_str = "{t}{k} {op} (?)"
            for n, (key, value) in enumerate(filter.items()):
                cond += where_str.format(t=table_alias, k=keys[key], op=value[0])
                values.append(value[1])
                if n < len(filter) - 1:
                    cond += " AND "
            sql_con = " WHERE {}".format(cond)
            sql = sql_sel + sql_con

        else:
            # SELECT whole table.
            sql = sql_sel
            values = None

        sql += " ORDER BY {k} {d}".format(k=self.primary_key, d="ASC")
        return self.execute_dql(sql, values)

    def get_column_setup(self, key: str, col: int=None):
        """Get a list or value for column setup.

        Parameters
        ----------
        key : str
            Key to value to get.
        col : int, optional
            Column index to get single value instead of a list, by default None

        Returns
        -------
        list
            List of setup values for this tables columns.
        """
        sql = """
            SELECT {k} FROM columns WHERE tablename=(?){c}ORDER BY col_idx ASC
        """
        if col is None:
            sql = sql.format(k=key, c=" ")
            values = (self.name,)
        else:
            sql = sql.format(k=key, c=" AND col_idx=(?) ")
            values = (self.name, col)
        result = self.execute_dql(sql, values)
        if col is None:
            return [s[0] for s in result]
        else:
            return result[0][0]

    def set_column_setup(self, key: str, col: int, value) -> bool:
        """Set a value to column setup.

        Parameters
        ----------
        key : str
            Key of the value to set.
        col : int
            Column index of the value.
        value : Any
            Value to set.

        Returns
        -------
        bool
            True on success.
        """
        sql = """
            UPDATE columns SET {k}=(?) WHERE tablename=(?) and col_idx=(?)
        """.format(k=key)
        values = (value, self.name, col)
        return self.execute_dml(sql, values)

    def get_column_search(self):
        """Get a list of (key, label) tuples of the columns of this table.

        Returns
        -------
        list
            List of tuples. (key, label)"""
        sql = """
            SELECT key, label FROM columns WHERE tablename=(?) ORDER BY col_idx ASC
        """
        return self.execute_dql(sql, (self.name,))

    def col2key(self, col: int) -> str:
        """Return a key matching the given column from display.

        Override this to handle any displays that use columns in different order
        or columns not specified in CREATE TABLE statement.

        Parameters
        ----------
        col : int
            Column index from display.

        Returns
        -------
        str
            Key used in SQL statements.
        """
        return self.table_keys[col]

    def get_insert_keys(self, inc_rowid=False):
        """Return a list of keys for INSERT statements.
        
        Override for tables that have columns that do not allow inserts.
        """
        return self.table_keys if inc_rowid else self.table_keys[1:]

    def get_select_query(self, count: bool=False):
        """Return a SQL SELECT FROM [* JOIN] string.

        Meant to be overridden when necessary to format selected keys
        as required for each table.

        Parameters
        ----------
        count : bool, optional
            Set True to return query for count of entries instead of content.
        """
        if count:
            return "SELECT COUNT(*) FROM {t}".format(t=self.name)
        return "SELECT {k} FROM {t}".format(k=",".join(self.table_keys), t=self.name)

    def get_table_alias(self) -> str:
        """Return the table alias used in SELECT queries.

        Override if a tables SELECT query uses an alias for the table name.

        Returns
        -------
        str
            Alias of the table name.
        """
        return self.name

    def get_num_columns(self) -> int:
        """Return the number of columns."""
        sql = "SELECT COUNT(*) FROM columns WHERE tablename=(?)"
        num = self.execute_dql(sql, (self.name,))[0][0]
        return num

    def get_column_label(self, col: int) -> str:
        """Return the label of the column."""
        return self.get_column_setup("label", col)

    def get_column_type(self, col: int) -> str:
        """Return the type string of the column."""
        return self.get_column_setup("type", col)

    def get_column_width(self, col: int) -> int:
        """Return the type string of the column."""
        return self.get_column_setup("width", col)

    def get_column_order(self) -> list:
        """Return a list of column positions."""
        return self.get_column_setup("col_order")

    def get_column_read_only(self) -> list:
        """Return a list of column read only states."""
        return self.get_column_setup("ro")

    def create_undo_triggers(self):
        """Format and create the undolog triggers."""
        ins_keys = self.get_insert_keys(True)
        set_strings = map(
            lambda k: "{key}='||quote(old.{key})||'".format(key=k),
            ins_keys
        )
        keys = ins_keys
        value_strings = map(
            lambda k: "'||quote(old.{key})||'".format(key=k),
            ins_keys
        )
        if self.foreign_key is None:
            fk_str = "NULL"
            dfk_str = "NULL"
        else:
            fk_str = "quote(new.{})".format(self.foreign_key)
            dfk_str = "quote(old.{})".format(self.foreign_key)

        script = """
        CREATE TEMP TRIGGER {t}_it AFTER INSERT ON {t} BEGIN
            INSERT INTO undolog VALUES(
                NULL,
                {fk},
                '{t}',
                'DELETE FROM {t} WHERE {pk}='||new.{pk}
                );
        END;
        CREATE TEMP TRIGGER {t}_ut AFTER UPDATE ON {t} BEGIN
            INSERT INTO undolog VALUES(
                NULL,
                {fk},
                '{t}',
                'UPDATE {t} SET {s} WHERE {pk}='||old.{pk}
            );
        END;
        CREATE TEMP TRIGGER {t}_dt BEFORE DELETE ON {t} BEGIN
            INSERT INTO undolog VALUES(
                NULL,
                {dfk},
                '{t}',
                'INSERT INTO {t}({k}) VALUES({v})'
            );
        END;
        """.format(
            t=self.name,
            fk=fk_str,
            dfk=dfk_str,
            pk=self.primary_key,
            s=','.join(set_strings),
            k=','.join(keys),
            v=','.join(value_strings)
        )
        self.con.executescript(script)

    def undo_freeze(self):
        """Stop accepting changes to undolog.

        Unfreezing deletes all entries to undolog during the time between
        undo_freeze and undo_unfreeze calls.
        """
        _undo = SQLTableBase._undo
        if _undo['freeze'] >= 0:
            raise Exception("Recursive call to SQLTableBase.undo_freeze")

        _undo['freeze'] = self.get_undo_maxseq()

    def undo_unfreeze(self):
        """Begin accepting undo actions again."""
        _undo = SQLTableBase._undo
        if _undo['freeze'] < 0:
            raise Exception("Called SQLTableBase.undo_unfreeze while not frozen.")

        self.execute_dml(
            "DELETE FROM undolog WHERE seq>(?)",
            (_undo['freeze'],)
        )
        _undo['freeze'] = -1

    def undo_barrier(self, fk: int):
        """Create an undo barrier."""
        _undo = SQLTableBase._undo
        SQLTableBase.pending = []

        end = self.get_undo_maxseq()
        if _undo['freeze'] >= 0 and end > _undo['freeze']:
            end = _undo['freeze']

        try:
            begin = _undo['firstlog'][fk]
        except KeyError:
            _undo['firstlog'][fk] = end
            begin = _undo['firstlog'][fk]

        self.start_interval(fk)

        # Nothing to undo after last start interval.
        if begin == _undo['firstlog'][fk]:
            return

        if begin > end:
            begin = end

        try:
            self.undostack[fk].append((begin, end))
        except KeyError:
            self.undostack[fk] = [(begin, end)]
        self.redostack[fk] = []

        # for k, v in self.undostack.items():
        #     # print("\nfk: {}".format(k))
        #     for interval in v:
        #         # print("\tinterval: {}".format(interval))

    def can_undo(self, fk: int) -> bool:
        """Return True if there is an action that can be undone."""
        try:
            return len(self.undostack[fk]) > 0
        except KeyError:
            return False

    def can_redo(self, fk: int) -> bool:
        """Return True if there is an action that can be redone."""
        try:
            return len(self.redostack[fk]) > 0
        except KeyError:
            return False

    def start_interval(self, fk: int):
        """Record the starting seq value of the interval."""
        _undo = SQLTableBase._undo
        _undo['firstlog'][fk] = self.execute_dql(
            "SELECT coalesce(max(seq),0)+1 FROM undolog")[0][0]

    def get_undo_maxseq(self) -> int:
        """Return the max undolog 'seq' value."""
        return self.execute_dql("""
            SELECT coalesce(max(seq),0) FROM undolog""", None, True).fetchone()[0]

    def undo_step(self, fk: int, is_undo: bool=True):
        """Do undo or redo action.

        Parameters
        ----------
        fk : int, optional
            Key to the specific undostack, by default None
        is_undo : bool, optional
            True for undo step, False for redo step.
        """
        _undo = SQLTableBase._undo
        if is_undo:
            (begin, end) = self.undostack[fk].pop()
        else:
            (begin, end) = self.redostack[fk].pop()

        result = self.execute_dql("""
            SELECT sql FROM undolog
            WHERE
                tablename=(?) AND
                fk=(?) AND
                seq>=(?) AND seq<=(?)
            ORDER BY seq DESC
        """, (self.name, fk, begin, end))

        self.execute_dml("""
            DELETE FROM undolog
            WHERE
                tablename=(?) AND
                fk=(?) AND
                seq>=(?) AND seq<=(?)
        """, (self.name, fk, begin, end))

        self.start_interval(fk)

        for (sql,) in result:
            self.execute_dml(sql)

        end = self.get_undo_maxseq()
        begin = _undo['firstlog'][fk]

        if is_undo:
            self.redostack[fk].append((begin, end))
        else:
            self.undostack[fk].append((begin, end))
        self.start_interval(fk)

    def format_for_insert(self, data):
        """Format a row for insert.
        
        Deletes non-insertable values from the row. Overwrite if more than ID needs
        to be deleted.
        """
        return data[1:]


class CatalogueTable(SQLTableBase):
    def __init__(self, connection, catalogue):
        super().__init__(connection)
        catalogue.create()
        self.catalogue = catalogue
    
    def get_catalogue_table(self):
        """Return the connected catalogue table."""
        return self.catalogue

    def from_catalogue(self, sql: str, values: list=None) -> int:
        """INSERT a row from catalogue table.

        Parameters
        ----------
        sql : str
            SQL INSERT INTO SELECT FROM statement.
            Provide this in overridden function.
        values : list
            Values to use in given sql statement bindings.

        Returns
        -------
        int
            Last inserted rowid.
        """
        return self.execute_dml(sql, values, rowid=True)

    def to_catalogue(self, sql: str, values: list=None) -> int:
        """Insert a row from this table to a catalogue table.

        Parameters
        ----------
        sql : str
            SQL statement string used for insert.
            Provide this in overridden function.
        values : list
            Values to use in given sql statement bindings.

        Returns
        -------
        int
            Inserted Primary key.
        """
        return self.execute_dml(sql, values, rowid=True)

    def get_catalogue(self):
        """Return the catalogue table."""
        return self.catalogue


class OffersTable(SQLTableBase):
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
            ("offers", "offer_id", "TarjousID", "string"),
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


class GroupsTable(SQLTableBase):
    def __init__(self, connection):
        super().__init__(connection)
        self.name = "groups"
        self.sql_create_table = """
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
        self.indexes = [
            """CREATE INDEX IF NOT EXISTS idx_groups_name ON groups(offer_id, name)"""
        ]
        self.primary_key = "group_id"
        self.foreign_key = "offer_id"
        self.read_only = ["group_id", "offer_id"]
        self.default_columns = [
            ("groups", "group_id", "RyhmäID", "string"),
            ("groups", "offer_id", "TarjousID", "string"),
            ("groups", "name", "Ryhmän nimi", "string")
        ]
        self.table_keys = [
            "group_id",
            "offer_id",
            "name"
        ]


class GroupPredefsTable(SQLTableBase):
    def __init__(self, connection):
        super().__init__(connection)
        self.name = "group_predefs"
        self.sql_create_table = """
            CREATE TABLE IF NOT EXISTS group_predefs (
                group_predef_id INTEGER PRIMARY KEY,
                group_id        INTEGER NOT NULL,
                part            TEXT,
                material        TEXT,

                FOREIGN KEY (group_id)
                    REFERENCES groups (group_id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE,
                UNIQUE(group_id, part)
            )
        """
        self.indexes = [
            """
            CREATE INDEX IF NOT EXISTS idx_group_predefs_part
            ON group_predefs(group_id, part)
            """
        ]
        self.primary_key = "group_predef_id"
        self.foreign_key = "group_id"
        self.read_only = ["group_predef_id", "group_id"]
        self.default_columns = [
            ("group_predefs", "group_predef_id", "EsimääritysID", "long"),
            ("group_predefs", "group_id", "RyhmäID", "long"),
            ("group_predefs", "part", "Osa", "string"),
            ("group_predefs", "material", "Materiaali", "string")
        ]
        self.table_keys = [
            "group_predef_id",  
            "group_id",  
            "part",      
            "material"
        ]


class GroupMaterialsTable(CatalogueTable):
    def __init__(self, connection):
        cat_table = MaterialsTable(connection)
        super().__init__(connection, cat_table)
        self.name = "group_materials"
        self.sql_create_table = """
            CREATE TABLE IF NOT EXISTS group_materials (
                group_material_id INTEGER PRIMARY KEY,
                group_id    INTEGER NOT NULL,
                code        TEXT,
                category    TEXT,
                desc        TEXT,
                prod        TEXT,
                thickness   INTEGER,
                is_stock    TEXT DEFAULT 'varasto',
                unit        TEXT,
                cost        PYDECIMAL,
                add_cost    PYDECIMAL,
                edg_cost    PYDECIMAL,
                loss        PYDECIMAL,
                discount    PYDECIMAL,
                tot_cost    PYDECIMAL
                    GENERATED ALWAYS AS (
                        material_cost(cost, add_cost, edg_cost, loss, discount)
                    ) STORED,

                FOREIGN KEY (group_id) REFERENCES groups (group_id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE,
                UNIQUE(group_id, code)
            )
        """
        self.indexes = [
            """CREATE INDEX IF NOT EXISTS idx_gm_code ON group_materials(group_id, code)"""
        ]
        self.primary_key = "group_material_id"
        self.foreign_key = "group_id"
        self.read_only = ["group_material_id", "group_id", "tot_cost"]
        self.default_columns = [
            ("group_materials", "group_material_id", "MateriaaliID", "long",),
            ("group_materials", "group_id", "RyhmäID", "long"),
            ("group_materials", "code", "Koodi", "string"),
            ("group_materials", "category", "Tuoteryhmä", "string"),
            ("group_materials", "desc", "Kuvaus", "string"),
            ("group_materials", "prod", "Valmistaja", "string"),
            ("group_materials", "thickness", "Paksuus", "long"),
            ("group_materials", "is_stock", "Onko varasto", "choice:varasto,tilaus,tarkista"),
            ("group_materials", "unit", "Hintayksikkö", "choice:€/m2,€/kpl"),
            ("group_materials", "cost", "Hinta", "decimal"),
            ("group_materials", "add_cost", "Lisähinta", "decimal"),
            ("group_materials", "edg_cost", "R.Nauhan hinta", "decimal"),
            ("group_materials", "loss", "Hukka", "decimal"),
            ("group_materials", "discount", "Alennus", "decimal"),
            ("group_materials", "tot_cost", "Kokonaishinta", "decimal")
        ]
        self.table_keys = [
            "group_material_id",        
            "group_id",  
            "code",  
            "category",  
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

    def format_for_insert(self, data):
        """Format a row for insert.
        
        Deletes non-insertable values from the row. Overwrite if more than ID needs
        to be deleted.
        """
        return data[1:-1]

    def get_insert_keys(self, inc_rowid=False):
        """Overridden member function to remove tot_cost column from insert."""
        return self.table_keys[:-1] if inc_rowid else self.table_keys[1:-1]

    def get_select_query(self, count: bool=False):
        """Return GroupMaterials SELECT statement with pydecimal formattings.
        
        Parameters
        ----------
        count : bool, optional
            Set True to return query for count of entries instead of content.
        """
        if count:
            return super().get_select_query(count)
        return """
            SELECT
                group_material_id,
                group_id,    
                code,        
                category,    
                desc,        
                prod,        
                thickness,   
                is_stock,    
                unit,        
                cost AS 'cost [pydecimal]',
                add_cost AS 'add_cost [pydecimal]',
                edg_cost AS 'edg_cost [pydecimal]',
                loss AS 'loss [pydecimal]',
                discount AS 'discount [pydecimal]',
                tot_cost AS 'tot_cost [pydecimal]'
            FROM group_materials
        """

    def from_catalogue(self, rowid: int, fk: int=None) -> int:
        """Insert a row from catalogue table to this table.

        Parameters
        ----------
        rowid : int
            Primary key of a row in catalogue table.

        Returns
        -------
        int
            Primary key of the inserted row.
        """
        sql = """
            INSERT INTO group_materials(
                group_id,
                code,
                category,
                desc,
                prod,
                thickness,
                is_stock,
                unit,
                cost,
                add_cost,
                edg_cost,
                loss,
                discount)
            SELECT
                (?),
                code,
                category,
                desc,
                prod,
                thickness,
                is_stock,
                unit,
                cost AS 'cost [pydecimal]',
                add_cost AS 'add_cost [pydecimal]',
                edg_cost AS 'edg_cost [pydecimal]',
                loss AS 'loss [pydecimal]',
                discount AS 'discount [pydecimal]'
            FROM
                materials
            WHERE
                material_id=(?)
        """
        return super().from_catalogue(sql, (fk, rowid))

    def to_catalogue(self, rowid: int) -> int:
        """Insert a row from this table to catalogue table.

        Parameters
        ----------
        rowid : int
            Primary key of a row in this table.

        Returns
        -------
        int
            Primary key of the inserted row.
        """
        sql = """
            INSERT INTO materials(
                code,
                category,
                desc,
                prod,
                thickness,
                is_stock,
                unit,
                cost,
                add_cost,
                edg_cost,
                loss,
                discount)
            SELECT
                code,
                category,
                desc,
                prod,
                thickness,
                is_stock,
                unit,
                cost AS 'cost [pydecimal]',
                add_cost AS 'add_cost [pydecimal]',
                edg_cost AS 'edg_cost [pydecimal]',
                loss AS 'loss [pydecimal]',
                discount AS 'discount [pydecimal]'
            FROM
                group_materials
            WHERE
                group_material_id=(?)
        """
        return super().to_catalogue(sql, (rowid,))


class GroupProductsTable(CatalogueTable):
    def __init__(self, connection):
        cat_table = ProductsTable(connection)
        super().__init__(connection, cat_table)
        self.name = "group_products"
        self.sql_create_table = """
            CREATE TABLE IF NOT EXISTS group_products (
                group_product_id INTEGER PRIMARY KEY,
                group_id    INTEGER NOT NULL,
                code        TEXT,
                count       INTEGER DEFAULT 1,
                category    TEXT,
                desc        TEXT,
                prod        TEXT,
                width       INTEGER,
                height      INTEGER,
                depth       INTEGER,
                inst_unit   PYDECIMAL,
                work_time   PYDECIMAL,

                FOREIGN KEY (group_id)
                    REFERENCES groups (group_id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE,
                UNIQUE(group_id, code)
            )
        """
        self.indexes = [
            """CREATE INDEX IF NOT EXISTS idx_gp_code ON group_products(group_id, code)"""
        ]
        self.primary_key = "group_product_id"
        self.foreign_key = "group_id"
        self.read_only = ["group_product_id", "group_id", "part_cost", "tot_cost"]
        self.default_columns = [
            ("group_products", "group_product_id", "TuoteID", "long"),
            ("group_products", "group_id", "RyhmäID", "long"),
            ("group_products", "code", "Koodi", "string"),
            ("group_products", "count", "Määrä", "long"),
            ("group_products", "category", "Tuoteryhmä", "string"),
            ("group_products", "desc", "Kuvaus", "string"),
            ("group_products", "prod", "Valmistaja", "string"),
            ("group_products", "width", "Leveys", "long"),
            ("group_products", "height", "Korkeus", "long"),
            ("group_products", "depth", "Syvyys", "long"),
            ("group_products", "inst_unit", "As.Yksikkö", "double:6,2"),
            ("group_products", "work_time", "Työaika", "double:6,2"),
            ("group_products", "part_cost", "Osahinta", "double:6,2"),
            ("group_products", "tot_cost", "Kokonaishinta", "double:6,2"),
        ]
        self.table_keys = [
            "group_product_id",
            "group_id",
            "code",
            "count",
            "category",
            "desc",
            "prod",
            "width",
            "height",
            "depth",
            "inst_unit",
            "work_time"
        ]

    def get_select_query(self, count: bool=False):
        """Return GroupProducts SELECT statement with pydecimal formattings.
        
        Parameters
        ----------
        count : bool, optional
            Set True to return query for count of entries instead of content.
        """
        if count:
            return "SELECT COUNT(*) FROM group_products as p"
        return """
            SELECT
                p.group_product_id,
                p.group_id, 
                p.code,     
                p.count,    
                p.category, 
                p.desc,     
                p.prod,     
                p.width,    
                p.height,   
                p.depth,    
                p.inst_unit AS 'inst_unit [pydecimal]',
                p.work_time AS 'work_time [pydecimal]',
                a.part_cost AS 'work_time [pydecimal]',
                product_cost(
                    part_cost,
                    p.work_time,
                    (
                        SELECT value_decimal
                        FROM variables
                        WHERE variable_id=0
                    )
                ) AS 'tot_cost [pydecimal]'

            FROM
                group_products as p
                LEFT JOIN (
                    SELECT a.group_product_id, dec_sum(a.cost) AS part_cost
                    FROM group_parts AS a
                    GROUP BY a.group_product_id
                ) a USING(group_product_id)
        """

    def get_table_alias(self) -> str:
        """Return the alias for table name used in SELECT query."""
        return "p"

    def from_catalogue(self, rowid: int, fk: int=None) -> int:
        """Insert a row from catalogue table to this table.

        Parameters
        ----------
        rowid : int
            Primary key of a row in catalogue table.

        Returns
        -------
        int
            Primary key of the inserted row.
        """
        sql = """
            INSERT INTO group_products(
                group_id,
                code,
                category,
                desc,
                prod,
                width,
                height,
                depth,
                inst_unit,
                work_time)
            SELECT
                (?),
                code,
                category,
                desc,
                prod,
                width,
                height,
                depth,
                inst_unit AS 'cost [pydecimal]',
                work_time AS 'cost [pydecimal]'
            FROM
                products
            WHERE
                product_id=(?)
        """
        return super().from_catalogue(sql, (fk, rowid))

    def to_catalogue(self, rowid: int) -> int:
        """Insert a row from this table to catalogue table.

        Parameters
        ----------
        rowid : int
            Primary key of a row in this table.

        Returns
        -------
        int
            Primary key of the inserted row.
        """
        sql = """
            INSERT INTO products(
                code,
                category,
                desc,
                prod,
                width,
                height,
                depth,
                inst_unit,
                work_time)
            SELECT
                code,
                category,
                desc,
                prod,
                width,
                height,
                depth,
                inst_unit AS 'cost [pydecimal]',
                work_time AS 'cost [pydecimal]'
            FROM
                group_products
            WHERE
                group_product_id=(?)
        """
        return super().to_catalogue(sql, (rowid,))


class GroupPartsTable(CatalogueTable):
    def __init__(self, connection):
        cat_table = PartsTable(connection)
        super().__init__(connection, cat_table)
        self.name = "group_parts"
        self.sql_create_table = """
            CREATE TABLE IF NOT EXISTS group_parts (
                group_part_id      INTEGER PRIMARY KEY,
                group_product_id   INTEGER NOT NULL,
                part        TEXT,
                count       INTEGER DEFAULt 1,
                code        TEXT,
                desc        TEXT,
                use_predef  INTEGER DEFAULT 0,
                default_mat TEXT,
                width       INTEGER DEFAULT 0,
                length      INTEGER DEFAULT 0,
                cost        PYDECIMAL,
                code_width  TEXT,
                code_length TEXT,
                code_cost   TEXT,

                FOREIGN KEY (group_product_id)
                    REFERENCES group_products (group_product_id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE,
                UNIQUE(group_product_id, part)
            )
        """
        self.indexes = [
            """
            CREATE INDEX IF NOT EXISTS idx_gpa_code 
            ON group_parts(group_product_id, code)"""
        ]
        self.primary_key = "group_part_id"
        self.foreign_key = "group_product_id"
        self.read_only = [
            "group_part_id",
            "group_product_id",
            "width",
            "length",
            "cost",
            # "m.thickness",
            # "m.tot_cost",
            # "pr.width",
            # "pr.height",
            # "pr.depth"
        ]
        self.default_columns = [
            ("group_parts", "group_part_id", "OsaID", "string"),
            ("group_parts", "group_product_id", "TuoteID", "string"),
            ("group_parts", "part", "Osa", "string"),
            ("group_parts", "count", "Määrä", "long"),
            ("group_parts", "code", "Koodi", "string"),
            ("group_parts", "desc", "Kuvaus", "string"),
            ("group_parts", "use_predef", "Käytä esimääritystä", "bool"),
            ("group_parts", "default_mat", "Oletus materiaali", "string"),
            ("group_parts", "width", "Leveys", "long"),
            ("group_parts", "length", "Pituus", "long"),
            ("group_parts", "cost", "Hinta", "double:6,2"),
            ("group_parts", "code_width", "Koodi Leveys", "string"),
            ("group_parts", "code_length", "Koodi Pituus", "string"),
            ("group_parts", "code_cost", "Koodi Hinta", "string"),
            ("group_parts", "used_mat", "Käyt. Mat.", "string"),
            # ("group_parts", "m.thickness", "Paksuus", "long"),
            # ("group_parts", "m.tot_cost", "Mat. Hinta", "double:6,2"),
            # ("group_parts", "pr.width", "Tuote leveys", "long"),
            # ("group_parts", "pr.height", "Tuote korkeus", "long"),
            # ("group_parts", "pr.depth", "Tuote syvyys", "long")
        ]
        self.table_keys = [
            "group_part_id",          
            "group_product_id",  
            "part",        
            "count",       
            "code",
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
        self.aeval = Interpreter(minimal=True)
        self.code2col = {
            "määrä": 3,
            "leveys": 8,
            "pituus": 9,
            "hinta": 10,
            "mpaksuus": 15,
            "mhinta": 16,
            "tleveys": 17,
            "tkorkeus": 18,
            "tsyvyys": 19
        }

    def select(self, fk: int=None, filter: dict=None) -> list:
        """Update parts values before returning the select list.
        
        Returns the parts only if it's foreign key
        product exists in group_products table.
        """
        # SELECT all parts of product with fk as id.
        parts = super().select(fk, None)
        # for part in parts:
        #     print(part)
        # Parse the codes in parts of this product and return changed values.
        new_values = self.parse_codes(parts)
        # UPDATE the changed values.
        self.execute_dml(
            """
            UPDATE
                group_parts
            SET
                width=(?), length=(?), cost=(?)
            WHERE
                group_part_id=(?)
            """, new_values, True
        )
        # Get the parts with updated values.
        return super().select(fk=fk, filter=filter)

    def parse_codes(self, parts: list):
        """Return list of changed values parsed from codes."""
        new_values_list = []
        for part_row, part in enumerate(parts):
            new_values = []
            is_changed = False

            for n in range(8, 11):
                old_value = part[n]
                code = part[n + 3]
                # print("\nCODE:\n{}".format(code))
                value = self.code2value(code, part_row, parts)
                # print("\nVALUE:\n{}".format(value))
                new_values.append(value)
                if value != old_value:
                    is_changed = True

            if is_changed:
                new_values.append(part[0])
                new_values_list.append(new_values)
        return new_values_list

    def code2value(self, code: str, row: int, parts: list):
        """Parse a code to a value.

        Parameters
        ----------
        code : str
            Code string.
        row : int
            Origin row in parts list.
        parts : list
            Parts data for finding values referred to in code.

        Returns
        -------
        int | Decimal
            Parsed value.
        """
        # Test for valididy of the code string.
        try:
            if code[0] != "=":
                return None
            code = code[1:]
        except (TypeError, IndexError):
            return None
        else:
            # Remove dublicates and split to list.
            split = list(dict.fromkeys(code.split(" ")))
            for word in split:
                # print(word)
                # Default values
                src_row = row
                key = word
                # Link format: "part".key
                # If word is link to another row in parts.
                # get value from parts list.
                if word[0] == '"':
                    try:
                        # ("part", key)
                        (source, key) = word.split(".")
                    except ValueError:
                        print('SyntaxError when parsing "{}"\n'.format(code) +
                              'to refer to another part use: "part".key')
                        return None
                    else:
                        # Find row for source part.
                        source_part = source.strip('"')
                        temp_row = None
                        for n, dr in enumerate(parts):
                            if dr[2] == source_part:
                                temp_row = n
                                break
                        if temp_row:
                            src_row = temp_row
                # if key in code2col:
                # if len(key) == 1 and key in '*/+-^()':
                #     continue
                try:
                    col = self.code2col[key]
                    value = parts[src_row][col]
                except KeyError:
                    continue
                else:
                    if value is None:
                        value_str = "0"
                    else:
                        value_str = str(value)
                    code = code.replace(word, value_str)
            try:
                # print("\nCODE TO EVAL:\{}".format(code))
                ev = self.aeval(code)
                if isinstance(ev, float):
                    return Decimal(str(ev))
                else:
                    return ev

            except NameError as e:
                print("{}: {}".format(type(e), e))
                return None

    def get_table_alias(self):
        """Return the alias used for this tables name."""
        return "pa"

    def get_select_query(self, count: bool=False):
        """Return GroupParts SELECT statement with pydecimal formattings.

        Parameters
        ----------
        count : bool, optional
            Set True to return query for count of entries instead of content.
        """
        if count:
            return """
                SELECT
                    COUNT(*)
                FROM
                    group_parts AS pa
            """
        return """
            SELECT
                pa.group_part_id,
                pa.group_product_id,
                pa.part,
                pa.count,
                pa.code,
                pa.desc,
                pa.use_predef,
                pa.default_mat,
                pa.width,
                pa.length,
                pa.cost AS 'pa.cost [pydecimal]',
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
                m.tot_cost AS 'm.tot_cost [pydecimal]',
                pr.width,
                pr.height,
                pr.depth,
                pr.group_id,
                d.material,
                m.code

            FROM group_parts AS pa
                INNER JOIN group_products AS pr
                    ON pr.group_product_id=pa.group_product_id

                LEFT JOIN group_predefs AS d
                    ON pr.group_id=d.group_id AND pa.part=d.part

                LEFT JOIN group_materials AS m
                    ON pr.group_id=m.group_id AND pa.default_mat=m.code
        """

    def from_catalogue(self, rowid: int, fk: int=None) -> int:
        """Insert a row from catalogue table to this table.

        Parameters
        ----------
        rowid : int
            Primary key of a row in catalogue table.

        Returns
        -------
        int
            Primary key of the inserted row.
        """
        sql = """
            INSERT INTO group_parts(
                group_product_id,
                part,
                count,
                code,
                desc,
                default_mat,
                code_width,
                code_length,
                code_cost)
            SELECT
                (?),
                part,
                count,
                code,
                desc,
                default_mat,
                code_width,
                code_length,
                code_cost
            FROM
                parts
            WHERE
                part_id=(?)
        """
        return super().from_catalogue(sql, (fk, rowid))

    def to_catalogue(self, rowid: int) -> int:
        """Insert a row from this table to catalogue table.

        Parameters
        ----------
        rowid : int
            Primary key of a row in this table.

        Returns
        -------
        int
            Primary key of the inserted row.
        """
        sql = """
            INSERT INTO parts(
                part,
                count,
                code,
                desc,
                default_mat,
                code_width,
                code_length,
                code_cost)
            SELECT
                part,
                count,
                code,
                desc,
                default_mat,
                code_width,
                code_length,
                code_cost
            FROM
                group_parts
            WHERE
                group_part_id=(?)
        """
        return super().to_catalogue(sql, (rowid,))


class MaterialsTable(SQLTableBase):
    def __init__(self, connection):
        super().__init__(connection)
        self.name = "materials"
        self.sql_create_table = """
            CREATE TABLE IF NOT EXISTS materials (
                material_id INTEGER PRIMARY KEY,
                code        TEXT UNIQUE,
                category    TEXT,
                desc        TEXT,
                prod        TEXT,
                thickness   INTEGER,
                is_stock    TEXT,
                unit        TEXT,
                cost        PYDECIMAL,
                add_cost    PYDECIMAL,
                edg_cost    PYDECIMAL,
                loss        PYDECIMAL,
                discount    PYDECIMAL
            )
        """
        self.indexes = [
            """CREATE INDEX IF NOT EXISTS idx_materials_code ON materials(code)""",
            """CREATE INDEX IF NOT EXISTS idx_materials_category ON materials(category, code)"""
        ]
        self.primary_key = "material_id"
        self.foreign_key = None
        self.read_only = ["material_id"]
        self.default_columns = [
            ("materials", "material_id", "MateriaaliID", "long"),
            ("materials", "code", "Koodi", "string"),
            ("materials", "category", "Tuoteryhmä", "string"),
            ("materials", "desc", "Kuvaus", "string"),
            ("materials", "prod", "Valmistaja", "string"),
            ("materials", "thickness", "Paksuus", "long"),
            ("materials", "is_stock", "Onko varasto", "choice:varasto,tilaus,tarkista"),
            ("materials", "unit", "Hintayksikkö", "choice:€/m2,€/kpl"),
            ("materials", "cost", "Hinta", "double:6,2"),
            ("materials", "add_cost", "Lisähinta", "double:6,2"),
            ("materials", "edg_cost", "R.Nauhan hinta", "double:6,2"),
            ("materials", "loss", "Hukka", "double:6,2"),
            ("materials", "discount", "Alennus", "double:6,2"),
        ]
        self.table_keys = [
            "material_id",
            "code",      
            "category",  
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
        ]

    def get_select_query(self, count: bool=False):
        """Return a SELECT FROM query string.
        
        Parameters
        ----------
        count : bool, optional
            Set True to return query for count of entries instead of content.
        """
        if count:
            return super().get_select_query(count)
        return """
            SELECT
                material_id,
                code,
                category,
                desc,
                prod,
                thickness,
                is_stock,
                unit,
                cost AS 'cost [pydecimal]',
                add_cost AS 'add_cost [pydecimal]',
                edg_cost AS 'edg_cost [pydecimal]',
                loss AS 'loss [pydecimal]',
                discount AS 'discount [pydecimal]'
            FROM 
                materials
        """


class ProductsTable(SQLTableBase):
    def __init__(self, connection):
        super().__init__(connection)
        self.name = "products"
        self.sql_create_table = """
            CREATE TABLE IF NOT EXISTS products (
                product_id  INTEGER PRIMARY KEY,
                code        TEXT UNIQUE,
                category    TEXT,
                desc        TEXT,
                prod        TEXT,
                width       INTEGER,
                height      INTEGER,
                depth       INTEGER,
                inst_unit   PYDECIMAL,
                work_time   PYDECIMAL
            )
        """
        self.indexes = [
            """CREATE INDEX IF NOT EXISTS idx_products_code ON products(code)""",
            """CREATE INDEX IF NOT EXISTS idx_products_category ON products(category, code)"""
        ]
        self.primary_key = "product_id"
        self.foreign_key = None
        self.read_only = ["product_id"]
        self.default_columns = [
            ("products", "product_id", "TuoteID", "long"),
            ("products", "code", "Koodi", "string"),
            ("products", "category", "Tuoteryhmä", "string"),
            ("products", "desc", "Kuvaus", "string"),
            ("products", "prod", "Valmistaja", "string"),
            ("products", "width", "Leveys", "long"),
            ("products", "height", "Korkeus", "long"),
            ("products", "depth", "Syvyys", "long"),
            ("products", "inst_unit", "As.Yksikkö", "double:6,2"),
            ("products", "work_time", "Työaika", "double:6,2")
        ]
        self.table_keys = [
            "product_id",
            "code",        
            "category",    
            "desc",        
            "prod",        
            "width",       
            "height",      
            "depth",       
            "inst_unit",
            "work_time"
        ]

    def get_select_query(self, count: bool=False):
        """Return a SELECT FROM query string.
        
        Parameters
        ----------
        count : bool, optional
            Set True to return query for count of entries instead of content.
        """
        if count:
            return super().get_select_query(count)
        return """
            SELECT
                product_id,
                code,
                category,
                desc,
                prod,
                width,
                height,
                depth,
                inst_unit AS 'cost [pydecimal]',
                work_time AS 'cost [pydecimal]'
            FROM 
                products
        """


class PartsTable(SQLTableBase):
    def __init__(self, connection):
        super().__init__(connection)
        self.name = "parts"
        self.sql_create_table = """
            CREATE TABLE IF NOT EXISTS parts (
                part_id         INTEGER PRIMARY KEY,
                product_id      INTEGER,
                part            TEXT,
                count           INTEGER DEFAULT 1,
                code            TEXT,
                desc            TEXT,
                default_mat     TEXT,
                code_width      TEXT,
                code_length     TEXT,
                code_cost       TEXT,

                UNIQUE (product_id, part),
                FOREIGN KEY (product_id)
                    REFERENCES products (product_id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE
            )
        """
        self.indexes = [
            """CREATE INDEX IF NOT EXISTS idx_parts_fk ON parts(product_id, part)"""
        ]
        self.primary_key = "part_id"
        self.foreign_key = "product_id"
        self.read_only = ["part_id", "product_id"]
        self.default_columns = [
            ("parts", "part_id", "OsaID", "long"),
            ("parts", "product_id", "TuoteID", "long"),
            ("parts", "part", "Osa", "string"),
            ("parts", "count", "Määrä", "long"),
            ("parts", "code", "Koodi", "string"),
            ("parts", "desc", "Kuvaus", "string"),
            ("parts", "default_mat", "Oletus materiaali", "string"),
            ("parts", "code_width", "Koodi Leveys", "string"),
            ("parts", "code_length", "Koodi Pituus", "string"),
            ("parts", "code_cost", "Koodi Hinta", "string")
        ]
        self.table_keys = [
            "part_id",
            "product_id",
            "part",
            "count",
            "code",
            "desc",
            "default_mat",
            "code_width",
            "code_length",
            "code_cost"
        ]

