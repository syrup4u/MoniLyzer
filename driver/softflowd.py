import subprocess
import json
from datetime import datetime, timedelta
import re

class DriverSoftflowd:
    def __init__(self, *, data_dir: str):
        self._data_dir = data_dir

    def read_data_from_file(self, fp) -> list[dict]:
        data = []
        cmd = ["nfdump", "-r", fp, "-o", "json"]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return data
        try:
            records = json.loads(result.stdout)
            for record in records:
                # filters out some fields
                keep_fields = ["t_first", "src4_addr", "dst4_addr", "src_port", "dst_port", "in_packets", "in_bytes"]
                new_record = {k: v for k, v in record.items() if k in keep_fields}
                data.append(new_record)
        except json.JSONDecodeError:
            pass

        return data

    def get_files(self, start_date, start_time, end_date, end_time):
        prefix = "nfcapd"
        files = []
        # find all files in the range
        # first get all files in the data dir
        import os
        all_files = os.listdir(self._data_dir)
        for file in all_files:
            # example: nfcapd.202511031536
            if re.match(r"nfcapd\.\d{12}", file):
                # extract date and time
                suffix = file[len(prefix)+1:]
                # compare the suffix
                start = start_date + start_time
                end = end_date + end_time
                if suffix >= start and suffix <= end:
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
    driver = DriverSoftflowd(data_dir="./monitor/softflowd/data")
    range_ = driver.get_range_from_now(180)
    files = driver.get_files(range_[0], range_[1], range_[2], range_[3])
    cnt = 0
    for fp in files:
        records = driver.read_data_from_file(fp)
        cnt += len(records)
    print(f"Total records found: {cnt}")
