A Domoticz plugin for IKEA Trådfri (Tradfri) gateway

# Plugin

Since domoticz plugins doesn't support COAP and also doesn't allow threads or async calls, the IKEA-tradfri plugin contains two parts, the domoticz plugin and a python3 IKEA-tradfri adaptor written with the twisted framework. The adaptor needs to be running at all times, and is intented to be run as a service using systemd.

## Requirements:
1. Domoticz compiled with support for Python-Plugins / lastest beta
2. Python library pytradfri by ggravlingen (https://github.com/ggravlingen/pytradfri)
3. Twisted (https://twistedmatrix.com/trac/)
3. IKEA-Tradfri-plugin (https://github.com/moroen/IKEA-Tradfri-plugin)

## Installation
1. Install libcoap as per ggravlingen's description
2. Install pytradfri-library 
```shell
  $ pip3 install pytradfri
```

### or

```
$ git clone https://github.com/ggravlingen/pytradfri.git
$ cd pytradfri
$ python3 setup.py install
```

3. Install twisted
```
$ pip3 install twisted
```

4. Clone IKEA-tradfri plugin into domoticz plugins-directory
```
~/$ cd /opt/domoticz/plugins/
/opt/domoticz/plugins$ git clone https://github.com/moroen/IKEA-Tradfri-plugin.git IKEA-Tradfri
```

5. Enable COAP-adaptor

### From prompt (for testing)
```
/opt/domoticz/plugins/IKEA-Tradfri$ python3 tradfri.tac
```

### Using systemd
Edit the ikea-tradfri.service-file, and specify the right path to the IKEA-tradfri directory and change user if not to be run as root, copy the service-file to systemd-service directory and reload systemd-daemon
```
/opt/domoticz/plugins/IKEA-Tradfri$ sudo cp ikea-tradfri.service /lib/systemd/system/
/opt/domoticz/plugins/IKEA-Tradfri$ sudo systemctl daemon-reload
/opt/domoticz/plugins/IKEA-Tradfri$ sudo systemctl start ikea-tradfri.service
```

#### Using systemd to start the COAP-adaptor on startup
```
$ sudo systemctl enable ike-tradfri.service
```

6. Restart domoticz and enable IKEA-Tradfri from the hardware page

## Usage
Lights and devices have to be added to the gateway as per IKEA's instructions, using the official IKEA-tradfri app. 
