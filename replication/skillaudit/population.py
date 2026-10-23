"""The study population and the per-skill measures shared by RQ1-RQ3.

Population: every distinct skill (fingerprint) whose header is valid (GitSkills'
frontmatter_valid), in two groups:
  Claude Code folders  skills whose representative file is in a .claude/skills folder and that
                       have commit history (99.6% of them do)
  other folders        all other distinct skills with a valid header
The paper reports all skills together and, where useful, the Claude Code group.

Per-skill measures (see the Methods section of the paper):
  outside action  the skill prescribes a listed outside-action command or sends a message
  unguarded       it has an outside action and does not set the manual-start option
  pre-approved    its allowed-tools cover that outside action
  no-approval     unguarded and pre-approved
  local commit    it runs git commit but has no outside action
"""
import hashlib
import json
import sqlite3

from .classes import REMOTE_WRITE_CATEGORY
from .paths import PAPER_DB, RESULTS
from .rules import UNRESTRICTED, covered, stems

CLAUDE, OTHER = "Claude Code folders", "other folders"


def connect():
    return sqlite3.connect(PAPER_DB)


def load(con, keep_commands=False):
    """sha -> dict of measures for every skill in the population."""
    lang = dict(con.execute("SELECT full_name, language FROM repos"))
    skills = {}
    for (sha, loc, repo, history, first, last, agent, name, desc, guarded, grants, scripts, strict, unl,
         sends) in con.execute("""
            SELECT sha, loc, repo, history, first_at, last_at, agent, name, description, manual_start, grants,
                   has_scripts, cmds_strict, cmds_unlabeled, sends
            FROM skills
            WHERE fm_valid = 1 AND (loc != 'canonical' OR history = 1)"""):
        cmds = set(filter(None, (strict + "," + unl).split(",")))
        grants = [g for g in grants.split("\t") if g]
        outside = [p for p in cmds if p in REMOTE_WRITE_CATEGORY]
        act = bool(outside) or bool(sends)
        pre = act and covered(outside, grants, sends)
        desc = (desc or "").strip()
        f = dict(group=CLAUDE if loc == "canonical" else OTHER, repo=repo, lang=lang.get(repo) or "(none)",
                 act=act, guarded=bool(guarded), unguarded=act and not guarded, preapproved=pre,
                 no_approval=pre and not guarded, local_commit="git commit" in cmds and not act,
                 declared=bool(grants), shell=any(UNRESTRICTED.match(g) for g in grants), scoped=bool(stems(grants)),
                 grants=frozenset(grants), dated=bool(history), agent=bool(agent),
                 first=first or "9999", last=last or "9999", long=len(desc) >= 100,
                 lineage=hashlib.md5(f"{(name or '').strip().lower()}\0{desc}".encode()).hexdigest() if desc else sha)
        if keep_commands:
            f["strict"], f["unlabeled"], f["sends"] = strict, unl, bool(sends)
        skills[sha] = f
    return skills


def pct(a, b, digits=1):
    return f"{100 * a / b:.{digits}f}%" if b else "-"


class Report:
    """Collects printed lines and key numbers, then writes results/<name>.txt and .json."""

    def __init__(self, name):
        self.name, self.lines, self.numbers = name, [], {}

    def say(self, s=""):
        print(s)
        self.lines.append(s)

    def keep(self, key, value):
        self.numbers[key] = value

    def write(self):
        RESULTS.mkdir(parents=True, exist_ok=True)
        (RESULTS / f"{self.name}.txt").write_text("\n".join(self.lines) + "\n")
        (RESULTS / f"{self.name}.json").write_text(json.dumps(self.numbers, indent=1) + "\n")
        print(f"\nwritten: results/{self.name}.txt, results/{self.name}.json")
