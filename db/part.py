"""The parts table class for database."""

from db.super import SQLTableBase, CatalogueTable


class GroupPartsTable(CatalogueTable):
    def __init__(self, connection):
        cat_table = PartsTable(connection)
        super().__init__(connection, cat_table)
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
        self.read_only = [
            "group_part_id",
            "group_product_id",
            "width",
            "length",
            "cost",
            # "m.thickness",
            # "m.tot_cost",
            # "pr.width",
            # "pr.height",
            # "pr.depth"
        ]
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
            # ("group_parts", "m.thickness", "Paksuus", "long"),
            # ("group_parts", "m.tot_cost", "Mat. Hinta", "double:6,2"),
            # ("group_parts", "pr.width", "Tuote leveys", "long"),
            # ("group_parts", "pr.height", "Tuote korkeus", "long"),
            # ("group_parts", "pr.depth", "Tuote syvyys", "long")
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
        """Update parts values before returning the select list.
        
        Returns the parts only if it's foreign key
        product exists in group_products table.
        """
        # SELECT all parts of product with fk as id.
        parts = super().select(fk, None)
        # for part in parts:
        #     print(part)
        # Parse the codes in parts of this product and return changed values.
        new_values = self.parse_codes(parts)
        # UPDATE the changed values.
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

    def get_select_query(self, count: bool=False):
        """Return GroupParts SELECT statement with pydecimal formattings.

        Parameters
        ----------
        count : bool, optional
            Set True to return query for count of entries instead of content.
        """
        if count:
            return """
                SELECT
                    COUNT(*)
                FROM
                    group_parts AS pa
            """
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
                pa.cost AS 'pa.cost [pydecimal]',
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
                m.tot_cost AS 'm.tot_cost [pydecimal]',
                pr.width,
                pr.height,
                pr.depth,
                pr.group_id,
                d.material,
                m.code

            FROM group_parts AS pa
                INNER JOIN group_products AS pr
                    ON pa.group_product_id=pr.group_product_id

                LEFT JOIN group_predefs AS d
                    ON pr.group_id=d.group_id AND pa.part=d.part

                LEFT JOIN group_materials AS m
                    ON 
                        pr.group_id=m.group_id AND 
                        m.code = (
                            CASE
                                WHEN pa.use_predef=0 THEN
                                    pa.default_mat
                                ELSE
                                    d.material
                            END
                        )
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
            INSERT INTO group_parts(
                group_product_id,
                part,
                count,
                code,
                desc,
                default_mat,
                code_width,
                code_length,
                code_cost)
            SELECT
                (?),
                part,
                count,
                code,
                desc,
                default_mat,
                code_width,
                code_length,
                code_cost
            FROM
                parts
            WHERE
                part_id=(?)
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
            INSERT INTO parts(
                part,
                count,
                code,
                desc,
                default_mat,
                code_width,
                code_length,
                code_cost)
            SELECT
                part,
                count,
                code,
                desc,
                default_mat,
                code_width,
                code_length,
                code_cost
            FROM
                group_parts
            WHERE
                group_part_id=(?)
        """
        return super().to_catalogue(sql, (rowid,))




class PartsTable(SQLTableBase):
    def __init__(self, connection):
        super().__init__(connection)
        self.name = "parts"
        self.sql_create_table = """
            CREATE TABLE IF NOT EXISTS parts (
                part_id         INTEGER PRIMARY KEY,
                product_id      INTEGER,
                part            TEXT,
                count           INTEGER DEFAULT 1,
                code            TEXT,
                desc            TEXT,
                default_mat     TEXT,
                code_width      TEXT,
                code_length     TEXT,
                code_cost       TEXT,

                UNIQUE (product_id, part),
                FOREIGN KEY (product_id)
                    REFERENCES products (product_id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE
            )
        """
        self.indexes = [
            """CREATE INDEX IF NOT EXISTS idx_parts_fk ON parts(product_id, part)"""
        ]
        self.primary_key = "part_id"
        self.foreign_key = "product_id"
        self.read_only = ["part_id", "product_id"]
        self.default_columns = [
            ("parts", "part_id", "OsaID", "long"),
            ("parts", "product_id", "TuoteID", "long"),
            ("parts", "part", "Osa", "string"),
            ("parts", "count", "Määrä", "long"),
            ("parts", "code", "Koodi", "string"),
            ("parts", "desc", "Kuvaus", "string"),
            ("parts", "default_mat", "Oletus materiaali", "string"),
            ("parts", "code_width", "Koodi Leveys", "string"),
            ("parts", "code_length", "Koodi Pituus", "string"),
            ("parts", "code_cost", "Koodi Hinta", "string")
        ]
        self.table_keys = [
            "part_id",
            "product_id",
            "part",
            "count",
            "code",
            "desc",
            "default_mat",
            "code_width",
            "code_length",
            "code_cost"
        ]
