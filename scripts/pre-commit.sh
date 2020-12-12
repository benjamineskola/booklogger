#!/bin/sh
set -e
pipenv run find library/jinja2/ -name '*.html' -exec curlylint --rule 'indent: 2' {} +
pipenv run flake8 library
pipenv run pytest -q
pipenv run mypy --show-error-codes -m library.models -m library.utils -m library.forms
