"""."""

GROUP_SELECT = 100  # [primary_key]
GROUP_CHANGE = 101  # []

QUOTE_OPEN = 200    # [primary_key, name]

TABLE_CELL = 300    # [table_id, primary_key, col, value]
TABLE_ROW = 301     # [table_id, foreign_key, primary_key]


class EventHandler:
    """."""
    queue = {}

    def bind(self, code, handler):
        """Bind an event."""
        try:
            self.queue[code].append(handler)
        except KeyError:
            self.queue[code] = [handler]

    def notify(self, code, event):
        """Notify of the occurance of an event."""
        try:
            for handler in self.queue[code]:
                handler(event)
        except KeyError:
            pass


class Event:
    """."""
    def __init__(self, source, data=None):
        self.data = data
        self.source = source
