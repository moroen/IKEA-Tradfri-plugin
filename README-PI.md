# A Domoticz plugin for IKEA Trådfri (Tradfri) gateway

## Instructions for installing on a Raspberry Pi
Verified on raspbian Buster, kernel 4.19.75-v7+

### 1. Install domoticz:
This will install the latest precompiled binary, default location is recommended
```
$ curl -L https://install.domoticz.com | bash
```

### 2. Install needed packages:
```
$ sudo apt update; sudo apt upgrade
$ sudo apt install golang python3 python3-dev python3-pip
```

### 3. Clone IKEA-tradfri plugin into domoticz plugins-directory:
```
$ cd /home/pi/domoticz/plugins/
$ git clone https://github.com/moroen/IKEA-Tradfri-plugin.git IKEA-Tradfri
```

### 4. Update pip and setuptools: 
```shell
$ sudo -H pip3 install --upgrade pip
$ sudo -H pip3 install --upgrade setuptools
```

### 5. Install py3coap:
```shell
$ sudo -H pip3 install -U py3coap
```


### 6. Configure and test connection:
```shell
$ cd IKEA-Tradfri
$ python3 plugin.py config IP KEY
$ python3 plugin.py list
```
### 8. Refer to the main [readme](README.md) for domoticz setup and usage


## Alternative installation of py3coap
On some systems, installing py3coap using pip fails. Installing py3coap manually might help, or at least give some more information on why installation fails.

```shell
$ git clone https://github.com/moroen/pycoap.git
$ cd pycoap
$ sudo -H python3 setup.py install
```

Note: The basic requirements, as described at point 2 above, still need to be installed when using this alternative method.

## Using coapcmd as an alternative to pycoap
Please refer to the main [readme](README.md).
