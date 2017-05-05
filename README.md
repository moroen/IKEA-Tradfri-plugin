A Domoticz plugin for IKEA Trådfri (Tradfri) gateway 

<H1>Plugin</H1>

Requirements:
1. Domoticz compiled with support for Python-Plugins
2. Python library pytradfri by ggravlingen (https://github.com/ggravlingen/pytradfri)
3. IKEA-Tradfri-plugin (https://github.com/moroen/IKEA-Tradfri-plugin)

Installation
1. Install libcoap as per ggravlingen's description
2. Download pytradfri-library
3. Download IKEA-tradfri-plugin and copy plugin.py and tradfri.py to ../domoticz/plugins/IKEA-tradfri
4. Copy the directory "pytradfri" from ggravlingen's python library into the plugins directory.
5. Restart domoticz and enable IKEA-Tradfri from the hardware page

<h1>tradfri.py</h1>
Command-line python-script for working with IKEA-gateway

Requirements
1. libcoap
2. pytradfri-library, either system-wide (pip3 install pytradfri) or by copying pytradfri-directiory from library to the same directory as tradfri.py

Usage<br>
./pytradfri.py --help for options

