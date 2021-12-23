""" Classes to store and retrieve single variables from db. """

import sqlite3


class VarID:
    """Use as primary key to find the variables in local database table 'variables'."""
    WORK_COST = 0
    INSTALL_UNIT_MULT = 1

    COL = {
        WORK_COST: "value_decimal",
        INSTALL_UNIT_MULT: "value_decimal"
    }

    @classmethod
    def col(cls, id, set=False) -> str:
        """Return the column name used by given 'id'.

        Parameters
        ----------
        id : int
            ID to row of a variable.
        set : bool, default: False
            Set to True to return column name for UPDATE statement instead of
            SELECT statement.
        """
        col_name = cls.COL[id]
        if set:
            return col_name
        else:
            if col_name == "value_decimal":
                col_name = "value_decimal AS 'value_decimal [pydecimal]'"
            return col_name


class Variables:
    """Get and set the local variables table values."""
    PRINT_ERRORS = False

    @classmethod
    def print_errors(cls, value=True):
        cls.PRINT_ERRORS = value

    @classmethod
    def get(cls, con: sqlite3.Connection, var_id: VarID):
        """Return the value for var_id."""
        col_name = VarID.col(var_id)
        sql = """
            SELECT {c}
            FROM variables
            WHERE variable_id = (?)
        """.format(c=col_name)
        try:
            with con:
                cur = con.execute(sql, (var_id,))
                return cur.fetchone()[0]

        except sqlite3.Error as e:
            if cls.print_errors:
                print("\n{}: {}".format(type(e), e))
                print("In SQLTableBase.execute_dql")
                print("Error with sql: {}".format(sql))
                print("using values: {}".format((var_id,)))
            return None

    @classmethod
    def set(cls, con: sqlite3.Connection, var_id: VarID, value):
        """Set the value for var_id."""
        col_name = VarID.col(var_id, True)
        sql = """
            UPDATE variables
            SET {c}=(?)
            WHERE variable_id=(?)
        """.format(c=col_name)
        values = (value, var_id)
        try:
            with con:
                con.execute(sql, values)
                return True

        except sqlite3.Error as e:
            if cls.print_errors:
                print("\n{}: {}".format(type(e), e))
                print("In SQLTableBase.execute_dql")
                print("Error with sql: {}".format(sql))
                print("using values: {}".format(values))
            return False
