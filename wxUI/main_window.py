import logging

import wx
from pubsub import pub
from serial import SerialException

from serial_comm.serial_comm import BadSerialResponseException, SerialCommander, SerialManager

logging.basicConfig(level=logging.DEBUG)

ERROR_MESSAGE = "Please check if the correct serial port is selected."


class MainWindow(wx.Frame):
    def __init__(self, parent, title: str) -> None:
        wx.Frame.__init__(self, parent, title=title, size=wx.Size(500, 300))
        pub.subscribe(self.OnBypassMessageReceived, "bypass")
        pub.subscribe(self.OnFilterOffsetMessageReceived, "filter_offset")
        pub.subscribe(self.OnResetFilterMessageReceived, "reset_filter")
        pub.subscribe(self.OnForceTXMessageReceived, "force_tx")

        self.serialCommander: SerialCommander = None

        self.updateStatusTimer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimerTick, self.updateStatusTimer)

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
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.controllsPanel = ControllsPanel(self)
        self.main_sizer.Add(self.controllsPanel, 1, wx.EXPAND | wx.ALL, 5)
        self.frequencyPanel = FrequencyPanel(self)
        self.main_sizer.Add(self.frequencyPanel, 1, wx.EXPAND | wx.ALL, 5)

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
            except BadSerialResponseException as bsre:
                wx.MessageBox(f"{bsre}", "Error", wx.OK | wx.ICON_ERROR)
            else:
                logging.debug(f"Using serial port: {selectedPort}")
                self.statusBar.SetStatusText(f"Using serial port: {selectedPort}")
                # since at this point everything should be fine we can start the status update timer
                if not self.updateStatusTimer.IsRunning():
                    self.updateStatusTimer.Start(1000)

    def OnBypassMessageReceived(self, message: bool) -> None:
        try:
            if message is True:
                self.serialCommander.set_bypass_on()
            else:
                self.serialCommander.set_bypass_off()
        except SerialException:
            logging.error(ERROR_MESSAGE)
            wx.MessageBox(ERROR_MESSAGE, "Error", wx.OK | wx.ICON_ERROR)

    def OnForceTXMessageReceived(self, message: bool) -> None:
        try:
            if message is True:
                self.serialCommander.set_mode_tx_on()
            else:
                self.serialCommander.set_mode_tx_off()
        except SerialException:
            logging.error(ERROR_MESSAGE)
            wx.MessageBox(ERROR_MESSAGE, "Error", wx.OK | wx.ICON_ERROR)

    def OnResetFilterMessageReceived(self, message: str) -> None:
        try:
            self.serialCommander.reset_filter()
        except SerialException:
            logging.error(ERROR_MESSAGE)
            wx.MessageBox(ERROR_MESSAGE, "Error", wx.OK | wx.ICON_ERROR)

    def OnFilterOffsetMessageReceived(self, message: str) -> None:
        try:
            match int(message):
                case -10:
                    self.serialCommander.filter_step_down_10()
                case -1:
                    self.serialCommander.filter_step_down_1()
                case 1:
                    self.serialCommander.filter_step_up_1()
                case 10:
                    self.serialCommander.filter_step_up_10()
        except SerialException:
            logging.error(ERROR_MESSAGE)
            wx.MessageBox(ERROR_MESSAGE, "Error", wx.OK | wx.ICON_ERROR)

    def OnTimerTick(self, event):
        try:
            statusMessage = self.serialCommander.get_status()
            statusMessageList = statusMessage.split(",")
            # Read current frequency
            self.frequencyPanel.frequencyStaticText.SetLabel(f"{statusMessageList[1]} MHz")
            # Read bypass status
            if statusMessageList[3] == "0":
                self.controllsPanel.bypassToggleButton.SetValue(False)
            else:
                self.controllsPanel.bypassToggleButton.SetValue(True)
            # Read TX Mode status
            if statusMessageList[5] == "0":
                self.controllsPanel.txModeToggleButton.SetValue(False)
            else:
                self.controllsPanel.txModeToggleButton.SetValue(True)
        except SerialException as se:
            logging.error("Could not find or configure the device: %s", se)
            wx.MessageBox("Could not find or configure the device", "Error", wx.OK | wx.ICON_ERROR)
            logging.debug("Stopping the update status timer...")
            self.updateStatusTimer.Stop()
        except BadSerialResponseException as bsre:
            wx.MessageBox(f"{bsre}", "Error", wx.OK | wx.ICON_ERROR)


class ControllsPanel(wx.Panel):
    def __init__(self, parent) -> None:
        wx.Panel.__init__(
            self, parent, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL, "ControllsPanel"
        )
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, "Filter"), wx.VERTICAL)

        self.bypassToggleButton = wx.ToggleButton(self, label="BYPASS")
        self.Bind(wx.EVT_TOGGLEBUTTON, self.OnBypassToggled, self.bypassToggleButton)
        sizer.Add(self.bypassToggleButton, 1, wx.EXPAND | wx.ALL)

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

        filterResetButton = wx.Button(self, label="RESET")
        filterResetButton.Bind(wx.EVT_BUTTON, self.OnResetFilterClicked)
        sizer.Add(filterResetButton, 1, wx.ALL | wx.EXPAND)

        self.txModeToggleButton = wx.ToggleButton(self, label="FORCE TX MODE")
        self.Bind(wx.EVT_TOGGLEBUTTON, self.OnTXModeToggled, self.txModeToggleButton)

        mainSizer.Add(sizer, 1, wx.EXPAND)
        stretchSizer = wx.BoxSizer(wx.VERTICAL)
        stretchSizer.AddStretchSpacer()
        stretchSizer.Add(self.txModeToggleButton, 1, wx.EXPAND | wx.TOP | wx.BOTTOM, 5)
        mainSizer.Add(stretchSizer, 1, wx.EXPAND)

        self.SetSizer(mainSizer)
        self.SetAutoLayout(1)
        mainSizer.Fit(self)

    def OnBypassToggled(self, event) -> None:
        value = event.GetEventObject().GetValue()
        pub.sendMessage("bypass", message=value)
        if value:
            logging.debug("BYPASS ON")
            event.GetEventObject().SetBackgroundColour(wx.BLUE)
        else:
            logging.debug("BYPASS OFF")
            event.GetEventObject().SetBackgroundColour(wx.Colour(38, 38, 38))

    def OnOffsetButtonClicked(self, event) -> None:
        label = event.GetEventObject().GetLabel()
        pub.sendMessage("filter_offset", message=label)
        logging.debug("FILTER OFFSET %s", label)

    def OnResetFilterClicked(self, event) -> None:
        pub.sendMessage("reset_filter", message="reset")
        logging.debug("%s clicked", event.GetEventObject().GetLabel())

    def OnTXModeToggled(self, event) -> None:
        value = event.GetEventObject().GetValue()
        pub.sendMessage("force_tx", message=value)
        if value:
            logging.debug("FORCE TX MODE ON")
            event.GetEventObject().SetBackgroundColour(wx.BLUE)
        else:
            logging.debug("FORCE TX MODE OFF")
            event.GetEventObject().SetBackgroundColour(wx.Colour(38, 38, 38))


class FrequencyPanel(wx.Panel):
    def __init__(self, parent) -> None:
        wx.Panel.__init__(
            self, parent, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL, "FrequencyPanel"
        )
        sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, "Frequency"), wx.VERTICAL)
        frequencyFont = wx.Font(48, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False)
        self.frequencyStaticText = wx.StaticText(self, wx.ID_ANY, "433.500 MHz", style=wx.ALIGN_CENTER_HORIZONTAL)
        self.frequencyStaticText.SetFont(frequencyFont)
        sizer.Add(self.frequencyStaticText, 0, wx.ALIGN_CENTER)

        self.SetSizer(sizer)
        self.SetAutoLayout(1)
        sizer.Fit(self)
