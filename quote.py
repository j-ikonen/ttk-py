"""Interface for database and container for app state"""

from db.database import Database
import values as val
#from event import EventHandler
import event as evt


class AppState:
    """Handle application state and it's changes."""
    def __init__(self):
        # Group id of the open group, None if no group is open
        self.open_group: int = None
        self.open_group_label: str = None
        self.open_quote: int = None
        self.open_quote_label: str = None


class Quote(evt.EventHandler):
    """Interface for database class."""
    def __init__(self):
        self.database: Database = Database("test", True, True, True)
        self.state = AppState()

    def get_group_list(self, quote_id: int=None):
        """Return a list of groups in quote as [[group_id, name], ...]

        If no quote_id is given and no quote is opened, return an empty list.

        Parameters
        ----------
        quote_id : int, optional
            ID of quote whose groups are returned, keep as None to return
            open quotes groups.
        """
        if quote_id is None:
            quote_id = self.state.open_quote

        if quote_id is None:
            return []

        values = self.database.groups.select(quote_id)
        return [[row[0], row[2]] for row in values]

    def set_group_name(self, name):
        """Update the opened groups name."""
        self.database.groups.update(self.state.open_group, 2, name)
        #self.state.event(val.EVT_GROUP_NAME)
        self.notify(evt.GROUP_CHANGE, evt.Event(self, [name]))

    def delete_groups(self, items: list):
        """Delete groups with ids given in items list"""
        for i in items:
            if i == self.state.open_group:
                self.state.open_group = None
                self.notify(evt.GROUP_SELECT, evt.Event(self, [i]))
                #self.state.event(val.EVT_SELECT_GROUP)

            success = self.database.groups.delete(i)
            if not success:
                print(f"Failed to delete group with id '{i}'.")

        self.notify(evt.GROUP_CHANGE, evt.Event(self, []))

    def select_group(self, group_id):
        """Select a group and run the events bound to it."""
        self.state.open_group = group_id
        # self.state.event(val.EVT_SELECT_GROUP)
        self.notify(evt.GROUP_SELECT, evt.Event(self, [group_id]))

    def get_group_name(self, group_id: int=None):
        """Return the name of the group with id, or the open group if id is None."""
        if group_id is None:
            group_id = self.state.open_group
        if group_id is None:
            return ""

        row = self.database.groups.select(filt={0: ["=", group_id]})
        try:
            return row[0][2]
        except IndexError:
            print(f"Could not find the group name with id {group_id}")
            return ""

    def get_quotes(self, search_term):
        """Return a list of [quote_id, quote_name] matching the search term."""
        filt = {1: ["like", f"{search_term}%"]}
        result = self.database.offers.select(filt=filt, pagination=(10,0))
        return [[row[0], row[1]] for row in result]

    def open_quote(self, quote_id, label):
        """Open the given quote."""
        self.state.open_quote = quote_id
        self.state.open_quote_label = label
        # self.state.event(val.EVT_OPEN_QUOTE)
        self.notify(evt.QUOTE_OPEN, evt.Event(self, [quote_id, label]))
        self.notify(evt.GROUP_CHANGE, evt.Event(self, []))

    def new_quote(self, name: str=""):
        """Create a new quote to db."""
        primary_key = self.database.offers.insert_empty()
        if primary_key:
            if self.database.offers.update(primary_key, val.COL_QUOTE_NAME, name):
                return primary_key

            self.database.offers.delete(primary_key)
        return None

    def new_group(self):
        """Create a new group to the opened quote."""
        foreign_key = self.state.open_quote
        if foreign_key:
            self.database.groups.insert([foreign_key, "Uusi Ryhmä"])
            self.notify(evt.GROUP_CHANGE, evt.Event(self, []))
        else:
            print("No quote is opened where a new group can be added.")

    def select_table(self, table: int):
        """Return the table class for given table id."""
        db_tb = None
        if table is val.TBL_QUOTE:
            db_tb = self.database.offers
        elif table is val.TBL_GROUP:
            db_tb = self.database.groups
        elif table is val.TBL_PREDEF:
            db_tb = self.database.group_predefs
        elif table is val.TBL_MATERIAL:
            db_tb = self.database.group_materials
        elif table is val.TBL_PRODUCT:
            db_tb = self.database.group_products
        elif table is val.TBL_PART:
            db_tb = self.database.group_parts

        return db_tb

    def n_cols(self, table_id):
        """Return the number of columns in the table."""
        table = self.select_table(table_id)
        try:
            return table.get_num_columns()
        except AttributeError:
            print(f"Table id {table_id} is not a valid table.")
            return 0

    def col_label(self, table_id, col):
        """Return the label for the column."""
        table = self.select_table(table_id)
        return table.get_column_label(col)

    def col_type(self, table_id, col):
        """Return the label for the column."""
        table = self.select_table(table_id)
        return table.get_column_type(col)

    def set_cell(self, table_id, primary_key, col, value):
        """Set the value of a cell in table."""
        table = self.select_table(table_id)
        return table.update(primary_key, col, value)

    def table_update(self, table_id, _col):
        """Handle the update of a value in a table.

        Process events related to it.
        """
        _table = self.select_table(table_id)


if __name__ == '__main__':
    from build_test_db import build_test_db
    build_test_db()
    quote = Quote()
    quote.get_group_list(1)
    quote.get_group_list(2)
    quote.get_group_list(3)
