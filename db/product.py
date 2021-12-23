"""The products table class for database."""

from db.super import SQLTableBase, CatalogueTable


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
                a.part_cost AS 'part_cost [pydecimal]',
                product_cost(
                    a.part_cost,
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
