"""Superclasses for database tables. """

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
