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
import pytradfri

class BasePlugin:
    enabled = False
    api = None
    gateway = None

    def __init__(self):
        #self.var = 123
        return

    def onStart(self):
        Domoticz.Log("onStart called")

        Domoticz.Log(Parameters["Address"])
        Domoticz.Log(Parameters["Mode1"])

        currentUnits = {}

        self.api = pytradfri.coap_cli.api_factory(Parameters["Address"],Parameters["Mode1"])
        self.gateway = pytradfri.gateway.Gateway(self.api)

        ikea_devices = self.gateway.get_devices()

        lights = [dev for dev in ikea_devices if dev.has_light_control]

        listOfIkeaIDs = [int(dev.id) for dev in lights]
        listOfDeviceIDs = [int(Devices[aUnit].DeviceID) for aUnit in Devices]
        listOfUnitIds = list(Devices.keys())

        if (len(Devices) == 0):
            i=1
        else:
            i=int(listOfUnitIds[-1])+1

        if Parameters["Mode6"] == "Debug":
            Domoticz.Debugging(1)

        # Add unregistered lights
        for aLight in lights:
            if not int(aLight.id) in listOfDeviceIDs:
                Domoticz.Device(Name=aLight.name, Unit=i,  TypeName="Switch", Switchtype=7, DeviceID=str(aLight.id)).Create()
                i=i+1

        # Remove registered lighst no longer found on the gateway
        for aUnit in listOfUnitIds:
            if not int(Devices[aUnit].DeviceID) in listOfIkeaIDs:
                Devices[aUnit].Delete()

        # Test
        # Domoticz.Device(Name="To be removed", Unit=100,  TypeName="Switch", Switchtype=7, DeviceID="12345").Create()

    def onStop(self):
        Domoticz.Log("onStop called")

    def onConnect(self, Status, Description):
        Domoticz.Log("onConnect called")

    def onMessage(self, Data, Status, Extra):
        Domoticz.Log("onMessage called")

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Log("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))
        Domoticz.Log(Devices[Unit].Name)
        targetDevice = self.gateway.get_device(int(Devices[Unit].DeviceID))



        if Command=="On":
            targetDevice.light_control.set_state(True)
            currentLevel = int((targetDevice.light_control.lights[0].dimmer/250)*100)
            Domoticz.Log("Current level: " + str(currentLevel))
            Devices[Unit].Update(nValue=1, sValue=str(currentLevel))
        if Command=="Off":
            currentLevel = int((targetDevice.light_control.lights[0].dimmer/250)*100)
            targetDevice.light_control.set_state(False)
            Devices[Unit].Update(nValue=0, sValue=str(currentLevel))
        if Command=="Set Level":
            targetLevel = int(int(Level)*250/100)
            targetDevice.light_control.set_dimmer(targetLevel)
            Devices[Unit].Update(nValue=1, sValue=str(Level))


    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Log("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self):
        Domoticz.Log("onDisconnect called")

    def onHeartbeat(self):
        Domoticz.Log("onHeartbeat called")

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Status, Description):
    global _plugin
    _plugin.onConnect(Status, Description)

def onMessage(Data, Status, Extra):
    global _plugin
    _plugin.onMessage(Data, Status, Extra)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect():
    global _plugin
    _plugin.onDisconnect()

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
