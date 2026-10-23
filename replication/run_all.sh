#!/usr/bin/env bash
# Reproduces every number and table in the paper. Set GITSKILLS_DB if the dataset is not next to
# this folder, and PYTHON to choose the interpreter (default: python3).
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
"$PY" step0_extract.py          # ~2.5 min: reads the dataset once, builds data/paper.db
"$PY" outside_actions_docs.py   # list of outside actions with documentation links
"$PY" dataset.py                # Section III-A
"$PY" rq1_commands.py           # RQ1: Tables I and II
"$PY" rq2_asking.py             # RQ2: Tables III and IV
"$PY" rq3_copies.py             # RQ3: Table V
"$PY" check_paper.py            # compares every number with the paper
