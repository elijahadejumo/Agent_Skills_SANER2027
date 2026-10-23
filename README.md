# Replication package: Borrowed Trust — Unguarded Actions and Inherited Permissions in Agent Skills

This package reproduces every number and table in the paper from the public GitSkills dataset.
There is one script per research question, and `check_paper.py` compares all 99 numbers reported
in the paper with the computed values.

## Three ways to reproduce the results

| Level | What it does | What you need | Time |
|---|---|---|---|
| 1. Check | Compares all 99 numbers in the paper with our results in `replication/results/` | Only this repository | Seconds |
| 2. Re-run | Recomputes every table and number from the shared database | `paper.db.gz` (664 MB) from this repository's **Releases** page | About 3 minutes |
| 3. Rebuild | Also rebuilds that database from the raw dataset | The GitSkills dataset (about 44 GB) | About 4 minutes |

All commands are run from inside the `replication/` folder, with Python 3.10 or later (tested with 3.14):

```bash
cd replication
pip install -r requirements.txt
```

### Level 1: check the numbers

```bash
python check_paper.py
```

Each line prints `PASS` or `FAIL` for one number in the paper; the last line should read
`99 of 99 numbers match the paper`. It also writes `results/paper_numbers.md`, which lists each
number, where it appears in the paper, and the script that produces it.

### Level 2: re-run every research question from the shared database

1. Download `paper.db.gz` from the **Releases** page of this repository.
2. Check that the download is complete; the output must match this checksum:
   ```bash
   shasum -a 256 paper.db.gz      # on Linux: sha256sum paper.db.gz
   # bb00e7a34d713453d64b982b0d1519fb058203befd84e599b1d38f955bfd3d59
   ```
3. Unpack it into `replication/data/`:
   ```bash
   mkdir -p data
   gunzip -c /path/to/paper.db.gz > data/paper.db
   ```
4. Run the research questions one by one (see *Each research question* below), or all at once
   with `bash run_all.sh`, which skips the extraction step when the dataset is not present.

`paper.db` (1.5 GB unpacked) is derived from GitSkills. It contains no full skill texts, commit
messages, or author names: only each skill's fingerprint, name, description, header settings and
extracted commands; where each file sits (repository and path); and each repository's stars and
main language.

### Level 3: rebuild everything from the GitSkills dataset

1. Get `agent_skills_release.db` (about 44 GB) from Destefanis et al., *GitSkills: A dataset of
   agent skills on GitHub* (MSR 2027; arXiv:2608.10906). Put it in the same folder as this README
   (next to `replication/`), or tell the scripts where it is:
   `export GITSKILLS_DB=/path/to/agent_skills_release.db`. The dataset is only ever opened read-only.
2. Build `data/paper.db` (about 2.5 minutes on an 8-core desktop; about 2 GB of disk space):
   ```bash
   python step0_extract.py
   ```
   A rebuilt `paper.db` can differ byte for byte from the shared one, because rows are written in
   parallel and in varying order, but it gives exactly the same results.
3. Run the research questions as below, or everything at once with `bash run_all.sh`.

## Each research question (Levels 2 and 3)

Each script can be run on its own, in any order, once `data/paper.db` exists.

**Dataset (Section III-A)** — about 20 seconds
```bash
python dataset.py
```
Output: `results/dataset.txt`. Compare with Section III-A: 1,624,613 distinct skills (243,833 in
Claude Code folders and 1,380,780 in other folders) and commit-history coverage (99.6% and 11.4%).

**RQ1: What are typical commands skills tell agents to run? (Section IV-A)** — about 30 seconds
```bash
python rq1_commands.py
```
Outputs:
- `results/table1_command_types.csv` → **Table I** (command types, share of all skills and of Claude Code skills)
- `results/table2_outside_actions.csv` → **Table II** (outside actions by kind)
- `results/rq1_commands.txt` → the numbers in the RQ1 text (40.6% of skills specify a shell
  command, 68,102 distinct commands, 63,517 skills with an outside action)
- `results/reviewed_command_names.csv` → every command name we reviewed by hand, with its label

The list of outside actions itself (140 commands from 37 tools, each with a documentation link)
is produced by `python outside_actions_docs.py` → `results/outside_actions.csv`.

**RQ2: Do skills ask a person before they act outside the repository? (Section IV-B)** — about 15 seconds
```bash
python rq2_asking.py
```
Outputs:
- `results/table3_unguarded.csv` → **Table III** (unguarded and no-approval skills)
- `results/table4_authorship_languages.csv` → **Table IV** (authorship and languages, with odds ratios and Cramér's V)
- `results/rq2_asking.txt` → the numbers in the RQ2 text (local commits, pre-approved commands)

**RQ3: When skills are copied, does anyone revisit these decisions? (Section IV-C)** — about 35 seconds
```bash
python rq3_copies.py
```
Outputs:
- `results/table5_inherited.csv` → **Table V** (installations from another owner, and edited copies)
- `results/rq3_copies.txt` → the numbers in the RQ3 text (receiving repositories), plus the
  check with descriptions of at least 100 characters

### Verify

```bash
python check_paper.py
```
Compares every number in the paper with your results and writes `results/paper_numbers.md`,
which lists each number, where it appears in the paper, and the script that produces it.

`bash run_all.sh` runs everything in one go: the extraction (only when the dataset is present),
every research question, and the check. Set `PYTHON=/path/to/python` to choose the interpreter.

## Repository layout

```
README.md                   this guide
replication/
  step0_extract.py          reads the dataset once and builds data/paper.db
  dataset.py                Section III-A
  rq1_commands.py           RQ1: Tables I and II
  rq2_asking.py             RQ2: Tables III and IV
  rq3_copies.py             RQ3: Table V
  outside_actions_docs.py   the list of outside actions with documentation links
  check_paper.py            compares all numbers with the paper
  skillaudit/               code shared by the scripts:
    commands.py             extracts the shell commands a skill tells the agent to run
    classes.py              command types, effect levels, reviewed names, and the list of outside actions
    frontmatter.py          reads the skill header: manual-start option and pre-approved tools
    rules.py                unrestricted vs scoped pre-approvals, coverage of outside actions, agent traces, statistics
    population.py           the study population and the measures shared by RQ1-RQ3
    paths.py                locations of the dataset, data/paper.db and results/
  results/                  outputs of our run (tables as CSV, numbers as TXT/JSON, paper_numbers.md)
  run_all.sh                runs steps 2-4 in one go
  requirements.txt          Python packages
```

The dataset (`agent_skills_release.db`) is not included; see *Level 3*. Other folders in our working
copy (`paper/` with the LaTeX source, `archive/` with earlier explorations) are not part of the
package and are not needed to reproduce the results.

