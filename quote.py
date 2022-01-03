"""Interface for database and container for app state"""

from db.database import Database
import values as val


class AppState:
    """Handle application state and it's changes."""
    def __init__(self):
        # Group id of the open group, None if no group is open
        self.open_group: int = None
        self.open_quote: int = None
        # Events for changing state
        self.select_group_events = []
        self.ch_group_name_events = []
        self.delete_group_events = []

    def select_event_list(self, event_id):
        """Return the list of events or None."""
#        print(f"EVENT_ID: {event_id}, TYPE: {type(event_id)}")
        if event_id is val.EVT_SELECT_GROUP:
            return self.select_group_events

        elif event_id is val.EVT_GROUP_NAME:
            return self.ch_group_name_events

        elif event_id is val.EVT_DELETE_GROUP:
            return self.delete_group_events

        else:
            return None

    def event(self, event_id):
        """Do the events bound with event_id."""
        events = self.select_event_list(event_id)
#        try:
        for evt in events:
            evt()
#        except AttributeError:
#            print(f"Undefined event id {event_id} in state.event")

    def bind(self, event_id, fun):
        """Register a listener."""
        events = self.select_event_list(event_id)
        try:
            events.append(fun)
        except AttributeError:
            print(f"Undefined event id {event_id} in state.bind")


class Quote:
    """Interface for database class."""
    def __init__(self):
        self.database: Database = Database("test", True, True, True)
        self.state = AppState()

    def get_group_list(self, quote_id: int=None):
        """Return a list of groups in quote as [[group_id, name], ...]

        Parameters
        ----------
        quote_id : int, optional
            ID of quote whose groups are returned, keep as None to return
            open quotes groups.
        """
        if quote_id is None:
            quote_id = self.state.open_quote

        values = self.database.groups.select(quote_id)
        return [[row[0], row[2]] for row in values]

    def set_group_name(self, name):
        """Update the opened groups name."""
        self.database.groups.update(self.state.open_group, 2, name)
        self.state.event(val.EVT_GROUP_NAME)

    def delete_groups(self, items: list):
        """Delete groups with ids given in items list"""
        for i in items:
            success = self.database.groups.delete(i)
            if not success:
                print(f"Failed to delete group with id '{i}'.")

    def select_group(self, group_id):
        """Select a group and run the events bound to it."""
        self.state.open_group = group_id
        self.state.event(val.EVT_SELECT_GROUP)

    def get_group_name(self, group_id: int=None):
        """Return the name of the group with id, or the open group if id is None."""
        if group_id is None:
            group_id = self.state.open_group
        row = self.database.groups.select(filt={0: ["=", group_id]})
#        print(f"ROW: {row}")
        return row[0][2]


if __name__ == '__main__':
    from build_test_db import build_test_db
    build_test_db()
    quote = Quote()
    quote.get_group_list(1)
    quote.get_group_list(2)
    quote.get_group_list(3)
