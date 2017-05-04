#!/usr/bin/env python3

import sys
import pytradfri

import argparse
import configparser
import os.path

def SaveConfig(args):
    config["Gateway"] = {"ip": args.gateway, "key": args.key}
    with open ('tradfri.ini', "w") as configfile:
        config.write(configfile)


config = configparser.ConfigParser()

config["Gateway"] = {"ip": "UNDEF", "key": "UNDEF"}

if os.path.exists("tradfri.ini"):
    config.read('tradfri.ini')

whiteTemps = {"cold":"f5faf6", "normal":"f1e0b5", "warm":"efd275"}

parser = argparse.ArgumentParser()
parser.add_argument("--gateway", "-g")
parser.add_argument("--key")
parser.add_argument("id", nargs='?', default=0)

subparsers = parser.add_subparsers(dest="command")
subparsers.required = True

subparsers.add_parser("on")
subparsers.add_parser("off")
subparsers.add_parser("list")
subparsers.add_parser("test")

parser_level = subparsers.add_parser("level")
parser_level.add_argument("value")

parser_colortemp = subparsers.add_parser("whitetemp")
parser_colortemp.add_argument("value", choices=['cold', 'normal', 'warm'])

args = parser.parse_args()

if args.gateway != None:
    config["Gateway"]["ip"] = args.gateway
    SaveConfig(args)

if args.key != None:
    config["Gateway"]["key"] = args.key
    SaveConfig(args)

if config["Gateway"]["ip"]=="UNDEF":
    print("Gateway not set. Use --gateway to specify")
    quit()

if config["Gateway"]["key"]=="UNDEF":
    print("Key not set. Use --key to specify")
    quit()

api = pytradfri.coap_cli.api_factory(config["Gateway"]["ip"], config["Gateway"]["key"])
gateway = pytradfri.gateway.Gateway(api)

device = gateway.get_device(int(args.id))

if args.command == "on":
    device.light_control.set_state(True)

if args.command == "off":
    device.light_control.set_state(False)

if args.command == "level":
    device.light_control.set_dimmer(int(args.value))

if args.command == "whitetemp":
    device.light_control.set_hex_color(whiteTemps[args.value])

if args.command == "list":
    devicesList = gateway.get_devices()
    for aDevice in devicesList:
        print(aDevice)

if args.command == "test":
    for aDevice in gateway.get_devices():
        print (aDevice.id)
        print (aDevice.name)
        print (aDevice.device_info.manufacturer)
