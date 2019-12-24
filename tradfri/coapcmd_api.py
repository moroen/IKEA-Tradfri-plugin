import logging, subprocess, os

from .config import get_config

_coapCMD = "{}/{}".format(os.path.dirname(os.path.abspath(__file__)), "coapcmd")

def setDebugLevel(level):
    pass

def request(uri, payload=None):

    conf = get_config()

    if conf["Gateway"] is None:
        logging.critical("Gateway not specified")
        return

    if payload == None:
        result = subprocess.run([_coapCMD, uri], stdout=subprocess.PIPE)
        return result.stdout.decode('utf-8')
    else:
        return None

        # return pycoap.Request(
        #     uri="coaps://{}:{}/{}".format(conf["Gateway"], 5684, uri),
        #     payload=payload,
        #     method=pycoap.PUT,
        #     ident=conf["Identity"],
        #     key=conf["Passkey"],
        # )
