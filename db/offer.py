"""The offers table class for database."""

from db.super import SQLTableBase


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
