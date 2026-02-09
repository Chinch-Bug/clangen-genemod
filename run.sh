#!/usr/bin/env bash

cd "$(dirname "$0")" # script location
uv sync
uv run python main.py
