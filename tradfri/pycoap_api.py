import logging

try: 
    from pycoap import setDebugLevel, Request, __version__
    from pycoap.errors import HandshakeError, UriNotFoundError

except ModuleNotFoundError:
    raise

from .config import get_config

def set_debug_level(level):
    global _debug
    _debug = level
    setDebugLevel(level)
    if level == 1:
        logging.basicConfig(level=logging.DEBUG)

def request(uri, payload=None):

    conf = get_config()

    if conf["Gateway"] is None:
        logging.critical("Gateway not specified")
        return

    if payload == None:
        return Request(
            uri="coaps://{}:{}/{}".format(conf["Gateway"], 5684, uri),
            ident=conf["Identity"],
            key=conf["Passkey"],
        )
            
    else:
        return Request(
            uri="coaps://{}:{}/{}".format(conf["Gateway"], 5684, uri),
            payload=payload,
            method=pycoap.PUT,
            ident=conf["Identity"],
            key=conf["Passkey"],
        )
