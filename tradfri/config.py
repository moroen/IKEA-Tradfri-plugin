import appdirs, logging, os, json

logger = logging.getLogger(__name__)

CONFIGFILE = "{0}/gateway.json".format(appdirs.user_config_dir(appname="tradfri"))

global_conf = None


class host_config(object):
    _confObj = {}

    def __init__(self):
        self._confObj.update(
            Server_type="Both",
            Gateway=None,
            Server_ip="127.0.0.1",
            Tcp_port=1234,
            Http_port=8085,
            Identity=None,
            Passkey=None,
            Transition_time=10,
            Verbosity=0,
        )
        self.load()

    def load(self):
        if os.path.isfile(CONFIGFILE):
            with open(CONFIGFILE) as json_data_file:
                loaded_conf = json.load(json_data_file)
                for key, value in loaded_conf.items():
                    self._confObj[key] = value
        else:
            self.save()

    def save(self):
        CONFDIR = appdirs.user_config_dir(appname="tradfri")
        if not os.path.exists(CONFDIR):
            os.makedirs(CONFDIR)

        with open(CONFIGFILE, "w") as outfile:
            json.dump(self._confObj, outfile)

        logging.info("Config created")

    def set_config_items(self, **kwargs):
        for key, value in kwargs.items():
            self._confObj[key] = value

    def set_config_item(self, key, value):
        try:
            self._confObj[key.capitalize().replace("-", "_")] = value.capitalize()
        except AttributeError:
            self._confObj[key.capitalize().replace("-", "_")] = value

    @property
    def configuation(self):
        return self._confObj

    @property
    def gateway(self):
        return self._confObj["Gateway"]


def get_config():
    global global_conf
    if global_conf is None:
        logger.info("Loading config")
        global_conf = host_config()

    return global_conf.configuation
