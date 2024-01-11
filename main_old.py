import os

import serial
import wx


def GetTty():
    ports = []
    sel = True
    selid = -1
    try:
        for file in os.listdir("/dev"):
            if file.startswith("tty"):
                ports.append(file)
                if file.startswith("ttyUSB") and sel:
                    ser = serial.Serial(f"/dev/{file}")
                    ser.write(b"ST?")
                    if ser.readline() == b"STST":
                        sel = False
                        selid = len(ports) - 1
                    ser.close()
    except Exception as e:
        wx.MessageBox(str(e), "Serial ports listing error", wx.OK | wx.ICON_ERROR)
    return [ports, selid]


class MyApp(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title="My App")
        self.InitUI()
        self.Show()
        self.bpwait = 0
        self.ftwait = 0
        self.port = None
        self.ser = None
        self.tryInitSerial()

    def InitUI(self):
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        menuBar = wx.MenuBar()

        portMenu = wx.Menu()
        portItem = portMenu.Append(wx.NewId(), "&Serial Port Settings", "Open Serial Port Settings")
        self.Bind(wx.EVT_MENU, self.OnPortMenu, portItem)
        menuBar.Append(portMenu, "Settings")
        self.SetMenuBar(menuBar)

        self.chboxBypass = wx.CheckBox(panel, label="bypass")  # checkbox for bypass function
        vbox.Add(self.chboxBypass, flag=wx.EXPAND, border=5)
        self.chboxBypass.Bind(wx.EVT_CHECKBOX, self.OnChBoxBypass)

        self.chboxForce = wx.CheckBox(panel, label="force TX")  # checkbox for force tx function
        vbox.Add(self.chboxForce, flag=wx.EXPAND, border=5)
        self.chboxForce.Bind(wx.EVT_CHECKBOX, self.OnChBoxForce)

        vbox2 = wx.BoxSizer(wx.HORIZONTAL)

        button1 = wx.Button(panel, label="Button 1")
        button1.Bind(wx.EVT_BUTTON, self.OnButtonClick)
        vbox2.Add(button1, flag=wx.EXPAND, border=5)

        button2 = wx.Button(panel, label="Button 2")
        vbox2.Add(button2, flag=wx.EXPAND, border=5)

        vbox.Add(vbox2, flag=wx.EXPAND, border=5)

        self.label = wx.StaticText(panel, label="")
        vbox.Add(self.label, flag=wx.EXPAND, border=5)
        self.timer = wx.Timer(self)
        self.timer.Start(1000)
        self.Bind(wx.EVT_TIMER, self.Update, self.timer)

        vboxM = wx.BoxSizer(wx.HORIZONTAL)

        vboxM.Add(vbox, flag=wx.EXPAND, border=5)

        panel.SetSizer(vboxM)

    def OnPortMenu(self, event):
        self.dlg = wx.Dialog(self, title="Another Window")
        self.mychoices = GetTty()
        panel = wx.Panel(self.dlg)
        vbox = wx.BoxSizer(wx.VERTICAL)

        self.portChoice = wx.Choice(panel, wx.ID_ANY, choices=self.mychoices[0], pos=(120, 20), size=(80, 30))
        if self.port in self.mychoices[0]:
            self.portChoice.SetSelection(self.mychoices[0].index(self.port))
        if self.portChoice.GetSelection() == -1:
            self.portChoice.SetSelection(self.mychoices[1])
        vbox.Add(self.portChoice, flag=wx.EXPAND, border=5)
        exitButton = wx.Button(panel, label="OK")
        exitButton.Bind(wx.EVT_BUTTON, self.onExitPortMenu)
        vbox.Add(exitButton, flag=wx.EXPAND, border=5)
        panel.SetSizer(vbox)
        self.dlg.ShowModal()
        self.dlg.Destroy()

    def onExitPortMenu(self, event):
        self.port = self.mychoices[0][self.portChoice.GetSelection()]
        try:
            self.ser = serial.Serial(f"/dev/{self.port}", timeout=3)
        except Exception as e:
            self.port = None
            wx.MessageBox(str(e), "Serial port initiation error", wx.OK | wx.ICON_ERROR)
        self.dlg.Destroy()

    def OnButtonClick(self, event):
        print("Button clicked!")

    def OnChBoxBypass(self, event):
        if self.ser is not None:
            if self.chboxBypass.IsChecked():
                print("Bypass is on")
                self.ser.write(b"STB1\n")
                self.bpwait = 4
            else:
                self.ser.write(b"STB0\n")
                print("Bypass is off")
                self.bpwait = 4
        else:
            self.chboxBypass.SetValue(False)
            wx.MessageBox("No serial port initialized", "Error", wx.OK | wx.ICON_ERROR)

    def OnChBoxForce(self, event):
        if self.ser is not None:
            if self.chboxForce.IsChecked():
                print("Force TX is on")
                self.ser.write(b"STT\n")
                self.ftwait = 4
            else:
                print("Force TX is off")
                self.ser.write(b"STR\n")
                self.ftwait = 4
        else:
            self.chboxForce.SetValue(False)
            wx.MessageBox("No serial port initialized", "Error", wx.OK | wx.ICON_ERROR)

    def Update(self, event):
        if self.port is not None:
            labelText = f"Port: /dev/{self.port}"
        else:
            labelText = "Please set serial port"
        self.label.SetLabel(labelText)
        if self.ser is not None and self.ser.is_open:
            self.ser.write(b"ST?\n")
            data = self.ser.readline().decode("UTF-8").replace("\r\n", "")
            data = data.split(",")
            if data[0] != "STST":
                self.port = None
                self.ser = None
                wx.MessageBox(
                    "incorrect response from device. Please check if the correct serial port is selected.",
                    "Error",
                    wx.OK | wx.ICON_ERROR,
                )
            else:
                if self.bpwait > 0:
                    self.bpwait -= 1
                else:
                    if data[3] == "0":
                        self.chboxBypass.SetValue(False)
                    else:
                        self.chboxBypass.SetValue(True)
                if self.ftwait > 0:
                    self.ftwait -= 1
                else:
                    if data[5] == "0":
                        self.chboxForce.SetValue(False)
                    else:
                        self.chboxForce.SetValue(True)

    def tryInitSerial(self):
        sr = GetTty()
        if sr[1] == -1:
            wx.MessageBox(
                "Unable to automatically detect the device. Configure it manually or check that it is connected and running",
                "Auto initialization error",
                wx.OK | wx.ICON_ERROR,
            )
        else:
            try:
                self.ser = serial.Serial(f"/dev/{self.port}", timeout=3)
            except Exception as e:
                wx.MessageBox(
                    str(e)
                    + "\n"
                    + "Unable to automatically detect the device. Configure it manually or check that it is connected and running",
                    "Serial port initiation error",
                    wx.OK | wx.ICON_ERROR,
                )


if __name__ == "__main__":
    app = wx.App()
    frame = MyApp()
    app.MainLoop()
