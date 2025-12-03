# Monitors

1. pmacct - traffic
2. softflowd - traffic
3. journalctl - ssh

## Run the monitor

In each directory, you can find the followings: (except for `journalctl` because it is a system service)

1. `requirements.sh`: install the service.
2. `run.sh`: run the service.
3. `crontab.sh`: create a script for cleaning obsolete data files. Can add a task to crontab if wanted.
4. `stop.sh`: to stop the service.

`sudo` are required for most of the steps.

You only need to start the monitor service you want to include.

**Make sure you have run `sudo apt update`**

### Pmacct

1. `bash requirements.sh`
2. modify the configuration file `pmacctd.conf`, change the `interface` to the listen NIC (e.g., eth[x], enp[xxxxx]), by `ip addr`.
3. `bash run.sh`
4. (if needed) to stop, `bash stop.sh`
5. (if needed) to clean, `bash clean_outdated_data.sh`, which is created by `bash crontab.sh`. Or comment the last line in `crontab.sh` to enable the regular task of cleaning.

### softflowd

1. `bash requirements.sh`
2. modify the `NIC_NAME` in `run.sh` to the listen NIC, as explained above in Pmacct.
3. `bash run.sh`
4. (if needed) to stop, `bash stop.sh`
5. (if needed) to clean, `bash clean_outdated_data.sh`, which is created by `bash crontab.sh`. Or comment the last line in `crontab.sh` to enable the regular task of cleaning.

### journalctl

System service, no need to run manually.
