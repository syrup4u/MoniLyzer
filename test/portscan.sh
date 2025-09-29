#!/usr/bin/env bash
# portscan.sh
# test script for port scanning (only TCP)
# Usage: ./portscan.sh <host> <start_port> <end_port>

set -u

if [[ $# -lt 3 ]]; then
  echo "Usage: $0 <host> <start_port> <end_port>"
  exit 1
fi

HOST=$1
START_PORT=$2
END_PORT=$3

if ! [[ $START_PORT =~ ^[0-9]+$ ]] || ! [[ $END_PORT =~ ^[0-9]+$ ]]; then
  echo "Ports must be integers."
  exit 1
fi

if (( START_PORT < 1 || END_PORT > 65535 || START_PORT > END_PORT )); then
  echo "Invalid port range. Valid ports: 1-65535"
  exit 1
fi

echo "Port scanning $HOST from port $START_PORT to $END_PORT..."
for ((port=START_PORT; port<=END_PORT; port++)); do
  if timeout 1 bash -c ">/dev/tcp/${HOST}/${port}" 2>/dev/null; then
    echo "Port $port: OPEN"
  fi
done
