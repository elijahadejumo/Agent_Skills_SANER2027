"""RQ1: what commands do skills tell agents to run? (Tables I and II, Section IV-A)

For every distinct skill, the commands from skillaudit.commands are kept when they name a known
program (skillaudit.classes.census_commands, classify), and each gets a type and an effect level.
A skill has an outside action when it uses a listed outside-action command or sends a message.

Writes results/rq1_commands.txt/.json, results/table1_command_types.csv,
results/table2_outside_actions.csv and results/reviewed_command_names.csv.
"""
import collections
import csv

from skillaudit.classes import REMOTE_WRITE_CATEGORY, WRITE, census_commands, classify, label
from skillaudit.paths import RESULTS
from skillaudit.population import CLAUDE, OTHER, Report, connect, load, pct
from skillaudit.rules import two_by_two

SEND = "(message send)"
KINDS = (("remote_vcs", "Push code, open PRs or issues"), ("deploy", "Deploy"), ("migrate", "Migrate databases"),
         ("publish", "Publish packages"), ("send", "Send messages"))


def known_commands(f):
    cmds = census_commands(set(filter(None, f["strict"].split(","))), filter(None, f["unlabeled"].split(",")))
    known = {p: c for p in cmds if (c := classify(p))}
    if f["sends"]:
        known[SEND] = ("Network clients", WRITE)
    return known, {c.split()[0] for c in cmds}


def main():
    r = Report("rq1_commands")
    skills = load(connect(), keep_commands=True)
    groups = {CLAUDE: [], OTHER: []}
    names = collections.Counter()           # every counted program name, recognised or not (for the review)
    for f in skills.values():
        known, heads = known_commands(f)
        groups[f["group"]].append(known)
        names.update(heads)
    groups["all"] = groups[CLAUDE] + groups[OTHER]
    order = ("all", CLAUDE, OTHER)
    n = {g: len(groups[g]) for g in order}
    has_outside = lambda k: any(e == WRITE for _, e in k.values())

    r.say("=== SKILLS THAT PRESCRIBE COMMANDS ===")
    for g in order:
        rec = sum(1 for k in groups[g] if k)
        out = sum(1 for k in groups[g] if has_outside(k))
        distinct = len({p for k in groups[g] for p in k})
        r.say(f"   {g:<20} {n[g]:>10,} skills | prescribe a command {rec:>9,} ({pct(rec, n[g])}) | distinct commands "
              f"{distinct:>7,} | outside action {out:>7,} ({pct(out, n[g])})")
        r.keep(f"{g}: prescribe a command", rec)
        r.keep(f"{g}: prescribe a command share", pct(rec, n[g]))
        r.keep(f"{g}: distinct commands", distinct)
        r.keep(f"{g}: outside action", out)
        r.keep(f"{g}: outside action share", pct(out, n[g]))
    a = sum(1 for k in groups[CLAUDE] if has_outside(k))
    c = sum(1 for k in groups[OTHER] if has_outside(k))
    _, p, v, odds, lo, hi = two_by_two(a, n[CLAUDE] - a, c, n[OTHER] - c)
    r.say(f"   outside action, Claude Code vs other folders: OR = {odds:.2f} [{lo:.2f}, {hi:.2f}], V = {v:.3f}")
    r.keep("outside action, Claude Code vs other: OR", f"{odds:.2f} [{lo:.2f}, {hi:.2f}]")

    r.say("\n=== TABLE I: COMMANDS BY TYPE (share of skills) ===")
    types = sorted({c for k in groups["all"] for c, _ in k.values()},
                   key=lambda t: -sum(1 for k in groups["all"] if any(c == t for c, _ in k.values())))
    rows = []
    r.say(f"   {'type':<28}{'all':>8}{'Claude Code':>13}{'other':>8}   most used (all skills)")
    for t in types:
        share = {g: pct(sum(1 for k in groups[g] if any(c == t for c, _ in k.values())), n[g]) for g in order}
        top = collections.Counter(p for k in groups["all"] for p, c in k.items() if c[0] == t).most_common(3)
        r.say(f"   {t:<28}{share['all']:>8}{share[CLAUDE]:>13}{share[OTHER]:>8}   " + ", ".join(p for p, _ in top))
        rows.append([t, share["all"], share[CLAUDE], share[OTHER], top[0][0]])
        r.keep(f"type {t}", {"all": share["all"], "Claude Code": share[CLAUDE], "other": share[OTHER],
                             "most used": top[0][0]})
    with open(RESULTS / "table1_command_types.csv", "w", newline="") as fh:
        csv.writer(fh).writerows([["type", "all", "Claude Code", "other folders", "most used"]] + rows)

    r.say("\n=== TABLE II: OUTSIDE ACTIONS BY KIND (all skills) ===")
    rows = []
    for kind, label_ in KINDS:
        test = (lambda k: SEND in k) if kind == "send" else (lambda k, kind=kind: any(REMOTE_WRITE_CATEGORY.get(p) == kind for p in k))
        k_all = sum(1 for k in groups["all"] if test(k))
        r.say(f"   {label_:<32}{k_all:>9,}{pct(k_all, n['all']):>8}")
        rows.append([label_, k_all, pct(k_all, n["all"])])
        r.keep(f"kind {kind}", k_all)
    out_all = sum(1 for k in groups["all"] if has_outside(k))
    r.say(f"   {'Any outside action':<32}{out_all:>9,}{pct(out_all, n['all']):>8}   (a skill can include more than one kind)")
    rows.append(["Any outside action", out_all, pct(out_all, n["all"])])
    with open(RESULTS / "table2_outside_actions.csv", "w", newline="") as fh:
        csv.writer(fh).writerows([["kind", "skills", "share"]] + rows)

    r.say("\n=== MOST COMMON COMMANDS ===")
    for g in ("all", CLAUDE):
        df = collections.Counter(p for k in groups[g] for p in k)
        ranked = [p for p, _ in df.most_common()]
        r.say(f"   {g}: " + ", ".join(f"{p} {pct(c, n[g])}" for p, c in df.most_common(10))
              + f" | git push is #{ranked.index('git push') + 1}")
        r.keep(f"{g}: git push rank", ranked.index("git push") + 1)
        r.keep(f"{g}: top commands", [[p, pct(c, n[g])] for p, c in df.most_common(3)])

    # every name used by at least 0.02% of skills was reviewed (50 skills in Claude Code folders)
    cut = round(50 * n["all"] / n[CLAUDE])
    reviewed = {h: c for h, c in names.items() if c >= cut}
    total = sum(names.values())
    by = collections.Counter(label(h) for h in reviewed)
    r.say(f"\n=== REVIEWED NAMES: used by >= {cut} skills (0.02%) ===")
    r.say(f"   {len(reviewed):,} names covering {pct(sum(reviewed.values()), total)} of command uses: "
          + ", ".join(f"{by[x]} {x}" for x in ("program", "shell grammar", "not a command", "unreviewed")))
    r.keep("reviewed names", len(reviewed))
    r.keep("reviewed names unreviewed", by["unreviewed"])
    with open(RESULTS / "reviewed_command_names.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["name", "skills", "label", "type", "effect"])
        for h, c in sorted(reviewed.items(), key=lambda x: -x[1]):
            cls = classify(h)
            w.writerow([h, c, label(h), *(cls if cls else ("", ""))])
    r.write()


if __name__ == "__main__":
    main()
