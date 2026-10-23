# Borrowed Trust: Unguarded Actions and Inherited Permissions in Agent Skills

This repository contains the results, code, and data tables behind every number and table in the paper.

## Results

All results are in `replication/results/`.

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

## Check the results

To compare the results with every number reported in the paper (needs only Python 3):

```bash
cd replication
python check_paper.py
```

It prints `PASS` or `FAIL` for each number and should end with `102 of 102 numbers match the paper`.

## Code

| File | Purpose |
|---|---|
| `step0_extract.py` | Reads the dataset and builds `data/paper.db`, used by all other scripts |
| `dataset.py`, `rq1_commands.py`, `rq2_asking.py`, `rq3_copies.py` | One script per section of the results |
| `outside_actions_docs.py` | The list of outside actions with a documentation link for each |
| `check_paper.py` | Compares all results with the numbers in the paper |
| `skillaudit/` | Shared code: command extraction, command types, skill settings, and the study population |

## Optional: regenerate the results from the dataset

The GitSkills dataset (`agent_skills_release.db`, about 44 GB) is not included in this repository;
it is distributed by its authors (Destefanis et al., *GitSkills: A dataset of agent skills on
GitHub*, arXiv:2608.10906). With the dataset, every result above can be regenerated:

1. Install the Python packages (Python 3.10 or later):
   ```bash
   pip install -r replication/requirements.txt
   ```
2. Put `agent_skills_release.db` in this folder, next to `replication/`.
3. Run:
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
