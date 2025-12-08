"""
Monitor module
"""

from driver.pmacct import DriverPmacct
from driver.softflowd import DriverSoftflowd
from driver.journalctl import DriverJournalctl
from transport.message import JournalMessage, NetworkPacketMessage

"""
- It is possible to implement concurrency by adding lock mechanism.
  But that's not necessary at this stage.
  I.e., we can assume that only one thread is running for each monitor call.
"""
class MonitorManager:
    def __init__(self):
        self.monitors = {}
        self.support = []

    def register_monitor(self, name, monitor):
        self.monitors[name] = monitor
        self.support.append(name)


class MonitorPmacct:
    def __init__(self, config):
        self.data = []
        self.load_config(config)

    def load_config(self, config):
        self.config = config
        self.driver = DriverPmacct(data_dir=self.config["data_dir"])
        self.ip = self.config["ip"]

    def preprocess(self, options: dict, data_filter: set = set()):
        """
        record structure:
        {ip_src, ip_dst, port_src, port_dst, ip_proto, packets, bytes, timestamp_start}
        """

        self.data = []

        # parameters
        hours = options.get("hours", 1)

        # fetch data from pmacct
        range_ = self.driver.get_range_from_now(hours)
        files = self.driver.get_files(range_[0], range_[1], range_[2], range_[3])
        all_data = []
        for fp in files:
            data = self.driver.read_data_from_file(fp)
            all_data.extend(data)
        
        # filter
        tcp_only = "tcp_only" in data_filter
        traffic_in_only = "traffic_in_only" in data_filter
        aggregation = {}
        for record in all_data:
            if tcp_only and record.get("ip_proto") != "tcp":
                continue
            if traffic_in_only and record.get("ip_src") == self.ip:
                continue
            aggregation_key = record.get("ip_src", None)
            if aggregation_key:
                if aggregation_key not in aggregation:
                    aggregation[aggregation_key] = [0, []] # packets, ports
                aggregation[aggregation_key][0] += record.get("packets", 0)
                aggregation[aggregation_key][1].append(record.get("port_dst"))
        
        for ip_src, (packets, ports) in aggregation.items():
            self.data.append({
                "ip_src": ip_src,
                "total_packets": packets,
                # "number_of_unique_access_ports (from 1-65536)": len(set(ports))
                "dst_ports": list(set(ports))
            })

    def to_message(self, options: dict):
        return NetworkPacketMessage({"packets_summary": self.data, "collected in hours": options.get("hours", 1)})


class MonitorSoftflowd:
    def __init__(self, config):
        self.data = []
        self.load_config(config)

    def load_config(self, config):
        self.driver = DriverSoftflowd(data_dir=config["data_dir"])
        self.ip = config["ip"]

    def preprocess(self, options: dict, data_filter: set = set()):
        """
        record structure:
        {t_first, src4_addr, dst4_addr, src_port, dst_port, in_packets, in_bytes}
        """

        self.data = []

        # parameters
        hours = options.get("hours", 1)
        
        # fetch data from softflowd
        range_ = self.driver.get_range_from_now(hours)
        files = self.driver.get_files(range_[0], range_[1], range_[2], range_[3])
        all_data = []
        for fp in files:
            data = self.driver.read_data_from_file(fp)
            all_data.extend(data)
        
        # filter
        traffic_in_only = "traffic_in_only" in data_filter
        aggregation = {}
        for record in all_data:
            if traffic_in_only and record.get("src4_addr") == self.ip:
                continue
            aggregation_key = record.get("src4_addr", None)
            if aggregation_key:
                if aggregation_key not in aggregation:
                    aggregation[aggregation_key] = [0, []] # packets, ports
                aggregation[aggregation_key][0] += record.get("in_packets", 0)
                aggregation[aggregation_key][1].append(record.get("dst_port"))
        
        for ip_src, (packets, ports) in aggregation.items():
            self.data.append({
                "ip_src": ip_src,
                "total_packets": packets,
                "dst_ports": list(set(ports))
            })

    def to_message(self, options: dict):
        return NetworkPacketMessage({"packets_summary": self.data, "collected in hours": options.get("hours", 1)})


class MonitorJournalctl:
    def __init__(self, config):
        self.data = []
        self.load_config(config)

    def load_config(self, config):
        services_str = config["services"]
        services = services_str.split(",")
        self.driver = DriverJournalctl(listen_services=services)

    def preprocess(self, options: dict, data_filter: set = set()):
        self.data = []
        # parameters
        hours = options.get("hours", 1)
        data = self.driver.get_logs(hours)

        # filter
        for record in data:
            f_items = {}
            for field in data_filter:
                f_items[field] = record[field]
            self.data.append(f_items)

    def to_message(self, options: dict):
        return JournalMessage(self.data)

def get_default_filter():
    return {
        "pmacct": {
            "tcp_only",
            "traffic_in_only"
        },
        "journalctl": {
            "MESSAGE",
            "_SOURCE_REALTIME_TIMESTAMP",
        },
        "softflowd": {
            "traffic_in_only"
        }
    }


if __name__ == "__main__":
    config = {"data_dir": "monitor/pmacct/data", "ip": "10.10.1.2"}
    monitor = MonitorPmacct(config)
    options = {"hours": 1}
    monitor.preprocess(options, data_filter=get_default_filter()['pmacct'])
    print(len(monitor.data))
    print(monitor.to_message(options).json_obj)
