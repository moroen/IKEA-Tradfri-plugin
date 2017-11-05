A Domoticz plugin for IKEA Trådfri (Tradfri) gateway

# Plugin

Since domoticz plugins doesn't support COAP and also doesn't allow threads or async calls, the IKEA-tradfri plugin contains two parts, the domoticz plugin and a python3 IKEA-tradfri adaptor written with the twisted framework. The adaptor needs to be running at all times, and is intented to be run as a service using systemd.

## A note about branches
The repository contains two primary branches. The 'master' branch is targeted at the master branch of domoticz, which should be the latest stable. The development branch tracks the domoticz developement branch, where the plugin interface still is in flux.

## Requirements:
1. Domoticz compiled with support for Python-Plugins / lastest beta
2. Python library pytradfri by ggravlingen (https://github.com/ggravlingen/pytradfri). Required version: 4.0.2 or greater.
3. Twisted (https://twistedmatrix.com/trac/)
3. IKEA-Tradfri-plugin (https://github.com/moroen/IKEA-Tradfri-plugin)

## Local Installation
### 1. Install libcoap as per ggravlingen's description
### 2a. Install pytradfri-library 
```shell
  $ pip3 install pytradfri
```

#### or

```
$ git clone https://github.com/ggravlingen/pytradfri.git
$ cd pytradfri
$ python3 setup.py install
```

### 3. Install twisted
```
$ pip3 install twisted
```
Note: Dpending on setup, it might be necessary to install twisted using sudo.

### 4. Clone IKEA-tradfri plugin into domoticz plugins-directory
```
~/$ cd /opt/domoticz/plugins/
/opt/domoticz/plugins$ git clone https://github.com/moroen/IKEA-Tradfri-plugin.git IKEA-Tradfri
```

### 5. Create identity and pre-shared-key 
```
~/$ coap-client -m post -u "Client_identity" -k "GATEWAY-KEY" -e '{"9090":"IDENT"}' "coaps://IP:5684/15011/9063"
```
where GATEWAY-KEY is the security-key located on the bottom of the gateway, IDENT is the desired identifikation-name, and IP the address of the gateway.

A sucessfull call will return the preshared key (PSK) for IDENT:
```
{"9091":"PSK","9029":"1.2.0042"}
```

### 6. Enable COAP-adaptor

#### From prompt (for testing)
```
/opt/domoticz/plugins/IKEA-Tradfri$ python3 tradfri.tac
```

#### Using systemd
Edit the ikea-tradfri.service-file, and specify the right path to the IKEA-tradfri directory and change user if the adaptor should run as another user than root. Then copy the service-file to systemd-service directory, reload systemd-daemon and start the IKEA-tradfri service:
```
/opt/domoticz/plugins/IKEA-Tradfri$ sudo cp ikea-tradfri.service /lib/systemd/system/
/opt/domoticz/plugins/IKEA-Tradfri$ sudo systemctl daemon-reload
/opt/domoticz/plugins/IKEA-Tradfri$ sudo systemctl start ikea-tradfri.service
```

#### Using systemd to start the COAP-adaptor on startup
```
$ sudo systemctl enable ikea-tradfri.service
```

### 7. Restart domoticz and enable IKEA-Tradfri from the hardware page
Input the IP of the gateway and the IDENT and PSK from step 5 on the plugin-setup page.

To get domoticz to recognize changed states (using IKEA-remote, app or any other way of switching lights), observe changes must be enabled in the plugin-settings page.

## Docker Installation

To run the plugin in a Docker (for example to on a Synology NAS), package the adapter using the provided Docker build file:
```
docker build -t ikea-tradfri-plugin:latest .
```

Copy the docker image to the system running Domoticz and start the Docker instance:
```
docker run -t -p 127.0.0.1:1234:1234 ikea-tradfri-plugin:1234
```

Now the IKEA Tradfri to Domoticz adaptor is available on the localhost.

Clone IKEA-tradfri plugin into Domoticz plugins-directory
```
~/$ cd /opt/domoticz/plugins/
/opt/domoticz/plugins$ git clone https://github.com/moroen/IKEA-Tradfri-plugin.git IKEA-Tradfri
```

Restart Domoticz and the plugin should show up. When the plugin is loaded, the adaptor running in the Docker is automatically used.

## Usage
Lights and devices have to be added to the gateway as per IKEA's instructions, using the official IKEA-tradfri app. 
