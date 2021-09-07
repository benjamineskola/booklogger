#!/bin/sh
set -e
poetry run find library/jinja2/ -name '*.html' -exec curlylint --rule 'indent: 2' {} +
poetry run flake8 library
poetry run pytest -q | grep 'Total coverage:'
poetry run mypy
