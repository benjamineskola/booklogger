#!/bin/sh
set -e
flake8 library
pytest -q
mypy -m library.models -m library.utils
