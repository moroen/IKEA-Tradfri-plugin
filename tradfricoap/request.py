from .config import get_config

def request(uri, payload=None, method="put"):
    CONF = get_config()

    if CONF["Api"] == "Pycoap":
        try:
            from .pycoap_api import (
                request as _request,
                set_debug_level,
                HandshakeError,
                UriNotFoundError,
                ReadTimeoutError,
                WriteTimeoutError,
                create_ident,
            )
        except ImportError:
            print(
                'Pycoap module not found!\nInstall with "pip3 install -r requirements.txt" or select another api with "python3 tradfricoap.py api"'
            )
            exit()

    if CONF["Api"] == "Coapcmd":
        try:
            from .coapcmd_api import (
                request as _request,
                set_debug_level,
                HandshakeError,
                UriNotFoundError,
                ReadTimeoutError,
                WriteTimeoutError,
                create_ident,
            )
        except ImportError:
            print(
                'coapcmd  not found!\nInstall with "bash install_coapcmd.sh" or select another api with "python3 tradfricoap.py api"'
            )
            exit()

    return _request(uri, payload, method)