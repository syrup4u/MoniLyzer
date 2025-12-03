# MoniLyzer

MoniLyzer: A Middleware Between Monitors and Attack Analyzer

## Environment

- Linux (Ubuntu is preferred, others would need to modify some `requirements.sh` scripts in monitors)
- Root Privilege (for monitors)
- Python 3.8+

## Before running the MoniLyzer

1. Run the monitors you want to include in MoniLyzer, refer to [README](./monitor/README.md).
2. Run the analyzers you want to include in MoniLyzer.
3. Install all dependencies in Python by `pip install -r requirements`, you can use virtual environment to do this, see below.

## How to run the MoniLyzer

Virtual environment:

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Configuration: `monilyzer.ini`, modify the `ip` under `[nic]`, set it to your local ip (later the MoniLyzer will filter out the outbound packets).

Run the MoniLyzer: `sudo python monilyzer.py` or `bash run.sh`.

## How to use

Example: Recent 1 hour traffic

`curl "<host>:<port>/opt?monitor=pmacct&hours=1"`

Or the script `test.sh`.

## Todo

1. Monitor Deployment
2. Analyzer Deployment
3. Basic API and main process in Processor
4. attack tests
5. Configuration (auto generation)
