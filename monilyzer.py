from api.monitor import *
from api.analyzer import AnalyzerManager
from processor import Processor

import configparser

CONFIG_PATH = "monilyzer.ini"

"""
1. Initializes all the modules we need.
2. Register the modules if needed.
3. Run the processor.
"""
if __name__ == "__main__":
    # load configurations
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)

    # initializes main modules
    monitor_manager = MonitorManager()
    analyzer_manager = AnalyzerManager()
    processor = Processor(monitor_manager, analyzer_manager, dict(config["server"]))

    # initializes and registers monitors
    pmacct_config = {
        "data_dir": config["pmacct"]["data_dir"],
        "ip": config["nic"]["ip"],
    }
    monitor_pmacct = MonitorPmacct(pmacct_config)
    monitor_manager.register_monitor("pmacct", monitor_pmacct)

    # TODO: initializes analyzers

    # run processor
    processor.run()
