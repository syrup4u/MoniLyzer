#!/bin/sh

# MONITOR="pmacct"
# MONITOR="softflowd"
MONITOR="journalctl"
ANALYZER="simple_journal"

curl "localhost:12345/opt?monitor=$MONITOR&hours=1&analyzer=$ANALYZER"