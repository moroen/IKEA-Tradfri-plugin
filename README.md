# A Domoticz plugin for IKEA Trådfri (Tradfri) gateway

## What's supported
The plugin supports and is able to controll the following devices:
- All bulbs, with dimming for bulbs that are dimmable and setting white temperature/color for CW and CWS bulbs.
- Outlets / sockets
- Floalt LED Panels
- Tradfri LED-drivers

The plugin partly works with:
- Remotes - It's possible to monitor battery levels, but not using a tradfri remote to controll lights through domoticz

The plugin doesn't work with:
- Motion sensors
- Curtains

## Requirements:
1. Python version 3.5.3 or higher, 3.7.x recommended. 
2. Domoticz compiled with support for Python-Plugins. 
3. Upgraded pip and setuptools
   

## Local Installation
### 1. Clone IKEA-tradfri plugin into domoticz plugins-directory and checkout the pycoap branch
```
$ cd domoticz/plugins/
$ git clone https://github.com/moroen/IKEA-Tradfri-plugin.git IKEA-Tradfri
$ cd IKEA-Tradfri
$ git checkout pycoap
```

### 2. Update pip and setuptools
```shell
  $ pip3 install --upgrade pip
  $ pip3 install --upgrade setuptools
```

### 3. Install other requirements
```shell
  $ pip3 install -r requirements.txt
```

#### Pycoap fails to install
The plugin uses manylinux wheels on linux, and there are compiled wheels for Windows and MacOS. If the above installation fails, a golang compiler (version 1.12 or greater recommende) must be installed and the above pip3 command runned again.

### 4. Configure Tradfri COAP: 
```shell
  $ python3 tradfricoap.py config IP KEY
```
  * IP is the address of the gateway, and KEY is the security-key located on the bottom of the gateway.

### 5. Check communication with the gateway:
```shell
  $ python3 tradfricoap.py list
```
### 6. Restart domoticz and enable IKEA-Tradfri from the hardware page

### Observing changes
To observe changes to buld or socket when switched using another method than domoticz, enable "Observe changes" and specify a poll interval in seconds. As long an intervall as possible is recommended. The mininum poll intervall is 10 seconds, and the intervall should be a multiple of 10 seconds. Using a too short interval tends to freeze the gateway, requiring cycling the power of the gateway to restore communication. A polling interval of 300 seconds or greater seems to be fine and reduce the occurence of freezes. 

### A note about colors
When using a CWS (color) bulb, a CWS color selector device is created. Due to a known limitation when setting levels in Domoticz scenes, it's only possible to specify the first half of the available colors in a scene. Selecting a color from the last half, gives the color for level 100 (lime) when the scene is activated. A workaround for this is planned, but currently not implemented. 

## Usage
Lights and devices have to be added to the gateway as per IKEA's instructions, using the official IKEA-tradfri app. 
