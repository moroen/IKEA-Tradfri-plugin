#!/usr/bin/env python3

__version__ = "0.7.1"

# Standard library
import json, logging, time, sys, site, argparse, os

# Need to set config before import from module
from tradfricoap.config import get_config, host_config
CONFIGFILE = "{}/config.json".format(os.path.dirname(os.path.realpath(__file__)))
CONF = get_config(CONFIGFILE)

# Module
from tradfricoap.config import get_config, host_config
from tradfricoap.device import get_devices
from tradfricoap import constants
from tradfricoap import colors, cli
from tradfricoap.errors import IllegalMethodError, UriNotFoundError, HandshakeError, WriteTimeoutError, ReadTimeoutError

site.main()

if __name__ == "__main__":
    args = cli.get_args()
    if args.command == "api":
        config = host_config(CONFIGFILE)
        config.set_config_item("api", args.API)
        config.save()
        exit()


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)

    args = cli.get_args()

    if args.debug:
        set_debug_level(1)

    if args.command is not None:

        if args.command == "api":
            config = host_config(CONFIGFILE)
            config.set_config_item("api", args.API)
            config.save()

        if args.command == "test":

            # dev = device(65538)

            dev = device(65560)
            print(dev.State)
            dev.Level = 10
            print(dev.State)

            exit()

            try:
                dev = device(158578)
            except UriNotFoundError:
                logging.error("Uri not found")
                exit()

            print(
                dev.Description, dev.State, dev.Level, dev.Color_space, dev.Color_level
            )

            dev.State = 1 if dev.State == 0 else 0

            dev.Level = 250 if dev.Level < 100 else 10

            # dev.Color_level = 30 if dev.Color_level == 10 else 10

        if args.command == "list":
            try:
                devices = get_devices(args.groups)
            except HandshakeError:
                print("Connection timed out")
                exit()

            if devices is None:
                logging.critical("Unable to get list of devices")
            else:
                lights = []
                plugs = []
                blinds = []
                groups = []
                others = []

                for dev in devices:
                    if dev.Type == "Light":
                        lights.append(dev.Description)
                    elif dev.Type == "Plug":
                        plugs.append(dev.Description)
                    elif dev.Type == "Blind":
                        blinds.append(dev.Description)
                    elif dev.Type == "Group":
                        groups.append(dev.Description)
                    else:
                        others.append(dev.Description)

                if len(lights):
                    print("Lights:")
                    print("\n".join(lights))

                if len(plugs):
                    print("\nPlugs:")
                    print("\n".join(plugs))

                if len(blinds):
                    print("\nBlinds:")
                    print("\n".join(blinds))

                if len(groups):
                    print("\nGroups:")
                    print("\n".join(groups))

                if len(others):
                    print("\nOthers:")
                    print("\n".join(others))

        elif args.command == "config":
            try:
                create_ident(args.IP, args.KEY, CONFIGFILE)
            except HandshakeError:
                logging.error("Connection timed out")
