# IKEA Tradfri Python Plugin
#
# Author: moroen
#
"""
<plugin key="IKEA-Tradfri" name="IKEA Tradfri" author="moroen" version="1.1.1" externallink="https://github.com/moroen/IKEA-Tradfri-plugin">
    <params>
        <param field="Address" label="Adaptor IP Address" width="200px" required="true" default="127.0.0.1"/>
        <param field="Mode2" label="Observe changes" width="75px">
            <options>
                <option label="Yes" value="True"/>
                <option label="No" value="False"  default="true" />
            </options>
        </param>

        <param field="Mode5" label="Transition time (tenth of a second)" width="75px" required="false" default="10"/>

        <param field="Mode4" label="Polling interval (seconds)" width="75px" required="true" default="30"/>

        <param field="Mode3" label="Add groups as devices" width="75px">
            <options>
                <option label="Yes" value="True"/>
                <option label="No" value="False"  default="true" />
            </options>
        </param>

        <param field="Mode1" label="Add psychedelic color change" width="75px">
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
import datetime
from ikeatradfri import colors
from random import randint


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

    def __init__(self):
        self.pluginStatus = 0
        self.lastPollTime = datetime.datetime.now()
        return

    def unitOfUnit(self, i):
        return Devices[i]

    def atLeastOneRGBgroupMember(self, group):
        if "Members" not in group:
            return "false"
        for member in group["Members"]:
            if str(member)+":CWS" in self.lights:
                return "true"
        return "false"

    def registerDevice(self, aLight):
        Domoticz.Debug("Registering: {0}".format(json.dumps(aLight)))

        whiteLevelNames, whiteLevelActions = colors.wbLevelDefinitions()
        WhiteOptions = {"LevelActions": whiteLevelActions,
                        "LevelNames": whiteLevelNames, "LevelOffHidden": "true", "SelectorStyle": "0"}

        Domoticz.Log("colordef "+str(colors.colorLevelDefinitions(Parameters["Mode1"]=="True")))
        colorLevelNames, colorLevelActions = colors.colorLevelDefinitions(Parameters["Mode1"]=="True")
        colorOptions = {"LevelActions": colorLevelActions,
                        "LevelNames": colorLevelNames, "LevelOffHidden": "false", "SelectorStyle": "1"}

        devID = str(aLight['DeviceID'])
        self.ikeaIds.append(devID)
        if "Members" not in aLight:
            aLight["Members"] = {}

        if devID in self.lights:
            self.lights[devID]["Members"] = aLight["Members"]
            self.lights[devID]["Type"]    = aLight["Type"]
            if devID+":WB" in self.lights:
                self.lights[devID+":WB"]["Members"] = aLight["Members"]
                self.lights[devID+":WB"]["Type"]    = aLight["Type"]
            if devID+":CWS" in self.lights:
                self.lights[devID+":CWS"]["Members"] = aLight["Members"]
                self.lights[devID+":CWS"]["Type"]    = aLight["Type"]
        else:
            if aLight["Type"] == "Outlet":
                Domoticz.Device(Name=aLight['Name'], Unit=self.nextDomoticzUnit, Type=244,
                                    Subtype=73, Switchtype=0, Image=1, DeviceID=devID).Create()
                self.lights[devID] = {
                        "DeviceID": aLight['DeviceID'], "Unit": self.nextDomoticzUnit, "Type": aLight["Type"]}
                self.nextDomoticzUnit += 1

            if aLight["Type"] == "Light" or aLight["Type"] == "Group":
                deviceType = 244
                subType = 73

                if not "HasRGB" in aLight:
                    aLight["HasRGB"] = "false"
                if aLight["Type"] == "Group":
                    aLight["HasRGB"] = self.atLeastOneRGBgroupMember(aLight)

                if aLight['Dimmable']:
                    switchType = 7
                else:
                    switchType = 0

                # Basic device
                Domoticz.Device(Name=aLight['Name'], Unit=self.nextDomoticzUnit,  Type=deviceType,
                                    Subtype=subType, Switchtype=switchType, DeviceID=devID).Create()
                self.lights[devID] = {
                        "DeviceID": aLight['DeviceID'], "Unit": self.nextDomoticzUnit, "Type": aLight["Type"], "Members": aLight["Members"]}
                self.nextDomoticzUnit += 1

                if str(aLight["HasRGB"]).lower() == "true":
                    Domoticz.Device(Name=aLight['Name'] + " - Color",  Unit=self.nextDomoticzUnit, TypeName="Selector Switch",
                                        Switchtype=18, Options=colorOptions, DeviceID=devID+":CWS").Create()
                    self.lights[devID +
                                    ":CWS"] = {"DeviceID": devID+":CWS", "Unit": self.nextDomoticzUnit, "Type": aLight["Type"], "Members": aLight["Members"]}
                    self.nextDomoticzUnit += 1

                if str(aLight['HasWB']).lower() == "true":
                    Domoticz.Device(Name=aLight['Name'] + " - WB",  Unit=self.nextDomoticzUnit, TypeName="Selector Switch",
                                        Switchtype=18, Options=WhiteOptions, DeviceID=devID+":WB").Create()
                    self.lights[devID +
                                    ":WB"] = {"DeviceID": devID+":WB", "Unit": self.nextDomoticzUnit, "Type": aLight["Type"], "Members": aLight["Members"]}
                    self.nextDomoticzUnit += 1

    def registerDevices(self, ikeaDevices):
        self.nextDomoticzUnit = 1
        if (len(Devices) > 0):
            self.nextDomoticzUnit = max(Devices)+1

        self.ikeaIds = []
        # Add unregistred lights
        for aLight in ikeaDevices:
            if aLight["Type"] != "Group":
                self.registerDevice(aLight)
        # Then add unregistered groups
        for aLight in ikeaDevices:
            if aLight["Type"] == "Group":
                self.registerDevice(aLight)

        # Remove registered lights no longer found on the gateway
        for aUnit in list(Devices.keys()):
            devID = str(Devices[aUnit].DeviceID)

            if devID[-3:] == ":WB":
                devID = devID[:-3]

            if devID[-4:] == ":CWS":
                devID = devID[:-4]

            if not devID in self.ikeaIds:
                Devices[aUnit].Delete()

    def updateGroup(self,dev):
        for devID in self.ikeaIds:
            light = self.lights[devID]
            if light["Type"] == "Group":
                if dev["DeviceID"] in light["Members"]:
                    targetDevice = Devices[light["Unit"]]
                    nVal = 0
                    sVal = "0"
                    if str(dev["State"]).lower() == "true":
                        nVal = 1
                        sVal = "1"
                    if str(dev["State"]).lower() == "false":
                        nVal = 0
                        sVal = "0"
                    if "Level" in dev:
                        sValInt = int((dev["Level"]/250)*100)
                        if sValInt == 0:
                            sValInt = 1
                        sVal = str(sValInt)
                    targetDevice.Update(nValue=nVal, sValue=sVal)
                    if "Hex" in dev:
                        if dev["Hex"] != None and dev["Hex"] != "000000":
                            if devID+":WB" in self.lights:
                                wbdevID = devID+":WB"
                                targetUnit = self.lights[wbdevID]['Unit']
                                if Devices[targetUnit].nValue != 210:
                                    Devices[targetUnit].Update(nValue=nVal, sValue=str(
                                        colors.wbLevelForHex(dev['Hex'])))
                            if devID+":CWS" in self.lights:
                                wbdevID = devID+":CWS"
                                targetUnit = self.lights[wbdevID]['Unit']
                                if Devices[targetUnit].nValue != 210:
                                    Devices[targetUnit].Update(nValue=nVal, sValue=str(
                                        colors.colorLevelForHex(dev['Hex'])))

    def updateDeviceState(self, deviceState):
        Domoticz.Debug("updateDeviceState "+str(deviceState))
        for aDev in deviceState:
            Domoticz.Debug(str(aDev))
            devID = str(aDev["DeviceID"])
            if self.lights[devID]['Type'] != "Group":
                self.updateGroup(aDev)
            targetUnit = self.lights[devID]['Unit']
            nVal = 0
            sVal = "0"

            if str(aDev["State"]).lower() == "true":
                nVal = 1
                sVal = "1"
            if str(aDev["State"]).lower() == "false":
                nVal = 0
                sVal = "0"

            if "Level" in aDev:
                sValInt = int((aDev["Level"]/250)*100)
                if sValInt == 0:
                    sValInt = 1

                sVal = str(sValInt)

            Devices[targetUnit].Update(nValue=nVal, sValue=sVal)

            if "Hex" in aDev:
                if aDev["Hex"] != None and aDev["Hex"] != "000000":
                    if devID+":WB" in self.lights:
                        wbdevID = devID+":WB"
                        targetUnit = self.lights[wbdevID]['Unit']
                        if Devices[targetUnit].nValue != 210:
                            Devices[targetUnit].Update(nValue=nVal, sValue=str(
                                colors.wbLevelForHex(aDev['Hex'])))

                    if devID+":CWS" in self.lights:
                        wbdevID = devID+":CWS"
                        targetUnit = self.lights[wbdevID]['Unit']
                        if Devices[targetUnit].nValue != 210:
                            Devices[targetUnit].Update(nValue=nVal, sValue=str(
                                colors.colorLevelForHex(aDev['Hex'])))

    def connectToAdaptor(self):
        self.CoapAdapter = Domoticz.Connection(
            Name="Main", Transport="TCP/IP", Protocol="JSON", Address=Parameters["Address"], Port="1234")
        self.CoapAdapter.Connect()

    def onStart(self):
        # Domoticz.Log("onStart called")

        if Parameters["Mode6"] == "Debug":
            Domoticz.Debugging(1)

        Domoticz.Heartbeat(5)
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
            Connection.Send(Message=json.dumps({"action": "initGateway", "observe": Parameters["Mode2"], "pollinterval": Parameters[
                            'Mode4'], "groups": Parameters["Mode3"], "transitiontime": Parameters["Mode5"]}).encode(encoding='utf_8'), Delay=1)
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
                Connection.Send(Message=json.dumps(
                    {"action": "getLights"}).encode(encoding='utf_8'), Delay=1)

            if action == "getLights":
                self.registerDevices(command['result'])

            if action == "deviceUpdate":
                self.updateDeviceState(command['result'])

        if command['status'] == "Failed":
            Domoticz.Log("Command {0} failed with error: {1}.".format(
                command['action'], command['error']))
            Domoticz.Log(str(command))

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Debug("Command: " + str(Command)+" Level: "+str(Level)+" Type: "+str(
            Devices[Unit].Type)+" SubType: "+str(Devices[Unit].SubType)+" Hue: "+str(Hue))

        if (Devices[Unit].Type == 244) and (Devices[Unit].SubType == 73):
            if Command == "On":
                self.CoapAdapter.Send(Message=json.dumps(
                    {"action": "setState", "state": "On", "deviceID": Devices[Unit].DeviceID}).encode(encoding='utf_8'))

            if Command == "Off":
                self.CoapAdapter.Send(Message=json.dumps(
                    {"action": "setState", "state": "Off", "deviceID": Devices[Unit].DeviceID}).encode(encoding='utf_8'))

            if Command == "Set Level":
                targetLevel = int(int(Level)*250/100)
                self.CoapAdapter.Send(Message=json.dumps(
                    {"action": "setLevel", "deviceID": Devices[Unit].DeviceID, "level": targetLevel}).encode(encoding='utf_8'))

        if (Devices[Unit].Type == 244) and (Devices[Unit].SubType == 62):
            # This is a WB-device
            hex = None

            # [0] is the DeviceID [1] is the subType (WB/CWS)
            devId = Devices[Unit].DeviceID.split(':')

            if Level == 0:
                # Off
                self.CoapAdapter.Send(Message=json.dumps(
                    {"action": "setState", "state": "Off", "deviceID": devId[0]}).encode(encoding='utf_8'))

            else:
                if devId[1] == "WB":
                    self.CoapAdapter.Send(Message=json.dumps(
                        {"action": "setHex", "deviceID": devId[0], "hex": colors.wb(Level)["Hex"]}).encode(encoding='utf_8'))
                if devId[1] == "CWS":
                    if Level != 210:
                        Devices[Unit].Update(nValue=0, sValue="Off")
                        self.CoapAdapter.Send(Message=json.dumps(
                                  {"action": "setHex", "deviceID": devId[0], "hex": colors.color(Level)["Hex"]}).encode(encoding='utf_8'))
                    else:
                        # Enter Psychedelic mode
                        Devices[Unit].Update(nValue=210, sValue=str(colors.colorLevelForHex("ffffff")))

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
                    self.CoapAdapter.Send(Message=json.dumps(
                        {"action": "announceChanged"}).encode(encoding='utf_8'))
        else:
            Domoticz.Debug(
                "Not connected - nextConnect: {0}".format(self.nextConnect))
            self.nextConnect = self.nextConnect - 1
            if self.nextConnect <= 0:
                self.nextConnect = 3
                self.CoapAdapter.Connect()
        if len(Devices) > 0:
            # Some devices are already defined
            for aUnit in Devices:
                devId = Devices[aUnit].DeviceID.split(":")
                if len(devId) > 1 and devId[1] == "CWS" and Devices[aUnit].nValue == 210:
                    x = randint(0, 65535)
                    y = randint(0, 65535)
                    Domoticz.Log("Setting color X="+str(x)+" Y="+str(y)+" for "+Devices[aUnit].Name)
                    self.CoapAdapter.Send(Message=json.dumps(
                            {"action": "setXY", "deviceID": devId[0], "x": x, "y": y}).encode(encoding='utf_8'))


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
