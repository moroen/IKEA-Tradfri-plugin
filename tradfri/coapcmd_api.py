import logging, subprocess, os, json

from .config import get_config

_coapCMD = "{}/{}".format(os.path.dirname(os.path.abspath(__file__)), "../bin/coapcmd")

class HandshakeError(Exception):
    pass

class UriNotFoundError(Exception):
    pass

def set_debug_level(level):
    pass

def request(uri, payload=None):
    conf = get_config()
    path = "coaps://{}:{}/{}".format(conf["Gateway"], 5684, uri)

    if conf["Gateway"] is None:
        logging.critical("Gateway not specified")
        return

    if payload == None:
        result = json.loads(subprocess.run([_coapCMD, "get", "--ident",conf["Identity"], "--key", conf["Passkey"], path], stdout=subprocess.PIPE).stdout.decode('utf-8'))

        if result["Status"] == "ok":
            return result["Result"]
        if result["Status"] == "HandshakeError":
            raise HandshakeError
        if result["Status"] == "UriNotFound":
            raise UriNotFoundError
        return None

    else:
        return None

        # return pycoap.Request(
        #     uri="coaps://{}:{}/{}".format(conf["Gateway"], 5684, uri),
        #     payload=payload,
        #     method=pycoap.PUT,
        #     ident=conf["Identity"],
        #     key=conf["Passkey"],
        # )
