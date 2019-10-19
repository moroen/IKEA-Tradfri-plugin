import pycoap

from config import host_config
from json import loads, dumps


def create_ident(ip, key):
    import uuid

    identity = uuid.uuid4().hex

    payload = '{{"{}":"{}"}}'.format(9090, identity)
    uri = "coaps://{}:{}/{}".format(ip, 5684, "15011/9063")

    res = loads(
        pycoap.Request(
            uri, payload=payload, method=pycoap.POST, ident="Client_identity", key=key
        )
    )

    conf_obj = host_config()

    conf_obj.set_config_items(Gateway=ip, Identity=identity, Passkey=res["9091"])
    conf_obj.save()
