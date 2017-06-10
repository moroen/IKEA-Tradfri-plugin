A Domoticz plugin for IKEA Trådfri (Tradfri) gateway

# Plugin

## Requirements:
1. Domoticz compiled with support for Python-Plugins / lastest beta
2. Python library pytradfri by ggravlingen (https://github.com/ggravlingen/pytradfri)
3. Twisted (https://twistedmatrix.com/trac/)
3. IKEA-Tradfri-plugin (https://github.com/moroen/IKEA-Tradfri-plugin)

## Installation
1. Install libcoap as per ggravlingen's description
2. Install pytradfri-library using either pip3 or Cloning the pytradfri repository and installing using setup.py
```shell
  $ pip3 install pytradfri
```
or
```shell
$ git clone https://github.com/ggravlingen/pytradfri.git
$ cd pytradfri
$ python3 setup.py install
```
  
3. Install twisted
```
$ pip3 install twisted
```

4. Install plugin and enable COAP-adaptor

5. Restart domoticz and enable IKEA-Tradfri from the hardware page

Usage<br>
Lights and devices have to be added to the gateway as per IKEA's instructions, using the official IKEA-tradfri app. 

<h1>tradfri.py</h1>
Command-line python-script for working with IKEA-gateway

Requirements
1. libcoap
2. pytradfri-library, either system-wide (pip3 install pytradfri) or by copying pytradfri-directiory from library to the same directory as tradfri.py

Usage<br>
./pytradfri.py --help for options
