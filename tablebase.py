import sqlite3


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

    def __init__(self, connection):
        self.con: sqlite3.Connection = connection

        self.name = None
        self.sql_create_table = None
        self.indexes = None
        self.primary_key = None
        self.foreign_key = None
        self.read_only = None
        self.default_columns = None
        self.keys_insert = None
    
    def create(self):
        """Create the table and it's indexes."""
        try:
            with self.con:
                self.con.execute(self.sql_create_table)
                for idx in self.indexes:
                    self.con.execute(idx)
                cols = []
                for n, col in enumerate(self.default_columns):
                    ro = 1 if col[self.KEY] in self.read_only else 0
                    cols.append(list(col) + [n, n, 60, ro, 1])
                self.con.execute("""
                    INSERT INTO columns (*) VALUES (?,?,?,?,?,?,?,?,?)
                """, self.cols)

        except sqlite3.OperationalError as e:
            print("\nsqlite3.OperationalError: {}".format(e))
            print("Could not create table: {}".format(self.name))

    def execute_dml(self, sql: str, values: list=None, many: bool=False) -> int:
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

        Returns
        -------
        int
            Last rowid. If statement was not INSERT or REPLACE or 'many' was set True
            return -1.
        None
            On sqlite3.IntegrityError
        """
        rowid = -1
        try:
            with self.con:
                if many:
                    if values is None:
                        self.con.executemany(sql)
                    else:
                        self.con.executemany(sql, values)
                else:
                    if values is None:
                        rowid = self.con.execute(sql).lastrowid
                    else:
                        rowid = self.con.execute(sql, values).lastrowid

        except sqlite3.IntegrityError as e:
            print("\nsqlite3.IntegrityError: {}".format(e))
            print("In SQLTableBase.execute_dml")
            print("Error with sql: {}".format(sql))
            print("using values: {}".format(values))
            return None
        return rowid

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

        except sqlite3.IntegrityError as e:
            print("\nsqlite3.IntegrityError: {}".format(e))
            print("In SQLTableBase.execute_dql")
            print("Error with sql: {}".format(sql))
            print("using values: {}".format(values))
            return None

        if cursor:
            return cur
        else:
            return cur.fetchall()

    def insert(self, values: list, many=False, include_rowid=True):
        """Insert one or many values to database.

        Parameters
        ----------
        values : list
            A list or values or a list of rows.

        Returns
        -------
        int
            Last rowid. If 'many' was set True return -1. On error return None.
        """
        if include_rowid:
            keys = self.keys_insert
        else:
            keys = self.keys_insert[1:]
        binds = ",".join(["?"] * len(keys))
        sql = "INSERT INTO {t}({k}) VALUES ({b})".format(t=self.name, k=keys, b=binds)

        return self.execute_dml(sql, values, many)

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
            sql = sql_ins.format(self.name)
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
        key = self.keys_select[col]
        sql = "UPDATE {t} SET {k}=(?) WHERE {pk}=(?)".format(
            t=self.name,
            k=key,
            pk=self.primary_key
        )
        values = (value, pk)
        result = self.execute_dml(sql, values)
        return True if result == -1 else False

    def delete(self, pk: int) -> bool:
        sql = "DELETE FROM {t} WHERE {pk}=(?)".format(t=self.name, pk=self.primary_key)
        values = (pk,)
        return True if self.execute_dml(sql, values) == -1 else False

    def get_labels(self) -> list:
        raise NotImplementedError("\nget_labels is not implemented")

    def get_width(self, col: int) -> int:
        raise NotImplementedError("\nget_width is not implemented")

    def set_width(self, col: int, width: int) -> bool:
        raise NotImplementedError("\nset_width is not implemented")

    def is_readonly(self, col: int) -> bool:
        """Return True if column at index 'col' is read only."""
        return self.keys_select.index(col) in self.read_only

    def get_visible(self) -> list:
        raise NotImplementedError("\nget_visible is not implemented")

    def set_visible(self, col: int, is_visible: bool) -> bool:
        raise NotImplementedError("\nset_visible is not implemented")


class GroupMaterialsTable(SQLTableBase):
    def __init__(self, connection):
        super().__init__(connection)
        self.name = "group_materials"
        self.sql_create_table = """
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
        self.indexes = [
            """CREATE INDEX idx_gm_group_id ON group_materials(group_id)"""
        ]
        self.primary_key = "gm_id"
        self.foreign_key = "group_id"
        self.read_only = ["gm_id", "group_id", "tot_cost"]
        self.default_columns = [
            ("group_materials", "gm_id", "MateriaaliID", "long",),
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
        self.keys_insert = [
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
            "discount"
        ]
        self.keys_select = []