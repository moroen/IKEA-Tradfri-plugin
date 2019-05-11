# IKEA Tradfri Python Plugin
#
# Author: moroen
#
"""
<plugin key="IKEA-Tradfri" name="IKEA Tradfri" author="moroen" version="1.1.2" externallink="https://github.com/moroen/IKEA-Tradfri-plugin">
    <params>
        <param field="Address" label="Adaptor IP Address" width="200px" required="true" default="127.0.0.1"/>
        <param field="Mode2" label="Observe changes" width="75px">
            <options>
                <option label="Yes" value="True"/>
                <option label="No" value="False"  default="true" />
            </options>
        </param>

        <param field="Mode4" label="Polling interval (seconds)" width="75px" required="true" default="30"/>

        <param field="Mode5" label="Transition time (tenth of a second)" width="75px" required="false" default="10"/>

        <param field="Mode3" label="Add groups as devices" width="75px">
            <options>
                <option label="Yes" value="True"/>
                <option label="No" value="False"  default="true" />
            </options>
        </param>

        <param field="Mode1" label="Monitor battry levels" width="75px">
            <options>
                <option label="Yes" value="True"/>
                <option label="No" value="False"  default="true" />
            </options>
        </param>

        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal"  default="true" />
            </options>
        </param>

    </params>
</plugin>
"""
import Domoticz
import json
import datetime,sys

import colors


colorOption = ""


class BasePlugin:
    #enabled = False
    #api = None
    #gateway = None

    pluginStatus = 0
    # Dict of registered lights
    lights = {}
    CoapAdapter = None
    outstandingPings = 0
    nextConnect = 3

    lastPollTime = None
    pollInterval = None

    lastBattryPollTime = None
    batteryPollInterval = 3600

    def __init__(self):
        self.pluginStatus = 0
        self.lastPollTime = datetime.datetime.now()
        self.lastBattryPollTime = datetime.datetime.now()
        return

    def unitOfUnit(self, i):
        return Devices[i]

    def registerDevices(self, ikeaDevices):
        i = 1
        if (len(Devices) == 0):
            i = 1
        else:
            i = max(Devices)+1

        whiteLevelNames, whiteLevelActions = colors.wbLevelDefinitions()
        WhiteOptions = {"LevelActions": whiteLevelActions,
                        "LevelNames": whiteLevelNames, "LevelOffHidden": "true", "SelectorStyle": "1"}

        colorLevelNames, colorLevelActions = colors.colorLevelDefinitions()
        colorOptions = {"LevelActions": colorLevelActions,
                        "LevelNames": colorLevelNames, "LevelOffHidden": "true", "SelectorStyle": "1"}

        ikeaIds = []
        # Add unregistred lights
        for aLight in ikeaDevices:
            Domoticz.Debug("Registering: {0}".format(json.dumps(aLight)))

            devID = str(aLight['DeviceID'])
            ikeaIds.append(devID)

            if not devID in self.lights:
                if aLight["Type"] == "Outlet":
                    Domoticz.Device(Name=aLight['Name'], Unit=i, Type=244,
                                    Subtype=73, Switchtype=0, Image=1, DeviceID=devID).Create()
                    self.lights[devID] = {
                        "DeviceID": aLight['DeviceID'], "Unit": i}
                    i = i+1

                if aLight["Type"] == "Remote":
                    Domoticz.Device(Name=aLight["Name"] + " - Battery level",
                                    Unit=i,  Type=243, Subtype=6, DeviceID=devID).Create()
                    self.lights[devID] = {
                        "DeviceID": aLight['DeviceID'], "Unit": i}
                    i = i+1

                if aLight["Type"] == "Light" or aLight["Type"] == "Group":
                    deviceType = 244
                    subType = 73

                    if not "HasRGB" in aLight:
                        aLight["HasRGB"] = "false"

                    if aLight['Dimmable']:
                        switchType = 7
                    else:
                        switchType = 0

                    # Basic device
                    Domoticz.Device(Name=aLight['Name'], Unit=i,  Type=deviceType,
                                    Subtype=subType, Switchtype=switchType, DeviceID=devID).Create()
                    self.lights[devID] = {
                        "DeviceID": aLight['DeviceID'], "Unit": i}
                    i = i+1

                    if aLight["Colorspace"] == "W":
                        continue

                    if str(aLight["Colorspace"]) == "CWS":
                        Domoticz.Device(Name=aLight['Name'] + " - Color",  Unit=i, TypeName="Selector Switch",
                                        Switchtype=18, Options=colorOptions, DeviceID=devID+":CWS").Create()
                        self.lights[devID +
                                    ":CWS"] = {"DeviceID": devID+":CWS", "Unit": i}
                        i = i+1

                        # Domoticz.Device(Name=aLight['Name'] + " - RGB",  Unit=i, Type=241,
                        #                Subtype=2, Switchtype=7, DeviceID=devID+":RGB").Create()
                        #self.lights[devID +
                        #            ":RGB"] = {"DeviceID": devID+":RGB", "Unit": i}
                        # i = i+1

                    if aLight['Colorspace'] == "WS":
                        Domoticz.Device(Name=aLight['Name'] + " - Color",  Unit=i, TypeName="Selector Switch",
                                        Switchtype=18, Options=WhiteOptions, DeviceID=devID+":WS").Create()
                        self.lights[devID +
                                    ":WS"] = {"DeviceID": devID+":WS", "Unit": i}
                        i = i+1

        # Remove registered lights no longer found on the gateway
        for aUnit in list(Devices.keys()):
            devID = str(Devices[aUnit].DeviceID)

            if devID[-3:] == ":WS":
                devID = devID[:-3]

            if devID[-4:] == ":CWS":
                devID = devID[:-4]

            if devID[-4:] == ":RGB":
                devID = devID[:-4]

            if not devID in ikeaIds:
                Devices[aUnit].Delete()

        # Set states
        self.updateDeviceState(ikeaDevices)

    def updateDeviceState(self, deviceState):
        for aDev in deviceState:

            if aDev["Type"] == "Battery_Level":
                continue

            if aDev["Type"] == "Remote":
                continue

            devID = str(aDev["DeviceID"])
            targetUnit = self.lights[devID]['Unit']
            nVal = 0
            sVal = "0"

            if str(aDev["State"]).lower() == "true":
                nVal = 1
            if str(aDev["State"]).lower() == "false":
                nVal = 0

            if aDev["Type"] == "Light":
                Domoticz.Debug("Level: {0}".format(aDev["Level"]))
                sValInt = int((aDev["Level"]/250)*100)
                sVal = str(sValInt)
            else:
                sVal = str(nVal)

            Devices[targetUnit].Update(nValue=nVal, sValue=sVal)

            if "Hex" in aDev:
                if aDev["Hex"] != None:
                    if devID+":WS" in self.lights:
                        wbdevID = devID+":WS"
                        targetUnit = self.lights[wbdevID]['Unit']
                        Devices[targetUnit].Update(nValue=nVal, sValue=str(
                            colors.wbLevelForHex(aDev['Hex'])))

                    if devID+":CWS" in self.lights:
                        wbdevID = devID+":CWS"
                        targetUnit = self.lights[wbdevID]['Unit']
                        Devices[targetUnit].Update(nValue=nVal, sValue=str(
                            colors.colorLevelForHex(aDev['Hex'])))

    def updateBatteryStatus(self, batteryStatus):
        for aDev in batteryStatus:
            devID = str(aDev["DeviceID"])
            targetUnit = self.lights[devID]['Unit']

            Domoticz.Debug(
                "Battery: {0} - Unit: {1} -Level: {2}".format(devID, targetUnit, aDev["Level"]))
            Devices[targetUnit].Update(nValue=int(
                aDev["Level"]), sValue=str(aDev["Level"]))

    def sendMessage(self, connection, messageobj):
        # connection.Send(Message="{0}\n".format(json.dumps(messageobj).encode(encoding='utf_8')))
        connection.Send(Message="{0}\n".format(
            json.dumps(messageobj), Delay=1))

    def connectToAdaptor(self):
        self.CoapAdapter = Domoticz.Connection(
            Name="Main", Transport="TCP/IP", Protocol="JSON", Address=Parameters["Address"], Port="1234")
        self.CoapAdapter.Connect()

    def onStart(self):
        # Domoticz.Log("onStart called")

        if Parameters["Mode6"] == "Debug":
            Domoticz.Debugging(1)

        Domoticz.Heartbeat(2)
        self.pollInterval = int(Parameters['Mode4'])

        if len(Devices) > 0:
            # Some devices are already defined
            for aUnit in Devices:
                self.lights[Devices[aUnit].DeviceID] = {
                    "DeviceID": Devices[aUnit].DeviceID, "Unit": aUnit}

        self.connectToAdaptor()

    def onStop(self):
        #Domoticz.Log("onStop called")
        return True

    def onConnect(self, Connection, Status, Description):
        #Domoticz.Log("onConnect called")

        if (Status == 0):
            Domoticz.Log("Connected successfully to: "+Parameters["Address"])
            self.sendMessage(Connection, {"action": "initGateway", "observe": Parameters["Mode2"], "pollinterval": Parameters[
                             'Mode4'], "groups": Parameters["Mode3"], "transitiontime": Parameters["Mode5"], "battery_levels": Parameters["Mode1"]})
        else:
            Domoticz.Log(
                "Failed to connect to IKEA tradfri COAP-adapter! Status: {0} Description: {1}".format(Status, Description))
        return True

    def onMessage(self, Connection, Data):

        if hasattr(Data, "decode"):
            # Stable API
            command = json.loads(Data.decode("utf-8"))
        else:
            # Beta APi
            command = Data

        if command['status'] == "Ok":
            action = command['action']

            if action == "initGateway":
                # Config set
                self.sendMessage(Connection, {"action": "getDevices", "groups": Parameters["Mode3"], "battery_levels": Parameters["Mode1"]})

            if action == "getDevices":
                self.registerDevices(command['result'])

            if action == "deviceUpdate":
                self.updateDeviceState(command['result'])

            if action == "setState" or action == "setLevel" or action == "setHex":
                self.updateDeviceState(command['result'])

            if action == "batteryStatus":
                self.updateBatteryStatus(command['result'])

        if command['status'] == "Error":
            Domoticz.Log("Command {0} failed with error: {1}.".format(
                command['action'], command['result']))
            Domoticz.Log(str(command))

    def onCommand(self, Unit, Command, Level, Color):
        Domoticz.Debug("Command: " + str(Command)+" Level: "+str(Level)+" Type: "+str(
            Devices[Unit].Type)+" SubType: "+str(Devices[Unit].SubType)+" Color: {0}".format(Color))

        devId = Devices[Unit].DeviceID.split(':')

        if Command == "On":
            self.sendMessage(self.CoapAdapter, {
                             "action": "setState", "state": "On", "deviceID": devId[0]})

        if Command == "Off":
            self.sendMessage(self.CoapAdapter, {
                             "action": "setState", "state": "Off", "deviceID": devId[0]})

        if Command == "Set Color":
            self.sendMessage(self.CoapAdapter, {"action": "setColor", "level": int(
                int(Level)*250/100), "color": json.loads(Color), "deviceID": devId[0]})

        if Command == "Set Level":
            if (Devices[Unit].Type == 244) and (Devices[Unit].SubType == 62):
                # This is a WB-device
                hex = None

                if Level == 0:
                    # Off
                    self.sendMessage(self.CoapAdapter, {
                                     "action": "setState", "state": "Off", "deviceID": devId[0]})

                else:
                    if devId[1] == "WS":
                        self.sendMessage(self.CoapAdapter, {
                                         "action": "setHex", "deviceID": devId[0], "hex": colors.wb(Level)["Hex"]})
                    if devId[1] == "CWS":
                        self.sendMessage(self.CoapAdapter, {
                                         "action": "setHex", "deviceID": devId[0], "hex": colors.color(Level)["Hex"]})
            else:
                targetLevel = int(int(Level)*250/100)
                self.sendMessage(self.CoapAdapter, {
                                 "action": "setLevel", "deviceID": devId[0], "level": targetLevel})

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Log("Notification: " + Name + "," + Subject + "," + Text +
                     "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        self.isConnected = False
        Domoticz.Log("Device has disconnected")
        return

    def onHeartbeat(self):
        if (self.CoapAdapter.Connected() == True):
            if Parameters["Mode2"] == "True":
                interval = (datetime.datetime.now()-self.lastPollTime).seconds
                if interval+1 > self.pollInterval:
                    self.lastPollTime = datetime.datetime.now()
                    self.sendMessage(self.CoapAdapter, {
                                     "action": "announceChanged"})

            if Parameters["Mode1"] == "True":
                # Poll batteries
                interval = (datetime.datetime.now() -
                            self.lastBattryPollTime).seconds
                if interval+1 > self.batteryPollInterval:
                    self.lastBattryPollTime = datetime.datetime.now()
                    self.sendMessage(self.CoapAdapter, {
                                     "action": "battery_status"})
        else:
            Domoticz.Debug(
                "Not connected - nextConnect: {0}".format(self.nextConnect))
            self.nextConnect = self.nextConnect - 1
            if self.nextConnect <= 0:
                self.nextConnect = 3
                self.CoapAdapter.Connect()


global _plugin
_plugin = BasePlugin()


def onStart():
    global _plugin
    _plugin.onStart()


def onStop():
    global _plugin
    _plugin.onStop()


def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)


def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)


def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)


def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status,
                           Priority, Sound, ImageFile)


def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)


def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

    # Generic helper functions


def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug("'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return
