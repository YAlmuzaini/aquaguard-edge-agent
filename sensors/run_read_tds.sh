#!/usr/bin/env bash
# Run TDS reader using the project virtual environment.
cd "$(dirname "$0")/.."
source bin/activate
exec python sensors/read_tds.py
