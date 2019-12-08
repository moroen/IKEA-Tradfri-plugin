# A Domoticz plugin for IKEA Trådfri (Tradfri) gateway

## Instructions for installing on a Raspberry Pi

### 1. Install needed packages
```
$ sudo apt install golang python3 python3-dev python3 pip
```

### 2. Clone IKEA-tradfri plugin into domoticz plugins-directory and checkout the pycoap branch
```
$ cd domoticz/plugins/
$ git clone https://github.com/moroen/IKEA-Tradfri-plugin.git IKEA-Tradfri
$ cd IKEA-Tradfri
$ git checkout pycoap
```

### 2. Update pip and setuptools
```shell
$ sudo -H pip3 install --upgrade pip
$ sudo -H pip3 install --upgrade setuptools
```

### 3. Install other requirements
```shell
$ sudo -H pip3 install -r requirements-pi.txt
```

### 4. Continue from point 4 in the main [readme](README.md).
