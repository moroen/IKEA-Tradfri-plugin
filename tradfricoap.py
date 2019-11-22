# Standard library
import json, logging, time, sys, site, argparse

# Module
from tradfri.config import get_config, host_config
from tradfri import constants
from tradfri import colors

site.main()

import pycoap

# logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)

_transition_time = 10

pycoap.setDebugLevel(1)


def request(uri, payload=None):
    conf = get_config()

    if payload == None:
        return pycoap.Request(
            uri="coaps://{}:{}/{}".format(conf["Gateway"], 5684, uri),
            ident=conf["Identity"],
            key=conf["Passkey"],
        )
    else:
        return pycoap.Request(
            uri="coaps://{}:{}/{}".format(conf["Gateway"], 5684, uri),
            payload=payload,
            method=pycoap.PUT,
            ident=conf["Identity"],
            key=conf["Passkey"],
        )


def set_transition_time(tt):
    global _transition_time
    _transition_time = int(tt)


class device:
    lightControl = None
    plugControl = None
    _id = None

    def __init__(self, id, is_group=False):
        self._id = id
        self._is_group = is_group

        if not self._is_group:
            uri = "{}/{}".format(constants.uriDevices, id)
            res = request(uri)

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
            res = request(uri)

            try:
                self.device = json.loads(res)
                self.device_info = self.device
            except TypeError:
                return

    def Update(self):
        self.__init__(self._id, self._is_group)

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

            for id in self.device[constants.attr_group_members][
                constants.attr_group_info
            ][constants.attrId]:
                b = get_device(id).Level
                if b is not None:
                    levels.append(b)

            if len(levels) > 0:
                return mean(levels)

        else:
            return self.State

        return None

    @Level.setter
    def Level(self, level):
        if self._is_group:
            uri = "{}/{}".format(constants.uri_groups, self._id)
            payload = '{{ "{0}": {1}, "{2}": {3} }}'.format(
                constants.attrLightDimmer,
                level,
                constants.attrTransitionTime,
                _transition_time,
            )
        else:
            uri = "{}/{}".format(constants.uriDevices, self._id)
            payload = '{{ "{0}": [{{ "{1}": {2}, "{3}": {4} }}] }}'.format(
                constants.attrLightControl,
                constants.attrLightDimmer,
                level,
                constants.attrTransitionTime,
                _transition_time,
            )

        request(uri, payload)
        self.Update()

    @property
    def ColorSpace(self):
        if self._is_group:
            color_spaces = []

            for id in self.device[constants.attr_group_members][
                constants.attr_group_info
            ][constants.attrId]:
                color_spaces.append(get_device(id).ColorSpace)

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
            for id in self.device[constants.attr_group_members][
                constants.attr_group_info
            ][constants.attrId]:
                hex = get_device(id).Hex
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
            for id in self.device[constants.attr_group_members][
                constants.attr_group_info
            ][constants.attrId]:
                col_lev = get_device(id).Color_level
                if col_lev is not None:
                    return col_lev

        hex = self.Hex
        if hex is not None:
            return colors.color_level_for_hex(hex, self.ColorSpace)
        return None

    @Color_level.setter
    def Color_level(self, level):
        if self._is_group:
            for id in self.device[constants.attr_group_members][
                constants.attr_group_info
            ][constants.attrId]:
                get_device(id).Color_level = level
        else:
            color = colors.color(level, self.ColorSpace)
            if color is not None:
                self.Hex = color["Hex"]


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
    logging.basicConfig(level=logging.INFO)

    from tradfri import cli

    args = cli.get_args()

    if args.command is not None:
        if args.command == "test":
            dev = get_device(158578, is_group=True)
            print(
                dev.Description, dev.State, dev.Level, dev.ColorSpace, dev.Color_level
            )

            # dev.State = 1 if dev.State == 0 else 0

            dev.Level = 250 if dev.Level < 100 else 10
            print (dev.Level)
            # dev.Color_level = 30 if dev.Color_level == 10 else 10
            
            

        if args.command == "list":
            devices = get_devices(args.groups)

            for dev in devices:
                print(dev.Description)

        elif args.command == "config":
            from tradfri.gw import create_ident

            create_ident(args.IP, args.KEY)
