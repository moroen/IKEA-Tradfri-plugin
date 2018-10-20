#!/usr/bin/env python3

from pytradfri import Gateway
from pytradfri.api.libcoap_api import APIFactory

import uuid
import argparse
import json

from string import Template
import getpass,os, shutil

config = {}

parser = argparse.ArgumentParser()

parser.add_argument('host', metavar='IP', type=str,  
                    help='IP Address of your Tradfri gateway', nargs="?")

parser.add_argument('key', 
                    help='Security code found on your Tradfri gateway', nargs="?")

parser.add_argument('--skip-config', help="Skip generating a config file", action="store_true")
parser.add_argument('--create-service', help="Generate a systemd service-file", action="store_true")

identity = uuid.uuid4().hex

args = parser.parse_args()

api_factory = APIFactory(host=args.host, psk_id=identity)

if not args.skip_config:
    if (args.host is None) or (args.key is None):
        print("Error: IP and KEY required!")
        exit()

    try:
        psk = api_factory.generate_psk(args.key)
        config["Gateway"] = args.host
        config["Identity"] = identity
        config["Passkey"] = psk

        with open('config.json', 'w') as outfile:
            json.dump(config, outfile)

        print("Config created!")

    except:
        print("Failed to generate ID/PSK-pair.\nCheck that the IP and Master Key is correct.")

if args.create_service:
    service = {"user": getpass.getuser(), "path": os.getcwd(), "twistd": shutil.which("twistd")}
    tpl=open("ikea-tradfri.service.tpl").read()
    src = Template(tpl)
    result=src.substitute(service)
    
    with open('ikea-tradfri.service', 'w+') as f:
        f.write(result)
