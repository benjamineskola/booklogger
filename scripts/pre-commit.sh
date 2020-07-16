#!/bin/sh
flake8 library
pytest -q
mypy -m library.models -m library.utils
