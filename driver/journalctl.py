import subprocess
import json

class DriverJournalctl:
    def __init__(self, *, listen_services):
        self.listen_services = listen_services # can be sshd, mysql, postgresql

    def get_logs(self, hours=1):
        if hours == 1:
            time_setting = f"{hours} hour ago"
        else:
            time_setting = f"{hours} hours ago"
        cmd = ["sudo", "journalctl", "--since", time_setting, "-o", "json"]

        for s in self.listen_services:
            if s.endswith('.service'):
                cmd.extend(['-u', s])
            else:
                cmd.append(f"_COMM={s}")
        result = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True)

        all_logs = []
        for line in result.stdout:
            line = line.strip()
            if line:
                try:
                    log_entry = json.loads(line)
                    all_logs.append(log_entry)
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON: {e} in line: {line}")
        
        return all_logs


if __name__ == "__main__":
    listen_services = ["sshd"]
    dj = DriverJournalctl(listen_services=listen_services)
    logs = dj.get_logs(hours=1)
    print(len(logs))
