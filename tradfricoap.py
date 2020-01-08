
__version__ = "0.6.0"

# Standard library
import json, logging, time, sys, site, argparse, os

# Module
from tradfri.config import get_config, host_config
from tradfri import constants
from tradfri import colors, cli

site.main()

_transition_time = 10
_debug = 0

CONFIGFILE = "{}/config.json".format(os.path.dirname(os.path.realpath(__file__)))
CONF = get_config(CONFIGFILE)

if CONF["Api"] == "Pycoap":
    try:
        from tradfri.pycoap_api import request, set_debug_level, HandshakeError, UriNotFoundError, create_ident
    except ModuleNotFoundError:
        if __name__ == "__main__":
            args = cli.get_args()
            if args.command == "api":
                config = host_config(CONFIGFILE)
                config.set_config_item("api", args.API)
                config.save()
            else:
                print("Pycoap module not found!\nInstall with \"pip3 install -r requirements.txt\" or select another api with \"python3 tradfricoap.py api\"")
            exit()
        else:
            raise

if CONF["Api"] == "Coapcmd":
    try:
        from tradfri.coapcmd_api import request, set_debug_level, HandshakeError, UriNotFoundError, create_ident
    except ModuleNotFoundError:
        if __name__ == "__main__":
            args = cli.get_args()
            if args.command == "api":
                config = host_config(CONFIGFILE)
                config.set_config_item("api", args.API)
                config.save()
            else:
                print("coapcmd  not found!\nInstall with \"bash install_coapcmd.sh\" or select another api with \"python3 tradfricoap.py api\"")
            exit()
        else:
            raise

def set_transition_time(tt):
    global _transition_time
    _transition_time = int(tt)

class device:
    lightControl = None
    plugControl = None
    _id = None
    _is_group = False
    _group_members = []

    def __init__(self, id, is_group=False):
        self._id = id

        res = None

        if is_group == True:
            self._is_group = True

        if not self._is_group:
            try:
                uri = "{}/{}".format(constants.uriDevices, id)
                res = request(uri)
            except HandshakeError:
                raise
            except UriNotFoundError:
                pass

            if res == None:
                self.__init__(id, is_group=True)

            try:
                self.device = json.loads(res)
                self.device_info = self.device[constants.attrDeviceInfo]
            except TypeError:
                return

            try:
                self.lightControl = self.device[constants.attrLightControl][0]
            except KeyError:
                try:
                    self.plugControl = self.device[constants.attrPlugControl][0]
                except KeyError:
                    pass
        else:
            uri = "{}/{}".format(constants.uri_groups, id)
            try:
                res = request(uri)
            except HandshakeError:
                raise

            try:
                self.device = json.loads(res)
                self.device_info = self.device
                self._is_group = True
            except TypeError:
                return

    def Update(self):
        self.__init__(self._id, self._is_group)
        self._group_members = []

    @property
    def Description(self):
        if not self._is_group:
            return "{}: {} ({} - {})".format(
                self.DeviceID, self.Name, self.State, self.Hex
            )
        else:
            return "{}: {}".format(self.DeviceID, self.Name)

    @property
    def DeviceID(self):
        return self.device[constants.attrId]

    @property
    def Name(self):
        return self.device[constants.attrName]

    @property
    def Type(self):
        if self.lightControl is not None:
            return "Light"

        if self.plugControl is not None:
            return "Plug"

        if self._is_group:
            return "Group"

        return None

    @property
    def State(self):
        if self.lightControl:
            return self.lightControl[constants.attrLightState]
        elif self.plugControl:
            return self.plugControl[constants.attrPlugState]
        elif self._is_group:
            return self.device_info[constants.attrLightState]

        return None

    @State.setter
    def State(self, state):
        if not self._is_group:
            uri = "{}/{}".format(constants.uriDevices, self._id)
            payload = '{{ "{0}": [{{ "{1}": {2} }}] }}'.format(
                constants.attrLightControl, constants.attrLightState, state
            )
        else:
            uri = "{}/{}".format(constants.uri_groups, self._id)
            payload = '{{ "{0}": {1} }}'.format(constants.attrLightState, state)

        request(uri, payload)

    @property
    def Level(self):
        if self.lightControl:
            return self.lightControl[constants.attrLightDimmer]
        elif self._is_group:
            from statistics import mean

            levels = []

            for dev in self.Members:
                b = dev.Level
                if b is not None:
                    levels.append(b)

            if len(levels) > 0:
                return mean(levels)

        else:
            return self.State

        return None

    @Level.setter
    def Level(self, level):

        state = 0 if level == 0 else 1

        if self._is_group:
            uri = "{}/{}".format(constants.uri_groups, self._id)
            payload = '{{ "{4}": {5}, "{0}": {1}, "{2}": {3} }}'.format(
                constants.attrLightDimmer,
                level,
                constants.attrTransitionTime,
                _transition_time,
                constants.attrLightState,
                state,
            )
        else:
            uri = "{}/{}".format(constants.uriDevices, self._id)
            payload = '{{ "{0}": [{{ "{5}": {6}, "{1}": {2}, "{3}": {4} }}] }}'.format(
                constants.attrLightControl,
                constants.attrLightDimmer,
                level,
                constants.attrTransitionTime,
                _transition_time,
                constants.attrLightState,
                state,
            )

        request(uri, payload)
        self.Update()

    @property
    def Color_space(self):
        if self._is_group:
            color_spaces = []

            for dev in self.Members:
                color_spaces.append(dev.Color_space)

            if "CWS" in color_spaces:
                return "CWS"
            if "WS" in color_spaces:
                return "WS"

            return "W"

        else:
            if self.lightControl is None:
                return None

            if "CWS" in self.device_info[constants.attrDeviceInfo_Model]:
                return "CWS"
            if "WS" in self.device_info[constants.attrDeviceInfo_Model]:
                return "WS"

        return "W"

    @property
    def Hex(self):
        if self._is_group:
            for dev in self.Members:
                hex = dev.Hex
                if hex is not None:
                    return hex

        if self.lightControl:
            if constants.attrLightHex in self.lightControl:
                return self.lightControl[constants.attrLightHex]
        return None

    @Hex.setter
    def Hex(self, hex):
        uri = "{}/{}".format(constants.uriDevices, self._id)
        payload = '{{ "{0}": [{{ "{1}": "{2}", "{3}": {4} }}] }}'.format(
            constants.attrLightControl,
            constants.attrLightHex,
            str(hex),
            constants.attrTransitionTime,
            _transition_time,
        )
        request(uri, payload)

    @property
    def Color_level(self):
        if self._is_group:
            for dev in self.Members:
                col_lev = dev.Color_level
                if col_lev is not None:
                    return col_lev

        hex = self.Hex
        if hex is not None:
            return colors.color_level_for_hex(hex, self.Color_space)
        return None

    @Color_level.setter
    def Color_level(self, level):
        if self._is_group:
            for dev in self.Members:
                dev.Color_level = level
        else:
            color = colors.color(level, self.Color_space)
            if color is not None:
                self.Hex = color["Hex"]

    @property
    def Members(self):
        if len(self._group_members) == 0:
            logging.debug("Getting members for device {}".format(self.DeviceID))

            if self.device is None:
                logging.debug("Device {} has no device info".format(self.DeviceID))
                return None
                
            for id in self.device[constants.attr_group_members][
                constants.attr_group_info
            ][constants.attrId]:
                self._group_members.append(device(id))

        return self._group_members


def get_device(id, is_group=False):
    dev = device(id, is_group)
    return dev


def get_devices(groups=False):
    devices = []

    uri = constants.uriDevices
    try:
        res = json.loads(request(uri))
    except TypeError:
        return
    except HandshakeError:
        logging.debug("Can't get devices, connection time out")
        raise

    for aDevice in res:
        devices.append(device(aDevice))

    if not groups:
        return devices

    uri = constants.uri_groups
    try:
        res = json.loads(request(uri))
    except TypeError:
        return

    for aGroup in res:
        devices.append(device(aGroup, is_group=True))
    return devices


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)

    args = cli.get_args()

    if args.debug:
        setDebugLevel(1)

    if args.command is not None:

        if args.command == "api":
                config = host_config(CONFIGFILE)
                config.set_config_item("api", args.API)
                config.save()

        if args.command == "test":
            # dev = get_device(158578, is_group=True)

            try:
                dev = device(158578)
            except UriNotFoundError:
                logging.error("Uri not found")
                exit()

            print(
                dev.Description, dev.State, dev.Level, dev.Color_space, dev.Color_level
            )

            dev.State = 1 if dev.State == 0 else 0

            dev.Level = 250 if dev.Level < 100 else 10

            # dev.Color_level = 30 if dev.Color_level == 10 else 10

        if args.command == "list":
            try:
                devices = get_devices(args.groups)
            except HandshakeError:
                print("Connection timed out")
                exit()

            if devices is None:
                logging.critical("Unable to get list of devices")
            else:
                for dev in devices:
                    print(dev.Description)

        elif args.command == "config":
            try:
                create_ident(args.IP, args.KEY, CONFIGFILE)
            except HandshakeError:
                logging.error("Connection timed out")
