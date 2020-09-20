from .config import get_config

CONF = get_config()

if CONF["Api"] == "Pycoap":
    from .pycoap_api import create_ident
    from .pycoap_api import close_connection

if CONF["Api"] == "Coapcmd":
    from .coapcmd_api import create_ident
    from .coapcmd_api import close_connection


