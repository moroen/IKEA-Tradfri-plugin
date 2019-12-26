# IKEA Tradfri Plugin - Pycoap version
#
# Author: Moroen
#
"""
<plugin key="IKEA-Tradfri" name="IKEA Tradfri Plugin - py
version" author="moroen" version="0.5.2" wikilink="http://www.domoticz.com/wiki/plugins/plugin.html" externallink="https://www.google.com/">
    <description>
        <h2>IKEA Tradfri</h2><br/>
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
        <param field="Mode3" label="Polling interval (seconds)" width="75px" required="true" default="300"/>
        <param field="Mode4" label="Transition time (tenth of a second)" width="75px" required="false" default="10"/>
        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal"  default="true" />
            </options>
        </param>
    </params>
</plugin>
"""
import json
import site
import sys
import threading
import time
import datetime

import Domoticz

import tradfricoap
from tradfricoap import HandshakeError

from tradfri.colors import WhiteOptions, colorOptions

site.main()


class BasePlugin:
    enabled = False

    lights = {}

    lastPollTime = None
    pollInterval = None

    hasTimedOut = False

    def __init__(self):
        # self.var = 123
        return

    def indexRegisteredDevices(self):
        if len(Devices) > 0:
            # Some devices are already defined
            try:
                for aUnit in Devices:
                    dev_id = Devices[aUnit].DeviceID.split(":")
                    self.updateDevice(aUnit, dev_id[0])

                return [dev.DeviceID for key, dev in Devices.items()]
            except HandshakeError:
                self.hasTimedOut = True
                return 
            else:
                self.hasTimedOut = False

    def updateDevice(self, Unit, device_id=None, override_level=None):
        Domoticz.Debug("Updating device {}".format(device_id))
        try:
            if device_id is not None:
                self.lights[Unit] = tradfricoap.device(id=device_id)
            else:
                self.lights[Unit].Update()

            if Devices[Unit].SwitchType == 0:
                # On/off - device
                Devices[Unit].Update(
                    nValue=self.lights[Unit].State, sValue=str(self.lights[Unit].Level)
                )

            elif Devices[Unit].SwitchType == 7:
                # Dimmer
                if self.lights[Unit].Level is not None:
                    if override_level is None:
                        level = str(int(100 * (int(self.lights[Unit].Level) / 255)))
                    else:
                        level = override_level

                    Devices[Unit].Update(nValue=self.lights[Unit].State, sValue=str(level))

            if (
                Devices[Unit].DeviceID[-3:] == ":WS"
                or Devices[Unit].DeviceID[-4:] == ":CWS"
            ):
                Devices[Unit].Update(
                    nValue=self.lights[Unit].State,
                    sValue=str(self.lights[Unit].Color_level),
                )

        except HandshakeError:
            Domoticz.Error("Error updating device {}: Connection time out".format(device_id))
            self.hasTimedOut = True
            raise
        else:
            self.hasTimedOut = False

    def registerDevices(self):
        unitIds = self.indexRegisteredDevices()
        if self.hasTimedOut:
            return
            
        ikeaIds = []

        # Add unregistred lights
        try:
            if Parameters["Mode1"] == "True":
                tradfriDevices = tradfricoap.get_devices(groups=True)
            else:
                tradfriDevices = tradfricoap.get_devices()
        
            if tradfriDevices == None:
                Domoticz.Log("Failed to get Tradfri-devices")
                return

            for aLight in tradfriDevices:
                devID = str(aLight.DeviceID)
                ikeaIds.append(devID)

                if not devID in unitIds:
                    Domoticz.Debug(
                        "Processing: {0} - {1}".format(aLight.Description, aLight.Type)
                    )
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
                        if aLight.Color_space == "W":
                            continue

                if aLight.Color_space == "CWS" and devID + ":CWS" not in unitIds:
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

                if aLight.Color_space == "WS" and devID + ":WS" not in unitIds:
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

        except HandShakeError:
            Domoticz.Log("Connection to gateway timed out")
            self.hasTimedOut = True
            return
        else:
            self.hasTimedOut = False

    def onStart(self):
        Domoticz.Debug("onStart called")

        if Parameters["Mode6"] == "Debug":
            Domoticz.Debugging(1)
            tradfricoap.set_debug_level(1)

        self.pollInterval = int(Parameters["Mode3"])
        self.lastPollTime = datetime.datetime.now()

        tradfricoap.set_transition_time(Parameters["Mode4"])
        self.registerDevices()

    def onStop(self):
        Domoticz.Debug("Stopping IKEA Tradfri plugin")

        Domoticz.Debug(
            "Threads still active: " + str(threading.active_count()) + ", should be 1."
        )
        while threading.active_count() > 1:
            for thread in threading.enumerate():
                if thread.name != threading.current_thread().name:
                    Domoticz.Debug(
                        "'"
                        + thread.name
                        + "' is still running, waiting otherwise Domoticz will crash on plugin exit."
                    )
            time.sleep(1.0)

        Domoticz.Debugging(0)

    def onConnect(self, Connection, Status, Description):
        Domoticz.Debug("onConnect called")

    def onMessage(self, Connection, Data):
        Domoticz.Debug("onMessage called")

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Debug(
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
            return

        if Command == "Off":
            self.lights[Unit].State = 0
            self.updateDevice(Unit)
            return

        if Command == "Set Level":
            if Devices[Unit].DeviceID[-4:] == ":CWS":
                self.lights[Unit].Color_level = Level
            if Devices[Unit].DeviceID[-3:] == ":WS":
                self.lights[Unit].Color_level = Level
            else:
                self.lights[Unit].Level = int(Level * 2.54)

            if self.lights[Unit].Type == "Group":
                self.updateDevice(Unit, override_level=Level)
            else:
                self.updateDevice(Unit)

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Debug(
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
        Domoticz.Debug("onDisconnect called")

    def onHeartbeat(self):
        # Domoticz.Debug("onHeartbeat called")
        if self.hasTimedOut:
            Domoticz.Debug("Timeout flag set, retrying...")
            self.registerDevices()
        else:
            if Parameters["Mode2"] == "True":
                interval = (datetime.datetime.now() - self.lastPollTime).seconds
                if interval + 1 > self.pollInterval:
                    self.lastPollTime = datetime.datetime.now()
                    self.indexRegisteredDevices()


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
