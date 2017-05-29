#!/usr/bin/env python3

from twisted.internet import protocol, reactor, endpoints, task
import json

class CoapAdapter(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory

    def connectionMade(self):

        print("Connected from " + str(self.transport.getPeer()))
        self.factory.clients.append(self)

    def dataReceived(self, data):
        print("Received: " + str(data))

    def connectionLost(self, reason):
        print("Disconnected")
        self.factory.clients.remove(self)


class AdaptorFactory(protocol.Factory):

    def __init__(self):
        self.clients = []
        self.lc = task.LoopingCall(self.announce)
        self.lc.start(10)

    def buildProtocol(self, addr):
        return CoapAdapter(self)

    def announce(self):
        print ("Number of clients: " + str(len(self.clients)))
        for client in self.clients:
            client.transport.write("Announce!\n".encode(encoding='utf_8'))


myFactory = AdaptorFactory()
reactor.listenTCP(1234, myFactory)
reactor.run()
