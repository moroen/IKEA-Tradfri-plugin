import asyncio
import json
import logging
import socket
import threading
import sys

from aiocoap import Message, Context
from aiocoap.error import RequestTimedOut, Error, ConstructionRenderableError
from aiocoap.numbers.codes import Code
from aiocoap.transports import tinydtls

from config import get_config



class PatchedDTLSSecurityStore:
    """Patched DTLS store in lieu of a credentials framework.
       https://github.com/chrysn/aiocoap/issues/97"""

    IDENTITY = None
    KEY = None

    def _get_psk(self, host, port):
        return PatchedDTLSSecurityStore.IDENTITY, PatchedDTLSSecurityStore.KEY


def init():
    tinydtls.DTLSSecurityStore = PatchedDTLSSecurityStore

async def _get_request(uri):

    print (sys.path)

    protocol = await Context.create_client_context()

    request = Message(code=Code.GET, uri=uri)

    pr = protocol.request(request)
    res = await pr.response
    await protocol.shutdown()
    return res.payload.decode("utf-8")


async def _put_request(uri, payload):

    protocol = await Context.create_client_context()

    request = Message(code=Code.PUT, uri=uri, payload=payload.encode("utf-8"))

    pr = protocol.request(request)
    res = await pr.response
    # print (res.payload.decode('utf-8'))

    await protocol.shutdown()
    return None


def DTLSRequest(uri, ident, key):
    PatchedDTLSSecurityStore.IDENTITY = ident.encode("utf-8")
    PatchedDTLSSecurityStore.KEY = key.encode("utf-8")

    loop = asyncio.get_event_loop()
    task = loop.create_task(_get_request(uri))
    print ("Id: {} Key: {}".format(PatchedDTLSSecurityStore.IDENTITY, PatchedDTLSSecurityStore.KEY))
    return loop.run_until_complete(task)


def DTLSPutRequest(uri, payload, ident, key):
    PatchedDTLSSecurityStore.IDENTITY = ident.encode("utf-8")
    PatchedDTLSSecurityStore.KEY = key.encode("utf-8")

    loop = asyncio.get_event_loop()
    task = loop.create_task(_put_request(uri, payload))
    return loop.run_until_complete(task)


def request(uri, payload=None):
    conf = get_config()

    print ("Uri: {}".format(uri))
    print ("Payload: {}".format(payload))

    if payload == None:
        return DTLSRequest(
            "coaps://{}:{}/{}".format(conf["Gateway"], 5684, uri),
            conf["Identity"],
            conf["Passkey"],
        )
    else:
        return DTLSPutRequest(
            "coaps://{}:{}/{}".format(conf["Gateway"], 5684, uri),
            payload,
            conf["Identity"],
            conf["Passkey"],
        )

async def stop_loop():
    loop = asyncio.get_event_loop()
    await loop.stop()

def close_loop():
    loop = asyncio.get_event_loop()
    loop.stop()

    # pending = asyncio.Task.all_tasks()
    # loop.run_until_complete(asyncio.gather(*pending))

if __name__ == "__main__":
    pass
