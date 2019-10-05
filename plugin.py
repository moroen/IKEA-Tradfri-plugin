# Basic Python Plugin Example
#
# Author: GizMoCuz
#
"""
<plugin key="IKEA-Tradfri" name="IKEA Tradfri Plugin - pycoap version" author="moroen" version="1.0.0" wikilink="http://www.domoticz.com/wiki/plugins/plugin.html" externallink="https://www.google.com/">
    <description>
        <h2>IKEA Tradfri</h2><br/>
        Overview...
        <h3>Features</h3>
        <ul style="list-style-type:square">
            <li>Feature one...</li>
            <li>Feature two...</li>
        </ul>
        <h3>Devices</h3>
        <ul style="list-style-type:square">
            <li>Device Type - What it does...</li>
        </ul>
        <h3>Configuration</h3>
        Configuration options...
    </description>
    <params>
        <param field="Mode1" label="Add groups as devices" width="75px">
            <options>
                <option label="Yes" value="True"/>
                <option label="No" value="False"  default="true" />
            </options>
        </param>
        <param field="Mode2" label="Observe changes" width="75px">
            <options>
                <option label="Yes" value="True"/>
                <option label="No" value="False"  default="true" />
            </options>
        </param>
        <param field="Mode3" label="Polling interval (seconds)" width="75px" required="true" default="30"/>
        <param field="Mode4" label="Transition time (tenth of a second)" width="75px" required="false" default="10"/>
    </params>
</plugin>
"""
import Domoticz
import site, sys, time, threading

site.main()

import tradfricoap, colors


class BasePlugin:
    enabled = False

    lights = {}

    def __init__(self):
        # self.var = 123
        return

    def registerDevices(self):

        if len(Devices) > 0:
            # Some devices are already defined
            for aUnit in Devices:
                Domoticz.Log("Getting info for id: {}".format(Devices[aUnit].DeviceID))
                dev_id = Devices[aUnit].DeviceID.split(":")
                              
                self.lights[aUnit] = tradfricoap.get_device(dev_id[0])
                Domoticz.Log(self.lights[aUnit].Description)
        
        return

        i = 1
        if len(Devices) == 0:
            i = 1
        else:
            i = max(Devices) + 1

        whiteLevelNames, whiteLevelActions = colors.color_level_definitions(
            colorspace="WS"
        )
        WhiteOptions = {
            "LevelActions": whiteLevelActions,
            "LevelNames": whiteLevelNames,
            "LevelOffHidden": "true",
            "SelectorStyle": "1",
        }

        colorLevelNames, colorLevelActions = colors.color_level_definitions(
            colorspace="CWS"
        )
        colorOptions = {
            "LevelActions": colorLevelActions,
            "LevelNames": colorLevelNames,
            "LevelOffHidden": "true",
            "SelectorStyle": "1",
        }

        ikeaIds = []
        # Add unregistred lights
        for aLight in tradfricoap.get_devices():
            devID = str(aLight.DeviceID)
            ikeaIds.append(devID)

            if not devID in self.lights:
                Domoticz.Debug(
                    "Registering: {0} - {1}".format(aLight.DeviceID, aLight.Name)
                )
                if aLight.Type == "Plug":
                    Domoticz.Device(
                        Name=aLight.Name,
                        Unit=i,
                        Type=244,
                        Subtype=73,
                        Switchtype=0,
                        Image=1,
                        DeviceID=devID,
                    ).Create()
                    self.lights[devID] = {"DeviceID": aLight.DeviceID, "Unit": i}
                    i = i + 1

                if aLight.Type == "Remote":
                    Domoticz.Device(
                        Name=aLight.Name + " - Battery level",
                        Unit=i,
                        Type=243,
                        Subtype=6,
                        DeviceID=devID,
                    ).Create()
                    self.lights[devID] = {"DeviceID": aLight.DeviceID, "Unit": i}
                    i = i + 1

                if aLight.Type == "Light" or aLight.Type == "Group":
                    deviceType = 244
                    subType = 73
                    switchType = 7

                    # if aLight["Dimmable"]:
                    #    switchType = 7
                    # else:
                    #    switchType = 0

                    # Basic device
                    Domoticz.Device(
                        Name=aLight.Name,
                        Unit=i,
                        Type=deviceType,
                        Subtype=subType,
                        Switchtype=switchType,
                        DeviceID=devID,
                    ).Create()
                    self.lights[devID] = {"DeviceID": aLight.DeviceID, "Unit": i}
                    i = i + 1

                    if aLight.ColorSpace == "W":
                        continue

            if str(aLight.ColorSpace) == "CWS" and devID + ":CWS" not in self.lights:
                Domoticz.Debug("Registering: {0}:CWS".format(aLight.DeviceID))
                Domoticz.Device(
                    Name=aLight.Name + " - Color",
                    Unit=i,
                    TypeName="Selector Switch",
                    Switchtype=18,
                    Options=colorOptions,
                    DeviceID=devID + ":CWS",
                ).Create()
                self.lights[devID + ":CWS"] = {"DeviceID": devID + ":CWS", "Unit": i}
                i = i + 1

            if aLight.ColorSpace == "WS" and devID + ":WS" not in self.lights:
                Domoticz.Debug("Registering: {0}:WS".format(aLight.DeviceID))
                Domoticz.Device(
                    Name=aLight.Name + " - Color",
                    Unit=i,
                    TypeName="Selector Switch",
                    Switchtype=18,
                    Options=WhiteOptions,
                    DeviceID=devID + ":WS",
                ).Create()
                self.lights[devID + ":WS"] = {"DeviceID": devID + ":WS", "Unit": i}
                i = i + 1

            # Set State
            # stateID = aLight.DeviceID
            # Domoticz.Log(str(stateID))

            # Domoticz.Log(str(self.lights[stateID]))
            # targetUnit = self.lights[stateID]["Unit"]

            # Domoticz.Log(str(targetUnit))
            # Devices[self.lights[aLight.DeviceID].Unit].Update(nValue=1, sValue="1")

            id = str(aLight.DeviceID)
            # Domoticz.Log("-{}-".format(id))
            # Domoticz.Log(str(self.lights[id]))

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

    def onStart(self):
        Domoticz.Log("onStart called")

        Domoticz.Debugging(1)

        self.registerDevices()

    def onStop(self):
        Domoticz.Log("Stopping IKEA Tradfri plugin")

        Domoticz.Debug(
            "Threads still active: " + str(threading.active_count()) + ", should be 1."
        )
        while threading.active_count() > 1:
            for thread in threading.enumerate():
                if thread.name != threading.current_thread().name:
                    Domoticz.Log(
                        "'"
                        + thread.name
                        + "' is still running, waiting otherwise Domoticz will crash on plugin exit."
                    )
            time.sleep(1.0)

        Domoticz.Debugging(0)

    def onConnect(self, Connection, Status, Description):
        Domoticz.Log("onConnect called")

    def onMessage(self, Connection, Data):
        Domoticz.Log("onMessage called")

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Log(
            "onCommand called for Unit "
            + str(Unit)
            + ": Parameter '"
            + str(Command)
            + "', Level: "
            + str(Level)
        )

        if Command == "On":
            self.lights[Unit].State=1
            Devices[Unit].Update(nValue=1, sValue="1")

        if Command == "Off":
            self.lights[Unit].State=0
            Devices[Unit].Update(nValue=0, sValue="0")

        if Command == "Set Level":
            self.lights[Unit].Level = int(Level*2.54)
            Devices[Unit].Update(nValue=1, sValue=str(Level))

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Log(
            "Notification: "
            + Name
            + ","
            + Subject
            + ","
            + Text
            + ","
            + Status
            + ","
            + str(Priority)
            + ","
            + Sound
            + ","
            + ImageFile
        )

    def onDisconnect(self, Connection):
        Domoticz.Log("onDisconnect called")

    def onHeartbeat(self):
        Domoticz.Log("onHeartbeat called")


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
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)


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

def firstFree():
    for num in range(1,250):
        if num not in Devices:
            return num
    return