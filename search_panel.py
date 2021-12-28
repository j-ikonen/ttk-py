from grid import DbGrid
import wx

from db.database import Database
from sizes import Sizes


class SearchPanel(wx.Panel):
    def __init__(self, parent, db: Database, open_table: int=0, open_column: int=0):
        super().__init__(parent)

        self.db = db
        self.table_keys = db.get_table_keys()
        self.table_labels = db.get_table_labels()
        self.col_keys = []
        self.col_labels = []
        operators = ("like", "=", "!=", ">", ">=", "<", "<=")
        self.selected_offer: int = None
        self.selected_group: int = None
        self.on_open_offer = []
        self.on_copy_group = []
        self.set_columns(open_table)

        self.choice_table = wx.Choice(self, choices=self.table_labels)
        self.choice_column = wx.Choice(self, choices=self.col_labels)
        self.choice_op = wx.Choice(self, choices=operators)
        self.search = wx.SearchCtrl(self, size=(Sizes.search,-1))
        self.btn_add_term = wx.Button(self, label="+", size=(Sizes.btn_s, -1))
        self.btn_to_offer = wx.Button(self, label="Lisää tarjoukseen.")
        self.grid = DbGrid(self, db.search_tables[self.table_keys[open_table]])
        # ADD CHECKLISTBOX FOR DISPLAYING SEARCH TERMS
        # ADD BUTTON TO REMOVE SELECTED SEARCH TERMS

        self.choice_table.Select(open_table)
        self.choice_column.Select(open_column)
        self.choice_op.Select(0)

        self.btn_add_term.SetToolTip("Lisää hakuehto.")
        self.btn_to_offer.SetToolTip("Lisää valitut rivit aktiiviseen tarjoukseen tai ryhmään.")
        self.choice_table.SetToolTip("Valitse etsittävä taulukko.")
        self.choice_column.SetToolTip("Valitse etsittävä sarake.")
        self.choice_op.SetToolTip("Valitse operaattori.")
        self.search.SetToolTip("Syötä hakutermi.")

        self.Bind(wx.EVT_CHOICE, self.on_choice_table, self.choice_table)
        self.Bind(wx.EVT_CHOICE, self.on_choice_column, self.choice_column)
        self.Bind(wx.EVT_SEARCH, self.on_search, self.search)
        self.Bind(wx.EVT_BUTTON, self.on_add_term, self.btn_add_term)
        self.Bind(wx.EVT_BUTTON, self.on_to_offer, self.btn_to_offer)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer_bar = wx.BoxSizer(wx.HORIZONTAL)

        sizer_bar.Add(self.choice_table, 0)
        sizer_bar.Add(self.choice_column, 0)
        sizer_bar.Add(self.choice_op, 0)
        sizer_bar.Add(self.search, 0, wx.EXPAND)
        sizer_bar.Add(self.btn_add_term, 0)
        sizer_bar.Add(self.btn_to_offer, 0)

        sizer.Add(sizer_bar, 0, wx.EXPAND)
        sizer.Add(self.grid, 1, wx.EXPAND)
        
        self.SetSizer(sizer)

        self.search.SetValue("%")
        self.on_search(None)


    def set_columns(self, table_idx):
        """Set the column keys and labels."""
        columns = self.db.get_columns_search(self.table_keys[table_idx])
        self.col_keys, self.col_labels = zip(*columns)

    def selected_column(self) -> int:
        """Return selected column index."""
        choice = self.choice_column.GetSelection()
        return choice if choice is not wx.NOT_FOUND else None

    def selected_table(self) -> int:
        """Return selected table index."""
        choice = self.choice_table.GetSelection()
        return choice if choice is not wx.NOT_FOUND else None
    
    def selected_operator(self) -> str:
        return self.choice_op.GetStringSelection()

    def on_choice_table(self, evt):
        """Handle choice table event."""
        # print("Selected table: {}".format(self.table_labels[evt.GetInt()]))
        self.set_columns(evt.GetInt())
        self.choice_column.Set(self.col_labels)
        self.choice_column.SetSelection(0)
        self.grid.Destroy()
        self.grid = DbGrid(self, self.db.search_tables[self.table_keys[evt.GetInt()]])
        self.GetSizer().Add(self.grid, 1, wx.EXPAND)
        self.Layout()

    def on_choice_column(self, evt):
        """Handle choice column event."""
        # print("Selected column: {}".format(self.col_labels[evt.GetInt()]))
        # print("choice_col")
        evt.Skip()

    def on_search(self, evt):
        """Handle search event.
        
        {key: [operator, value]}
        """
        # print("search")
        # table = self.db.get_table(self.table_keys[self.selected_table()])
        self.grid.set_filter({
            self.selected_column(): [
                self.selected_operator(),
                self.search.GetValue()
            ]
        })

    def on_add_term(self, evt):
        """Handle add term event."""
        print("add term")

    def select_offer(self, offer_id: int):
        """Select the offer for copying groups from database."""
        self.selected_offer = offer_id

    def select_group(self, group_id: int):
        """Select the group where copied materials, products and parts from database go."""
        self.selected_group = group_id

    def update(self):
        """Update the panel content."""
        self.grid.update_content()

    def on_to_offer(self, evt):
        """Handle event for adding selected rows to the selected group or offer."""
        selected_ids = [self.grid.get_rowid(row) for row in self.grid.GetSelectedRows()]
        self.grid.ClearSelection()
        key = self.table_keys[self.selected_table()]

        if key == "offers":
            for offer_id in selected_ids:
                self.db.open_offer(offer_id)
                for fn in self.on_open_offer:
                    fn()

        elif key == "groups":
            for group_id in selected_ids:
                self.db.copy_group(group_id)
                for fn in self.on_copy_group:
                    fn()

        else:
            target_table = self.db.get_cattable(key)
            for rowid in selected_ids:
                target_table.from_catalogue(rowid, self.selected_group)

    def get_db_table(self):
        """Return the active database table."""
        return self.db.search_tables[self.table_keys[self.selected_table()]]

    def register_on_open_offer(self, fn):
        """Register a function to run when an offer is opened."""
        self.on_open_offer.append(fn)

    def register_on_copy_group(self, fn):
        """Register a function to run when a group is copied."""
        self.on_copy_group.append(fn)


if __name__ == '__main__':
    app = wx.App()

    database = Database(print_err=True)
    frame = wx.Frame(None, title="SearchPanelTest")
    panel = SearchPanel(frame, database)

    Sizes.scale(frame)
    frame_size = (Sizes.frame_w, Sizes.frame_h)
    frame.SetClientSize(frame_size)

    frame.Show()
    app.MainLoop()
