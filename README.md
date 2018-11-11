A Domoticz plugin for IKEA Trådfri (Tradfri) gateway

# Plugin

Since domoticz plugins doesn't support COAP and also doesn't allow threads or async calls, the IKEA-tradfri plugin contains two parts, the domoticz plugin and a python3 IKEA-tradfri adaptor written with the twisted framework. The adaptor needs to be running at all times, and is intented to be run as a service using systemd.

# What's supported
The plugin supports and is able to controll the following devices:
- All bulbs, with dimming for bulbs that are dimmable and setting white temperature/color for CW and CWS bulbs.
- Outlets / sockets
- Floalt LED Panels

The plugin doesn't work with:
- Motion sensors
- Remotes 

Untested devices:
- Tradfri LED-drivers

## Requirements:
1. Domoticz compiled with support for Python-Plugins. 
2. Python library pytradfri by ggravlingen (https://github.com/ggravlingen/pytradfri). Required version: 6.0.1 or greater.
3. Twisted (https://twistedmatrix.com/trac/)
3. IKEA-Tradfri-plugin (https://github.com/moroen/IKEA-Tradfri-plugin)

## Local Installation
### 1. Install libcoap

The provided install-coap-client script will try to compile and install libcoap. Some steps will require root-access via sudo, and as such the scipt will ask for your password.
```shell
  $ bash ./install-coap-client.sh
```

### 2. Install pytradfri-library 
```shell
  $ pip3 install pytradfri
```

### 3. Install twisted
```
$ pip3 install twisted
```
Note: Depending on the setup, it might be necessary to install twisted using sudo:
```
$ sudo pip3 install twisted
```

### 4. Clone IKEA-tradfri plugin into domoticz plugins-directory
```
~/$ cd /opt/domoticz/plugins/
/opt/domoticz/plugins$ git clone https://github.com/moroen/IKEA-Tradfri-plugin.git IKEA-Tradfri
```

### 5. Configure the Tradfri COAP-adapter: 
```shell
  $ ./configure.py IP GATEWAY-KEY
```
where IP is the address of the gateway, and GATEWAY-KEY is the security-key located on the bottom of the gateway.

### 6. Enable COAP-adaptor

#### From prompt (for testing)
```
/opt/domoticz/plugins/IKEA-Tradfri$ python3 tradfri.tac
```

#### Using systemd
1. Create a (reasonably sane) systemd-service file:
```shell
  $ ./configure.py --skip-config --create-service
```

This should be run from the IKEA-Tradfri directoy, and as the user indented to run the adapter.

2. Verify that the generated ikea-tradfri.service-file has the correct paths and user, then copy the service-file to systemd-service directory, reload systemd-daemon and start the IKEA-tradfri service:
```shell
/opt/domoticz/plugins/IKEA-Tradfri$ sudo cp ikea-tradfri.service /etc/systemd/system
/opt/domoticz/plugins/IKEA-Tradfri$ sudo systemctl daemon-reload
/opt/domoticz/plugins/IKEA-Tradfri$ sudo systemctl start ikea-tradfri.service
```

#### Using systemd to start the COAP-adaptor on startup
```
$ sudo systemctl enable ikea-tradfri.service
```

### 7. Restart domoticz and enable IKEA-Tradfri from the hardware page
Input the IP of the host where the adapter is running.
NOTE: This is NOT the IP of the IKEA-Tradfri gateway. When running domoticz and the adapter on the same machine, the default IP (localhost / 127.0.0.1) should work. 

To get domoticz to recognize changed states (using IKEA-remote, app or any other way of switching lights), observe changes must be enabled in the plugin-settings page and a reasonable polling intervall specified. 

### Observing changes
To observe changes to buld or socket when switched using another method than domoticz, enable "Observe changes" and specify a poll interval in seconds. As long an intervall as possible is recommended. The mininum poll intervall is 5, and the intervall should be a multiple of 5. 

### Upgrading from previous version of the plugin and adapter
After upgrading to the lastest version, make sure to configure the adapter as described above.

Then restart domoticz and on the hardware-page, select the IKEA-Plugin, change the IP from the previous address (IKEA-Gateway) to the host running the adapter, and press "Update".

## Docker Installation

Put IKEA gateway IP and preshared key from sticker into GW_config file.

To run the plugin in a Docker (for example to on a Synology NAS), package the adapter using the provided Docker build file:
```
docker build -t ikea-tradfri-plugin:latest .
```
RPI docker build:
```
docker build -t ikea-tradfri-plugin:latest . -f DockerfileRPI
```

Copy the docker image to the system running Domoticz and start the Docker instance:
```
docker run -d \
  --name ikea-tradfri-plugin \
  --restart unless-stopped \
  --env-file=GW_config \
  -p 1234:1234 \
  ikea-tradfri-plugin
```
config.json file will be created automaticaly.

Now the IKEA Tradfri to Domoticz adaptor is available on the localhost.

Clone IKEA-tradfri plugin into Domoticz plugins-directory
```
~/$ cd /opt/domoticz/plugins/
/opt/domoticz/plugins$ git clone https://github.com/moroen/IKEA-Tradfri-plugin.git IKEA-Tradfri
```

Restart Domoticz and the plugin should show up. When the plugin is loaded, the adaptor running in the Docker is automatically used.

## Usage
Lights and devices have to be added to the gateway as per IKEA's instructions, using the official IKEA-tradfri app. 
