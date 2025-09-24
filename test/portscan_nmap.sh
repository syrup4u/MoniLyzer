#!/usr/bin/env bash
# portscan_nmap.sh
# test script for port scanning using nmap (mainly TCP)
# Usage: ./portscan_nmap.sh <host> [ports]
# Default ports = 1-65535

HOST=${1:-}
PORTS=${2:-1-65535}

if [[ -z "$HOST" ]]; then
  echo "Usage: $0 <host> [ports]"
  exit 1
fi

nmap -sT -p "$PORTS" "$HOST"
