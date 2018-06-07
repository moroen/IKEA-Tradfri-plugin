#!/usr/bin/env python3

from pytradfri import Gateway
from pytradfri.api.libcoap_api import APIFactory

import uuid
import argparse

parser = argparse.ArgumentParser()

parser.add_argument('host', metavar='IP', type=str,  
                    help='IP Address of your Tradfri gateway')

parser.add_argument('key', 
                    help='Security code found on your Tradfri gateway')

identity = uuid.uuid4().hex

args = parser.parse_args()

api_factory = APIFactory(host=args.host, psk_id=identity)

try:
    psk = api_factory.generate_psk(args.key)
    print('Identity: ', identity)
    print('Generated PSK: ', psk)
except AttributeError:
    print("Failed")