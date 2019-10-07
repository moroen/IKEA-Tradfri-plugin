# Standard library
import json, logging, time, sys, site



# Module
from config import get_config
import constants
from pycoap_asyncio import request, close_loop, init

site.main()

# logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)

_transition_time = 10

def initDTLS():
    init()


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

    @property
    def Description(self):
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

def perform_shutdown():
    close_loop()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # dev = get_device(65554)
    # print (dev.Description)
    # dev.Level=10

    # level(65554, 100, 10)
    get_devices()
