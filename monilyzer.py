from api.monitor import MonitorManager, MonitorPmacct, MonitorJournalctl, MonitorSoftflowd
from api.analyzer import AnalyzerManager
from analyzer import SnortAnalyzer, LLMAnalyzer, SimpleJournalAnalyzer
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

    softflowd_config = {
        "data_dir": config["softflowd"]["data_dir"],
        "ip": config["nic"]["ip"],
    }
    monitor_softflowd = MonitorSoftflowd(softflowd_config)
    monitor_manager.register_monitor("softflowd", monitor_softflowd)

    journalctl_config = {
        "services": config["journalctl"]["services"]
    }
    monitor_journalctl = MonitorJournalctl(journalctl_config)
    monitor_manager.register_monitor("journalctl", monitor_journalctl)

    analyzer_snort = SnortAnalyzer()
    analyzer_llm = LLMAnalyzer()
    analyzer_simple_journal = SimpleJournalAnalyzer()
    analyzer_manager.register_analyzer("snort", analyzer_snort)
    analyzer_manager.register_analyzer("llm", analyzer_llm)
    analyzer_manager.register_analyzer("simple_journal", analyzer_simple_journal)

    # run processor
    processor.run()
