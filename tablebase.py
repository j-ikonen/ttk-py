import sqlite3


VAR_ID_WORK_COST = 0
VAR_ID_INSTALL_UNIT_MULT = 1


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

    def __init__(self, connection):
        self.con: sqlite3.Connection = connection
        self.create_columns = """
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
            )
        """
        self.idx_columns = [
            """CREATE INDEX IF NOT EXISTS idx_columns ON columns(tablename, col_idx)"""
        ]
        self.columns_keys = [
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
        self.create_variables = """
            CREATE TABLE IF NOT EXISTS variables (
                variable_id INTEGER PRIMARY KEY,
                label       TEXT,
                value_real  REAL,
                value_int   INTEGER,
                value_txt   TEXT,

                CHECK(
                    (value_real IS NOT NULL AND value_int IS NULL AND value_txt IS NULL)
                    OR
                    (value_real IS NULL AND value_int IS NOT NULL AND value_txt IS NULL)
                    OR
                    (value_real IS NULL AND value_int IS NULL AND value_txt IS NOT NULL)
                )
            )
        """
        self.default_variables = [
            [VAR_ID_WORK_COST, "Työn hinta", None, 0, None],
            [VAR_ID_INSTALL_UNIT_MULT, "Asennusyksikön kerroin", None, 0, None]
        ]
        self.variables_table_keys = [
            "variable_id", "label", "value_real", "value_int", "value_txt"
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
                # Create columns and variables table if not done yet.
                if not self.setup_done:
                    self.con.execute(self.create_columns)
                    self.con.execute(self.create_variables)
                    self.execute_dml(
                        "INSERT INTO variables({}) VALUES(?,?,?,?,?)".format(
                            ",".join(self.variables_table_keys)
                        ),
                        self.default_variables,
                        True
                    )

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
                                k=",".join(self.columns_keys[1:])
                            ),
                            list(col) + [n, n, 60, ro, 1]
                        )

        except sqlite3.OperationalError as e:
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

        except sqlite3.IntegrityError as e:
            print("\nsqlite3.IntegrityError: {}".format(e))
            print("In SQLTableBase.execute_dml")
            print("Error with sql: {}".format(sql))
            print("using values: {}".format(values))
            return False
        except sqlite3.Error as e:
            print("\n{}: {}".format(type(e), e))
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
        if include_rowid:
            keys = ",".join(self.table_keys)
            binds = ",".join(["?"] * len(self.table_keys))
        else:
            keys = ",".join(self.table_keys[1:])
            binds = ",".join(["?"] * len(self.table_keys[1:]))
        if upsert:
            rep_str = " OR REPLACE "
        else:
            rep_str = " "
        sql = "INSERT{u}INTO {t}({k}) VALUES ({b})".format(
            u=rep_str, t=self.name, k=keys, b=binds
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
            return self.execute_dml(sql)
        else:
            sql = sql_ins.format(t=self.name) + sql_val.format(k=self.foreign_key)
            return self.execute_dml(sql, (fk,))

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
        sql_sel = "SELECT {k} FROM {t}".format(k=",".join(keys), t=self.name)

        # Add the foreign key to filter for parsing.
        if fk is not None and self.foreign_key is not None:
            fk_idx = self.table_keys.index(self.foreign_key)
            if filter is None:
                filter = {fk_idx: ["=", fk]}
            else:
                filter[fk_idx] = ["=", fk]

        if filter is not None:
            # Parse a WHERE string from filter dictionary.
            where_str = "{k} {op} (?)"
            for n, (key, value) in enumerate(filter.items()):
                cond += where_str.format(k=keys[key], op=value[0])
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


class GroupsPredefsTable(SQLTableBase):
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
                cost        TEXT,
                add_cost    TEXT DEFAULT '0.0',
                edg_cost    TEXT DEFAULT '0.0',
                loss        TEXT DEFAULT '0.0',
                discount    TEXT DEFAULT '0.0',
                tot_cost    TEXT
                    GENERATED ALWAYS AS (
                        decimal_mul(decimal_add(decimal_mul(cost, decimal_add(1, loss)), add_cost, edg_cost), decimal_sub(1, discount))
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


