import logging, os, json

logger = logging.getLogger(__name__)

global_conf = None

class host_config(object):
    _confObj = {}

    _configFile = None
    _configDir = None

    def __init__(self, configFile = None):

        if configFile == None:
            logging.critical("Configfile not defined...")
            exit()
        else:
            self._configFile = configFile
        
        self._confObj.update(
            Gateway=None,
            Identity=None,
            Passkey=None,
            Transition_time=10,
            Verbosity=0,
            Api="Pycoap"
        )
        self.load()

    def load(self):

        if os.path.isfile(self._configFile):
            with open(self._configFile) as json_data_file:
                loaded_conf = json.load(json_data_file)
                for key, value in loaded_conf.items():
                    self._confObj[key] = value
        else:
            self.save()

    def save(self):
        self._configDir = os.path.dirname(self._configFile)
        if not os.path.exists(self._configDir):
            os.makedirs(self._configDir)

        with open(self._configFile, "w") as outfile:
            json.dump(self._confObj, outfile)

        logging.info("Config set")

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


def get_config(configfile = None):
    global global_conf
    if global_conf is None:
        logger.info("Loading config")
        global_conf = host_config(configfile)

    return global_conf.configuation
