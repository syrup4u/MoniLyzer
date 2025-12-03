#!/bin/sh

PYTHON=${PYTHON:-python}

echo "Use Python executable $(which $PYTHON)"

sudo "$PYTHON" monilyzer.py