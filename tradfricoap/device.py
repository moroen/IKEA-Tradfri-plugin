import json
from . import constants
from . import colors
from .request import request
from .gateway import close_connection
from .errors import HandshakeError, UriNotFoundError, ReadTimeoutError,WriteTimeoutError, DeviceNotFoundError


_transition_time = 10


def set_transition_time(tt):
    global _transition_time
    _transition_time = int(tt)


class device:
    lightControl = None
    plugControl = None
    blindControl = None

    _id = None
    _is_group = False
    _group_members = []

    def __init__(self, id, is_group=False):
        self._id = id
        self._group_members = []

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
                self.__init__(id, is_group=True)

            self.process_result(res)

            
        else:
            uri = "{}/{}".format(constants.uri_groups, id)
            try:
                res = request(uri)
            except HandshakeError:
                raise
            except UriNotFoundError:
                # Illeagal deviceID
                self._is_group = False
                raise DeviceNotFoundError(id)
            
            self.process_result(res)

    def process_result(self, res):
        if not self._is_group:
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
                    try:
                        self.blindControl = self.device[constants.attrBlindControl][0]
                    except KeyError:
                        pass
        elif self._is_group:
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
            return "{}: {} (State: {} - Level: {} - Hex: {})".format(
                self.DeviceID, self.Name, self.State, self.Level, self.Hex
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

        if self.blindControl is not None:
            return "Blind"

        if self._is_group:
            return "Group"

        return None

    @property
    def Raw(self):
        return self.device

    @property
    def State(self):
        if self.lightControl:
            return self.lightControl[constants.attrLightState]
        elif self.plugControl:
            return self.plugControl[constants.attrPlugState]
        elif self.blindControl:
            if self.Level == 0:
                return 0
            elif self.Level == 100:
                return 1
            else:
                return 2

        elif self._is_group:
            return self.device_info[constants.attrLightState]

        return None

    @State.setter
    def State(self, state):
        if not self._is_group:
            if self.lightControl or self.plugControl:
                uri = "{}/{}".format(constants.uriDevices, self._id)
                payload = '{{ "{0}": [{{ "{1}": {2} }}] }}'.format(
                    constants.attrLightControl, constants.attrLightState, state
                )
            elif self.blindControl:
                if state == 0:
                    self.Level = 0
                else:
                    self.Level = 100
                return

        else:
            uri = "{}/{}".format(constants.uri_groups, self._id)
            payload = '{{ "{0}": {1} }}'.format(constants.attrLightState, state)

        
        res = request(uri, payload)
        self.process_result(res)        
        close_connection()

    @property
    def Level(self):
        if self.lightControl:
            if not constants.attrLightDimmer in self.lightControl:
                # Device have no dimmer control
                return self.State
            else:
                return self.lightControl[constants.attrLightDimmer]
        elif self.blindControl:
            return self.blindControl[constants.attrBlindPosition]
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
            if self.lightControl is not None:
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
            elif self.blindControl is not None:
                uri = "{}/{}".format(constants.uriDevices, self._id)
                payload = '{{ "{0}": [{{ "{1}": {2} }}] }}'.format(
                    constants.attrBlindControl, constants.attrBlindPosition, level
                )

        res = request(uri, payload)
        self.process_result(res)
        close_connection()
        # self.Update()

    @property
    def Color_space(self):
        from .device_info import deviceInfo

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
            # Use defined deviceInfo if exists
            model = self.device_info[constants.attrDeviceInfo_Model]
            if model in deviceInfo:
                return deviceInfo[model]["Color_space"]

            if self.lightControl is None:
                return None

            if "CWS" in model:
                return "CWS"
            if "WS" in model:
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
        close_connection()

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
            if self.device is None:
                return None

            for id in self.device[constants.attr_group_members][
                constants.attr_group_info
            ][constants.attrId]:
                self._group_members.append(device(id))

        return self._group_members

    @property
    def Battery_level(self):
        if self.device_info is not None:
            if constants.attrBatteryLevel in self.device_info:
                return self.device_info[constants.attrBatteryLevel]

        return None


def get_device(id, is_group=False):
    dev = device(id, is_group)
    return dev


def get_devices(groups=False):
    devices = {}

    uri = constants.uriDevices
    try:
        res = json.loads(request(uri))
    except TypeError:
        return
    except HandshakeError:
        raise

    for aDevice in res:
        devices[aDevice] = device(aDevice)

    if groups:
        uri = constants.uri_groups
        try:
            res = json.loads(request(uri))
        except TypeError:
            return

        for aGroup in res:
            devices[aGroup] = device(aGroup, is_group=True)
    
    # close_connection()
    return devices