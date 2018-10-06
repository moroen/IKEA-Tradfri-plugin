# IKEA Tradfri Python Plugin
#
# Author: moroen
#
"""
<plugin key="IKEA-Tradfri" name="IKEA Tradfri" author="moroen" version="1.0.6" externallink="https://github.com/moroen/IKEA-Tradfri-plugin">
    <params>
        <param field="Address" label="Apdaptor IP Address" width="200px" required="true" default="127.0.0.1"/>
        <param field="Mode2" label="Observe changes" width="75px">
            <options>
                <option label="Yes" value="True"/>
                <option label="No" value="False"  default="true" />
            </options>
        </param>

        <param field="Mode4" label="Polling interval (seconds)" width="75px" required="true" default="30"/>

        <param field="Mode3" label="Add groups as devices" width="75px">
            <options>
                <option label="Yes" value="True"/>
                <option label="No" value="False"  default="true" />
            </options>
        </param>

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
import colors

colorOption=""

class BasePlugin:
    #enabled = False
    #api = None
    #gateway = None

    pluginStatus = 0
    # Dict of registered lights
    lights = {}
    CoapAdapter = None
    outstandingPings = 0
    nextConnect = 3

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

        whiteLevelNames, whiteLevelActions = colors.wbLevelDefinitions()
        WhiteOptions = {"LevelActions": whiteLevelActions, "LevelNames": whiteLevelNames, "LevelOffHidden": "true","SelectorStyle": "0"}
        
        colorLevelNames, colorLevelActions = colors.colorLevelDefinitions()
        colorOptions = {"LevelActions": colorLevelActions, "LevelNames": colorLevelNames, "LevelOffHidden": "false", "SelectorStyle": "1"}

        ikeaIds = []
        # Add unregistred lights
        for aLight in ikeaDevices:
            Domoticz.Debug ("Registering: {0}".format(json.dumps(aLight)))
            
            devID = str(aLight['DeviceID'])
            ikeaIds.append(devID)

            if not devID in self.lights:
                if aLight["Type"] == "Outlet":
                    Domoticz.Device(Name=aLight['Name'], Unit=i, Type=244, Subtype=73, Switchtype=0, Image=1, DeviceID=devID).Create()
                    self.lights[devID] = {"DeviceID": aLight['DeviceID'], "Unit": i}
                    i=i+1

                if aLight["Type"] == "Light":
                    deviceType = 244
                    subType = 73

                    if not "HasRGB" in aLight:
                        aLight["HasRGB"] = "false"

                    if aLight['Dimmable']:
                        switchType=7
                    else:
                        switchType=0

                    #Basic device
                    Domoticz.Device(Name=aLight['Name'], Unit=i,  Type=deviceType, Subtype=subType, Switchtype=switchType, DeviceID=devID).Create()
                    self.lights[devID] = {"DeviceID": aLight['DeviceID'], "Unit": i}
                    i=i+1 

                    if aLight["HasRGB"] == "true":
                        Domoticz.Device(Name=aLight['Name'] + " - Color",  Unit=i, TypeName="Selector Switch", Switchtype=18, Options=colorOptions, DeviceID=devID+":CWS").Create()
                        self.lights[devID+":CWS"] = {"DeviceID": devID+":CWS", "Unit": i}
                        i=i+1
                                    
                    if aLight['HasWB'] == "true":
                        Domoticz.Device(Name=aLight['Name'] + " - WB",  Unit=i, TypeName="Selector Switch", Switchtype=18, Options=WhiteOptions, DeviceID=devID+":WB").Create()
                        self.lights[devID+":WB"] = {"DeviceID": devID+":WB", "Unit": i}
                        i=i+1

        #Remove registered lights no longer found on the gateway
        for aUnit in list(Devices.keys()):
            devID = str(Devices[aUnit].DeviceID)

            if devID[-3:] == ":WB":
                devID = devID[:-3]

            if devID[-4:] == ":CWS":
                devID = devID[:-4]

            if not devID in ikeaIds:
                Devices[aUnit].Delete()

    def updateDeviceState(self, deviceState):
        for aDev in deviceState:
            Domoticz.Debug(str(aDev))
            devID = str(aDev["DeviceID"])
            targetUnit = self.lights[devID]['Unit']
            nVal = 0
            sVal = 0

            if aDev["State"] == "true":
                nVal = 1
                sVal = "1"
            if aDev["State"] == "false":
                nVal = 0
                sVal = "0"

            if "Level" in aDev:
                sValInt = int((aDev["Level"]/250)*100)
                if sValInt == 0:
                    sValInt = 1

                sVal = str(sValInt)

            Devices[targetUnit].Update(nValue=nVal, sValue=sVal)

            if "Hex" in aDev:
                if aDev["Hex"] != None:
                    if devID+":WB" in self.lights:
                        wbdevID = devID+":WB"
                        targetUnit = self.lights[wbdevID]['Unit']
                        Devices[targetUnit].Update(nValue=nVal, sValue=str(colors.wbLevelForHex(aDev['Hex'])))

                    if devID+":CWS" in self.lights:
                        wbdevID = devID+":CWS"
                        targetUnit = self.lights[wbdevID]['Unit']
                        Devices[targetUnit].Update(nValue=nVal, sValue=str(colors.colorLevelForHex(aDev['Hex'])))

    def connectToAdaptor(self):
        self.CoapAdapter = Domoticz.Connection(Name="Main", Transport="TCP/IP", Protocol="JSON", Address=Parameters["Address"], Port="1234")
        self.CoapAdapter.Connect()

    def onStart(self):
        # Domoticz.Log("onStart called")

        if Parameters["Mode6"] == "Debug":
            Domoticz.Debugging(1)

        Domoticz.Heartbeat(15)

        if len(Devices) > 0:
            # Some devices are already defined
            for aUnit in Devices:
                self.lights[Devices[aUnit].DeviceID] = {"DeviceID": Devices[aUnit].DeviceID, "Unit": aUnit}

        self.connectToAdaptor()

    def onStop(self):
        #Domoticz.Log("onStop called")
        return True

    def onConnect(self, Connection, Status, Description):
        #Domoticz.Log("onConnect called")

        if (Status==0):
            Domoticz.Log("Connected successfully to: "+Parameters["Address"])
            Connection.Send(Message=json.dumps({"action":"initGateway", "observe": Parameters["Mode2"], "pollinterval": Parameters['Mode4'], "groups": Parameters["Mode3"]}).encode(encoding='utf_8'), Delay=1)
        else:
            Domoticz.Log("Failed to connect to IKEA tradfri COAP-adapter! Status: {0} Description: {1}".format(Status, Description))
        return True

    def onMessage(self, Connection, Data):
        #Domoticz.Debug("Received: " + str(Data))
        #command = json.loads(Data.decode("utf-8"))

        command = Data

        #Domoticz.Log("Command: " + command['action'])
        if command['status'] == "Ok":
            action = command['action']

            if action == "initGateway":
                # Config set
                Connection.Send(Message=json.dumps({"action":"getLights"}).encode(encoding='utf_8'), Delay=1)

            if action == "getLights":
                self.registerDevices(command['result'])

            if action == "deviceUpdate":
                self.updateDeviceState(command['result'])

        if command['status'] == "Failed":
            Domoticz.Log("Command {0} failed with error: {1}.".format(command['action'],command['error']))
            Domoticz.Log(str(command))

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Debug("Command: " + str(Command)+" Level: "+str(Level)+" Type: "+str(Devices[Unit].Type)+" SubType: "+str(Devices[Unit].SubType)+" Hue: "+str(Hue))

        if (Devices[Unit].Type == 244) and (Devices[Unit].SubType == 73):
            if Command=="On":
                self.CoapAdapter.Send(Message=json.dumps({"action": "setState", "state": "On", "deviceID": Devices[Unit].DeviceID}).encode(encoding='utf_8'))

            if Command=="Off":
                self.CoapAdapter.Send(Message=json.dumps({"action":"setState", "state": "Off", "deviceID": Devices[Unit].DeviceID}).encode(encoding='utf_8'))

            if Command=="Set Level":
                targetLevel = int(int(Level)*250/100)
                self.CoapAdapter.Send(Message=json.dumps({"action":"setLevel", "deviceID": Devices[Unit].DeviceID, "level": targetLevel }).encode(encoding='utf_8'))

        if (Devices[Unit].Type == 244) and (Devices[Unit].SubType == 62):
            # This is a WB-device
            hex = None

            # [0] is the DeviceID [1] is the subType (WB/CWS)
            devId = Devices[Unit].DeviceID.split(':')
            
            if Level==0:
                #Off
                self.CoapAdapter.Send(Message=json.dumps({"action":"setState", "state": "Off", "deviceID": devId[0]}).encode(encoding='utf_8'))

            else:
                if devId[1] == "WB":
                    self.CoapAdapter.Send(Message=json.dumps({"action":"setHex", "deviceID": devId[0], "hex": colors.wb(Level)["Hex"]}).encode(encoding='utf_8'))
                if devId[1] == "CWS":
                    self.CoapAdapter.Send(Message=json.dumps({"action":"setHex", "deviceID": devId[0], "hex": colors.color(Level)["Hex"]}).encode(encoding='utf_8'))

        # if (Devices[Unit].Type == 241) and (Devices[Unit].SubType == 1):
        #     # This is a RGB-Device
        #     Domoticz.Debug("RGB - Command: {0} Level: {1} Hue: {2}".format(Command, Level, Hue))

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Log("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        self.isConnected = False
        Domoticz.Log("Device has disconnected")
        return

    def onHeartbeat(self):
        if (self.CoapAdapter.Connected() == True):
            pass
        else:
            Domoticz.Debug("Not connected - nextConnect: {0}".format(self.nextConnect))
            self.nextConnect = self.nextConnect -1
            if self.nextConnect <=0:
                self.nextConnect = 3
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

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

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
