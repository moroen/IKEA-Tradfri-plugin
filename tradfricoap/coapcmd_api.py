import logging, subprocess, os, json

from .config import get_config
from . import ApiNotFoundError

class HandshakeError(Exception):
    pass

class UriNotFoundError(Exception):
    pass

class ReadTimeoutError(Exception):
    pass

class WriteTimeoutError(Exception):
    pass

# _coapCMD = "{}/{}".format(os.path.dirname(os.path.abspath(__file__)), "../bin/coapcmd")
_coapCMD = "coapcmd"


def set_debug_level(level):
    pass

def set_coapcmd(cmd):
    global _coapCMD
    _coapCMD = cmd

def request(uri, payload=None, method="put"):
    if not os.path.exists(_coapCMD):
        raise ApiNotFoundError("coapcmd", "'coapcmd' not found.")
        return

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
        if result["Status"] == "ReadTimeoutError":
            raise ReadTimeoutError
        if result["Status"] == "WriteTimeoutError":
            raise WriteTimeoutError
        return None

    else:
        result = json.loads(subprocess.run([_coapCMD, method, "--ident",conf["Identity"], "--key", conf["Passkey"], path, payload], stdout=subprocess.PIPE).stdout.decode('utf-8'))

        if result["Status"] == "ok":
            return result["Result"]
        if result["Status"] == "HandshakeError":
            raise HandshakeError
        if result["Status"] == "UriNotFound":
            raise UriNotFoundError
        if result["Status"] == "ReadTimeoutError":
            raise ReadTimeoutError
        if result["Status"] == "WriteTimeoutError":
            raise WriteTimeoutError
        return None

def create_ident(ip, key, configFile=None):
    import uuid
    from .config import host_config, get_config
    from json import loads, dumps

    identity = uuid.uuid4().hex

    payload = '{{"{}":"{}"}}'.format(9090, identity)
    uri = "coaps://{}:{}/{}".format(ip, 5684, "15011/9063")

    result = json.loads(subprocess.run([_coapCMD, "post", "--ident", "Client_identity", "--key", key, uri, payload], stdout=subprocess.PIPE).stdout.decode('utf-8'))
    logging.debug("Create ident result: {}".format(result))

    print(result)

    if result is None:
        logging.critical("Create_ident: No data from gateway")
        return None

    if result["Status"] == "ok":      
        res = json.loads(result["Result"])
        conf_obj = host_config(configFile)
        conf_obj.set_config_items(Gateway=ip, Identity=identity, Passkey=res["9091"])
        conf_obj.save()

    if result["Status"] == "HandshakeError":
        raise HandshakeError
    if result["Status"] == "UriNotFound":
        raise UriNotFoundError
    if result["Status"] == "ReadTimeoutError":
        raise ReadTimeoutError
    if result["Status"] == "WriteTimeoutError":
        raise WriteTimeoutError
    return None