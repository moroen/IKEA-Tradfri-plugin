#!/usr/bin/env twistd

from twisted.internet import protocol, task, reactor, endpoints
from twisted.internet.protocol import ServerFactory
from twisted.application.internet import TCPServer
from twisted.application.service import Application
import json

import twisted.scripts.twistd as t
import pytradfri

class CoapAdapter(protocol.Protocol):
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
            self.factory.api = pytradfri.coap_cli.api_factory(command['gateway'], command['key'])
            self.factory.gateway = pytradfri.gateway.Gateway(self.factory.api)
            self.transport.write(json.dumps({"action":"setConfig", "status": "Ok"}).encode(encoding='utf_8'))

        if command['action']=="getLights":
            self.factory.sendDeviceList(self)

    def connectionLost(self, reason):
        print("Disconnected")
        self.factory.clients.remove(self)


class AdaptorFactory(protocol.Factory):

    def __init__(self):
        self.clients = []
        self.gateway = None
        self.api = None

        self.lc = task.LoopingCall(self.announce)
        # self.lc.start(10)

    def buildProtocol(self, addr):
        return CoapAdapter(self)

    def announce(self):
        print ("Number of clients: " + str(len(self.clients)))
        for client in self.clients:
            client.transport.write("Announce!\n".encode(encoding='utf_8'))

    def sendDeviceList(self, client):
        devices = []
        answer = {}

        devicesList = self.gateway.get_devices()
        for aDevice in devicesList:
            print(aDevice)
            if aDevice.has_light_control:
                devices.append({"DeviceID": aDevice.id, "Name": aDevice.name, "State": aDevice.light_control.lights[0].state})

        answer["action"] = "getLights"
        answer["status"] = "Ok"
        answer["result"] =  devices

        client.transport.write(json.dumps(answer).encode(encoding='utf_8'))


if __name__ == "__main__":
    endpoints.serverFromString(reactor, "tcp:1234").listen(AdaptorFactory())
    reactor.run()
else:
    factory = AdaptorFactory()
    service = TCPServer(1234, factory)
    application = Application("IKEA Tradfri Adaptor")
    service.setServiceParent(application)
