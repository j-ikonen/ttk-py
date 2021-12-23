"""The predefs table class for database."""

from db.super import SQLTableBase


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
