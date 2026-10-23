"""RQ2: do skills ask a person before they act outside the repository? (Tables III and IV, Section IV-B)

  unguarded     the skill has an outside action and does not set disable-model-invocation: true
  no-approval   unguarded, and its allowed-tools cover the outside action
Authorship is compared among skills with commit history; languages among all skills.

Writes results/rq2_asking.txt/.json, results/table3_unguarded.csv and
results/table4_authorship_languages.csv.
"""
import collections
import csv

from skillaudit.paths import RESULTS
from skillaudit.population import CLAUDE, Report, connect, load, pct
from skillaudit.rules import cramers_v, two_by_two

COLS = (("outside action", "act", None, 1), ("unguarded", "unguarded", "act", 1), ("no-approval", "no_approval", None, 2))


def main():
    r = Report("rq2_asking")
    skills = load(connect())
    allf = list(skills.values())
    claude = [f for f in allf if f["group"] == CLAUDE]

    r.say("=== TABLE III: SKILLS WITH OUTSIDE ACTIONS AND PRE-APPROVED COMMANDS ===")
    rows = []
    for g, ss in (("all", allf), (CLAUDE, claude)):
        act = [f for f in ss if f["act"]]
        ung = sum(f["unguarded"] for f in act)
        noa = sum(f["no_approval"] for f in act)
        r.say(f"   {g:<20} outside action {len(act):>7,} | no manual-start option (unguarded) {ung:>7,} "
              f"({pct(ung, len(act))}) | also pre-approved (no-approval) {noa:>6,} ({pct(noa, len(act))})")
        rows.append([g, len(act), ung, pct(ung, len(act)), noa, pct(noa, len(act))])
        r.keep(f"{g}: outside action", len(act))
        r.keep(f"{g}: unguarded", ung)
        r.keep(f"{g}: unguarded share", pct(ung, len(act)))
        r.keep(f"{g}: no-approval", noa)
        r.keep(f"{g}: no-approval share", pct(noa, len(act)))
    with open(RESULTS / "table3_unguarded.csv", "w", newline="") as fh:
        csv.writer(fh).writerows([["group", "outside action", "unguarded", "unguarded share", "no-approval",
                                   "no-approval share"]] + rows)

    commit = [f for f in allf if f["local_commit"]]
    ung = sum(not f["guarded"] for f in commit)
    r.say(f"\n   skills that only commit locally (git commit, no outside action): {len(commit):,}; unguarded {ung:,} "
          f"({pct(ung, len(commit))})")
    r.keep("local commit only", len(commit))
    r.keep("local commit only unguarded share", pct(ung, len(commit)))

    r.say("\n=== PRE-APPROVED COMMANDS (all skills) ===")
    n = len(allf)
    for key, text in (("declared", "list pre-approved tools"), ("shell", "pre-approve every shell command"),
                      ("scoped", "pre-approve scoped shell commands")):
        k = sum(f[key] for f in allf)
        r.say(f"   {text:<36}{k:>9,} ({pct(k, n)})")
        r.keep(f"pre-approval {key}", k)
        r.keep(f"pre-approval {key} share", pct(k, n))
    act = [f for f in allf if f["act"]]
    pre = sum(f["preapproved"] for f in act)
    r.say(f"   of {len(act):,} skills with outside actions, {pre:,} ({pct(pre, len(act))}) pre-approve them, and "
          f"{sum(f['no_approval'] for f in act):,} of those are also unguarded (no-approval)")
    r.keep("outside action pre-approved", pre)
    r.keep("outside action pre-approved share", pct(pre, len(act)))

    r.say("\n=== TABLE IV: AUTHORSHIP (skills with commit history) AND LANGUAGES (all skills) ===")
    rows = []

    def row(label, ss):
        cells = []
        for _, key, within, digits in COLS:
            d = [f for f in ss if not within or f[within]]
            cells.append(pct(sum(f[key] for f in d), len(d), digits))
        r.say(f"   {label:<22}{len(ss):>10,}" + "".join(f"{c:>12}" for c in cells))
        rows.append([label, len(ss)] + cells)
        r.keep(f"table IV {label}", [len(ss)] + cells)

    dated = [f for f in allf if f["dated"]]
    ag, no = [f for f in dated if f["agent"]], [f for f in dated if not f["agent"]]
    r.say(f"   skills with commit history: {len(dated):,}; agent-written: {len(ag):,} ({pct(len(ag), len(dated))})")
    r.keep("skills with commit history", len(dated))
    r.keep("agent-written", len(ag))
    r.keep("agent-written share", pct(len(ag), len(dated)))
    r.say(f"   {'':<22}{'skills':>10}" + "".join(f"{c[0]:>12}" for c in COLS))
    row("Agent-written", ag)
    row("No agent trace", no)
    ors = []
    for name, key, within, _ in COLS:
        a = [f for f in ag if not within or f[within]]
        b = [f for f in no if not within or f[within]]
        x, y = sum(f[key] for f in a), sum(f[key] for f in b)
        _, p, v, odds, lo, hi = two_by_two(x, len(a) - x, y, len(b) - y)
        ors.append(f"{odds:.2f}")
        r.say(f"      {name}: OR = {odds:.2f} [{lo:.2f}, {hi:.2f}], p = {p:.2g}, V = {v:.3f}")
        r.keep(f"authorship {name}: OR", f"{odds:.2f}")
        r.keep(f"authorship {name}: p", p)
    rows.append(["Odds ratio", ""] + ors)

    top = [l for l, _ in collections.Counter(f["lang"] for f in allf).most_common(10)]
    for l in top:
        row("No detected language" if l == "(none)" else l, [f for f in allf if f["lang"] == l])
    vs = []
    for name, key, within, _ in COLS:
        table = []
        for l in top:
            ss = [f for f in allf if f["lang"] == l and (not within or f[within])]
            k = sum(f[key] for f in ss)
            table.append([k, len(ss) - k])
        v, p = cramers_v(table)
        vs.append(f"{v:.3f}")
        r.say(f"      {name} across languages: V = {v:.3f}, p = {p:.2g}")
        r.keep(f"languages {name}: V", f"{v:.3f}")
        r.keep(f"languages {name}: p", p)
    rows.append(["Cramer's V", ""] + vs)
    with open(RESULTS / "table4_authorship_languages.csv", "w", newline="") as fh:
        csv.writer(fh).writerows([["group", "skills"] + [c[0] for c in COLS]] + rows)
    r.write()


if __name__ == "__main__":
    main()
