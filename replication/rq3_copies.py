"""RQ3: when skills are copied, does anyone revisit these decisions? (Table V, Section IV-C)

  installation   one skill in one repository: every repository that holds a file with the
                 skill's fingerprint, counted once per repository, in any folder
  owner          the user or organization in the repository's name
  exact copies   the same fingerprint in repositories of different owners
  edited copies  the same name and description, different instructions, different owners

From another owner (a range, since copies carry no dates of their own):
  at least  each skill (exact or edited copies grouped together) is assumed to come from the
            owner holding most of its installations; ties go to the owner with the most-starred
            repository, so popular repositories are never counted as receivers by chance
  at most   every installation of a skill held by more than one owner, plus every skill kept in
            a collection folder (.claude/skills/<collection>/<skill>/SKILL.md)

Revisiting decisions: each edited copy is compared with the earliest version of the skill (by
first commit), using only pairs whose earliest version did not change after the copy was made.
Only the header settings are compared: the allowed-tools entries (as a set) and the
manual-start option.

Writes results/rq3_copies.txt/.json and results/table5_inherited.csv.
"""
import collections
import csv
import re

from skillaudit.paths import RESULTS
from skillaudit.population import Report, connect, load, pct

PACK = re.compile(r"(^|/)\.claude/skills/[^/]+/[^/]+/")
owner = lambda repo: repo.split("/")[0].lower()


def main():
    r = Report("rq3_copies")
    con = connect()
    skills = load(con)
    stars = dict(con.execute("SELECT full_name, stars FROM repos"))
    pairs = {}  # (repository, skill) -> (in a .claude/skills folder, inside a collection folder)
    for repo, sha, loc, path in con.execute("SELECT repo, sha, loc, path FROM installations"):
        if sha in skills:
            claude = loc == "canonical"
            old = pairs.get((repo, sha), (False, False))
            pairs[(repo, sha)] = (old[0] or claude, old[1] or (claude and bool(PACK.search(path))))
    lin_owners = collections.defaultdict(set)
    for repo, sha in pairs:
        lin_owners[skills[sha]["lineage"]].add(owner(repo))

    def others(repos):
        """Installations by owners other than the assumed origin's."""
        count = collections.Counter(map(owner, repos))
        top = max(count.values())
        main_owner = max((o for o in count if count[o] == top),
                         key=lambda o: (max(stars.get(x, 0) for x in repos if owner(x) == o), o))
        return {x for x in repos if owner(x) != main_owner}

    r.say("=== TABLE V (top): INSTALLATIONS FROM ANOTHER OWNER ===")
    r.say(f"   {'':<20}{'skills':>10}{'installations':>15}{'at least':>10}{'at most':>9}{'receiving repos':>17}"
          f"{'long desc. only':>17}")
    rows = []
    for label, pick in (("All skills", lambda f: True), ("Unguarded skills", lambda f: f["unguarded"]),
                        ("No-approval skills", lambda f: f["no_approval"])):
        n_skills = sum(1 for f in skills.values() if pick(f))
        P = [(x, s) for (x, s) in pairs if pick(skills[s])]
        lin, lin_long = collections.defaultdict(set), collections.defaultdict(set)
        for x, s in P:
            lin[skills[s]["lineage"]].add(x)
            lin_long[skills[s]["lineage"] if skills[s]["long"] else s].add(x)
        inherited_repos = {k: others(v) for k, v in lin.items()}
        inherited = {(x, s) for x, s in P if x in inherited_repos[skills[s]["lineage"]]}
        long_repos = {k: others(v) for k, v in lin_long.items()}
        inherited_long = sum(1 for x, s in P if x in long_repos[skills[s]["lineage"] if skills[s]["long"] else s])
        upper = sum(1 for x, s in P if len(lin_owners[skills[s]["lineage"]]) > 1 or pairs[(x, s)][1])
        receiving = len({x for x, s in inherited})
        lo, hi = pct(len(inherited), len(P)), pct(upper, len(P))
        r.say(f"   {label:<20}{n_skills:>10,}{len(P):>15,}{lo:>10}{hi:>9}{receiving:>17,}{pct(inherited_long, len(P)):>17}")
        rows.append([label, n_skills, len(P), lo, hi, receiving])
        r.keep(f"{label}: skills", n_skills)
        r.keep(f"{label}: installations", len(P))
        r.keep(f"{label}: at least", lo)
        r.keep(f"{label}: at most", hi)
        r.keep(f"{label}: receiving repositories", receiving)
        r.keep(f"{label}: at least, long descriptions only", pct(inherited_long, len(P)))

    r.say("\n=== TABLE V (bottom): EDITED COPIES COMPARED WITH THE EARLIEST VERSION ===")
    holders = collections.defaultdict(set)
    for x, s in pairs:
        holders[s].add(x)
    versions = collections.defaultdict(set)
    for s in holders:
        if skills[s]["dated"]:
            versions[skills[s]["lineage"]].add(s)
    edits = []  # (earliest version, edited copy by another owner, made after the earliest version last changed)
    for shas in versions.values():
        if len(shas) < 2:
            continue
        origin = min(shas, key=lambda s: (skills[s]["first"], s))
        first_owners = {owner(x) for x in holders[origin]}
        o = skills[origin]
        edits += [(o, skills[v]) for v in shas - {origin}
                  if {owner(x) for x in holders[v]} - first_owners and o["last"] < skills[v]["first"]]
    for label, key in (("Unguarded skills", "unguarded"), ("No-approval skills", "no_approval")):
        for only_long in (False, True):
            E = [(o, v) for o, v in edits if o[key] and (o["long"] or not only_long)]
            same = pct(sum(o["grants"] == v["grants"] for o, v in E), len(E))
            narrowed = pct(sum(v["grants"] < o["grants"] for o, v in E), len(E))
            widened = pct(sum(v["grants"] > o["grants"] for o, v in E), len(E))
            added = pct(sum(v["guarded"] and not o["guarded"] for o, v in E), len(E))
            still = pct(sum(v[key] for _, v in E), len(E))
            # a skill without pre-approvals has nothing to keep, so pre-approvals are also compared
            # only for pairs whose earliest version pre-approved at least one command
            P = [(o, v) for o, v in E if o["grants"]]
            p_same = pct(sum(o["grants"] == v["grants"] for o, v in P), len(P))
            p_narrowed = pct(sum(v["grants"] < o["grants"] for o, v in P), len(P))
            p_widened = pct(sum(v["grants"] > o["grants"] for o, v in P), len(P))
            tag = " (long descriptions only)" if only_long else ""
            r.say(f"   {label + tag:<46} copies {len(E):>6,} | same pre-approvals {same:>6} | narrowed {narrowed:>5}"
                  f" | widened {widened:>5} | manual-start added {added:>5} | still risky {still:>6}")
            r.say(f"   {'   ... earliest version had pre-approvals':<46} copies {len(P):>6,} | same pre-approvals "
                  f"{p_same:>6} | narrowed {p_narrowed:>5} | widened {p_widened:>5}")
            if not only_long:
                rows.append([f"{label} (edited copies)", len(E), added, len(P), p_same])
            r.keep(f"edited copies of {label.lower()}{tag}", {"copies": len(E), "same pre-approvals": same,
                                                               "narrowed": narrowed, "widened": widened,
                                                               "manual-start added": added, "still risky": still,
                                                               "with pre-approvals": len(P),
                                                               "with pre-approvals: same": p_same,
                                                               "with pre-approvals: narrowed": p_narrowed,
                                                               "with pre-approvals: widened": p_widened})
    with open(RESULTS / "table5_inherited.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["group", "skills", "installations", "from another owner (at least)", "at most", "receiving repos"])
        w.writerows(rows[:3])
        w.writerow([])
        w.writerow(["edited copies of", "copies", "manual-start added", "with pre-approvals", "same pre-approvals"])
        w.writerows(rows[3:])
    r.write()


if __name__ == "__main__":
    main()
