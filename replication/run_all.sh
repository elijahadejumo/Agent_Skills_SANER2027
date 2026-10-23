#!/usr/bin/env bash
# Reproduces every number and table in the paper (see README). Set PYTHON to choose the interpreter.
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
"$PY" step0_extract.py          # reads the dataset once, builds data/paper.db
"$PY" outside_actions_docs.py   # list of outside actions with documentation links
"$PY" dataset.py                # Section III-A
"$PY" rq1_commands.py           # RQ1: Tables I and II
"$PY" rq2_asking.py             # RQ2: Tables III and IV
"$PY" rq3_copies.py             # RQ3: Table V
"$PY" check_paper.py            # compares every number with the paper
