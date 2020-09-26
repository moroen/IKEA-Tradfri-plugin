from .config import get_config
from . import ApiNotFoundError

_debug = 0

CONF = get_config()

if CONF["Api"] == "Pycoap":
    try:
        from .pycoap_api import (
            HandshakeError,
            UriNotFoundError,
            ReadTimeoutError,
            WriteTimeoutError,
            set_debug_level,
        )
    except ImportError:
        raise ApiNotFoundError("py3coap not found")

if CONF["Api"] == "Coapcmd":
    try:
        from .coapcmd_api import (
            HandshakeError,
            UriNotFoundError,
            ReadTimeoutError,
            WriteTimeoutError,
            set_debug_level,
        )
    except ImportError:
        raise


class DeviceNotFoundError(Exception):
    def __init__(self, deviceid):
        self.DeviceID = deviceid


class MethodNotSupported(Exception):
    def __init__(self, api, message):
        self.message = message
        self.api = api
