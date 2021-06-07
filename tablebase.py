import sqlite3
from decimal import Decimal
from asteval import Interpreter


VAR_ID_WORK_COST = 0
VAR_ID_INSTALL_UNIT_MULT = 1


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

def connect(db_name: str) -> sqlite3.Connection:
    """Return a connection object to sqlite3 database with given name.

    Custom types must be declared in data queries to get
    the correct type instead of bytes.
        SELECT a AS 'a [pydecimal]' FROM table
    
    Do adapter/converter registering for custom types:
        pydecimal
    Create functions:
        dec_add, dec_sub, dec_mul, dec_div
    Create aggregates:
        dec_sum
    """
    # Converter and adapter for Decimal type.
    sqlite3.register_adapter(Decimal, adapter_decimal)
    sqlite3.register_converter("pydecimal", converter_decimal)

    # Custom type is parsed from table declaration.
    con = sqlite3.connect(db_name, detect_types=sqlite3.PARSE_COLNAMES)
    con.execute("PRAGMA foreign_keys = ON")

    # Create functions to handle math in queries for custom types.
    con.create_function("dec_add", -1, decimal_add, deterministic=True)
    con.create_function("dec_sub", 2, decimal_sub, deterministic=True)
    con.create_function("dec_mul", 2, decimal_mul, deterministic=True)
    con.create_function("dec_div", 2, decimal_div, deterministic=True)
    con.create_function("material_cost", 5, material_cost, deterministic=True)
    con.create_aggregate("dec_sum", 1, DecimalSum)

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
            UNIQUE (tablename, col_idx),
            UNIQUE (tablename, col_order)
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
            [VAR_ID_WORK_COST, "Työn hinta", Decimal('0.0'), None, None],
            [VAR_ID_INSTALL_UNIT_MULT, "Asennusyksikön kerroin", Decimal('0.0'), None, None]
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
        try:
            with self.con:
                # Create table and indexes.
                self.con.execute(self.sql_create_table)
                for idx in self.indexes:
                    self.con.execute(idx)

                # Insert default columns values if required.
                count = self.con.execute(
                    """SELECT COUNT(*) FROM columns WHERE tablename=(?)""",
                    (self.name,)
                )
                if count != len(self.default_columns):
                    for n, col in enumerate(self.default_columns):
                        ro = 1 if col[self.KEY] in self.read_only else 0
                        self.con.execute(
                            "INSERT INTO columns ({k}) VALUES (?,?,?,?,?,?,?,?,?)".format(
                                k=",".join(self.columns_table_keys[1:])
                            ),
                            list(col) + [n, n, 60, ro, 1]
                        )

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

        ret_rowid = False if many else True
        return self.execute_dml(sql, values, many, ret_rowid)

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
            return self.execute_dml(sql, rowid=True)
        else:
            sql = sql_ins.format(t=self.name) + sql_val.format(k=self.foreign_key)
            return self.execute_dml(sql, (fk,), rowid=True)

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

    def select(self, fk: int=None, filter: dict=None) -> list:
        """Get list of rows from the table.

        Filters results by using foreign key or filter dictionary.
        If both are set as None or left to default, returns whole table.

        Parameters
        ----------
        fk : int, optional
            Foreign key used for filtering the results, by default None
        filter : dict, optional
            A dictionary as a filter in format {key: [operator, value]}, by default None

        Returns
        -------
        list
            List of selected values.
        """
        cond = ""
        values = []
        keys = self.table_keys
        sql_sel = self.get_select_query()
        table_alias = self.get_table_alias()

        # Add the foreign key to filter for parsing.
        if fk is not None and self.foreign_key is not None:
            fk_idx = keys.index(self.foreign_key)
            if filter is None:
                filter = {fk_idx: ["=", fk]}
            else:
                filter[fk_idx] = ["=", fk]

        if filter is not None:
            # Parse a WHERE string from filter dictionary.
            where_str = "{t}.{k} {op} (?)"
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

    def get_select_query(self):
        """Return a SQL SELECT FROM [* JOIN] string.

        Meant to be overridden when necessary to format selected keys
        as required for each table.
        """
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
            ("offers", "group_id", "RyhmäID", "string"),
            ("offers", "offer_id", "TarjousID", "string"),
            ("offers", "name", "Ryhmän nimi", "string")
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


class GroupMaterialsTable(SQLTableBase):
    def __init__(self, connection):
        super().__init__(connection)
        self.name = "group_materials"
        self.sql_create_table = """
            CREATE TABLE IF NOT EXISTS group_materials (
                group_materials_id INTEGER PRIMARY KEY,
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
        self.primary_key = "group_materials_id"
        self.foreign_key = "group_id"
        self.read_only = ["group_materials_id", "group_id", "tot_cost"]
        self.default_columns = [
            ("group_materials", "group_materials_id", "MateriaaliID", "long",),
            ("group_materials", "group_id", "RyhmäID", "long"),
            ("group_materials", "category", "Tuoteryhmä", "string"),
            ("group_materials", "code", "Koodi", "string"),
            ("group_materials", "desc", "Kuvaus", "string"),
            ("group_materials", "prod", "Valmistaja", "string"),
            ("group_materials", "thickness", "Paksuus", "long"),
            ("group_materials", "is_stock", "Onko varasto", "choice:varasto,tilaus,tarkista"),
            ("group_materials", "unit", "Hintayksikkö", "choice:€/m2,€/kpl"),
            ("group_materials", "cost", "Hinta", "double:6,2"),
            ("group_materials", "add_cost", "Lisähinta", "double:6,2"),
            ("group_materials", "edg_cost", "R.Nauhan hinta", "double:6,2"),
            ("group_materials", "loss", "Hukka", "double:6,2"),
            ("group_materials", "discount", "Alennus", "double:6,2"),
            ("group_materials", "tot_cost", "Kokonaishinta", "double:6,2")
        ]
        self.table_keys = [
            "group_materials_id",        
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

    def get_insert_keys(self, inc_rowid=False):
        """Overridden member function to remove tot_cost column from insert."""
        return self.table_keys[:-1] if inc_rowid else self.table_keys[1:-1]

    def get_select_query(self):
        """Return GroupMaterials SELECT statement with pydecimal formattings."""
        return """
            SELECT
                group_materials_id,
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


class GroupProductsTable(SQLTableBase):
    def __init__(self, connection):
        super().__init__(connection)
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
        self.read_only = ["group_product_id", "group_id", "tot_cost"]
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
            "inst_unit",
            "width",
            "height",
            "depth",
            "work_time"
        ]

    def get_select_query(self):
        """Return GroupProducts SELECT statement with pydecimal formattings."""
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
                    a.part_cost,
                    work_time,
                    (
                        SELECT value_decimal
                        FROM variables
                        WHERE variable_id=0
                    )
                ) tot_cost

            FROM
                group_products as p
                LEFT JOIN (
                    SELECT a.group_product_id, dec_sum(a.cost) AS 'part_cost [pydecimal]'
                    FROM group_parts AS a
                    GROUP BY a.group_product_id
                ) a USING(group_product_id)
        """


class GroupPartsTable(SQLTableBase):
    def __init__(self, connection):
        super().__init__(connection)
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
        self.read_only = ["group_part_id", "group_product_id"]
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
            ("group_parts", "m.thickness", "Paksuus", "long"),
            ("group_parts", "m.tot_cost", "Mat. Hinta", "double:6,2"),
            ("group_parts", "pr.width", "Tuote leveys", "long"),
            ("group_parts", "pr.height", "Tuote korkeus", "long"),
            ("group_parts", "pr.depth", "Tuote syvyys", "long"),
            ("group_parts", "product_code", "Tuote Koodi", "string"),
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
        """Update the changed coded parts values before returning the select list."""
        # SELECT parts of the product.
        parts = super().select(fk, None)
        # Parse part codes to list of values to update.
        # print("\nPARTS:\n{}".format(parts))
        new_values = self.parse_codes(parts)
        # print("\nNEW VALUES:\n{}".format(new_values))
        # UPDATE with rows in update queue.
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

    def get_select_query(self):
        """Return GroupParts SELECT statement with pydecimal formattings."""
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
                pa.cost AS 'inst_unit [pydecimal]',
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
                m.tot_cost AS 'inst_unit [pydecimal]',
                pr.width,
                pr.height,
                pr.depth,
                pr.code as product_code

            FROM group_parts AS pa
                INNER JOIN group_products AS pr
                    ON pr.group_product_id=pa.group_product_id

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
        """
