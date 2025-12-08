#!/bin/sh

PYTHON=${PYTHON:-python}
API_KEY=${API_KEY:-"default_api_key"}

echo "Use Python executable $(which $PYTHON)"
echo "Using OpenAI API Key: $API_KEY"

# sudo "$PYTHON" monilyzer.py
OPENAI_API_KEY=$API_KEY $PYTHON monilyzer.py