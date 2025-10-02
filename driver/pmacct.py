import json
from datetime import datetime, timedelta

class DriverPmacct:
    def __init__(self, *, data_dir: str):
        self._data_dir = data_dir

    """
    read records from a pmacct json file
    key fields of each record:
    - ip_src
    - ip_dst
    - port_src
    - port_dst
    - ip_proto
    - packets
    - bytes
    - timestamp_start
    """
    def read_data_from_file(self, fp) -> list[dict]:
        data = []
        with open(fp, 'r') as f:
            for line in f:
                try:
                    record = json.loads(line)
                    # filters out some fields
                    record.pop("event_type", None)
                    record.pop("timestamp_end", None)
                    data.append(record)
                except json.JSONDecodeError:
                    continue
        return data
    
    def get_files(self, start_date, start_time, end_date, end_time):
        prefix = "traffic_"
        files = []
        # find all files in the range
        # first get all files in the data dir
        import os
        all_files = os.listdir(self._data_dir)
        for file in all_files:
            if file.startswith(prefix) and file.endswith(".json"):
                # extract date and time
                parts = file[len(prefix):-5].split('_')
                if len(parts) != 2:
                    continue
                file_date, file_time = parts
                if (file_date > start_date or (file_date == start_date and file_time >= start_time)) and \
                   (file_date < end_date or (file_date == end_date and file_time <= end_time)):
                    files.append(os.path.join(self._data_dir, file))
        files.sort()
        return files

    def get_range_from_now(self, hours=1):
        end = datetime.now()
        start = end - timedelta(hours=hours)

        start_date = start.strftime("%Y%m%d")
        start_time = start.strftime("%H%M")
        end_date = end.strftime("%Y%m%d")
        end_time = end.strftime("%H%M")

        return [start_date, start_time, end_date, end_time]


if __name__ == "__main__":
    driver = DriverPmacct(data_dir="./monitor/pmacct/data")
    files = driver.get_files("20250929", "1019", "20250929", "1030")
    for fp in files:
        print(f"Reading file: {fp}")
        records = driver.read_data_from_file(fp)
        print(f"Read {len(records)} records")
        print(records[:2])
