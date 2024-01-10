import logging
from serial import SerialException

import wx

from serial_comm.serial_comm import BadSerialResponseException, SerialCommander, SerialManager

logging.basicConfig(level=logging.DEBUG)


class MainWindow(wx.Frame):
    def __init__(self, parent, title: str) -> None:
        wx.Frame.__init__(self, parent, title=title, size=wx.Size(500, 300))

        self.serialCommander: SerialCommander = None

        # Menu configuration
        # TODO: add About menu
        settingsMenu = wx.Menu()
        portSettingsItem = settingsMenu.Append(wx.NewId(), "&Serial Port Settings", "Open Serial Port Settings")
        self.Bind(wx.EVT_MENU, self.OnPortSettings, portSettingsItem)
        menuBar = wx.MenuBar()
        menuBar.Append(settingsMenu, "Settings")
        self.SetMenuBar(menuBar)

        # Status bar config
        self.statusBar = self.CreateStatusBar()

        # Layout views
        self.main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        # Don't think we need the indicators for now
        # self.indicatorsPanel = IndicatorsPanel(self)
        # self.main_sizer.Add(self.indicatorsPanel, 0, wx.ALL, 5)

        self.controllsPanel = ControllsPanel(self)
        self.main_sizer.Add(self.controllsPanel, 1, wx.EXPAND | wx.ALL, 5)

        self.SetAutoLayout(1)
        self.main_sizer.Fit(self)
        self.main_sizer.SetSizeHints(self)
        self.SetSizer(self.main_sizer)

    def OnPortSettings(self, event):
        serial_ports = SerialManager.get_com_ports()
        if len(serial_ports) == 0:
            logging.error("Could not find suitable serial ports!")
            wx.MessageBox("Could not find suitable serial ports!", "Error", wx.OK | wx.ICON_ERROR)
            return
        setPortDialog = wx.SingleChoiceDialog(self, "Please select a serial port", "Select port", serial_ports)
        if setPortDialog.ShowModal() == wx.ID_OK:
            selectedPort = setPortDialog.GetStringSelection()
            try:
                self.serialCommander = SerialCommander(selectedPort)
                self.serialCommander.get_status()
            except SerialException as se:
                logging.error("Could not find or configure the device: %s [%s]", selectedPort, se)
                wx.MessageBox(
                    f"Could not find or configure the device: {selectedPort}", "Error", wx.OK | wx.ICON_ERROR
                )
                return
            except BadSerialResponseException as bsre:
                wx.MessageBox(f"{bsre}", "Error", wx.OK | wx.ICON_ERROR)
                return
            logging.debug(f"Using serial port: {selectedPort}")
            self.statusBar.SetStatusText(f"Using serial port: {selectedPort}")
            # TODO: SP2WIE: start the update timer here?


# Don't think we need the indicators for now
# class IndicatorsPanel(wx.Panel):
#     def __init__(self, parent) -> None:
#         wx.Panel.__init__(
#             self, parent, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL, "IndicatorsPanel"
#         )
#         self.sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, "Indicators"), wx.VERTICAL)
#         for x in range(10):
#             ctr = wx.StaticText(self, label="Label: ")
#             ctr1 = wx.StaticText(self, label=str(x))
#             xsizer = wx.BoxSizer(wx.HORIZONTAL)
#             xsizer.Add(ctr, 1, wx.EXPAND)
#             xsizer.Add(ctr1, 1, wx.EXPAND)
#             self.sizer.Add(xsizer, 1, wx.EXPAND)
#         self.SetSizer(self.sizer)
#         self.SetAutoLayout(1)
#         self.sizer.Fit(self)


class ControllsPanel(wx.Panel):
    def __init__(self, parent) -> None:
        wx.Panel.__init__(
            self, parent, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL, "ControllsPanel"
        )
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, "Filter"), wx.VERTICAL)

        bypassToggleButton = wx.ToggleButton(self, label="&BYPASS")
        self.Bind(wx.EVT_TOGGLEBUTTON, self.OnBypassToggled, bypassToggleButton)
        sizer.Add(bypassToggleButton, 1, wx.EXPAND | wx.ALL)

        offsetSizer = wx.BoxSizer(wx.HORIZONTAL)
        offsetDown1Button = wx.Button(self, label="-1")
        offsetDown1Button.Bind(wx.EVT_BUTTON, self.OnOffsetButtonClicked)
        offsetSizer.Add(offsetDown1Button, 1, wx.EXPAND | wx.ALL)
        offsetDown10Button = wx.Button(self, label="-10")
        offsetDown10Button.Bind(wx.EVT_BUTTON, self.OnOffsetButtonClicked)
        offsetSizer.Add(offsetDown10Button, 1, wx.EXPAND | wx.ALL)
        offsetUp10Button = wx.Button(self, label="+10")
        offsetUp10Button.Bind(wx.EVT_BUTTON, self.OnOffsetButtonClicked)
        offsetSizer.Add(offsetUp10Button, 1, wx.EXPAND | wx.ALL)
        offsetUp1Button = wx.Button(self, label="+1")
        offsetUp1Button.Bind(wx.EVT_BUTTON, self.OnOffsetButtonClicked)
        offsetSizer.Add(offsetUp1Button, 1, wx.EXPAND | wx.ALL)
        sizer.Add(offsetSizer, 1, wx.EXPAND)

        filterResetButton = wx.Button(self, label="&RESET")
        filterResetButton.Bind(wx.EVT_BUTTON, self.OnResetFilterClicked)
        sizer.Add(filterResetButton, 1, wx.ALL | wx.EXPAND)

        txModeToggleButton = wx.ToggleButton(self, label="FORCE TX MODE")
        self.Bind(wx.EVT_TOGGLEBUTTON, self.OnTXModeToggled, txModeToggleButton)

        mainSizer.Add(sizer, 1, wx.EXPAND)
        stretchSizer = wx.BoxSizer(wx.VERTICAL)
        stretchSizer.AddStretchSpacer()
        stretchSizer.Add(txModeToggleButton, 1, wx.EXPAND | wx.TOP | wx.BOTTOM, 5)
        mainSizer.Add(stretchSizer, 1, wx.EXPAND)

        self.SetSizer(mainSizer)
        self.SetAutoLayout(1)
        mainSizer.Fit(self)

    def OnBypassToggled(self, event) -> None:
        if event.GetEventObject().GetValue() is True:
            logging.debug("BYPASS ON")
        else:
            logging.debug("BYPASS OFF")

    def OnOffsetButtonClicked(self, event) -> None:
        logging.debug("FILTER OFFSET %s", event.GetEventObject().GetLabel())

    def OnResetFilterClicked(self, event) -> None:
        logging.debug("%s clicked", event.GetEventObject().GetLabel())

    def OnTXModeToggled(self, event) -> None:
        if event.GetEventObject().GetValue() is True:
            logging.debug("FORCE TX MODE ON")
        else:
            logging.debug("FORCE TX MODE OFF")
