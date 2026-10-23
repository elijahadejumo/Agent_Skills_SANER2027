#!/usr/bin/env bash
# Reproduces every number and table in the paper.
#   Level 3: with the GitSkills dataset next to this repository (or GITSKILLS_DB set), rebuilds data/paper.db first.
#   Level 2: without the dataset, uses data/paper.db unpacked from paper.db.gz (see README).
# Set PYTHON to choose the interpreter (default: python3).
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
DATASET="${GITSKILLS_DB:-../agent_skills_release.db}"
if [ -f "$DATASET" ]; then
    "$PY" step0_extract.py      # ~2.5 min: reads the dataset once, builds data/paper.db
elif [ -f data/paper.db ]; then
    echo "Dataset not found; using the existing data/paper.db (Level 2)."
else
    echo "Need either the GitSkills dataset ($DATASET) or data/paper.db unpacked from paper.db.gz; see README." >&2
    exit 1
fi
"$PY" outside_actions_docs.py   # list of outside actions with documentation links
"$PY" dataset.py                # Section III-A
"$PY" rq1_commands.py           # RQ1: Tables I and II
"$PY" rq2_asking.py             # RQ2: Tables III and IV
"$PY" rq3_copies.py             # RQ3: Table V
"$PY" check_paper.py            # compares every number with the paper
