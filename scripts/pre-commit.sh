#!/bin/sh
set -e
flake8 library
pytest -q
mypy --show-error-codes -m library.models -m library.utils
