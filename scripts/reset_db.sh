#!/usr/bin/env bash

export PYTHONPATH=${PYTHONPATH}:$(pwd)/server

python scripts/reset_db.py