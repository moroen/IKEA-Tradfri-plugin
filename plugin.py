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

import tradfricoap
from colors import WhiteOptions, colorOptions


class BasePlugin:
    enabled = False

    lights = {}

    def __init__(self):
        # self.var = 123
        return

    def indexRegisteredDevices(self):
        if len(Devices) > 0:
            # Some devices are already defined
            for aUnit in Devices:
                dev_id = Devices[aUnit].DeviceID.split(":")
                self.updateDevice(aUnit, dev_id[0])

        return [dev.DeviceID for key, dev in Devices.items()]

    def updateDevice(self, Unit, device_id=None):
        if device_id is not None:
            self.lights[Unit] = tradfricoap.get_device(device_id)
        else:
            self.lights[Unit].Update()

        if Devices[Unit].SwitchType == 0:
            # On/off - device
            Devices[Unit].Update(
                nValue=self.lights[Unit].State, sValue=str(self.lights[Unit].Level)
            )

        elif Devices[Unit].SwitchType == 7:
            # Dimmer
            level = str(int(100 * (int(self.lights[Unit].Level) / 255)))
            Devices[Unit].Update(nValue=self.lights[Unit].State, sValue=level)

    def registerDevices(self):

        unitIds = self.indexRegisteredDevices()
        ikeaIds = []

        for key, aLight in self.lights.items():
            print("Unit {}: {}".format(key, aLight.Description))

        # Add unregistred lights
        tradfriDevices = tradfricoap.get_devices()

        if tradfriDevices == None:
            Domoticz.Log("Failed to get Tradfri-devices")
            return

        for aLight in tradfriDevices:
            devID = str(aLight.DeviceID)
            ikeaIds.append(devID)

            if not devID in unitIds:
                Domoticz.Debug("Processing: {0}".format(aLight.Description))
                new_unit_id = firstFree()

                if aLight.Type == "Plug":
                    Domoticz.Device(
                        Name=aLight.Name,
                        Unit=new_unit_id,
                        Type=244,
                        Subtype=73,
                        Switchtype=0,
                        Image=1,
                        DeviceID=devID,
                    ).Create()
                    self.updateDevice(new_unit_id, devID)

                if aLight.Type == "Remote":
                    Domoticz.Device(
                        Name=aLight.Name + " - Battery level",
                        Unit=new_unit_id,
                        Type=243,
                        Subtype=6,
                        DeviceID=devID,
                    ).Create()

                if aLight.Type == "Light" or aLight.Type == "Group":
                    deviceType = 244
                    subType = 73
                    switchType = 7

                    # Basic device
                    Domoticz.Device(
                        Name=aLight.Name,
                        Unit=new_unit_id,
                        Type=deviceType,
                        Subtype=subType,
                        Switchtype=switchType,
                        DeviceID=devID,
                    ).Create()
                    self.updateDevice(new_unit_id, devID)
                    if aLight.ColorSpace == "W":
                        continue

            if str(aLight.ColorSpace) == "CWS" and devID + ":CWS" not in self.lights:
                new_unit_id = firstFree()
                Domoticz.Debug("Registering: {0}:CWS".format(aLight.DeviceID))
                Domoticz.Device(
                    Name=aLight.Name + " - Color",
                    Unit=new_unit_id,
                    TypeName="Selector Switch",
                    Switchtype=18,
                    Options=colorOptions,
                    DeviceID=devID + ":CWS",
                ).Create()
                self.updateDevice(new_unit_id, devID)

            if aLight.ColorSpace == "WS" and devID + ":WS" not in unitIds:
                new_unit_id = firstFree()
                Domoticz.Debug("Registering: {0}:WS".format(aLight.DeviceID))
                Domoticz.Device(
                    Name=aLight.Name + " - Color",
                    Unit=new_unit_id,
                    TypeName="Selector Switch",
                    Switchtype=18,
                    Options=WhiteOptions,
                    DeviceID=devID + ":WS",
                ).Create()
                self.updateDevice(new_unit_id, devID)

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
        tradfricoap.set_transition_time(Parameters["Mode4"])
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
            self.lights[Unit].State = 1
            self.updateDevice(Unit)

        if Command == "Off":
            self.lights[Unit].State = 0
            self.updateDevice(Unit)

        if Command == "Set Level":
            if devID[-4:] == ":CWS":
                pass
            elif devID[-3:] == ":WS":
                pass
            else:
                self.lights[Unit].Level = int(Level * 2.54)

            self.updateDevice(Unit)

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
    for num in range(1, 250):
        if num not in Devices:
            return num
    return
