"""
Monitor module
"""

from driver.pmacct import DriverPmacct

"""
- It is possible to implement concurrency by adding lock mechanism.
  But that's not necessary at this stage.
  I.e., we can assume that only one thread is running for each monitor call.
"""
class MonitorManager:
    def __init__(self):
        self.monitors = {}

    def register_monitor(self, name, monitor):
        self.monitors[name] = monitor

class MonitorPmacct:
    def __init__(self, config):
        self.data = []
        self.load_config(config)

    def load_config(self, config):
        self.config = config
        self.driver = DriverPmacct(data_dir=self.config["data_dir"])
        self.ip = self.config["ip"]

    def preprocess(self, options: dict, data_filter: dict = {}):
        # parameters
        hours = options.get("hours", 1)

        # fetch data from pmacct
        range = self.driver.get_range_from_now(hours)
        files = self.driver.get_files(range[0], range[1], range[2], range[3])
        all_data = []
        for fp in files:
            data = self.driver.read_data_from_file(fp)
            all_data.extend(data)
        
        # filter
        tcp_only = "tcp_only" in data_filter
        traffic_in_only = "traffic_in_only" in data_filter
        for record in all_data:
            if tcp_only and record.get("ip_proto") != "tcp":
                continue
            if traffic_in_only and record.get("ip_src") == self.ip:
                continue
            self.data.append(record)

def get_default_filter():
    return {
        "tcp_only": None,
        "traffic_in_only": None,
    }

if __name__ == "__main__":
    config = {"data_dir": "monitor/pmacct/data", "ip": "10.10.1.1"}
    monitor = MonitorPmacct(config)
    options = {"hours": 16800}
    monitor.preprocess(options, data_filter=get_default_filter())
    print(len(monitor.data))
    print(monitor.data[:2])
