"""Dataset numbers (Section III-A, Dataset Selection; Introduction).

Writes results/dataset.txt and results/dataset.json.
"""
from skillaudit.population import CLAUDE, OTHER, Report, connect, load, pct


def main():
    r = Report("dataset")
    con = connect()
    files, repos = con.execute("SELECT count(*), count(DISTINCT repo) FROM installations").fetchone()
    distinct, valid = con.execute("SELECT count(*), sum(fm_valid) FROM skills").fetchone()
    claude_distinct, claude_dated = con.execute(
        "SELECT count(*), sum(history) FROM skills WHERE loc = 'canonical'").fetchone()
    r.say(f"SKILL.md files: {files:,} in {repos:,} repositories")
    r.say(f"distinct skills (fingerprints): {distinct:,}; with a valid header: {valid:,}")
    r.say(f"distinct skills in .claude/skills folders: {claude_distinct:,}; with commit history: {claude_dated:,} "
          f"({pct(claude_dated, claude_distinct)})")

    skills = load(con)
    groups = {g: [f for f in skills.values() if f["group"] == g] for g in (CLAUDE, OTHER)}
    groups["all"] = list(skills.values())
    r.say("\npopulation (distinct skills with a valid header; Claude Code skills also need commit history):")
    for g, ss in groups.items():
        n_repos = len({f["repo"] for f in ss})
        dated = sum(f["dated"] for f in ss)
        r.say(f"   {g:<20} {len(ss):>10,} skills in {n_repos:>8,} repositories | with commit history {dated:>9,} "
              f"({pct(dated, len(ss))})")
        r.keep(f"{g}: skills", len(ss))
        r.keep(f"{g}: repositories", n_repos)
        r.keep(f"{g}: with commit history", dated)
    r.keep("files", files)
    r.keep("repositories", repos)
    r.keep("distinct skills", distinct)
    r.keep("Claude Code history coverage", pct(claude_dated, claude_distinct))
    r.keep("other folders history coverage", pct(sum(f["dated"] for f in groups[OTHER]), len(groups[OTHER])))
    r.write()


if __name__ == "__main__":
    main()
