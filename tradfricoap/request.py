from .config import get_config
from . import ApiNotFoundError

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
            raise ApiNotFoundError("pycoap", "Module 'py3coap' not found.")

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
            raise ApiNotFoundError("coapcmd", "'coapcmd' not found.")

    return _request(uri, payload, method)