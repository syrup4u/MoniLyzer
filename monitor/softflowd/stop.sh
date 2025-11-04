#!/bin/sh

TARGET1="softflowd"
TARGET2="nfcapd"

ps -ef | grep $TARGET1 | awk '{print $2}' | xargs sudo kill
ps -ef | grep $TARGET2 | awk '{print $2}' | xargs sudo kill
