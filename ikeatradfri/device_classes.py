import logging, json

class ikeaBatteryDevice():
    _device = None 

    def __init__(self, factory, device):
        self._device = device
        self.forceAnnouce = True
        
    @property
    def deviceID(self):
        return self._device.id

    @property
    def deviceName(self):
        return self._device.name

    @property
    def battery_level(self):
        return self._device.device_info.battery_level

    @property
    def state(self):
        return {"DeviceID": self.deviceID, "Name": self.deviceName, "Level": self.battery_level}

class ikeaSocket():
    deviceID = None
    deviceName = None
    lastState = None
    modelNumber = None

    device = None
    factory = None

    def __init__(self, factory, device):
        self.deviceID = device.id
        self.deviceName = device.name
        self.modelNumber = device.device_info.model_number
        self.lastState = device.socket_control.sockets[0].state
        self.device = device
        self.factory = factory

    def setState(self, client, state):
        answer = {}
        answer["action"] = "setState"
        answer["status"] = "Ok"

        self.lastState = state

        targetDevice = self.factory.api(self.factory.gateway.get_device(int(self.deviceID)))
        setStateCommand = targetDevice.socket_control.set_state(state)
        
        try:
            self.factory.api(setStateCommand)
        except Exception as e:
            logging.error("Failed to set state for socked with ID: {0}".format(self.deviceID))
            answer["status"]="Failed"

        if client != None:
            client.transport.write(json.dumps(answer).encode(encoding='utf_8'))
            self.sendState(client)

    def sendState(self, client):
        devices = []
        answer = {}

        devices.append({"DeviceID": self.deviceID, "Name": self.deviceName, "State": self.lastState})

        answer["action"] = "deviceUpdate"
        answer["status"] = "Ok"
        answer["result"] =  devices

        logging.info(answer)

        if client != None:
            try:
                client.transport.write(json.dumps(answer).encode(encoding='utf_8'))
            except Exception as e:
                logging.error("Error sending socket state")

    def hasChanged(self, device):
        # NOTE: Device is a pytradfri-device-object
        curState = device.socket_control.sockets[0].state

        if curState != self.lastState:
            self.lastState = curState
            return True
        else:
            return False

class ikeaLight():

    whiteTemps = {"cold":"f5faf6", "normal":"f1e0b5", "warm":"efd275"}

    deviceID = None
    deviceName = None
    lastState = None
    lastLevel = None
    lastWB = None
    modelNumber = None

    device = None
    factory = None

    def __init__(self, factory, device):
        self.device = device
        self.deviceID = device.id
        self.deviceName = device.name
        self.modelNumber = device.device_info.model_number
        # self.lastState = device.light_control.lights[0].state
        # self.lastLevel = device.light_control.lights[0].dimmer
        # self.lastWB = device.light_control.lights[0].hex_color
        self.factory = factory
 

    def hasChanged(self, device):
        curState = device.light_control.lights[0].state
        curLevel = device.light_control.lights[0].dimmer
        curWB = device.light_control.lights[0].hex_color

        if (curState == self.lastState) and (curLevel == self.lastLevel) and (curWB == self.lastWB):
            return False
        else:
            self.lastState = curState
            self.lastLevel = curLevel
            self.lastWB = curWB
            return True

    def sendState(self, client):
        devices = []
        answer = {}
    
        targetLevel = self.lastLevel
        if targetLevel == None:
            targetLevel = 0

        devices.append({"DeviceID": self.deviceID, "Name": self.deviceName, "State": self.lastState, "Level": targetLevel, "Hex": self.lastWB})

        answer["action"] = "deviceUpdate"
        answer["status"] = "Ok"
        answer["result"] =  devices
        
        logging.info(answer)
        try:
            client.transport.write(json.dumps(answer).encode(encoding='utf_8'))
        except Exception as e:
            logging.error("Error sending light state")
        

class ikeaGroup():
    deviceID = None
    deviceName = None
    members = None
    lastState = None
    lastLevel = None
    factory = None

    def __init__(self, factory, group):
        self.deviceID = group.id
        self.deviceName = group.name
        self.members = group.raw['9018']['15002']['9003']
        self.lastState = group.state
        self.lastLevel = group.dimmer
        self.factory = factory

    def hasChanged(self, group):
        # targetGroup = self.factory.api(self.factory.gateway.get_group(int(self.deviceID)))

        curState = group.state
        curLevel = group.dimmer

        if (curState == self.lastState) and (curLevel == self.lastLevel):
            return False
        else:
            self.lastState = curState
            self.lastLevel = curLevel
            return True
        
    def sendState(self, client):
        devices = []
        answer = {}
        
        devices.append({"DeviceID": self.deviceID, "Name": self.deviceName, "State": self.lastState, "Level": self.lastLevel})

        answer["action"] = "deviceUpdate"
        answer["status"] = "Ok"
        answer["result"] =  devices

        logging.info(answer)
        try:
            client.transport.write(json.dumps(answer).encode(encoding='utf_8'))
        except Exception as e:
            logging.error("Error sending group state")
