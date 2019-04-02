from twisted.conch.telnet import TelnetTransport, TelnetProtocol
from twisted.internet import protocol, task, reactor, endpoints
from twisted.internet.protocol import ServerFactory
from twisted.application.internet import TCPServer
from twisted.application.service import Application

import json
import sys
import configparser
import os
import time
import argparse

import twisted.scripts.twistd as t
from pytradfri import Gateway
from pytradfri.api.libcoap_api import APIFactory
from pytradfri import error as tradfriError

# Kludge to support rel. imports when running via twisted
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from ikeatradfri.device_classes import ikeaGroup, ikeaLight, ikeaSocket

version = "0.8.8"
verbose = False
dryRun = False

hostConfig = {}


def verbosePrint(txt):
    if verbose:
        print(txt)

INIFILE = "{0}/devices.ini".format(os.path.dirname(os.path.realpath(__file__)))
deviceDefaults = {"Dimmable": True, "HasWB": True, "HasRGB": False}

deviceConfig = configparser.ConfigParser()

if os.path.exists(INIFILE):
    deviceConfig.read(INIFILE)

currentError = False

CONFIGFILE = "{0}/config.json".format(
    os.path.dirname(os.path.realpath(__file__)))

if os.path.isfile(CONFIGFILE):
    with open(CONFIGFILE) as json_data_file:
        hostConfig = json.load(json_data_file)
else:
    print("Fatal: No config.json found!")
    print("Looking for: {0}".format(CONFIGFILE))
    exit()


def error(f):
    global currentError
    print(f.getErrorMessage())
    currentError = True


def stringToBool(boolString):
    if boolString == "True":
        return True
    elif boolString == "False":
        return False
    else:
        return None


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
            if command['action'] == "initGateway":
                # print("Setting config")
                self.factory.initGateway(self, command)
                #self.factory.initGateway(self, command['gateway'], command['key'], command['observe'], command['pollinterval'], command['groups'])

            if command['action'] == "getLights":
                self.factory.sendDeviceList(self)

            if command['action'] == "setLevel":
                self.factory.setLevel(
                    self, command["deviceID"], command["level"])

            if command['action'] == "setState":
                self.factory.setState(
                    self, command["deviceID"], command["state"])

            if command['action'] == "setHex":
                self.factory.setHex(self, command["deviceID"], command['hex'])

            if command['action'] == "announceChanged":
                self.factory.announceChanged()

        # except:
        #    print("Error: Failed to parse JSON")
        #    print("Unexpected error:", sys.exc_info()[0])

    def connectionLost(self, reason):
        print("Disconnected")
        self.factory.clients.remove(self)


class AdaptorFactory(ServerFactory):

    ikeaLights = {}
    ikeaGroups = {}
    ikeaSockets = {}

    devices = None
    groups = None

    observe = False
    groups = False

    transitionTime = 10

    def __init__(self):
        self.clients = []
        self.gateway = None
        self.api = None
        self.devices = None
        self.lights = None
        self.groups = None

        self.lighStatus = {}

        if dryRun:
            self.initGateway(None, None)
            self.sendDeviceList(None)
            self.setState(None, "65548", False)
            print("Sleeping for 10 seconds before announceChanged")
            time.sleep(10)
            self.announceChanged()
            exit()

    def logout(self):
        # print("Logout")
        reactor.stop()

    def buildProtocol(self, addr):
        return CoapAdapter(self)

    def announceChanged(self):
        verbosePrint("Announcing changed devices!")
        try:
            self.devices = self.api(self.api(self.gateway.get_devices()))

            for dev in self.devices:
                if dev.has_light_control:
                    if self.ikeaLights[dev.id].hasChanged(dev):
                        for client in self.clients:
                            self.ikeaLights[dev.id].sendState(client)

                if dev.has_socket_control:
                    if self.ikeaSockets[dev.id].hasChanged(dev):
                        for client in self.clients:
                            self.ikeaSockets[dev.id].sendState(client)

            if self.groups:
                self.groups = self.api(self.api(self.gateway.get_groups()))

                for group in self.groups:
                    if self.ikeaGroups[group.id].hasChanged(group):
                        for client in self.clients:
                            self.ikeaGroups[group.id].sendState(client)
        except tradfriError.RequestTimeout:
            print("Error in announce: Request timed out")
            for client in self.clients:
                client.transport.loseConnection()
            return
        except Exception as e:
            print("Error in announce: Unspecified error")
            for client in self.clients:
                client.transport.loseConnection()
            raise

    # def initGateway(self, client, ip, key, observe, interval, groups):
    def initGateway(self, client, command):
        verbosePrint("Initializing gateway")
        connectedToGW = False

        if command != None:
            if command['groups'] == "True":
                self.groups = True
            else:
                self.groups = False

            if command['transitiontime'] == "":
                self.transitionTime = 10
            else:
                self.transitionTime = int(command['transitiontime'])

        print("Transitiontime: {0}".format(self.transitionTime))

        api_factory = APIFactory(
            hostConfig["Gateway"], hostConfig['Identity'], hostConfig['Passkey'])

        self.api = api_factory.request
        self.gateway = Gateway()
        connectedToGW = True

        if connectedToGW:
            try:
                self.devices = self.api(self.api(self.gateway.get_devices()))
                if self.groups:
                    self.groups = self.api(self.api(self.gateway.get_groups()))
            except tradfriError.RequestTimeout:
                print("Error in initGateway: Request timeout")
                client.transport.loseConnection()
                return
            except:
                print("Error in initGateway: Unspecified error")
                client.transport.loseConnection()
                return

            try:
                for dev in self.devices:
                    if dev.has_light_control:
                        verbosePrint(
                            "Adding light with ID: {0}".format(dev.id))
                        self.ikeaLights[dev.id] = ikeaLight(
                            factory=self, device=dev)
                    if dev.has_socket_control:
                        verbosePrint(
                            "Adding socket with ID: {0}".format(dev.id))
                        self.ikeaSockets[dev.id] = ikeaSocket(
                            factory=self, device=dev)
            except Exception as e:
                print("Unable to iterate devices")

            if self.groups:
                try:
                    for group in self.groups:
                        self.ikeaGroups[group.id] = ikeaGroup(
                            factory=self, group=group)
                except Exception as e:
                    print("Unable to iterate groups")

            if client != None:
                client.transport.write(json.dumps(
                    {"action": "initGateway", "status": "Ok"}).encode(encoding='utf_8'))
        else:
            if client != None:
                client.transport.write(json.dumps(
                    {"action": "initGateway", "status": "Failed", "error": "Connection timed out"}).encode(encoding='utf_8'))

    def sendDeviceList(self, client):
        devices = []
        answer = {}
        configChanged = False

        # Lights
        for key, aDevice in self.ikeaLights.items():
            # print (aDevice.modelNumber)
            if not aDevice.modelNumber in deviceConfig:
                verbosePrint("Device settings not found for {0}. Creating defaults!".format(
                    aDevice.modelNumber))
                if not aDevice.modelNumber == "":
                    deviceConfig[aDevice.modelNumber] = deviceDefaults
                    configChanged = True

            devices.append({"DeviceID": aDevice.deviceID, "Name": aDevice.deviceName, "Type": "Light", "Dimmable": stringToBool(
                deviceConfig[aDevice.modelNumber]['dimmable']), "HasWB": stringToBool(deviceConfig[aDevice.modelNumber]['haswb']), "HasRGB": stringToBool(deviceConfig[aDevice.modelNumber]['hasrgb'])})

        # Outlets
        for key, aDevice in self.ikeaSockets.items():
            devices.append({"DeviceID": aDevice.deviceID,
                            "Name": aDevice.deviceName, "Type": "Outlet"})

        if self.groups:
            for key, aGroup in self.ikeaGroups.items():
                #print (aGroup)
                devices.append({"DeviceID": aGroup.deviceID, "Name": "Group - " +
                                aGroup.deviceName, "Type": "Group", "Dimmable": True, "HasWB": False})

        if configChanged:
            with open(INIFILE, "w") as configfile:
                deviceConfig.write(configfile)

        answer["action"] = "getLights"
        answer["status"] = "Ok"
        answer["result"] = devices

        verbosePrint(json.dumps(answer))

        if client != None:
            client.transport.write(json.dumps(answer).encode(encoding='utf_8'))

        self.announceChanged()
        # for aDev in self.ikeaLights:
        #     self.ikeaLights[aDev].sendState(client)

        # for aSocket in self.ikeaSockets:
        #     self.ikeaSockets[aSocket].sendState(client)

        # if self.groups:
        #     for aGroup in self.ikeaGroups:
        #         self.ikeaGroups[aGroup].sendState(client)

    def setLevel(self, client, deviceID, level):
        answer = {}
        answer["action"] = "setLevel"
        answer["status"] = "Ok"

        setLevelCommand = None
        targetDevice = None

        deviceID = int(deviceID)
        target = None

        if deviceID in self.ikeaLights.keys():
            targetDeviceCommand = self.gateway.get_device(deviceID)
            targetDevice = self.api(targetDeviceCommand)
            setLevelCommand = targetDevice.light_control.set_dimmer(
                level, transition_time=self.transitionTime)
            target = self.ikeaLights[deviceID]
            # Set
            self.api(setLevelCommand)

        if self.groups:
            if deviceID in self.ikeaGroups.keys():
                # First set level
                targetDevice = self.api(self.gateway.get_group(int(deviceID)))
                setLevelCommand = targetDevice.set_dimmer(
                    level, transition_time=self.transitionTime)
                target = self.ikeaGroups[deviceID]
                self.api(setLevelCommand)

                # Then switch the group on

                setStateCommand = targetDevice.set_state(True)
                target = self.ikeaGroups[deviceID]
                self.api(setStateCommand)

        client.transport.write(json.dumps(answer).encode(encoding='utf_8'))

        self.announceChanged()

    def setState(self, client, deviceID, state):
        answer = {}
        answer["action"] = "setState"
        answer["status"] = "Ok"

        setStateCommand = None
        target = None
        targetDevice = None
        deviceID = int(deviceID)

        if state == "On":
            state = True

        if state == "Off":
            state = False

        # Device is a light
        if deviceID in self.ikeaLights.keys():
            targetDevice = self.api(self.gateway.get_device(int(deviceID)))
            setStateCommand = targetDevice.light_control.set_state(state)
            target = self.ikeaLights[deviceID]

        # Device is as outlet
        if deviceID in self.ikeaSockets.keys():
            self.ikeaSockets[deviceID].setState(client, state)
            return

        # Device is a group
        if self.groups:
            if deviceID in self.ikeaGroups.keys():
                targetDevice = self.api(self.gateway.get_group(int(deviceID)))
                setStateCommand = targetDevice.set_state(state)
                target = self.ikeaGroups[deviceID]

        try:
            self.api(setStateCommand)
        except Exception as e:
            print("Failed to set state")
            answer["status"] = "Failed"

        client.transport.write(json.dumps(answer).encode(encoding='utf_8'))

        self.announceChanged()

    def setHex(self, client, deviceID, hex):
        answer = {}
        answer["action"] = "setHex"
        answer["status"] = "Ok"

        deviceID = int(deviceID)

        if deviceID in self.ikeaLights.keys():
            targetDevice = self.api(self.gateway.get_device(int(deviceID)))
            setStateCommand = targetDevice.light_control.set_hex_color(
                hex, transition_time=self.transitionTime)

        self.api(setStateCommand)
        client.transport.write(json.dumps(answer).encode(encoding='utf_8'))

        self.announceChanged()


if __name__ == "__main__":
    print(
        "IKEA-tradfri COAP-adaptor version {0} started (command line)!".format(version))
    verbose = True

    parser = argparse.ArgumentParser()
    parser.add_argument("--dryrun", action="store_true")

    args = parser.parse_args()

    if args.dryrun:
        dryRun = True

    endpoints.serverFromString(reactor, "tcp:1234").listen(
        AdaptorFactory()).addErrback(error)

    if not currentError:
        reactor.run()

else:
    factory = AdaptorFactory()
    service = TCPServer(1234, factory)
    application = Application("IKEA Tradfri Adaptor")
    service.setServiceParent(application)
