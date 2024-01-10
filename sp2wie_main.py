import wx
from wxUI.main_window import MainWindow

app = wx.App(False)
frame = MainWindow(None, "Testowe")
frame.Show()
app.MainLoop()
