"""The groups table class for database."""

from super import SQLTableBase


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
