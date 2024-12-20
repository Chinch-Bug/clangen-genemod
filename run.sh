#!/usr/bin/env bash

cd "$(dirname "$0")" # script location
poetry install --no-root
poetry run python main.py
