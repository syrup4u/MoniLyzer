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

    """
    Return Message object
    """
    def fetch_data(self, options: dict):
        pass

class MonitorPmacct:
    def __init__(self, config):
        self.data = []
        self.load_config(config)

    def load_config(self, config):
        self.config = config
        self.driver = DriverPmacct(data_dir=self.config["data_dir"])

    def preprocess(self, options: dict):
        # parameters
        hours = options.get("hours", 1)

        # fetch data from pmacct
        range = self.driver.get_range_from_now(hours)
        files = self.driver.get_files(range[0], range[1], range[2], range[3])
        all_data = []
        for fp in files:
            data = self.driver.read_data_from_file(fp)
            all_data.extend(data)
        
        # filter and aggregate data
        tcp_only = True # can be configured
        for record in all_data:
            if tcp_only and record.get("ip_proto") != "tcp":
                continue
            # TODO: aggregation
            self.data.append(record)

    """
    wrap the data in a Message object and return it
    """
    def process(self, options: dict):
        pass

if __name__ == "__main__":
    config = {"data_dir": "monitor/pmacct/data"}
    monitor = MonitorPmacct(config)
    options = {"hours": 168}
    monitor.preprocess(options)
    print(len(monitor.data))
    print(monitor.data[:2])
