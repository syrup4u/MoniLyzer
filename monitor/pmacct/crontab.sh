#!/bin/bash

SCRIPT_PATH=$(pwd)"/clean_outdated_data.sh"
TARGET_DIR=$(pwd)"/data"

cat <<EOF > $SCRIPT_PATH
find $TARGET_DIR -type f -mmin +2880 -delete # two days
EOF
chmod +x $SCRIPT_PATH

( crontab -l 2>/dev/null; echo "0 3 * * * $SCRIPT_PATH" ) | crontab -