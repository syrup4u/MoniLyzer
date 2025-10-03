from api.monitor import *

import configparser

CONFIG_PATH = "monilyzer.ini"

"""
1. Initializes all the modules we need.
2. Register the modules if needed.
3. Run the processor.
"""
if __name__ == "__main__":
    # TODO: load configurations
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)

    # initializes main modules
    monitor_manager = MonitorManager()

    # initializes and registers monitors
    monitor_pmacct = MonitorPmacct()
    monitor_manager.register_monitor("pmacct", monitor_pmacct)

    # TODO: initializes analyzers
