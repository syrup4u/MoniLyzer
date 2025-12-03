#!/bin/bash

pid_pmacct_core=733460
pid_pmacct_output=733461

pid_softflowd=731541
pid_nfcapd=731546

pid_MoniLyzer=735598

# echo "Monitoring pmacct process $pid_pmacct_core ..."
# bash ./monitor_precise.sh $pid_pmacct_core &
# echo "Monitoring pmacct process $pid_pmacct_output ..."
# bash ./monitor_precise.sh $pid_pmacct_output &
# echo "Monitoring softflowd process $pid_softflowd ..."
# bash ./monitor_precise.sh $pid_softflowd &
# echo "Monitoring nfcapd process $pid_nfcapd ..."
# bash ./monitor_precise.sh $pid_nfcapd &
# echo "Monitoring nfcapd process $pid_MoniLyzer ..."
# bash ./monitor_precise.sh $pid_MoniLyzer &

python plot_precise.py "resource_usage_precise_$pid_pmacct_core.csv"
python plot_precise.py "resource_usage_precise_$pid_pmacct_output.csv"
python plot_precise.py "resource_usage_precise_$pid_softflowd.csv"
python plot_precise.py "resource_usage_precise_$pid_nfcapd.csv"
# python plot_precise.py "resource_usage_precise_$pid_MoniLyzer.csv"
