import wx
import wx.grid as wxg


class SetupGrid(wxg.Grid):
    def __init__(self, parent, setup):
        super().__init__(parent)
        self.CreateGrid(len(setup['fields']), 1)
        self.SetColLabelSize(1)

        for n, (key, value) in enumerate(setup['fields'].items()):
            self.SetRowLabelValue(n, value[2])
            self.index_to_key.append(key)

            split = value[1].split(':')
            if split[0] == 'long':
                self.SetCellEditor(n, 0, wxg.GridCellNumberEditor())
            elif split[0] == 'double':
                self.SetCellEditor(n, 0,
                    wxg.GridCellFloatEditor(precision=split[1].split(',')[1])
                )
    
    def update(self, data: list):
        self.ClearGrid()
        for n, value in enumerate(data):
            self.SetCellValue(n, 0, value)
