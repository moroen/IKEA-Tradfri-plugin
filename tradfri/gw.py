import pycoap

from .config import host_config
from json import loads, dumps

import logging


def create_ident(ip, key, configFile=None):
    import uuid

    identity = uuid.uuid4().hex

    payload = '{{"{}":"{}"}}'.format(9090, identity)
    uri = "coaps://{}:{}/{}".format(ip, 5684, "15011/9063")

    result = pycoap.Request(
            uri, payload=payload, method=pycoap.POST, ident="Client_identity", key=key
        )
    
    logging.debug("Create ident result: {}".format(result))

    if result is None:
        logging.critical("Create_ident: No data from gateway")
        return None

    res = loads(result)
    conf_obj = host_config(configFile)

    conf_obj.set_config_items(Gateway=ip, Identity=identity, Passkey=res["9091"])
    conf_obj.save()
