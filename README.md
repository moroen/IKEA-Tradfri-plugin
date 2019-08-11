A Domoticz plugin for IKEA Trådfri (Tradfri) gateway

# Plugin

Since domoticz plugins doesn't support COAP and also doesn't allow threads or async calls, the IKEA-tradfri plugin contains two parts, the domoticz plugin and a python3 IKEA-tradfri adaptor. The adaptor needs to be running at all times, and is intented to be run as a service using systemd.

# What's supported
The plugin supports and is able to controll the following devices:
- All bulbs, with dimming for bulbs that are dimmable and setting white temperature/color for CW and CWS bulbs.
- Outlets / sockets
- Floalt LED Panels
- Tradfri LED-drivers

The plugin partly works with:
- Remotes - It's possible to monitor battery levels, but not using a tradfri remote to controll lights through domoticz

The plugin doesn't work with:
- Motion sensors


## Requirements:
1. Python version 3.5.3 or higher, 3.7.x recommended. 
2. Domoticz compiled with support for Python-Plugins. 
3. IKEA-Tradfri command line utility (https://github.com/moroen/ikea-tradfri)


## Local Installation
### 1. Clone IKEA-tradfri plugin into domoticz plugins-directory
```
$ cd domoticz/plugins/
$ git clone https://github.com/moroen/IKEA-Tradfri-plugin.git IKEA-Tradfri
$ cd IKEA-Tradfri
```

### 2. Virtual python environment
Using a virtual environment is supported and recommended. Any python virtual environment tool should work, built in is recommended:
```shell
  $ python3 -m venv env
  $ source env/bin/activate
```

### 3. Update pip and setuptools
```shell
  $ pip3 install --upgrade pip
  $ pip3 install --upgrade setuptools
```

### 4. Install tradfri command line tool and required python packages
```shell
  $ python3 setup.py install
```
#### Note: For python 3.5.3, install using setup.py fails intermittently. Installing required packages with pip before running setup.py works around this issue:
```shell
  $ pip3 install -r requirements.txt
  $ python3 setup.py install
```

### 4. Configure the Tradfri COAP-adapter: 
```shell
  $ tradfri config IP GATEWAY-KEY
```
  * IP is the address of the gateway, and GATEWAY-KEY is the security-key located on the bottom of the gateway.

### 5. Check communication with the gateway:
```shell
  $ tradfri list
```
For a full set of commands, try:
```shell
  $ tradfri --help
```
  * Note: The tradfri command line tool is a work in progress, some commands might not work as expected or indeed work at all!

### 6. Enable COAP-adaptor

#### From prompt (for testing)
```shell
$ tradfri -v server
```

#### From prompt (for debug)
```shell
$ tradfri -vv server
```

#### Using systemd
1. Create a (reasonably sane) systemd-service file:
```shell
  $ tradfri service create
```
   - This should be run from the IKEA-Tradfri directory. If the tradfri command line tool has been installed in a virtual environment, make sure the virtual environment is activated before creating the service-file. 
   
   - By default, the service-file will set the service to run as the user running the tradfri command. To specify another user or group, use the --user and --group flags:

```shell
  $ tradfri service create --user domoticz --group domogroup
```
   * Note: If only --user is specified, the group will be set to the same name as the user

2. Verify that the generated ikea-tradfri.service-file has the correct paths and user, then copy the service-file to systemd-service directory, reload systemd-daemon and start the IKEA-tradfri service:
```shell
  $ sudo cp ikea-tradfri.service /etc/systemd/system
  $ sudo systemctl daemon-reload
  $ sudo systemctl start ikea-tradfri.service
```

3. Using systemd to start the COAP-adaptor on startup
```shell
$ sudo systemctl enable ikea-tradfri.service
```

### 6. Restart domoticz and enable IKEA-Tradfri from the hardware page
Input the IP of the host where the adapter is running.
NOTE: This is NOT the IP of the IKEA-Tradfri gateway. When running domoticz and the adapter on the same machine, the default IP (localhost / 127.0.0.1) should work. 

### Observing changes
To observe changes to buld or socket when switched using another method than domoticz, enable "Observe changes" and specify a poll interval in seconds. As long an intervall as possible is recommended. The mininum poll intervall is 5, and the intervall should be a multiple of 5 seconds. Using to short an interval tends to freeze the gateway, requiring cycling the power of the gateway to restore communication. A polling interval of 300 seconds or greater seems to be fine and reduce the occurence of freezes. 

### Upgrading from previous version of the plugin and adapter
After upgrading to the lastest version, make sure to configure the adapter as described above.

Then restart domoticz and on the hardware-page, select the IKEA-Plugin, change the IP from the previous address (IKEA-Gateway) to the host running the adapter, and press "Update".

All regular devices (light, sockets, drivers) should upgrade without intervension. The code for color devices (white balance and full color) has been completely rewritten, and on first upgrade the old color devices will be removed and new devices for setting white balanse (WS) and color (CWS) will be created. 

### A note about colors
When using a CWS (color) bulb, a CWS color selector device is created. Due to a known limitation when setting levels in Domoticz scenes, it's only possible to specify the first half of the available colors in a scene. Selecting a color from the last half, gives the color for level 100 (lime) when the scene is activated. A workaround for this is planned, but currently not implemented. 

## Docker Installation

It's possible to run the adapter as a docker container app. Please refer to IKEA-tradfri (https://github.com/moroen/ikea-tradfri) for instructions. 

## Usage
Lights and devices have to be added to the gateway as per IKEA's instructions, using the official IKEA-tradfri app. 
