#!/usr/bin/env twistd

from twisted.conch.telnet import TelnetTransport, TelnetProtocol
from twisted.internet import protocol, task, reactor, endpoints
from twisted.internet.protocol import ServerFactory
from twisted.application.internet import TCPServer
from twisted.application.service import Application

import json

import twisted.scripts.twistd as t
import pytradfri

class CoapAdapter(TelnetProtocol):
    api = ""
    gateway = ""

    def __init__(self, factory):
        self.factory = factory

    def connectionMade(self):
        print("Connected from " + str(self.transport.getPeer()))
        self.factory.clients.append(self)

    def dataReceived(self, data):
        print("Received: " + str(data))
        command = json.loads(data)
        print(command['action'])

        if command['action']=="setConfig":
            print("Setting config")
            self.factory.initGateway(self, command['gateway'], command['key'])

        if command['action']=="getLights":
            self.factory.sendDeviceList(self)

        if command['action']=="setLevel":
            self.factory.setLevel(self, command["deviceID"], command["level"])

        if command['action']=="setState":
            self.factory.setState(self, command["deviceID"], command["state"])

    def connectionLost(self, reason):
        print("Disconnected")
        self.factory.clients.remove(self)

class ikeaLight():
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
        targetDevice = self.factory.gateway.get_device(int(self.deviceID))
        curState = targetDevice.light_control.lights[0].state

        print ("Checking change for {0} lastState: {1} currentState: {2}".format(self.deviceName, self.lastState, curState))

        if curState != self.lastState:
            self.lastState = curState
            return True
        else:
            return False

    def sendState(self, client):
        devices = []
        answer = {}
        targetDevice = self.factory.gateway.get_device(int(self.deviceID))

        devices.append({"DeviceID": targetDevice.id, "Name": targetDevice.name, "State": targetDevice.light_control.lights[0].state, "Level": targetDevice.light_control.lights[0].dimmer, "WhiteBalance": targetDevice.light_control.lights[0].hex_color})

        answer["action"] = "deviceUpdate"
        answer["status"] = "Ok"
        answer["result"] =  devices

        client.transport.write(json.dumps(answer).encode(encoding='utf_8'))


class AdaptorFactory(ServerFactory):

    ikeaLights = {}

    def __init__(self):
        self.clients = []
        self.gateway = None
        self.api = None
        self.devices = None
        self.lights = None

        self.lighStatus = {}

        self.lc = task.LoopingCall(self.announce)
        #self.lc.start(5)

        # reactor.addSystemEventTrigger("before", "shutdown", self.logout)

    def logout(self):
        print("Logout")
        reactor.stop()

    def buildProtocol(self, addr):
        return CoapAdapter(self)

    def announce(self):

        #print ("Number of clients: " + str(len(self.clients)))
        #for client in self.clients:
        #    client.transport.write("Announce!\n".encode(encoding='utf_8'))

        for key, aDevice in self.ikeaLights.items():
            if aDevice.hasChanged():
                print("Device changed: " + aDevice.deviceName)
                #for client in self.clients:
                #    self.sendState(client, aDevice.deviceID)

    # def deviceChanged(self, deviceID):
    #     print("Executed in reactor thread")
    #
    #
    # def change_listener(self, device):
    #     print(device.name + " is now " + str(device.light_control.lights[0].state))
    #     print("Calling in reactor thread")
    #     reactor.callFromThread(self.deviceChanged, device.id)
    #
    # def blockingSetListen(self):
    #     while 1:
    #         self.lights[0].observe(self.change_listener)

    def initGateway(self, client, ip, key):
        self.api = pytradfri.coap_cli.api_factory(ip, key)
        self.gateway = pytradfri.gateway.Gateway(self.api)

        self.devices = self.gateway.get_devices()
        # self.lights = [dev for dev in self.devices if dev.has_light_control]

        client.transport.write(json.dumps({"action":"setConfig", "status": "Ok"}).encode(encoding='utf_8'))

        for dev in self.devices:
            if dev.has_light_control:
                self.ikeaLights[dev.id] = ikeaLight(factory=self, device=dev)

    def sendDeviceList(self, client):
        devices = []
        answer = {}

        for key, aDevice in self.ikeaLights.items():
            print (aDevice)
            devices.append({"DeviceID": aDevice.deviceID, "Name": aDevice.deviceName})

        answer["action"] = "getLights"
        answer["status"] = "Ok"
        answer["result"] =  devices

        client.transport.write(json.dumps(answer).encode(encoding='utf_8'))

        for aDev in self.ikeaLights:
            self.ikeaLights[aDev].sendState(client)

    def setLevel(self, client, deviceID, level):
        answer = {}
        answer["action"] = "setLevel"
        answer["status"] = "Ok"

        targetDevice = self.gateway.get_device(int(deviceID))
        targetDevice.light_control.set_dimmer(level)

        client.transport.write(json.dumps(answer).encode(encoding='utf_8'))

    def setState(self, client, deviceID, state):
        answer = {}
        answer["action"] = "setState"
        answer["status"] = "Ok"

        targetDevice = self.gateway.get_device(int(deviceID))

        if state == "On":
            targetDevice.light_control.set_state(True)

        if state == "Off":
            targetDevice.light_control.set_state(False)

        client.transport.write(json.dumps(answer).encode(encoding='utf_8'))

        self.sendState(client, deviceID)





# devices = gateway.get_devices()
# lights = [dev for dev in devices if dev.has_light_control]
#
#

#

if __name__ == "__main__":
    endpoints.serverFromString(reactor, "tcp:1234").listen(AdaptorFactory())
    reactor.run()
else:
    factory = AdaptorFactory()
    service = TCPServer(1234, factory)
    application = Application("IKEA Tradfri Adaptor")
    service.setServiceParent(application)
