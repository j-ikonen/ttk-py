
import os
import json

import wx
from wx.core import MultiChoiceDialog

from ttk_data import Data, DataItem, DataRoot
from panel import Panel, FRAME_SIZE


FRAME_TITLE = "Ttk-py"
WORKSPACE_FILE = "workspace.json"
SAVE_FILE_MESSAGE = "Tallenna nimellä ..."
SAVING_TO = "Tallennetaan tarjous tiedostoon {}"
SAVEAS_CANCEL = "Tallennus peruttu."
WILDCARD = "JSON file (*.json) |*.json"
OPEN_FILE_MESSAGE = "Valitse tiedosto."
OPENING_FILE = "Avataan tiedosto {}"
SAVE_NO_PATH = ("Tarjoukselle ei ole määritetty tallenus tiedostoa." +
                " Avataan Tallenna nimellä ...")
MENU_TITLE_DB = "Tietokanta"
LABEL_ADD_TO_DB = "Lisää"
HELP_ADD_TO_DB = "Lisää tietokantaan."

ID_ADD_TO_DB = wx.NewIdRef()

CLOSE_ITEM_MSG = "Sulje valitut tarjoukset"
CLOSE_ITEM_CAP = "Sulje tarjoukset"
ROOTDATA_FILE = "ttk_rootdata.json"
SETUP_FILE = "ttk_setup.json"


def read_file(path, file) -> dict:
    if path is None:
        filepath = file
    else:
        filepath = path + '\\' + file
    try:
        with open(filepath, 'r') as rf:
            return json.load(rf)
    except FileNotFoundError as e:
        print(f"{e}")
        return None
    except json.decoder.JSONDecodeError as e:
        print(f"{filepath}\n\tFile is not a valid json.")
        return None

def write_file(path, file, data):
    if path is None:
        filepath = file
    else:
        filepath = path + '\\' + file
    with open(filepath, 'w') as wf:
        json.dump(data, wf, indent=4)


class AppFrame(wx.Frame):
    def __init__(self, data, setup):
        super().__init__(
            None,
            title=FRAME_TITLE,
            size=FRAME_SIZE,
            style=wx.DEFAULT_FRAME_STYLE|wx.FULL_REPAINT_ON_RESIZE
        )

        self.setup: dict = read_file(None, SETUP_FILE)
        if self.setup is None:
            self.setup: dict = setup

        from_file = read_file(None, ROOTDATA_FILE)
        if from_file is None:
            self.data: Data = data
        else:
            self.data: Data = Data.from_dict(from_file, self.setup)

        self.CenterOnScreen()
        self.create_menubar()

        self.panel = Panel(self, data, setup)

        self.Bind(wx.EVT_CLOSE, self.on_close_window)

    def on_close_window(self, evt):
        print("Closing frame.")
        root = self.data.get([0])
        root.delete_all_children()
        # write_file(None, ROOTDATA_FILE, root.get_dict())
        # write_file(None, SETUP_FILE, self.setup)

        self.Destroy()

    def create_menubar(self):
        menu_bar = wx.MenuBar()
        menu_file = wx.Menu()
        # menu_db = wx.Menu()

        menu_file.Append(wx.ID_NEW)
        menu_file.Append(wx.ID_OPEN)
        menu_file.Append(wx.ID_CLOSE)
        menu_file.Append(wx.ID_SAVE)
        menu_file.Append(wx.ID_SAVEAS)
        menu_file.Append(wx.ID_SEPARATOR)
        menu_file.Append(wx.ID_EXIT)

        # menu_db.Append(ID_ADD_TO_DB, LABEL_ADD_TO_DB, HELP_ADD_TO_DB)
        # menu_db.Append(wx.ID_OPEN)

        menu_bar.Append(menu_file, wx.GetStockLabel(wx.ID_FILE))
        # menu_bar.Append(menu_db, MENU_TITLE_DB)

        self.SetMenuBar(menu_bar)

        self.Bind(wx.EVT_MENU, self.menu_new, id=wx.ID_NEW)
        self.Bind(wx.EVT_MENU, self.menu_open, id=wx.ID_OPEN)
        self.Bind(wx.EVT_MENU, self.menu_close, id=wx.ID_CLOSE)
        self.Bind(wx.EVT_MENU, self.menu_save, id=wx.ID_SAVE)
        self.Bind(wx.EVT_MENU, self.menu_saveas, id=wx.ID_SAVEAS)
        self.Bind(wx.EVT_MENU, self.menu_exit, id=wx.ID_EXIT)

        # self.Bind(wx.EVT_MENU, self.menu_db_add, id=ID_ADD_TO_DB)

    def menu_new(self, evt):
        """Create new offer."""
        # self.panel.data.new_offer()
        data_item = self.data.get([0]).push("Uusi Tarjous", self.setup)
        data_item.push("Uusi ryhmä", self.setup)
        self.panel.refresh_tree()

    def menu_open(self, evt):
        """Handle event for opening an offer from a file."""
        print("Frame.menu_open - TO BE IMPLEMENTED")
        dlg = wx.FileDialog(
            self,
            message=OPEN_FILE_MESSAGE,
            defaultDir=os.getcwd(),
            defaultFile="",
            wildcard=WILDCARD,
            style=wx.FD_OPEN | wx.FD_MULTIPLE | wx.FD_CHANGE_DIR |
                  wx.FD_FILE_MUST_EXIST | wx.FD_PREVIEW
        )

        # Get return code from dialog.
        if dlg.ShowModal() == wx.ID_OK:
            root = self.data.get([0])
            for path in dlg.GetPaths():
                # Check if an offer with 'path' is already open.
                if root.file_open(path):
                    print(f"Selected offer is already opened from path\n\t{path}.")
                    dlg.Destroy()
                    return

                # Open and read the file at path.
                print(OPENING_FILE.format(path))
                item_dict = read_file(None, path)

                # Create DataItem object from dictionary
                item: DataItem = DataItem.from_dict(item_dict)
                itemdata = item.get_data('file')
                itemdata['Polku'] = path

            # Refresh TreeList with new offers.
            self.panel.refresh_tree()
        dlg.Destroy()

    def menu_close(self, evt):
        """Open dialog for closing DataItems."""
        print("Frame.menu_close - TO BE IMPLEMENTED")
        itemlist = [item.get_name() for item in self.data.get([0]).get_children()]
        with MultiChoiceDialog(
            self, CLOSE_ITEM_MSG, CLOSE_ITEM_CAP, itemlist
        ) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                selected: list = dlg.GetSelections()
                selected.sort(reverse=True)
                root: DataRoot = self.data.get([0])
                for n in selected:
                    root.delete_child(n)
                self.panel.refresh_tree()

    def menu_save(self, evt):
        """Save selected offer to file.path if not empty."""
        # Get dictionary of selected offer.
        item: DataItem = self.data.get_active()

        if not isinstance(item, DataItem):
            print("No offer selected.")
            return

        path = item.get_data('file')['Polku']
        # file = item.get_data('file')['Tiedosto']

        if path != "":
            print(f"Saving '{item.get_name()}' to \n\t{path}")

            # Save offer dictionary to selected file.
            write_file(None, path, item.get_dict())
        else:
            print(SAVE_NO_PATH)
            self.menu_saveas(self, evt)

    def menu_saveas(self, evt):
        """Handle event for 'save as'."""
        # Get selected offer.
        item: DataItem = self.data.get_active()

        if not isinstance(item, DataItem):
            print("No offer selected.")
            return

        print(f"Saving '{item.get_name()}'")

        # Open FileDialog for Saving.
        dlg = wx.FileDialog(
            self,
            message=SAVE_FILE_MESSAGE,
            defaultDir=os.getcwd(),
            defaultFile="",
            wildcard=WILDCARD,
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        )
        # dlg.SetFilterIndex(1)     # For default WILDCARD

        # Get return code from dialog.
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            item.get_data('file')['Polku'] = path
            print(SAVING_TO.format(path))

            # Save item dictionary to selected file.
            write_file(None, path, item.get_dict())

        else:
            print(SAVEAS_CANCEL)

        dlg.Destroy()

    def menu_exit(self, evt):
        self.Close()

    # def menu_db_add(self, evt):
    #     print("Frame.menu_db_add")
        # from dialog import InsertToDbDialog

        # with InsertToDbDialog(self) as dlg:
        #     if dlg.ShowModal() == wx.ID_OK:
        #         pass
        #     else:
        #         pass
