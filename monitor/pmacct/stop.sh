#!/bin/sh

TARGET1="pmacctd"

ps -ef | grep $TARGET1 | awk '{print $2}' | xargs sudo kill
