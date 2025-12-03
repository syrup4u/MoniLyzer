#!/bin/bash

# configure parameters
PID="$1" 
INTERVAL=1   # interval between samples (seconds)
DURATION=60  # total running time (seconds)
OUTPUT_FILE="resource_usage_precise_${PID}.csv"

# --- Check parameters ---
if [ -z "$PID" ]; then
    echo "Usage: $0 <PID>" >&2
    exit 1
fi

# --- Get system Jiffies/second (for Python calculation) ---
# This line is very important, write it to the file header for the Python script to read
CLK_TCK=$(getconf CLK_TCK)

# --- Write CSV header ---
# Header includes CLK_TCK and collected metrics
echo "#CLK_TCK:$CLK_TCK" > "$OUTPUT_FILE"
echo "Timestamp,CPU_Jiffies_Cumulative,RSS_Pages" >> "$OUTPUT_FILE"

echo "Starting high-precision monitoring of process $PID (CLK_TCK=$CLK_TCK)... Data will be written to $OUTPUT_FILE"

# --- Loop to collect data ---
END_TIME=$(( $(date +%s) + $DURATION ))

while [ $(date +%s) -lt $END_TIME ]; do
    
    # Core modification: directly read /proc/[PID]/stat
    # Extract utime (14) and stime (15) fields for CPU Jiffies
    # Extract rss (24) field for Memory Pages
    
    # Attempt to read /proc/PID/stat
    STAT_DATA=$(cat /proc/$PID/stat 2>/dev/null)
    
    if [ -z "$STAT_DATA" ]; then
        echo "Process $PID has exited or /proc/$PID/stat is not readable. Stopping monitoring."
        break
    fi
    
    # Use awk to extract and calculate total Jiffies from stat file
    JIFFIES_TOTAL=$(echo "$STAT_DATA" | awk '{print $14 + $15}')
    RSS_PAGES=$(echo "$STAT_DATA" | awk '{print $24}')
    
    TIMESTAMP=$(date +%s)
    echo "$TIMESTAMP,$JIFFIES_TOTAL,$RSS_PAGES" >> "$OUTPUT_FILE"
    
    sleep $INTERVAL
done

echo "Data collection completed."