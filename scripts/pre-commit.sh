#!/bin/sh
set -e
curlylint library/jinja2/
flake8 library
pytest -q
mypy --show-error-codes -m library.models -m library.utils
