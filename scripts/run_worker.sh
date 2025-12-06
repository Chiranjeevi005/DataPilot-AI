#!/bin/bash
# Run from project root
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
python src/worker.py
