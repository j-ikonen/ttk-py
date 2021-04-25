
import os
import json

import wx

from data import Offer
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


class AppFrame(wx.Frame):
    def __init__(self, data):
        super().__init__(
            None,
            title=FRAME_TITLE,
            size=FRAME_SIZE,
            style=wx.DEFAULT_FRAME_STYLE|wx.FULL_REPAINT_ON_RESIZE
        )
        self.workspace = {
            "open_offers": []
        }
        
        # Load workspace info from file.
        try:
            with open(WORKSPACE_FILE, 'r') as rf:
                self.workspace = json.load(rf)
        except FileNotFoundError as e:
            print(f"No workspace file found: {e}")
        else:
            # Load offers open in last session.
            for path in self.workspace['open_offers']:
                try:
                    with open(path, 'r') as rf:
                        offer = Offer.from_dict(json.load(rf))
                        data.offers.append(offer)
                except FileNotFoundError as e:
                    print(f"{e}")
                except json.decoder.JSONDecodeError as e:
                    print(f"{path}\n\tFile is not a valid json.")

        self.CenterOnScreen()
        self.create_menubar()

        self.panel = Panel(self, data)

        self.Bind(wx.EVT_CLOSE, self.on_close_window)

    def on_close_window(self, evt):
        print("Closing frame.")
        # Save open offers to session workspace file.
        self.workspace['open_offers'] = []
        for offer in self.panel.data.offers:
            if offer.info.filepath != "":
                self.workspace['open_offers'].append(offer.info.filepath)

        # Save offer dictionary to selected file.
        with open(WORKSPACE_FILE, 'w') as fp:
            json.dump(self.workspace, fp, indent=4)

        self.Destroy()

    def create_menubar(self):
        menu_bar = wx.MenuBar()
        menu_file = wx.Menu()
        # menu_db = wx.Menu()

        menu_file.Append(wx.ID_NEW)
        menu_file.Append(wx.ID_OPEN)
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
        self.Bind(wx.EVT_MENU, self.menu_save, id=wx.ID_SAVE)
        self.Bind(wx.EVT_MENU, self.menu_saveas, id=wx.ID_SAVEAS)
        self.Bind(wx.EVT_MENU, self.menu_exit, id=wx.ID_EXIT)

        # self.Bind(wx.EVT_MENU, self.menu_db_add, id=ID_ADD_TO_DB)

    def menu_new(self, evt):
        """Create new offer."""
        self.panel.data.new_offer()
        self.panel.create_tree()

    def menu_open(self, evt):
        """Handle event for opening an offer from a file."""
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

            for path in dlg.GetPaths():
                # Check if an offer with 'path' is already open.
                if self.panel.data.file_opened(path):
                    print(f"Selected offer is already opened from path {path}.")
                    dlg.Destroy()
                    return

                # Open and read the file at path.
                print(OPENING_FILE.format(path))
                with open(path, 'r') as rf:
                    offer_dict = json.load(rf)

                # Create offer object from dictionary
                offer = Offer.from_dict(offer_dict)
                offer.info.filepath = path
                self.panel.data.offers.append(offer)

            # Refresh TreeList with new offers.
            self.panel.create_tree()
        dlg.Destroy()

    def menu_save(self, evt):
        """Save selected offer to info.filepath if not empty."""
        # Get dictionary of selected offer.
        offer = self.panel.get_selected_offer()
        path = offer.info.filepath
        if path != "":
            print(f"Saving '{offer.info.offer_name}' to '{path}'")
            
            # Save offer dictionary to selected file.
            with open(path, 'w') as fp:
                json.dump(offer.to_dict(), fp, indent=4)
        else:
            print(SAVE_NO_PATH)
            self.menu_saveas(self, evt)

    def menu_saveas(self, evt):
        """Handle event for 'save as'."""
        # Get selected offer.
        offer = self.panel.get_selected_offer()
        print(f"Saving '{offer.info.offer_name}'")

        # Open FileDialog for Saving.
        dlg = wx.FileDialog(
            self,
            message=SAVE_FILE_MESSAGE,
            defaultDir=os.getcwd(),
            defaultFile=offer.info.offer_name,
            wildcard=WILDCARD,
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        )
        # dlg.SetFilterIndex(1)     # For default WILDCARD

        # Get return code from dialog.
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            offer.info.filepath = path
            print(SAVING_TO.format(path))

            # Save offer dictionary to selected file.
            with open(path, 'w') as fp:
                json.dump(offer.to_dict(), fp, indent=4)

        else:
            print(SAVEAS_CANCEL)

        dlg.Destroy()

    def menu_exit(self, evt):
        self.Close()

    def menu_db_add(self, evt):
        print("Frame.menu_db_add")
        # from dialog import InsertToDbDialog

        # with InsertToDbDialog(self) as dlg:
        #     if dlg.ShowModal() == wx.ID_OK:
        #         pass
        #     else:
        #         pass
