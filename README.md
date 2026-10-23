# Borrowed Trust: Unguarded Actions and Inherited Permissions in Agent Skills

This repository contains the code and results to reproduce every number and table in the paper.

## Requirements

- Python 3.10 or later
- The GitSkills dataset, `agent_skills_release.db` (about 44 GB), from Destefanis et al.,
  *GitSkills: A dataset of agent skills on GitHub* (arXiv:2608.10906)

Install the Python packages:

```bash
pip install -r replication/requirements.txt
```

Put `agent_skills_release.db` in this folder (next to `replication/`), or tell the scripts where it is:

```bash
export GITSKILLS_DB=/path/to/agent_skills_release.db
```

## How to run

```bash
cd replication
python step0_extract.py    # reads the dataset once (about 3 minutes)
python dataset.py          # dataset numbers (Section III-A)
python rq1_commands.py     # RQ1: Tables I and II
python rq2_asking.py       # RQ2: Tables III and IV
python rq3_copies.py       # RQ3: Table V
python check_paper.py      # checks every number against the paper
```

Or run everything at once with `bash run_all.sh`.

`check_paper.py` prints `PASS` or `FAIL` for each number in the paper and should end with
`99 of 99 numbers match the paper`.

## Results

All outputs are written to `replication/results/`. Our own results are already included there.

| Paper | File |
|---|---|
| Table I | `table1_command_types.csv` |
| Table II | `table2_outside_actions.csv` |
| Table III | `table3_unguarded.csv` |
| Table IV | `table4_authorship_languages.csv` |
| Table V | `table5_inherited.csv` |
| Numbers in the text | `dataset.txt`, `rq1_commands.txt`, `rq2_asking.txt`, `rq3_copies.txt` |
| List of outside actions | `outside_actions.csv` |
| Every number and its source | `paper_numbers.md` |

## Code

| File | Purpose |
|---|---|
| `step0_extract.py` | Reads the dataset and builds `data/paper.db`, used by all other scripts |
| `dataset.py`, `rq1_commands.py`, `rq2_asking.py`, `rq3_copies.py` | One script per section of the results |
| `outside_actions_docs.py` | The list of outside actions with a documentation link for each |
| `check_paper.py` | Compares all results with the numbers in the paper |
| `skillaudit/` | Shared code: command extraction, command types, skill settings, and the study population |
