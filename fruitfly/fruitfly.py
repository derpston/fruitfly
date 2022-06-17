# stdlib
import os
import imp
import glob
import time
import yaml
import logging.handlers
import inspect
import module

class FruitFly(object):
    def __init__(self, basedir = None, debug = False, logdestination = "stderr"):
        # Find basedir
        self._basedir = basedir or os.path.dirname(os.path.abspath(inspect.getfile(inspect.stack()[-1][0])))

        # Load config
        configpath = os.path.join(self._basedir, "fruitfly.yaml")
        self._config = yaml.safe_load(open(configpath))
        

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

        try:
            # The user provided a dict of modules.
            all_module_config = [{key: value} for key, value in self._config['modules'].items()]
        except AttributeError:
            # The user provided a list of modules.
            all_module_config = self._config['modules']

        for module_config in all_module_config:
            # Use only the first key in this dict. The key is used to specify
            # the module name.
            modname, modconfig = module_config.items()[0]

            # If this is not the first instance of this module, choose
            # a similar but unique name and use that instead.
            modname_internal = modname
            index = 0
            while modname_internal in self._modules:
                index += 1
                modname_internal = "%s-%d" % (modname_internal, index)

            # Set this hacky global so the 'module' module knows what
            # the name of the eventually-loaded module is going to be
            # so it can be added to the scheduler and event handlers
            # correctly. Without this, trying to load two copies of
            # one module breaks because all events go to the second
            # instance of the same module loaded.
            module.current_modname = modname_internal

            modpath = os.path.join(self._basedir, "mod_%s.py" % modname)
            self._logger.debug("Loading module %s from %s with config %s", modname, modpath, repr(modconfig))

            # Load a copy of this module.
            try:
                mod = imp.load_source(modname, modpath)
            except IOError as ex:
                self._logger.error("Config specifies module '%s', but failed to load that module. (%s)", modname, repr(ex))
                continue

            # Create an instance of the module and store it.
            self._modules[modname_internal] = getattr(mod, modname)(self, modname_internal, modconfig)

            self._logger.info("Enabled module %s", modname_internal)

    def send_event(self, event, payload):
        self._logger.debug("Distributing event %s '%s'", event, repr(payload))
        for (modname, modinst) in self._modules.items():
            modinst._observe_event(event, payload)

    def run(self):
        # Blocks forever.
        while True:
            time.sleep(1)

