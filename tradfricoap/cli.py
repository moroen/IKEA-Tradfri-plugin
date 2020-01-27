import argparse


def get_args():

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    parser.add_argument("--debug", action="store_true")

    subparsers.add_parser("test")

    parser_list = subparsers.add_parser("list")
    parser_list.add_argument("--groups", action="store_true")

    parser_config_gateway = subparsers.add_parser("config")
    parser_config_gateway.add_argument("IP")
    parser_config_gateway.add_argument("KEY")

    parser_config_api = subparsers.add_parser("api")
    parser_config_api.add_argument("API", choices=["pycoap", "coapcmd"])
    
    return parser.parse_args()