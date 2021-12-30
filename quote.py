"""Interface for database and container for app state"""

from db.database import Database
import values as val


class Quote:
    """Interface for database class."""
    def __init__(self):
        self.open_group = None
        self.sel_group_listeners = []
        self.group_name_listeners = []
        self.database = Database()


class TestQuote:
    """Mock class for quote."""
    def __init__(self):
        self.open_group = None
        self.sel_group_listeners = []
        self.group_name_listeners = []
        self.data = [["Ryhmä1", 1], ["Toinen", 2], ["Kolmas", 3]]

    def get_group_list(self):
        """."""
        return self.data

    def set_group_name(self, name):
        """Update the opened groups name."""
        for group in self.data:
            if group[1] == self.open_group:
                group[0] = name

        for listener in self.group_name_listeners:
            listener()

    def delete_groups(self, items):
        """."""
        self.data = [i for i in self.data if i[1] not in items]

    def select_group(self, group_id):
        """."""
        self.open_group = group_id
        print(f"TestQuote.select_group({group_id})")
        for listener in self.sel_group_listeners:
            listener()

    def get_group_title(self):
        """Return the id and title string of the open group"""
        for group in self.data:
            if group[1] == self.open_group:
                return group[0]
        return ""

    def register(self, tar, listener):
        """Register a listener."""
        if tar is val.SELECT_GROUP:
            self.sel_group_listeners.append(listener)
        elif tar is val.GROUP_NAME:
            self.group_name_listeners.append(listener)
        else:
            print(f"Undefined target '{tar}' in quote.register.")
