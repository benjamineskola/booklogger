#!/usr/bin/env python
import sys

import toml
from bs4 import BeautifulSoup

config = toml.load("pyproject.toml")
threshold = 90
if (
    "tool" in config
    and "github-coverage-action" in config["tool"]
    and "threshold" in config["tool"]["github-coverage-action"]
):
    threshold = config["tool"]["github-coverage-action"]["threshold"]

with open("coverage.xml") as xml:
    data = BeautifulSoup(xml.read(), "lxml")
    coverage = float(data.find("coverage")["line-rate"]) * 100
    if coverage >= threshold:
        print(
            f"Coverage {coverage:.2f}% above threshold {threshold:.0f}%",
            file=sys.stderr,
        )
        sys.exit(0)
    else:
        print(
            f"Coverage {coverage:.2f}% below threshold {threshold:.0f}%",
            file=sys.stderr,
        )
        sys.exit(max(int(coverage), 1))
