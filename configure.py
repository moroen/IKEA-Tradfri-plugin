#!/usr/bin/env python3

try:
    from pytradfri import Gateway
    from pytradfri.api.libcoap_api import APIFactory
    from pytradfri.error import RequestError, RequestTimeout

except ModuleNotFoundError:
    print ("Error: Unable to import pytradfri. Please check your installation!")
    exit()

import uuid
import argparse
import json

from string import Template
import getpass,os, shutil

config = {}

parser = argparse.ArgumentParser()

subparsers = parser.add_subparsers(dest="command")
subparsers.required = True

parser_config = subparsers.add_parser("config")
parser_config.add_argument("IP")
parser_config.add_argument("KEY")

parser_service = subparsers.add_parser("service").add_subparsers(dest="service_command")
parser_service.required = True
service_create = parser_service.add_parser("create")
service_create.add_argument("--user")
service_create.add_argument("--group")

service_show = parser_service.add_parser("show")

args = parser.parse_args()

print (args)

def show_service_file():
    try:
        with open("ikea-tradfri.service", 'r') as fin:
            print(fin.read(), end="")
    except FileNotFoundError:
        print("Error: No ikea-tradfri.service-file found!\nGenerate file with 'configure.py service create'")

if args.command == "config":
    identity = uuid.uuid4().hex
    api_factory = APIFactory(host=args.IP, psk_id=identity)


    try:
        psk = api_factory.generate_psk(args.KEY)
    except RequestTimeout:
        print("Error: Connection to gateway timed out!\nPlease check IP/KEY.")
        exit()
    except:
        print("Error: Unknown error")
        exit()

    config["Gateway"] = args.IP
    config["Identity"] = identity
    config["Passkey"] = psk

    try:
        with open('config.json', 'w') as outfile:
            json.dump(config, outfile)
        print("Config created!")
    except PermissionError:
        print("Error: Could not write config.json")

elif args.command == "service":
    if args.service_command == "create":
        twistd_binary = shutil.which("twistd")
        if twistd_binary == None:
            print("Error: Unable to locate twistd. Please check your installation!")
        else: 
            service = {"user": getpass.getuser(), "group": getpass.getuser(), "path": os.getcwd(), "twistd": twistd_binary}
            if args.user is not None:
                service["user"] = args.user
                if args.group is None:
                    service["group"] = args.user

            if args.group is not None:
                service["group"] = args.group
            
            tpl=open("ikea-tradfri.service.tpl").read()
            src = Template(tpl)
            result=src.substitute(service)
            try:
                with open('ikea-tradfri.service', 'w+') as f:
                    f.write(result)

                print("ikea-tradfri.service created:")
                show_service_file()
            except PermissionError:
                print("Error: Could not write ikea-tradfri.service")

    elif args.service_command == "show":
        show_service_file()
