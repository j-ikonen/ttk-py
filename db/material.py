"""The materials table class for database."""

from db.super import SQLTableBase, CatalogueTable


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
