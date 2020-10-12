from .config import get_config
from . import ApiNotFoundError
from .errors import MethodNotSupported

CONF = get_config()

if CONF["Api"] == "Pycoap":
    from py3coap import Observe, ObserveStop

if CONF["Api"] == "Coapcmd":
    pass


def observe_start():
    if CONF["Api"] == "Pycoap":
        Observe(
            "coaps://192.168.1.15:5684/",
            '["15001/65554", "15001/65550"]',
            ident=CONF["Identity"],
            key=CONF["Passkey"],
        )
    else:
        raise MethodNotSupported("coapcmd", "Method observe_start not supported")


def observe_stop():
    if CONF["Api"] == "Pycoap":
        ObserveStop()
    else:
        raise MethodNotSupported("coapcmd", "Method observe_stop not supported")
