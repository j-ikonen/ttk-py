import sqlite3
from sqlite3.dbapi2 import PARSE_DECLTYPES


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
            print("Could not create table: {}".format(self.name))
            print("sqlite3.OperationalError: {}".format(e))

    def insert(self, values: list, many=False, include_rowid=True):
        """Insert one or many values to database.

        Parameters
        ----------
        values : list
            A list or values or a list of rows.

        Returns
        -------
        int
            Last row id if inserting a single row. None otherwise.
        """
        if include_rowid:
            keys = self.keys_insert
        else:
            keys = self.keys_insert[1:]
        binds = ",".join(["?"] * len(keys))
        sql = "INSERT INTO {t}({k}) VALUES ({b})".format(t=self.name, k=keys, b=binds)

        with self.con:
            if many:
                self.con.executemany(sql, values)
            else:
                return self.con.execute(sql, values).lastrowid
        return None


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