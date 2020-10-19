# A Domoticz plugin for IKEA Trådfri (Tradfri) gateway


## What's supported
The plugin supports and is able to controll the following devices:
- All bulbs, with dimming for bulbs that are dimmable and setting white temperature/color for CW and CWS bulbs.
- Outlets / sockets
- Floalt LED Panels
- Tradfri LED-drivers
- Curtains/Blinds (Kadrilj and Fyrtur)

The plugin doesn't work with:
- Motion sensors
- Remotes

## Compatible hardware
Most systems capable of running domoticz and has a version of python3 available should be able to run the plugin. There are special instructions for:
- [Raspberry Pi](README-PI.md)
- [Synology NAS](README-Synology.md)

## Sofware requirements:
1. Python version 3.5.3 or higher, 3.7.x recommended. 
2. Domoticz compiled with support for Python-Plugins. 
3. Upgraded pip and setuptools

## Local Installation

For instructions on installing the plugin on a Raspberry PI, please see the [readme](README-PI.md) for Raspberry. For Synology NAS, please check the [Synology-readme](README-Synology.md).

### 1. Clone IKEA-tradfri plugin into domoticz plugins-directory:
```
$ cd domoticz/plugins/
$ git clone https://github.com/moroen/IKEA-Tradfri-plugin.git IKEA-Tradfri
```

### 2. Update pip and setuptools:
```shell
  $ pip3 install -U pip
  $ pip3 install -U setuptools
```

### 3.1 Install tradfricoap
The plugin uses the tradfricoap python module ([PyPi](https://pypi.org/search/?q=tradfricoap)) 

```shell
  $ pip3 install -U tradfricoap
```

If upgrading from version 0.9.13 or lower, remove the tradfri directory after upgradring the plugin to version 0.9.14 or higher.


### 3.2 Installing an API for coap requests
Tradfricoap supports two different COAP-transports for communicating with the IKEA Tradfri gateway. The pycoap module is the default, recommended transport. 

On systems with a working GO compiler, but without the needed libraries for creating python3 modules (like a Synology NAS), a command line utility - coapcmd (https://github.com/moroen/coapcmd) - can be used. For systems without a working go compiler, prebuild binaries are available in the repository on github.com. 

#### 3.2a Pycoap (recommended)
Py3coap is available as precompiled wheels for linux (amd64), Windows (win32 and amd64) and MacOS. On other systems, and for installing on a Raspberry PI ([PI readme](README-PI.md)), a go compiler (version 1.11 or greater recommended) and the python3 development libraries must be installed before installing via pip3 and requirements.txt.

```shell
  $ pip3 install py3coap
```

##### Alternative installation of pycoap
On some systems, installing pycoap using pip fails. Installing pycoap manually might help, or at least give some more information on why installation fails.

```shell
$ git clone https://github.com/moroen/pycoap.git
$ cd pycoap
$ sudo -H python3 setup.py install
```

#### 3b coapcmd (alternative)
The coapcmd command must be installed as IKEA-Tradfri/bin/coapcmd and the plugin configured to use coapcmd for COAP-requests. On systems with git and go installed, coapcmd can be installed with the provided install-script:

```shell
$ bash install_coapcmd.sh
```

Configure the plugin to use coapcmd:
```shell
$ python3 plugin.py config api coapcmd
```

For systems without a working git and/or go compiler, please refer to the repository for coapcmd (https://github.com/moroen/coapcmd) for alternative install options and prebuilt binaries for common systems. To use a prebuild binary, download the correct file from https://github.com/moroen/coapcmd/releases, rename it to coapcmd (coapcmd.exe on windows) and place it in the bin directory of the plugin (domoticz/plugins/IKEA-Tradfri/bin).

#### Switching between transports:
```shell
$ python3 plugin.py config api pycoap # Use pycoap module
$ python3 plugin.py config api coapcmd # Use coapcmd
```


### 4. Configure Tradfri COAP: 
```shell
  $ python3 plugin.py config gw IP KEY
```
  * IP is the address of the gateway, and KEY is the security-code located on the bottom of the gateway. 

### 5. Check communication with the gateway:
```shell
  $ python3 plugin.py list
```

For other command line commands, refer to help
```shell
  $ python3 plugin.py --help
```

### 6. Restart domoticz and enable IKEA-Tradfri from the hardware page
## Usage
Lights and devices have to be added to the gateway as per IKEA's instructions, using the official IKEA-tradfri app.

### Observing changes
To observe changes to buld or socket when switched using another method than domoticz, enable "Observe changes" and specify a poll interval in seconds. As long an intervall as possible is recommended. The mininum poll intervall is 10 seconds, and the intervall should be a multiple of 10 seconds. Using a too short interval tends to freeze the gateway, requiring cycling the power of the gateway to restore communication. A polling interval of 300 seconds or greater seems to be fine and reduce the occurence of freezes. 

### A note about colors
When using a CWS (color) bulb, a CWS color selector device is created. Due to a known limitation when setting levels in Domoticz scenes, it's only possible to specify the first half of the available colors in a scene. Selecting a color from the last half, gives the color for level 100 (lime) when the scene is activated. A workaround for this is planned, but currently not implemented. 

### Curtains
Domoticz sets the position of a curtain as a percentage between 0 (fully open) to 100 (fully closed). You need to set the maximum posistion of the curtain before using Domoticz. Please refer to the instructions from IKEA on how to set the maximum position of a curtain. 

## Check installed version
To find the current version of the plugin and modules:
```shell
  $ cd domoticz/plugins/IKEA-Tradfri
  $ python3 plugin.py version
```

## Updating plugin
To update the plugin to the newest version, stop domoticz, enter the plugin directory, pull the latest changes from git and restart domoticz:
```shell
  $ cd domoticz/plugins/IKEA-Tradfri
  $ git pull
```

It's usually recommended to upgrade to the latest version of tardfricoap py3coap as well:
```shell
  $ sudo -H pip3 install -U tradfricoap py3coap
```