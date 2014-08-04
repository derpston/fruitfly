# stdlib
import os
import imp
import glob
import time
import yaml
import logging.handlers
import inspect

class FruitFly(object):
    def __init__(self, basedir = None, debug = False, logdestination = "stderr"):
        # Find basedir
        self._basedir = basedir or os.path.dirname(os.path.abspath(inspect.getfile(inspect.stack()[-1][0])))

        # Load config
        configpath = os.path.join(self._basedir, "fruitfly.yaml")
        self._config = yaml.load(open(configpath))
        

         # Set up logging
        rootlogger = logging.getLogger()
        if self._config.get("logging", {}).get("level", "debug") == "debug":
            rootlogger.setLevel(logging.DEBUG)
        else:
            rootlogger.setLevel(logging.INFO)
            
        if self._config.get("logging", {}).get("destination", "syslog") == "debug":
            handler = logging.handlers.SysLogHandler(address = '/dev/log')
        else:
            # Writes to stderr.
            handler = logging.StreamHandler()

        handler.setFormatter(logging.Formatter('fruitfly[%(process)d] %(levelname)s %(name)s %(message)s'))
        rootlogger.addHandler(handler)
        self._logger = logging.getLogger('fruitfly')
        
        self._logger.info("Using %s to find config and modules.", self._basedir)
        self._logger.info("Loaded config from %s", configpath)
       
        # Load modules
        self._modules = {}
        self.load_modules()


    def load_modules(self):
        # Load all the modules.
        module_search_path = os.path.join(self._basedir, "mod_*.py")
        self._logger.info("Loading modules from %s", module_search_path)

        for (modname, modconfig) in self._config['modules'].items():
            modpath = os.path.join(self._basedir, "mod_%s.py" % modname)
            self._logger.debug("Loading module %s from %s with config %s", modname, modpath, repr(modconfig))

            try:
                mod = imp.load_source(modname, modpath)
            except IOError as ex:
                self._logger.error("Config specifies module '%s', but failed to load that module. (%s)", modname, repr(ex))
                continue

            # Create an instance of the module and store it.
            self._modules[modname] = getattr(mod, modname)(self, modname, modconfig)

            self._logger.info("Enabled module %s", modname)

    def send_event(self, event, payload):
        self._logger.debug("Distributing event %s '%s'", event, repr(payload))
        for (modname, modinst) in self._modules.items():
            modinst._observe_event(event, payload)

    def run(self):
        # Blocks forever.
        while True:
            time.sleep(1)

