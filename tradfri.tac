from twisted.conch.telnet import TelnetTransport, TelnetProtocol
from twisted.internet import protocol, task, reactor, endpoints
from twisted.internet.protocol import ServerFactory
from twisted.application.internet import TCPServer
from twisted.application.service import Application

import json
import sys

import twisted.scripts.twistd as t
from pytradfri import Gateway
from pytradfri.api.libcoap_api import api_factory

version = "0.3"
verbose = False

def verbosePrint(txt):
    if verbose:
        print(txt)

class CoapAdapter(TelnetProtocol):
    api = ""
    gateway = ""


    def __init__(self, factory):
        self.factory = factory

    def connectionMade(self):
        answer = {}
        print("Connected from " + str(self.transport.getPeer()))
        self.factory.clients.append(self)

        answer["action"] = "clientConnect"
        answer["status"] = "Ok"
        answer["version"] = version

        self.transport.write(json.dumps(answer).encode(encoding='utf_8'))

    def dataReceived(self, data):
        verbosePrint("Data received: " + str(data))

        decoded = data.decode("utf-8")
        decoded = '[' + decoded.replace('}{', '},{') + ']'
        
        commands = json.loads(decoded)

        for command in commands:
            if command['action']=="setConfig":
                # print("Setting config")
                self.factory.initGateway(self, command['gateway'], command['key'], command['observe'])

            if command['action']=="getLights":
                self.factory.sendDeviceList(self)

            if command['action']=="setLevel":
                self.factory.setLevel(self, command["deviceID"], command["level"])

            if command['action']=="setState":
                self.factory.setState(self, command["deviceID"], command["state"])

            if command['action']=="setHex":
                self.factory.setHex(self, command["deviceID"], command['hex'])

        # except:
        #    print("Error: Failed to parse JSON")
        #    print("Unexpected error:", sys.exc_info()[0])

    def connectionLost(self, reason):
        print("Disconnected")
        self.factory.clients.remove(self)

class ikeaGroup():
    deviceID = None
    deviceName = None
    lastState = None
    lastLevel = None
    factory = None

    def __init__(self, factory, group):
        self.deviceID = group.id
        self.deviceName = group.name
        self.lastState = group.state
        self.lastLevel = group.dimmer
        self.factory = factory

    def hasChanged(self):
        targetGroup = self.factory.api(self.factory.gateway.get_group(int(self.deviceID)))

        curState = targetGroup.state
        curLevel = targetGroup.dimmer

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

        verbosePrint(answer)

        client.transport.write(json.dumps(answer).encode(encoding='utf_8'))


class ikeaLight():

    whiteTemps = {"cold":"f5faf6", "normal":"f1e0b5", "warm":"efd275"}

    deviceID = None
    deviceName = None
    lastState = None
    lastLevel = None
    lastWB = None

    device = None
    factory = None

    def __init__(self, factory, device):
        self.device = device
        self.deviceID = device.id
        self.deviceName = device.name
        self.lastState = device.light_control.lights[0].state
        self.lastLevel = device.light_control.lights[0].dimmer
        self.lastWB = device.light_control.lights[0].hex_color
        self.factory = factory


    def hasChanged(self):
        targetDeviceCommand = self.factory.gateway.get_device(int(self.deviceID))
        targetDevice = self.factory.api(targetDeviceCommand)

        curState = targetDevice.light_control.lights[0].state
        curLevel = targetDevice.light_control.lights[0].dimmer
        curWB = targetDevice.light_control.lights[0].hex_color

        # print ("Checking change for {0} lastState: {1} currentState: {2}".format(self.deviceName, self.lastState, curState))

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
        targetDeviceCommand = self.factory.gateway.get_device(int(self.deviceID))
        targetDevice = self.factory.api(targetDeviceCommand)

        targetLevel = targetDevice.light_control.lights[0].dimmer
        if targetLevel == None:
            targetLevel = 0

        devices.append({"DeviceID": targetDevice.id, "Name": targetDevice.name, "State": targetDevice.light_control.lights[0].state, "Level": targetLevel, "Hex": targetDevice.light_control.lights[0].hex_color})

        answer["action"] = "deviceUpdate"
        answer["status"] = "Ok"
        answer["result"] =  devices

        verbosePrint(answer)

        client.transport.write(json.dumps(answer).encode(encoding='utf_8'))

class AdaptorFactory(ServerFactory):

    ikeaLights = {}
    ikeaGroups = {}

    def __init__(self):
        self.clients = []
        self.gateway = None
        self.api = None
        self.devices = None
        self.lights = None
        self.groups = None

        self.lighStatus = {}
        self.lc = task.LoopingCall(self.announce)

    def logout(self):
        # print("Logout")
        reactor.stop()

    def buildProtocol(self, addr):
        return CoapAdapter(self)

    def announce(self):

        for key, aGroup in self.ikeaGroups.items():
            if aGroup.hasChanged():
                for client in self.clients:
                        aGroup.sendState(client)

        try:
            for key, aDevice in self.ikeaLights.items():
                if aDevice.hasChanged():
                    for client in self.clients:
                        aDevice.sendState(client)
        except Exception as e: 
            print(e)

    def initGateway(self, client, ip, key, observe):
        connectedToGW = False
        try:
            self.api = api_factory(ip, key)
            self.gateway = Gateway()
            connectedToGW = True
        except:
            connectedToGW = False

        if connectedToGW:
            devices_command = self.gateway.get_devices()
            devices_commands = self.api(devices_command)
            self.devices = self.api(*devices_commands)
            self.groups = self.api(*self.api(self.gateway.get_groups()))
        
            for dev in self.devices:
                if dev.has_light_control:
                    self.ikeaLights[dev.id] = ikeaLight(factory=self, device=dev)

            for group in self.groups:
                self.ikeaGroups[group.id] = ikeaGroup(factory=self, group=group)

            if observe=="True":
                if not self.lc.running:
                    self.lc.start(2)
            else:
                if self.lc.running:
                    self.lc.stop()

            client.transport.write(json.dumps({"action":"setConfig", "status": "Ok"}).encode(encoding='utf_8'))
        else:
            client.transport.write(json.dumps({"action":"setConfig", "status": "Failed", "error": "Connection timed out"}).encode(encoding='utf_8'))

    def sendDeviceList(self, client):
        devices = []
        answer = {}

        for key, aDevice in self.ikeaLights.items():
            # print (aDevice)
            devices.append({"DeviceID": aDevice.deviceID, "Name": aDevice.deviceName, "Type": "Dimmer", "HasWB": True})

        for key, aGroup in self.ikeaGroups.items():
            #print (aGroup)
            devices.append({"DeviceID": aGroup.deviceID, "Name": "Group - "+aGroup.deviceName, "Type": "Group", "HasWB": False})


        answer["action"] = "getLights"
        answer["status"] = "Ok"
        answer["result"] =  devices

        verbosePrint(json.dumps(answer))
        client.transport.write(json.dumps(answer).encode(encoding='utf_8'))

        for aDev in self.ikeaLights:
            self.ikeaLights[aDev].sendState(client)

        for aGroup in self.ikeaGroups:
            self.ikeaGroups[aGroup].sendState(client)

    def setLevel(self, client, deviceID, level):
        answer = {}
        answer["action"] = "setLevel"
        answer["status"] = "Ok"

        setLevelCommand = None
        deviceID=int(deviceID)

        if deviceID in self.ikeaLights.keys():
            targetDeviceCommand = self.gateway.get_device(deviceID)
            targetDevice = self.api(targetDeviceCommand)
            setLevelCommand = targetDevice.light_control.set_dimmer(level)

        if deviceID in self.ikeaGroups.keys():
            targetDevice=self.api(self.gateway.get_group(deviceID))
            setLevelCommand = targetDevice.set_dimmer(level)

        if setLevelCommand != None:
            self.api(setLevelCommand)
        else:
            answer["status"] = "Error"

        client.transport.write(json.dumps(answer).encode(encoding='utf_8'))

    def setState(self, client, deviceID, state):
        answer = {}
        answer["action"] = "setState"
        answer["status"] = "Ok"

        setStateCommand = None
        deviceID = int(deviceID)

        if state == "On":
            state = True

        if state == "Off":
            state = False

        if deviceID in self.ikeaLights.keys():
            # targetDeviceCommand = self.gateway.get_device(int(deviceID))
            targetDevice = self.api(self.gateway.get_device(int(deviceID)))
            setStateCommand = targetDevice.light_control.set_state(state)

        if deviceID in self.ikeaGroups.keys():
            # targetDeviceCommand = self.gateway.get_group(int(deviceID))
            targetDevice = self.api(self.gateway.get_group(int(deviceID)))
            print(targetDevice)
            setStateCommand = targetDevice.set_state(state)

        self.api(setStateCommand)
        client.transport.write(json.dumps(answer).encode(encoding='utf_8'))

    def setHex(self, client, deviceID, hex):
        answer = {}
        answer["action"] = "setHex"
        answer["status"] = "Ok"

        targetDeviceCommand = self.gateway.get_device(int(deviceID))
        targetDevice = self.api(targetDeviceCommand)

        setHexCommand = targetDevice.light_control.set_hex_color(hex)

        self.api(setHexCommand)

        client.transport.write(json.dumps(answer).encode(encoding='utf_8'))

if __name__ == "__main__":
    print ("IKEA-tradfri COAP-adaptor version {0} started (command line)!\nWaiting for connection".format(version))
    verbose = True
    endpoints.serverFromString(reactor, "tcp:1234").listen(AdaptorFactory())
    reactor.run()
else:
    factory = AdaptorFactory()
    service = TCPServer(1234, factory)
    application = Application("IKEA Tradfri Adaptor")
    service.setServiceParent(application)

def start_reactor():
    print ("IKEA-tradfri COAP-adaptor version {0} started (command line)!\nWaiting for connection".format(version))
    verbose = True
    endpoints.serverFromString(reactor, "tcp:1234").listen(AdaptorFactory())
    reactor.run()
