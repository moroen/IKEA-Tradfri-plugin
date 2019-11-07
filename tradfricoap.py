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

    def __init__(self, id):
        self._id = id
        uri = "{}/{}".format(constants.uriDevices, id)
        res = request(uri)
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

    def Update(self):
        self.__init__(self._id)

    @property
    def Description(self):
        return "{}: {} ({} - {})".format(self.DeviceID, self.Name, self.State, self.Hex)

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

        return None

    @property
    def State(self):
        if self.lightControl:
            return self.lightControl[constants.attrLightState]
        if self.plugControl:
            return self.plugControl[constants.attrPlugState]

        return None

    @State.setter
    def State(self, state):
        uri = "{}/{}".format(15001, self._id)
        payload = '{{ "{0}": [{{ "{1}": {2} }}] }}'.format(3311, 5850, state)
        request(uri, payload)

    @property
    def Level(self):
        if self.lightControl:
            return self.lightControl[constants.attrLightDimmer]
        else:
            return self.State

        return None

    @Level.setter
    def Level(self, level):
        uri = "{}/{}".format(constants.uriDevices, self._id)
        payload = '{{ "{0}": [{{ "{1}": {2}, "{3}": {4} }}] }}'.format(
            constants.attrLightControl,
            constants.attrLightDimmer,
            level,
            constants.attrTransitionTime,
            _transition_time,
        )

        request(uri, payload)

    @property
    def ColorSpace(self):
        if self.lightControl is None:
            return None

        if "CWS" in self.device_info[constants.attrDeviceInfo_Model]:
            return "CWS"
        if "WS" in self.device_info[constants.attrDeviceInfo_Model]:
            return "WS"

        return "W"

    @property
    def Hex(self):
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
        hex = self.Hex
        if hex is not None:
            return colors.color_level_for_hex(hex, self.ColorSpace)
        return None

    @Color_level.setter
    def Color_level(self, level):
        color = colors.color(level, self.ColorSpace)
        if color is not None:
            self.Hex = color["Hex"]


def get_device(id):
    dev = device(id)
    return dev


def get_devices():
    uri = constants.uriDevices
    try:
        res = json.loads(request(uri))
    except TypeError:
        return

    devices = []

    for aDevice in res:
        devices.append(device(aDevice))

    return devices


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    parser_config_gateway = subparsers.add_parser("list")

    parser_config_gateway = subparsers.add_parser("config")
    parser_config_gateway.add_argument("IP")
    parser_config_gateway.add_argument("KEY")

    args = parser.parse_args()

    if args.command is not None:
        if args.command == "list":
            devices = get_devices()
            for dev in devices:
                print(dev.Description)

        elif args.command == "config":
            from tradfri.gw import create_ident

            create_ident(args.IP, args.KEY)
