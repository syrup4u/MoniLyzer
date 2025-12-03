#!/bin/sh

# MONITOR="pmacct"
# MONITOR="softflowd"
MONITOR="journalctl"

curl "localhost:12345/opt?monitor=$MONITOR&hours=1"