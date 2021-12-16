#!/bin/sh
set -e
poetry run find library/jinja2/ -name '*.html' -exec curlylint --rule 'indent: 2' {} +
poetry run flake518
poetry run pylint -- */
poetry run pytest -q | grep 'Total coverage:'
poetry run mypy
