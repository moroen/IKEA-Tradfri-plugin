# Basic Python Plugin Example
#
# Author: GizMoCuz
#
"""
<plugin key="IKEA-Tradfri" name="IKEA Tradfri" author="moroen" version="1.0.0" wikilink="http://www.domoticz.com/wiki/plugins/plugin.html" externallink="https://www.google.com/">
    <params>
        <param field="Address" label="IP Address" width="200px" required="true" default="127.0.0.1"/>
        <param field="Mode1" label="Key" width="200px" required="true" default=""/>
        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal"  default="true" />
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz
import json
#import pytradfri

class BasePlugin:
    #enabled = False
    #api = None
    #gateway = None

    pluginStatus = 0
    # Dict of registered lights
    lights = {}

    CoapAdapter = None

    def __init__(self):
        self.pluginStatus = 0
        return

    def unitOfUnit(self, i):
        return Devices[i]

    def registerDevices(self, ikeaDevices):
        i = 1
        if (len(Devices) == 0):
            i=1
        else:
            i=max(Devices)+1

        WhiteOptions = {"LevelActions": "||", "LevelNames": "Cold|Normal|Warm", "LevelOffHidden": "false","SelectorStyle": "0"}

        ikeaIds = []
        # Add unregistred lights
        for aLight in ikeaDevices:
            devID = str(aLight['DeviceID'])
            ikeaIds.append(devID)
            if not devID in self.lights:
                Domoticz.Device(Name=aLight['Name'], Unit=i,  TypeName="Switch", Switchtype=7, DeviceID=devID).Create()
                self.lights[devID] = {"DeviceID": aLight['DeviceID'], "Unit": i}
                i=i+1
                Domoticz.Device(Name=aLight['Name'] + " - WB",  Unit=i, TypeName="Selector Switch", Switchtype=18, Options=WhiteOptions, DeviceID=devID+":WB").Create()
                self.lights[devID+":WB"] = {"DeviceID": devID+":WB", "Unit": i}
                i=i+1

        #Remove registered lights no longer found on the gateway
        for aUnit in list(Devices.keys()):
            devID = str(Devices[aUnit].DeviceID)

            if devID[-3:] == ":WB":
                devID = devID[:-3]

            if not devID in ikeaIds:
                Devices[aUnit].Delete()

    def updateDeviceState(self, deviceState):
        print("DeviceState")
        print(deviceState)

        for aDev in deviceState:
            devID = str(aDev["DeviceID"])
            targetUnit = self.lights[devID]['Unit']
            nVal = 0
            sVal = str(int((aDev["Level"]/250)*100))
            #Domoticz.Log("Current level: " + str(currentLevel))

            if aDev["State"] == True:
                nVal = 1
            if aDev["State"] == False:
                nVal = 0

            Devices[targetUnit].Update(nValue=nVal, sValue=sVal)



    def onStart(self):
        Domoticz.Log("onStart called")

        if Parameters["Mode6"] == "Debug":
            Domoticz.Debugging(1)

        #Test
        # Domoticz.Device(Name="To be removed", Unit=100,  TypeName="Switch", Switchtype=7, DeviceID="12345").Create()

        if len(Devices) > 0:
            # Some devices are already defined
            for aUnit in Devices:
                self.lights[Devices[aUnit].DeviceID] = {"DeviceID": Devices[aUnit].DeviceID, "Unit": aUnit}

        # myConn = Domoticz.Connection(Transport="TCP/IP", Protocol="line", Address=Parameters["Address"], Port=Parameters["Port"])
        self.CoapAdapter = Domoticz.Connection(Name="Main", Transport="TCP/IP", Protocol="JSON", Address="127.0.0.1", Port="1234")
        self.CoapAdapter.Connect()
        #myListen = Domoticz.Connection(Transport="TCP/IP", Protocol="JSON", Port=1235)
        #myListen.Listen()

        #Domoticz.Transport(Transport="TCP/IP", Address=Parameters["Address"], Port=Parameters["Port"])

        # currentUnits = {}
        #
        # self.api = pytradfri.coap_cli.api_factory(Parameters["Address"],Parameters["Mode1"])
        # self.gateway = pytradfri.gateway.Gateway(self.api)
        #
        # ikea_devices = self.gateway.get_devices()
        # lights = [dev for dev in ikea_devices if dev.has_light_control]
        #
        # listOfIkeaIDs = [int(dev.id) for dev in lights]
        # listOfDeviceIDs = [int(Devices[aUnit].DeviceID) for aUnit in Devices]
        # listOfUnitIds = list(Devices.keys())
        #
        # WhiteOptions = {"LevelActions": "||", "LevelNames": "Cold|Normal|Warm", "LevelOffHidden": "false","SelectorStyle": "0"}
        #
        # if (len(Devices) == 0):
        #     i=1
        # else:
        #     i=int(listOfUnitIds[-1])+1
        #
        # if Parameters["Mode6"] == "Debug":
        #     Domoticz.Debugging(1)
        #
        # # Add unregistered lights
        # for aLight in lights:
        #     if not int(aLight.id) in listOfDeviceIDs:
        #         Domoticz.Device(Name=aLight.name, Unit=i,  TypeName="Switch", Switchtype=7, DeviceID=str(aLight.id)).Create()
        #         i=i+1
        #         Domoticz.Device(Name=aLight.name + " - White Temperature",  Unit=i, TypeName="Selector Switch", Switchtype=18, Options=WhiteOptions, DeviceID=str(aLight.id)).Create()
        #         i=i+1
        #
        # # Remove registered lights no longer found on the gateway
        # for aUnit in listOfUnitIds:
        #     if not int(Devices[aUnit].DeviceID) in listOfIkeaIDs:
        #         Devices[aUnit].Delete()
        #
        # # Sync deviceStates
        # for aUnit in Devices:
        #     targetDevice = self.gateway.get_device(int(Devices[aUnit].DeviceID))
        #     currentLevel = int((targetDevice.light_control.lights[0].dimmer/250)*100)
        #     state = int(targetDevice.light_control.lights[0].state)
        #     Devices[aUnit].Update(nValue=state, sValue=str(currentLevel))

        #Test
        #Domoticz.Device(Name="To be removed", Unit=100,  TypeName="Switch", Switchtype=7, DeviceID="12345").Create()



    def onStop(self):
        Domoticz.Log("onStop called")
        return True

    def onConnect(self, Connection, Status, Description):
        Domoticz.Log("onConnect called")

        if Status==0:
            if self.pluginStatus == 0:
                Connection.Send(Message=json.dumps({"action":"setConfig", "gateway": Parameters["Address"], "key": Parameters["Mode1"]}).encode(encoding='utf_8'), Delay=1)
                self.pluginStatus=1
        else:
            Domoticz.Log("Connection failed")

    def onMessage(self, Connection, Data, Status, Extra):
        Domoticz.Log("onMessage called")
        Domoticz.Log("Received: " + str(Data))

        command = json.loads(Data)

        Domoticz.Log("Command: " + command['action'])
        if command['status'] == "Ok":
            action = command['action']

            if action == "setConfig":
                # Config set
                Connection.Send(Message=json.dumps({"action":"getLights"}).encode(encoding='utf_8'), Delay=1)

            if action == "getLights":
                self.registerDevices(json.loads(Data)['result'])

            if action == "deviceUpdate":
                self.updateDeviceState(json.loads(Data)['result'])



    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Log("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))
        #
        # #Domoticz.Log(Devices[Unit].Name + " - Type: "+str(Devices[Unit].Type) + "Subtype: " + str(Devices[Unit].SubType))
        #
        # targetDevice = self.gateway.get_device(int(Devices[Unit].DeviceID))
        #
        if (Devices[Unit].Type == 244) and (Devices[Unit].SubType == 73):
            if Command=="On":
                self.CoapAdapter.Send(Message=json.dumps({"action": "setState", "state": "On", "deviceID": Devices[Unit].DeviceID}).encode(encoding='utf_8'), Delay=1)
                #targetDevice.light_control.set_state(True)
                #currentLevel = int((targetDevice.light_control.lights[0].dimmer/250)*100)
                #Domoticz.Log("Current level: " + str(currentLevel))
                #Devices[Unit].Update(nValue=1, sValue=str(currentLevel))
                #pass
            if Command=="Off":
                self.CoapAdapter.Send(Message=json.dumps({"action":"setState", "state": "Off", "deviceID": Devices[Unit].DeviceID}).encode(encoding='utf_8'), Delay=1)
                #currentLevel = int((targetDevice.light_control.lights[0].dimmer/250)*100)
                #targetDevice.light_control.set_state(False)
                #Devices[Unit].Update(nValue=0, sValue=str(currentLevel))
                pass
            if Command=="Set Level":
                targetLevel = int(int(Level)*250/100)
                self.CoapAdapter.Send(Message=json.dumps({"action":"setLevel", "deviceID": Devices[Unit].DeviceID, "level": targetLevel }).encode(encoding='utf_8'), Delay=1)
                #targetDevice.light_control.set_dimmer(targetLevel)
                #Devices[Unit].Update(nValue=1, sValue=str(Level))
        #
        # if (Devices[Unit].Type == 244) and (Devices[Unit].SubType == 62):
        #     Domoticz.Log("nValue: "+str(Devices[Unit].nValue)+" sValue: "+str(Devices[Unit].sValue))
        #     if Level==0:
        #         targetDevice.light_control.set_hex_color("f5faf6")
        #     if Level==10:
        #         targetDevice.light_control.set_hex_color("f1e0b5")
        #     if Level==20:
        #         targetDevice.light_control.set_hex_color("efd275")
        #
        #     Devices[Unit].Update(nValue=1, sValue=str(Level))


    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Log("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Log("onDisconnect called")

    def onHeartbeat(self):
        # Domoticz.Log("onHeartbeat called")
        if not self.CoapAdapter.Connected():
            Domoticz.Log("onHeartbeat called - not connected")
            self.CoapAdapter.Connect()

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data, Status, Extra):
    global _plugin
    _plugin.onMessage(Connection, Data, Status, Extra)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

    # Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return
