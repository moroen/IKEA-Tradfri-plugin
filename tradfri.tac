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

    def connectionLost(self, reason):
        print("Disconnected")
        self.factory.clients.remove(self)


class AdaptorFactory(ServerFactory):

    def __init__(self):
        self.clients = []
        self.gateway = None
        self.api = None
        self.devices = None
        self.lights = None

        self.lc = task.LoopingCall(self.announce)
        # self.lc.start(10)

        reactor.addSystemEventTrigger("before", "shutdown", self.logout)

    def logout(self):
        print("Logout")
        reactor.stop()

    def buildProtocol(self, addr):
        return CoapAdapter(self)

    def announce(self):
        print ("Number of clients: " + str(len(self.clients)))
        for client in self.clients:
            client.transport.write("Announce!\n".encode(encoding='utf_8'))

    def deviceChanged(self, deviceID):
        print("Executed in reactor thread")


    def change_listener(self, device):
        print(device.name + " is now " + str(device.light_control.lights[0].state))
        print("Calling in reactor thread")
        reactor.callFromThread(self.deviceChanged, device.id)

    def blockingSetListen(self):
        while 1:
            self.lights[0].observe(self.change_listener)

    def initGateway(self, client, ip, key):
        self.api = pytradfri.coap_cli.api_factory(ip, key)
        self.gateway = pytradfri.gateway.Gateway(self.api)

        self.devices = self.gateway.get_devices()
        self.lights = [dev for dev in self.devices if dev.has_light_control]

        print("Set listener")
        reactor.callInThread(self.blockingSetListen)
        print("Set listener done")
        client.transport.write(json.dumps({"action":"setConfig", "status": "Ok"}).encode(encoding='utf_8'))

    def sendDeviceList(self, client):
        devices = []
        answer = {}

        for aDevice in self.lights:
            devices.append({"DeviceID": aDevice.id, "Name": aDevice.name, "State": aDevice.light_control.lights[0].state})

        answer["action"] = "getLights"
        answer["status"] = "Ok"
        answer["result"] =  devices

        client.transport.write(json.dumps(answer).encode(encoding='utf_8'))

    def setLevel(self, client, deviceID, level):
        answer = {}
        answer["action"] = "setLevel"
        answer["status"] = "Ok"

        targetDevice = self.gateway.get_device(int(deviceID))
        targetDevice.light_control.set_dimmer(level)

        client.transport.write(json.dumps(answer).encode(encoding='utf_8'))

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
