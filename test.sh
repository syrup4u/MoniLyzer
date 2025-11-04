#!/bin/sh

# MONITOR="pmacct"
MONITOR="journalctl"

curl "localhost:8080/opt?monitor=$MONITOR&hours=1"