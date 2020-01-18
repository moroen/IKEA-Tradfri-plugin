from .config import get_config

def IllegalMethodError(Exception):
    pass


_debug = 0

CONF = get_config()

if CONF["Api"] == "Pycoap":
    try:
        from .pycoap_api import (
            HandshakeError,
            UriNotFoundError,
            ReadTimeoutError,
            WriteTimeoutError,
            set_debug_level
        )
    except ImportError:
        print(
            'Pycoap module not found!\nInstall with "pip3 install -r requirements.txt" or select another api with "python3 tradfricoap.py api"'
        )
        exit()

if CONF["Api"] == "Coapcmd":
    try:
        from .coapcmd_api import (
            HandshakeError,
            UriNotFoundError,
            ReadTimeoutError,
            WriteTimeoutError,
            set_debug_level
        )
    except ImportError:
        print(
            'coapcmd  not found!\nInstall with "bash install_coapcmd.sh" or select another api with "python3 tradfricoap.py api"'
        )
        exit()

