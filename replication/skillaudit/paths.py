"""Where the input dataset, the intermediate database and the results live.

GITSKILLS_DB  the GitSkills release (agent_skills_release.db); default: next to replication/
PAPER_DB      the intermediate database built by step0_extract.py; default: replication/data/
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATASET = os.environ.get("GITSKILLS_DB", str(ROOT.parent / "agent_skills_release.db"))
PAPER_DB = os.environ.get("PAPER_DB", str(ROOT / "data" / "paper.db"))
RESULTS = ROOT / "results"


def dataset_uri():
    """Read-only URI for the dataset, so it is never modified."""
    return f"file:{DATASET}?mode=ro"
