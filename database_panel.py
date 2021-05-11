from bson.objectid import ObjectId
import wx
import wx.dataview as dv

import grid
import table as db


class DatabasePanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)


if __name__ == '__main__':
    app = wx.App(useBestVisual=True)
    offer_keys = ["id", "name"]
    offer_data = [
        (str(ObjectId()), "Tarjous 1"),
        (str(ObjectId()), "Tarjous 2"),
        (str(ObjectId()), "Testi tarjous"),
        (str(ObjectId()), "Uusi tarjous")
    ]
    group_keys = ["id", "offer_id", "name"]
    group_data = [
        (str(ObjectId()), offer_data[0][0], "Keittiö"),
        (str(ObjectId()), offer_data[0][0], "Kylpyhuone"),
        (str(ObjectId()), offer_data[1][0], "Keittiö"),
        (str(ObjectId()), offer_data[2][0], "Keittiö"),
        (str(ObjectId()), offer_data[3][0], "Keittiö"),
        (str(ObjectId()), offer_data[3][0], "...")
    ]

    tables = db.OfferTables()

    offer_id = tables.insert_many("offers", offer_keys, offer_data)
    group_id = tables.insert_many("offer_groups", group_keys, group_data)

    frame = wx.Frame(None, size=(1200, 500))
    panel = DatabasePanel(frame)

    frame.Show()
    frame.Layout()

    app.MainLoop()
