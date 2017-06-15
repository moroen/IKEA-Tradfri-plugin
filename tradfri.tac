#!/usr/bin/env twistd

from twisted.conch.telnet import TelnetTransport, TelnetProtocol
from twisted.internet import protocol, task, reactor, endpoints
from twisted.internet.protocol import ServerFactory
from twisted.application.internet import TCPServer
from twisted.application.service import Application

import json
import sys

import twisted.scripts.twistd as t
import pytradfri

version = "0.1"
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
        # try:
        command = json.loads(data.decode("utf-8"))

        if command['action']=="setConfig":
            # print("Setting config")
            self.factory.initGateway(self, command['gateway'], command['key'], command['observe'])

        if command['action']=="getLights":
            self.factory.sendDeviceList(self)

        if command['action']=="setLevel":
            self.factory.setLevel(self, command["deviceID"], command["level"])

        if command['action']=="setState":
            self.factory.setState(self, command["deviceID"], command["state"])
        #except:
        #    print("Error: Failed to parse JSON")
        #    print("Unexpected error:", sys.exc_info()[0])

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
        # self.lc.start(5)

        # reactor.addSystemEventTrigger("before", "shutdown", self.logout)

    def logout(self):
        # print("Logout")
        reactor.stop()

    def buildProtocol(self, addr):
        return CoapAdapter(self)

    def announce(self):
        for key, aDevice in self.ikeaLights.items():
            if aDevice.hasChanged():
                for client in self.clients:
                    aDevice.sendState(client)

    def initGateway(self, client, ip, key, observe):
        self.api = pytradfri.coap_cli.api_factory(ip, key)
        self.gateway = pytradfri.gateway.Gateway(self.api)

        self.devices = self.gateway.get_devices()
        # self.lights = [dev for dev in self.devices if dev.has_light_control]

        client.transport.write(json.dumps({"action":"setConfig", "status": "Ok"}).encode(encoding='utf_8'))

        for dev in self.devices:
            if dev.has_light_control:
                self.ikeaLights[dev.id] = ikeaLight(factory=self, device=dev)

        if observe=="True":
            if not self.lc.running:
                self.lc.start(2)
        else:
            if self.lc.running:
                self.lc.stop()

    def sendDeviceList(self, client):
        devices = []
        answer = {}

        for key, aDevice in self.ikeaLights.items():
            # print (aDevice)
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
