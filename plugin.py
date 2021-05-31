# IKEA Tradfri Plugin - Pycoap version
#
# Author: Moroen
#

#
# Battery-icons from wpclipart.com (PD), prepared for Domoticz by Logread (https://www.domoticz.com/forum/memberlist.php?mode=viewprofile&u=11209)
#

"""
<plugin key="IKEA-Tradfri" name="IKEA Tradfri Plugin - version 0.11.1" author="moroen" version="0.11.1" externallink="https://github.com/moroen/IKEA-Tradfri-plugin">
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
                <!–– <option label="Observe" value="observe"/> -->
            </options>
        </param>
        <param field="Mode3" label="Polling interval (seconds)" width="75px" required="true" default="300"/>
        <!–– <param field="Port" label="Observe port" width="30px" required="true" default="5000"/> -->
        <param field="Mode5" label="Montior batteries" width="75px">
            <options>
                <option label="No" value="False"/>
                <option label="On value changed" value="onChanged" default="true"/>
                <option label="On every poll" value="onPoll"/>
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
from json.decoder import JSONDecodeError
import traceback
import os, platform
import json
import site
import sys
import threading
import time
import datetime
from importlib import reload

# Get full import PATH
site.main()

_globalError = None

_version = "0.11.1"

_use_local_tradfricoap = False

# See if there is a local tradfricoap-directory
_use_local_tradfricoap = os.path.isdir(
    "{}/tradfricoap".format(os.path.dirname(os.path.realpath(__file__)))
)

_development = os.path.exists("{}/development".format(os.path.dirname(os.path.realpath(__file__))))

if _use_local_tradfricoap:
    # Check if local tradfricoap is usable
    print("Using local")
    from pkg_resources import get_distribution, DistributionNotFound

    if not os.path.exists(
        "{}/tradfricoap/setup.py".format(os.path.dirname(os.path.realpath(__file__)))
    ):
        print("Fy og føy")
        _globalError = "There seems to be an empty tradfricoap directory present. Please remove it before running the plugin!"
    else:
        try:
            get_distribution("tradfricoap")
            _globalError = "Tradfricoap appears to be installed both as a system- and local module. Please remove the tradfricoap directory before running the plugin!"
        except DistributionNotFound:
            pass

if _globalError is None:
    # Need to set config before import from module
    try:
        if _use_local_tradfricoap:
            from tradfricoap.tradfricoap.config import get_config, host_config
            from tradfricoap.tradfricoap import ApiNotFoundError
            from tradfricoap.tradfricoap.coapcmd_api import set_coapcmd
        else:
            from tradfricoap.config import get_config, host_config
            from tradfricoap import ApiNotFoundError
            from tradfricoap.coapcmd_api import set_coapcmd

        if os.path.isdir("/config"):
            # Running in the moroen/domoticz-tradfri docker container
            CONFIGFILE = "/config/tradfri.json"
        else:
            # Running on system
            CONFIGFILE = "{}/config.json".format(
                os.path.dirname(os.path.realpath(__file__))
            )

        CONF = get_config(CONFIGFILE).configuation

        if platform.system() == "Windows":
            set_coapcmd(
                "{}/bin/coapcmd.exe".format(os.path.dirname(os.path.realpath(__file__)))
            )
        else:
            set_coapcmd(
                "{}/bin/coapcmd".format(os.path.dirname(os.path.realpath(__file__)))
            )

    except ImportError:
        _globalError = "Module 'tradfricoap' not found"

if __name__ == "__main__":
    if _globalError is not None:
        print(_globalError)
        exit()

    if _use_local_tradfricoap:
        from tradfricoap.tradfricoap.cli import process_args, get_args
        from tradfricoap.tradfricoap.version import get_version_info
    else:
        from tradfricoap.cli import process_args, get_args
        from tradfricoap.version import get_version_info

    try:
        args = get_args()
        if args.command == "version":
            if args.short:
                print(_version)
            else:
                print("IKEA Tradfri Plugin: {}".format(_version))
        
        process_args(args)
    except ApiNotFoundError as e:
        print("Error: {}".format(e.message))
    exit()


## Domoticz Plugin
import Domoticz

from shutil import copy2, SameFileError

if _globalError is None:

    try:
        if _use_local_tradfricoap:
            from tradfricoap.tradfricoap.device import (
                get_device,
                get_devices,
                set_transition_time,
            )

            import tradfricaop.tradfricoap.server as server

            from tradfricoap.tradfricoap.errors import (
                HandshakeError,
                UriNotFoundError,
                ReadTimeoutError,
                WriteTimeoutError,
                set_debug_level,
                DeviceNotFoundError,
                MethodNotAllowedError,
                GatewayNotSpecified,
            )
            from tradfricoap.tradfricoap.colors import WhiteOptions, colorOptions
            from tradfricoap.tradfricoap.gateway import close_connection
        else:
            from tradfricoap.device import get_device, get_devices, set_transition_time
            import tradfricoap.server as server
            from tradfricoap.errors import (
                HandshakeError,
                UriNotFoundError,
                ReadTimeoutError,
                WriteTimeoutError,
                set_debug_level,
                DeviceNotFoundError,
                MethodNotAllowedError,
                GatewayNotSpecified,
            )
            from tradfricoap.colors import WhiteOptions, colorOptions
            from tradfricoap.gateway import close_connection

            # from tradfricoap.observe import observe_start, observe_stop

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

    monitor_batteries = False
    monitor_batteries_method = "onChanged"

    lastPollTime = None
    pollInterval = None

    hasTimedOut = False
    devicesMoving = []
    commandQueue = []

    httpServerConn = None
    httpServerConns = {}
    httpClientConn = None

    icons = {
        "IKEA-Tradfri_batterylevelfull": "icons/battery_full.zip",
        "IKEA-Tradfri_batterylevelok": "icons/battery_ok.zip",
        "IKEA-Tradfri_batterylevellow": "icons/battery_low.zip",
        "IKEA-Tradfri_batterylevelempty": "icons/battery_empty.zip",
    }

    templates = {
        "tradfri.html", "tradfri.js", "tradfri.requests.js"
    }

    def __init__(self):
        return

    def install_templates(self):
        Domoticz.Log("Installing custom pages")
        if not _development:
            source_path = Parameters['HomeFolder'] + 'templates/'
            templates_path = Parameters['StartupFolder'] + 'www/templates/'
            try: 
                for aFile in self.templates:
                    Domoticz.Log("Copy file {} to {}".format(source_path+aFile, templates_path))
                    copy2(source_path + aFile, templates_path)
            except SameFileError:
                self.uninstall_templates()
                self.install_templates()       
        else:
            Domoticz.Log("Developement mode set, skipping templates copy")

    def uninstall_templates(self):
        templates_path = Parameters['StartupFolder'] + 'www/templates/'
        
        Domoticz.Log("Removing custom pages")

        if not _development:
            for aFile in self.templates:   
                if (os.path.exists(templates_path + aFile)):
                    os.remove(templates_path + aFile)
        else:
            Domoticz.Log("Developement mode set, skipping templates remove")

    def indexRegisteredDevices(self):

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

        try:
            devID = int(str(Devices[Unit].DeviceID).split(":")[0])

            if devID in self.tradfri_devices:
                ikea_device = self.tradfri_devices[devID]
            else:
                return
        except TypeError:
            self.hasTimedOut = True
            return

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
                        nValue=ikea_device.State,
                        sValue=str(ikea_device.Level),
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
                        nValue=ikea_device.State,
                        sValue=str(ikea_device.Level),
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

        elif Devices[Unit].Type == 243 and self.monitor_batteries:
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

                if (
                    Devices[Unit].sValue != str(ikea_device.Battery_level)
                ) or self.monitor_batteries_method == "onPoll":
                    Devices[Unit].Update(
                        nValue=0,
                        sValue=str(ikea_device.Battery_level),
                        Image=Images[image].ID,
                    )

        self.hasTimedOut = False
        return deviceUpdated

        # except (HandshakeError, ReadTimeoutError, WriteTimeoutError):
        #     Domoticz.Debug(
        #         "Error updating device {}: Connection time out".format(devID)
        #     )
        #     self.hasTimedOut = True
        # except Exception as err:
        #     raise

    def registerDevices(self):

        try:
            if self.includeGroups:
                self.tradfri_devices = get_devices(groups=True)
            else:
                self.tradfri_devices = get_devices()
        except (HandshakeError, ReadTimeoutError, WriteTimeoutError):
            Domoticz.Debug("Connection to gateway timed out")
            self.hasTimedOut = True
            return

        if self.hasTimedOut:
            return

        unitIds = self.indexRegisteredDevices()

        # Fallback if json fails with unraised error
        if self.tradfri_devices == None:
            Domoticz.Error("Failed to get Tradfri-devices")
            self.hasTimedOut = True
            return

        # Add unregistred ikea_devices

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

            if self.monitor_batteries:
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

        # Add reboot button
        if "15011" not in unitIds:
            new_unit_id = firstFree()
            Domoticz.Debug("Registering 15011")

            Domoticz.Device(
                Name="Reboot Tradfri Gateway",
                Unit=new_unit_id,
                TypeName="Push On",
                DeviceID="15011",
            ).Create()

        # Remove registered ikea_devices no longer found on the gateway
        for aUnit in list(Devices.keys()):
            devID = str(Devices[aUnit].DeviceID).split(":")

            if devID[0] == "15011":
                continue

            if not int(devID[0]) in self.tradfri_devices:
                Devices[aUnit].Delete()

            if not self.monitor_batteries and len(devID) == 2:
                if devID[1] == "Battery":
                    Devices[aUnit].Delete()

        self.hasTimedOut = False

    def onStart(self):

        if _globalError is not None:
            Domoticz.Error("Failed to initialize tradfri module.")
            Domoticz.Error(_globalError)
            return

        try:
            if Parameters["Mode6"] == "Debug":
                Domoticz.Debugging(1)
                set_debug_level(1)
        except ValueError:
            Domoticz.Debugging(0)

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

        try:
            self.monitor_batteries_method = Parameters["Mode5"]
            self.monitor_batteries = False if Parameters["Mode5"] == "False" else True
        except ValueError:
            Domoticz.Error(
                "Illegal value for 'Montior batteries'. Using default (On value changed)"
            )
            self.monitor_batteries = True
            self.monitor_batteries_method = "onChanged"

        try:
            set_transition_time(int(Parameters["Mode4"]))
        except ValueError:
            Domoticz.Error("Illegal value for 'Transition time'. Using default (10)")
            set_transition_time(10)

        # Install icons
        for key, filename in self.icons.items():
            if key not in Images:
                Domoticz.Image(filename).Create()

        Domoticz.Debug("Number of icons loaded = " + str(len(Images)))
        for image in Images:
            Domoticz.Debug("Icon {} {}".format(Images[image].ID, Images[image].Name))

        # Install templates
        self.install_templates()

        try:
            self.registerDevices()

            # Observe

            if Parameters["Mode2"] == "observe":
                observe_start()

        except ApiNotFoundError as e:
            Domoticz.Error("Failed to initialize tradfri module.")
            Domoticz.Error(e.message)

        except GatewayNotSpecified as e:
            Domoticz.Error("Gateway config not found...")

        # Server
        if _globalError is None:
            Domoticz.Debug("Starting http-server")
            self.httpServerConn = Domoticz.Connection(
                Name="Server Connection",
                Transport="TCP/IP",
                Protocol="HTTP",
                Port="8085",
            )
            self.httpServerConn.Listen()

    def onStop(self):
        Domoticz.Debug("Stopping IKEA Tradfri plugin")

        # Stopping server
        if self.httpClientConn is not None:
            self.httpServerConn.Disconnect()

        if Parameters["Mode2"] == "observe":
            pass
            # Domoticz.Debug("Stopping observe")
            # observe_stop()

        self.uninstall_templates()

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
        # if (Status == 0):
        #     Domoticz.Log("Connected successfully to: "+Connection.Address+":"+Connection.Port)
        # else:
        #     Domoticz.Log("Failed to connect ("+str(Status)+") to: "+Connection.Address+":"+Connection.Port+" with error: "+Description)
        # Domoticz.Log(str(Connection))
        # if (Connection != self.httpClientConn):
        #     self.httpServerConns[Connection.Name] = Connection

    def onMessage(self, Connection, Data):
        Domoticz.Log(
            "onMessage called for connection: "
            + Connection.Address
            + ":"
            + Connection.Port
        )
        
        # reload(server)
        # DumpHTTPResponseToLog(Data)

        ret_val = server.handle_request(Data)
        data = ret_val.response
        try:
            command = json.loads(data.decode("utf-8"))["Command"]
            if command == "/setup":
                self.registerDevices()

        except JSONDecodeError:
            Domoticz.Error("Unable to process server command")

        Connection.Send(
            {
                "Status": str(ret_val.status),
                "Headers": {
                    "Connection": "keep-alive",
                    "Content-Type": ret_val.content_type,
                    "Access-Control-Allow-Origin": "*",
                },
                "Data": data,
            }
        )

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
            # Reboot
            if devID == 15011:
                if _use_local_tradfricoap:
                    from tradfricoap.tradfricoap.gateway import reboot
                else:
                    from tradfricoap.gateway import reboot

                Domoticz.Debug("Reboot IKEA Gateway called")
                reboot()

            elif Command == "On":
                self.tradfri_devices[devID].State = 1
                self.updateDevice(Unit)
                if self.tradfri_devices[devID].Type == "Blind":
                    self.devicesMoving.append(Unit)
                # return

            elif Command == "Off":
                self.tradfri_devices[devID].State = 0
                self.updateDevice(Unit)
                if self.tradfri_devices[devID].Type == "Blind":
                    self.devicesMoving.append(Unit)
                # return

            elif Command == "Set Level":
                Domoticz.Debug("Command Level: {}".format(Level))
                Level = int(Level)

                if Devices[Unit].DeviceID[-4:] == ":CWS":
                    self.tradfri_devices[devID].Color_level = Level
                elif Devices[Unit].DeviceID[-3:] == ":WS":
                    self.tradfri_devices[devID].Color_level = Level
                else:
                    if Level not in range(0, 101):
                        Level = 100 if Level > 100 else 0
                    if self.tradfri_devices[devID].Type == "Blind":
                        self.tradfri_devices[devID].Level = Level
                        self.devicesMoving.append(Unit)
                    else:
                        self.tradfri_devices[devID].Level = int(Level * 2.54)

                if self.tradfri_devices[devID].Type == "Group":
                    self.updateDevice(Unit, override_level=Level)
                else:
                    self.updateDevice(Unit)

                Domoticz.Debug(
                    "Ikea Level: {}".format(self.tradfri_devices[devID].Level)
                )

            Domoticz.Debug("Finnished command")

        except KeyError:
            Domoticz.Error(
                "OnCommand failed for device: {} with command: {} and level: {}".format(
                    devID, Command, Level
                )
            )

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
        Domoticz.Log("onDisconnect called for connection '" + Connection.Name + "'.")
        Domoticz.Log("Server Connections:")
        for x in self.httpServerConns:
            Domoticz.Log("--> " + str(x) + "'.")
        if Connection.Name in self.httpServerConns:
            del self.httpServerConns[Connection.Name]

    def onHeartbeat(self):
        # Domoticz.Debug("onHeartbeat called")

        for aUnit in self.devicesMoving:
            Domoticz.Debug(
                "Device {} has moving flag set".format(Devices[aUnit].DeviceID)
            )
            if self.updateDevice(aUnit) is False:
                self.devicesMoving.remove(aUnit)

        for aCommand in self.commandQueue:
            Domoticz.Log("Command in queue")
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

        if _globalError is None:
            close_connection()
            # pass


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


#
# Generic helper functions
#


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


def DumpHTTPResponseToLog(httpDict):
    if isinstance(httpDict, dict):
        Domoticz.Log("HTTP Details (" + str(len(httpDict)) + "):")
        for x in httpDict:
            if isinstance(httpDict[x], dict):
                Domoticz.Log("--->'" + x + " (" + str(len(httpDict[x])) + "):")
                for y in httpDict[x]:
                    Domoticz.Log("------->'" + y + "':'" + str(httpDict[x][y]) + "'")
            else:
                Domoticz.Log("--->'" + x + "':'" + str(httpDict[x]) + "'")
