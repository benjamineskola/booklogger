#!/bin/sh
set -e
find library/jinja2/ -type f -exec curlylint --rule 'indent: 2' {} +
flake8 library
pytest -q
mypy --show-error-codes -m library.models -m library.utils
