import logging

from . import ApiNotFoundError

try: 
    from py3coap import setDebugLevel, Request, __version__, POST, PUT, GET
    from py3coap.errors import HandshakeError, UriNotFoundError, WriteTimeoutError, ReadTimeoutError

except ImportError:
    raise ApiNotFoundError("pycoap", "Module 'py3coap' not found.")

from .config import get_config

def set_debug_level(level):
    global _debug
    _debug = level
    setDebugLevel(level)
    if level == 1:
        logging.basicConfig(level=logging.DEBUG)

def request(uri, payload=None, method="put"):
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
        method = POST if method=="post" else PUT
        return Request(
            uri="coaps://{}:{}/{}".format(conf["Gateway"], 5684, uri),
            payload=payload,
            method=method,
            ident=conf["Identity"],
            key=conf["Passkey"],
        )

def create_ident(ip, key, configFile=None):
    import uuid
    from .config import host_config, get_config
    from json import loads, dumps

    identity = uuid.uuid4().hex

    payload = '{{"{}":"{}"}}'.format(9090, identity)
    uri = "coaps://{}:{}/{}".format(ip, 5684, "15011/9063")

    result = Request(
            uri, payload=payload, method=POST, ident="Client_identity", key=key
        )
    
    logging.debug("Create ident result: {}".format(result))

    if result is None:
        logging.critical("Create_ident: No data from gateway")
        return None

    res = loads(result)
    conf_obj = host_config(configFile)

    conf_obj.set_config_items(Gateway=ip, Identity=identity, Passkey=res["9091"])
    conf_obj.save()
