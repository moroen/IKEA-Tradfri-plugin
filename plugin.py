# IKEA Tradfri Plugin - Pycoap version
#
# Author: Moroen
#

#
# Battery-icons from wpclipart.com (PD), prepared for Domoticz by Logread (https://www.domoticz.com/forum/memberlist.php?mode=viewprofile&u=11209)
#

"""
<plugin key="IKEA-Tradfri" name="IKEA Tradfri Plugin - version 0.9.1" author="moroen" version="0.9.1" externallink="https://github.com/moroen/IKEA-Tradfri-plugin">
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
        <param field="Mode2" label="Monitor changes" width="75px">
            <options>
                <option label="No" value="none"  default="true" />
                <option label="Poll" value="poll"/>
                <option label="Observe" value="observe"/>
            </options>
        </param>
        <param field="Mode3" label="Polling interval (seconds)" width="75px" required="true" default="300"/>
        <param field="Mode5" label="Montior batteries" width="75px">
            <options>
                <option label="Yes" value="True"/>
                <option label="No" value="False"  default="true" />
            </options>
        </param>
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
import traceback
import os
import json
import site
import sys
import threading
import time
import datetime

# Get full import PATH
site.main()

_globalError = None

# Need to set config before import from module
try:
    from tradfricoap.config import get_config, host_config
    from tradfricoap import ApiNotFoundError

    CONFIGFILE = "{}/config.json".format(os.path.dirname(os.path.realpath(__file__)))
    CONF = get_config(CONFIGFILE)

    if CONF["Api"] == "Coapcmd":
        from tradfricoap.coapcmd_api import set_coapcmd

        set_coapcmd(
            "{}/bin/coapcmd".format(os.path.dirname(os.path.realpath(__file__)))
        )

except ImportError:
    _globalError = "Module 'tradfricoap' not found"

if __name__ == "__main__":
    from cli import get_args

    # from tradfri.config import host_config

    args = get_args()
    if args.command == "api":
        config = host_config(CONFIGFILE)
        config.set_config_item("api", args.API)
        config.save()
        exit()

    try:
        from tradfricoap.device import get_devices, get_device
        from tradfricoap.gateway import create_ident
        from tradfricoap.errors import HandshakeError

    except ImportError:
        print("Module 'tradfricoap' not found!")
        exit()

    except ApiNotFoundError as e:
        if e.api == "pycoap":
            print(
                'Py3coap module not found!\nInstall with "pip3 install py3coap" or select another api with "python3 plugin.py api"'
            )
        elif e.api == "coapcmd":
            print(
                'coapcmd  not found!\nInstall with "bash install_coapcmd.sh" or select another api with "python3 plugin.py api"'
            )
        exit()

    # if args.command == "observe":
    #     from tradfricoap.observe import startObserve, stopObserve

    #     print("observe")
    #     startObserve()
    #     time.sleep(10)
    #     stopObserve()

    if args.command == "list":
        try:
            devices = get_devices(args.groups)
        except HandshakeError:
            print("Connection timed out")
            exit()

        except ApiNotFoundError as e:
            print(e.message)
            exit()

        if devices is None:
            print("Unable to get list of devices")
        else:
            ikea_devices = []
            plugs = []
            blinds = []
            groups = []
            batteries = []
            others = []

            for key, dev in devices.items():
                if dev.Type == "Light":
                    ikea_devices.append(dev.Description)
                elif dev.Type == "Plug":
                    plugs.append(dev.Description)
                elif dev.Type == "Blind":
                    blinds.append(dev.Description)
                elif dev.Type == "Group":
                    groups.append(dev.Description)
                else:
                    others.append(dev.Description)

                if dev.Battery_level is not None:
                    batteries.append(
                        "{}: {} - {}".format(dev.DeviceID, dev.Name, dev.Battery_level)
                    )

            if len(ikea_devices):
                print("ikea_devices:")
                print("\n".join(ikea_devices))

            if len(plugs):
                print("\nPlugs:")
                print("\n".join(plugs))

            if len(blinds):
                print("\nBlinds:")
                print("\n".join(blinds))

            if len(groups):
                print("\nGroups:")
                print("\n".join(groups))

            if len(others):
                print("\nOthers:")
                print("\n".join(others))

            if len(batteries):
                print("\nBatteries:")
                print("\n".join(batteries))

    elif args.command == "config":
        try:
            create_ident(args.IP, args.KEY, CONFIGFILE)
        except HandshakeError:
            print("Connection timed out")

    exit()


## Domoticz Plugin
import Domoticz

try:
    from tradfricoap.device import get_device, get_devices, set_transition_time
    from tradfricoap.errors import (
        HandshakeError,
        UriNotFoundError,
        ReadTimeoutError,
        WriteTimeoutError,
        set_debug_level,
        DeviceNotFoundError,
        MethodNotSupported,
    )
    from tradfricoap.colors import WhiteOptions, colorOptions
    from tradfricoap.observe import observe_start, observe_stop

except ImportError:
    _globalError = "Unable to find tradfricoap"
except SystemExit:
    _globalError = "Unable to initialize tradfricoap"
except ApiNotFoundError as e:
    _globalError = e.message


class BasePlugin:
    enabled = False

    tradfri_devices = {}
    batteries = []

    includeGroups = False
    updateMode = "none"
    monitorBatteries = False

    lastPollTime = None
    pollInterval = None

    hasTimedOut = False
    devicesMoving = []
    commandQueue = []

    icons = {
        "IKEA-Tradfri_batterylevelfull": "icons/battery_full.zip",
        "IKEA-Tradfri_batterylevelok": "icons/battery_ok.zip",
        "IKEA-Tradfri_batterylevellow": "icons/battery_low.zip",
        "IKEA-Tradfri_batterylevelempty": "icons/battery_empty.zip",
    }

    def __init__(self):
        return

    def indexRegisteredDevices(self):

        try:
            if self.includeGroups:
                self.tradfri_devices = get_devices(groups=True)
            else:
                self.tradfri_devices = get_devices()
        except (HandshakeError, ReadTimeoutError, WriteTimeoutError):
            Domoticz.Debug("Connection to gateway timed out")
            self.hasTimedOut = True
            return

        if len(Devices) > 0:
            # Some devices are already defined

            try:
                for aUnit in Devices:
                    dev_id = Devices[aUnit].DeviceID.split(":")
                    if len(dev_id) > 1:
                        if dev_id[1] == "Battery":
                            pass

                    self.updateDevice(aUnit)

                return [dev.DeviceID for key, dev in Devices.items()]

            except (HandshakeError, ReadTimeoutError, WriteTimeoutError):
                self.hasTimedOut = True
                return
            else:
                self.hasTimedOut = False
        else:
            deviceID = [-1]
            return deviceID

    def updateDevice(self, Unit, override_level=None):
        # Domoticz.Debug("Updating device {} - Type {} Subtype {} Switchtype {}".format(Devices[Unit].DeviceID, Devices[Unit].Type, Devices[Unit].SubType, Devices[Unit].SwitchType))
        deviceUpdated = False
        # try:

        devID = int(str(Devices[Unit].DeviceID).split(":")[0])
        ikea_device = self.tradfri_devices[devID]

        if self.updateMode == "poll":
            ikea_device.Update()

        if Devices[Unit].Type == 244:
            # Switches

            if Devices[Unit].SwitchType == 0:
                # On/off - device
                if (Devices[Unit].nValue != ikea_device.State) or (
                    Devices[Unit].sValue != str(ikea_device.Level)
                ):
                    Devices[Unit].Update(
                        nValue=ikea_device.State, sValue=str(ikea_device.Level),
                    )

            elif Devices[Unit].SwitchType == 7:
                # Dimmer
                if ikea_device.Level is not None:
                    if override_level is None:
                        level = str(int(100 * (int(ikea_device.Level) / 255)))
                    else:
                        level = override_level

                    if (Devices[Unit].nValue != ikea_device.State) or (
                        Devices[Unit].sValue != str(level)
                    ):
                        Devices[Unit].Update(
                            nValue=ikea_device.State, sValue=str(level)
                        )

            elif Devices[Unit].SwitchType == 13:
                # Blinds
                if (Devices[Unit].nValue != ikea_device.State) or (
                    Devices[Unit].sValue != str(ikea_device.Level)
                ):
                    Devices[Unit].Update(
                        nValue=ikea_device.State, sValue=str(ikea_device.Level),
                    )
                    deviceUpdated = True

            elif Devices[Unit].SwitchType == 18:
                # Selector
                if (
                    Devices[Unit].DeviceID[-3:] == ":WS"
                    or Devices[Unit].DeviceID[-4:] == ":CWS"
                ):
                    if (Devices[Unit].nValue != ikea_device.State) or (
                        Devices[Unit].sValue != str(ikea_device.Color_level)
                    ):
                        Devices[Unit].Update(
                            nValue=ikea_device.State,
                            sValue=str(ikea_device.Color_level),
                        )

        elif Devices[Unit].Type == 243 and self.monitorBatteries:
            if Devices[Unit].SubType == 31:
                # Custom sensor
                if ikea_device.Battery_level >= 75:
                    image = "IKEA-Tradfri_batterylevelfull"
                elif ikea_device.Battery_level >= 50 and ikea_device.Battery_level < 75:
                    image = "IKEA-Tradfri_batterylevelok"
                elif ikea_device.Battery_level >= 25 and ikea_device.Battery_level < 50:
                    image = "IKEA-Tradfri_batterylevellow"
                else:
                    image = "IKEA-Tradfri_batterylevelempty"

                if Devices[Unit].sValue != str(ikea_device.Battery_level):
                    Devices[Unit].Update(
                        nValue=0,
                        sValue=str(ikea_device.Battery_level),
                        Image=Images[image].ID,
                    )

        self.hasTimedOut = False
        return deviceUpdated

        # except (HandshakeError, ReadTimeoutError, WriteTimeoutError):
        #     Domoticz.Debug(
        #         "Error updating device {}: Connection time out".format(device_id)
        #     )
        #     self.hasTimedOut = True
        # except Exception as err:
        #     # traceback.print_tb(err.__traceback__)
        #     # raise
        #     exc_type, exc_obj, exc_tb = sys.exc_info()
        #     fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        #     print(exc_type, fname, exc_tb.tb_lineno)
        #     raise

    def registerDevices(self):
        unitIds = self.indexRegisteredDevices()
        if self.hasTimedOut:
            return

        # Add unregistred ikea_devices
        # try:

        if self.tradfri_devices == None:
            Domoticz.Log("Failed to get Tradfri-devices")
            return

        for id, aLight in self.tradfri_devices.items():

            devID = str(id)

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
                    self.updateDevice(new_unit_id)

                if aLight.Type == "Remote":
                    Domoticz.Device(
                        Name=aLight.Name + " - Battery level",
                        Unit=new_unit_id,
                        Type=243,
                        Subtype=6,
                        DeviceID=devID,
                    ).Create()

                if aLight.Type == "Blind":
                    deviceType = 244
                    subType = 73
                    switchType = 13

                    Domoticz.Device(
                        Name=aLight.Name,
                        Unit=new_unit_id,
                        Type=deviceType,
                        Subtype=subType,
                        Switchtype=switchType,
                        DeviceID=devID,
                    ).Create()
                    self.updateDevice(new_unit_id)

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
                    self.updateDevice(new_unit_id)
                    if aLight.Color_space == "W":
                        continue

            if self.monitorBatteries:
                if (
                    aLight.Battery_level is not None
                    and devID + ":Battery" not in unitIds
                ):
                    new_unit_id = firstFree()
                    Domoticz.Debug("Registering: {0}:Battery".format(aLight.DeviceID))
                    Domoticz.Device(
                        Name=aLight.Name + " - Battery",
                        Unit=new_unit_id,
                        TypeName="Custom",
                        Options={"Custom": "1;%"},
                        DeviceID=devID + ":Battery",
                    ).Create()
                    self.updateDevice(new_unit_id)

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
                self.updateDevice(new_unit_id)

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
                self.updateDevice(new_unit_id)

        # Remove registered ikea_devices no longer found on the gateway
        for aUnit in list(Devices.keys()):
            devID = str(Devices[aUnit].DeviceID).split(":")

            if not int(devID[0]) in self.tradfri_devices:
                Devices[aUnit].Delete()

            if not self.monitorBatteries and len(devID) == 2:
                if devID[1] == "Battery":
                    Devices[aUnit].Delete()

        self.hasTimedOut = False

    def onStart(self):
        try:
            if Parameters["Mode6"] == "Debug":
                Domoticz.Debugging(1)
                set_debug_level(1)
        except ValueError:
            Domoticz.Debugging(0)

        if _globalError is not None:
            Domoticz.Error("Failed to initialize tradfri module.")
            Domoticz.Error(_globalError)
            return

        try:
            if Parameters["Mode1"] == "True":
                self.includeGroups = True
        except ValueError:
            Domoticz.Error(
                "Illegal value for 'Add groups as devices'. Using default (No)"
            )

        try:
            if Parameters["Mode2"] == "poll":
                self.updateMode = "poll"
                self.lastPollTime = datetime.datetime.now()
            elif Parameters["Mode2"] == "observe":
                self.updateMode = "observe"
            elif Parameters["Mode2"] == "none":
                self.updateMode = "none"
        except ValueError:
            Domoticz.Error("Illegal value for 'Observe changes'. Using default (No)")
            self.updateMode = "none"

        Domoticz.Debug("Monitor changes method: {}".format(self.updateMode))

        try:
            self.pollInterval = int(Parameters["Mode3"])
        except ValueError:
            Domoticz.Error("Illegal value for 'Polling interval'. Using default (300)")
            self.pollInterval = 300

        if Parameters["Mode5"] == "True":
            self.monitorBatteries = True
        elif Parameters["Mode5"] == "False":
            self.monitorBatteries = False
        else:
            Domoticz.Error("Illegal value for 'Montior batteries'. Using default (No)")
            self.monitorBatteries = False

        try:
            set_transition_time(int(Parameters["Mode4"]))
        except ValueError:
            Domoticz.Error("Illegal value for 'Transition time'. Using default (10)")
            set_transition_time(10)

        for key, filename in self.icons.items():
            if key not in Images:
                Domoticz.Image(filename).Create()

        Domoticz.Debug("Number of icons loaded = " + str(len(Images)))
        for image in Images:
            Domoticz.Debug("Icon {} {}".format(Images[image].ID, Images[image].Name))

        # try:
        self.registerDevices()

        if Parameters["Mode2"] == "observe":
            Domoticz.Debug("Starting observe")
            observe_start()

        #except ApiNotFoundError as e:
        #    Domoticz.Error("Failed to initialize tradfri module.")
        #    Domoticz.Error(e.message)

    def onStop(self):
        Domoticz.Debug("Stopping IKEA Tradfri plugin")
        
        if Parameters["Mode2"] == "observe":
            Domoticz.Debug("Stopping observe")
            observe_stop()


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

        devID = int(str(Devices[Unit].DeviceID).split(":")[0])

        try:
            if Command == "On":
                self.tradfri_devices[devID].State = 1
                self.updateDevice(Unit)
                if self.tradfri_devices[devID].Type == "Blind":
                    self.devicesMoving.append(Unit)
                return

            if Command == "Off":
                self.tradfri_devices[devID].State = 0
                self.updateDevice(Unit)
                if self.tradfri_devices[devID].Type == "Blind":
                    self.devicesMoving.append(Unit)
                return

            if Command == "Set Level":
                if Devices[Unit].DeviceID[-4:] == ":CWS":
                    self.tradfri_devices[devID].Color_level = Level
                if Devices[Unit].DeviceID[-3:] == ":WS":
                    self.tradfri_devices[devID].Color_level = Level
                else:
                    if self.tradfri_devices[devID].Type == "Blind":
                        self.tradfri_devices[devID].Level = int(Level)
                        self.devicesMoving.append(Unit)
                    else:
                        self.tradfri_devices[devID].Level = int(Level * 2.54)

                if self.tradfri_devices[devID].Type == "Group":
                    self.updateDevice(Unit, override_level=Level)
                else:
                    self.updateDevice(Unit)
        except (HandshakeError, ReadTimeoutError, WriteTimeoutError):
            comObj = {"Unit": Unit, "Command": Command, "Level": Level}
            Domoticz.Debug(
                "Command timed out. Pushing {} onto commandQueue".format(comObj)
            )
            self.commandQueue.append(comObj)

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

        for aUnit in self.devicesMoving:
            Domoticz.Debug(
                "Device {} has moving flag set".format(Devices[aUnit].DeviceID)
            )
            if self.updateDevice(aUnit) is False:
                self.devicesMoving.remove(aUnit)

        for aCommand in self.commandQueue:
            Domoticz.Debug("Trying to execute {} from commandQueue".format(aCommand))
            self.commandQueue.remove(aCommand)
            self.onCommand(
                aCommand["Unit"], aCommand["Command"], aCommand["Level"], None
            )

        if self.hasTimedOut:
            Domoticz.Debug("Timeout flag set, retrying...")
            self.hasTimedOut = False
            self.registerDevices()
        else:
            if self.updateMode == "poll":
                if self.lastPollTime is None:
                    self.lastPollTime = datetime.datetime.now()
                else:
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
