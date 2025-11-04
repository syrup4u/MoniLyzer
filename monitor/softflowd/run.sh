#!/bin/sh

NIC_NAME="enp6s0f1"
EXPORT_PORT="2055"
EXPORT="127.0.0.1:$EXPORT_PORT"
DATA_DIR=$(pwd)/data

mkdir -p $DATA_DIR
sudo softflowd -i $NIC_NAME -n $EXPORT -v 9
sudo nfcapd -D -w -l $DATA_DIR -p $EXPORT_PORT -t 60
