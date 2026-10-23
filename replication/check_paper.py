"""Checks every number reported in the paper against the results computed by the scripts.

Run after dataset.py, rq1_commands.py, rq2_asking.py and rq3_copies.py. Prints one line per
number (PASS/FAIL) and writes results/paper_numbers.md, which maps each number in the paper to
the script and result that produce it. Exits with status 1 if any number does not match.
"""
import json
import sys

from skillaudit.paths import RESULTS

R = {name: json.loads((RESULTS / f"{name}.json").read_text())
     for name in ("dataset", "rq1_commands", "rq2_asking", "rq3_copies")}
C, A = "Claude Code folders", "all"

# (where in the paper, what it says, expected value as printed, script, key, optional sub-key)
CHECKS = [
    ("III-A Dataset", "SKILL.md files", 3797117, "dataset", "files"),
    ("III-A Dataset", "repositories", 282200, "dataset", "repositories"),
    ("III-A Dataset", "distinct skills in the population", 1624613, "dataset", "all: skills"),
    ("III-A Dataset", "skills in other folders", 1380780, "dataset", "other folders: skills"),
    ("III-A Dataset", "repositories of skills in other folders", 177511, "dataset", "other folders: repositories"),
    ("III-A Dataset", "skills in Claude Code folders", 243833, "dataset", f"{C}: skills"),
    ("III-A Dataset", "repositories of Claude Code skills", 53935, "dataset", f"{C}: repositories"),
    ("III-A Dataset", "commit history, Claude Code skills", "99.6%", "dataset", "Claude Code history coverage"),
    ("VI Threats", "commit history, other skills (a ninth)", "11.4%", "dataset", "other folders history coverage"),
    ("IV-A RQ1", "skills that specify a shell command", "40.6%", "rq1_commands", "all: prescribe a command share"),
    ("IV-A RQ1", "version control, Claude Code folders", "15.2%", "rq1_commands", "type Version control", "Claude Code"),
    ("IV-A RQ1", "version control, other folders", "8.4%", "rq1_commands", "type Version control", "other"),
    ("Abstract, IV-A", "skills with an outside action", 63517, "rq1_commands", "all: outside action"),
    ("IV-A RQ1", "share with an outside action", "3.9%", "rq1_commands", "all: outside action share"),
    ("IV-A RQ1", "outside action, Claude Code folders", "6.9%", "rq1_commands", f"{C}: outside action share"),
    ("IV-A RQ1", "outside action, other folders", "3.4%", "rq1_commands", "other folders: outside action share"),
    ("IV-A RQ1", "odds ratio, Claude Code vs other", "2.11 [2.07, 2.15]", "rq1_commands",
     "outside action, Claude Code vs other: OR"),
    ("Table II", "push code, open PRs or issues", 50501, "rq1_commands", "kind remote_vcs"),
    ("Table II", "deploy", 9774, "rq1_commands", "kind deploy"),
    ("Table II", "migrate databases", 2466, "rq1_commands", "kind migrate"),
    ("Table II", "publish packages", 2272, "rq1_commands", "kind publish"),
    ("Table II", "send messages", 904, "rq1_commands", "kind send"),
    ("Table III", "outside action, all", 63517, "rq2_asking", "all: outside action"),
    ("Table III", "outside action, Claude Code", 16763, "rq2_asking", f"{C}: outside action"),
    ("Table III", "unguarded, all", 59892, "rq2_asking", "all: unguarded"),
    ("Table III", "unguarded share, all", "94.3%", "rq2_asking", "all: unguarded share"),
    ("Table III", "unguarded, Claude Code", 15139, "rq2_asking", f"{C}: unguarded"),
    ("Table III", "unguarded share, Claude Code", "90.3%", "rq2_asking", f"{C}: unguarded share"),
    ("Table III", "no-approval, all", 8054, "rq2_asking", "all: no-approval"),
    ("Table III", "no-approval share, all", "12.7%", "rq2_asking", "all: no-approval share"),
    ("Table III", "no-approval, Claude Code", 2303, "rq2_asking", f"{C}: no-approval"),
    ("Table III", "no-approval share, Claude Code", "13.7%", "rq2_asking", f"{C}: no-approval share"),
    ("IV-B RQ2", "skills that only commit locally", 15621, "rq2_asking", "local commit only"),
    ("IV-B RQ2", "... unguarded", "94.7%", "rq2_asking", "local commit only unguarded share"),
    ("IV-B RQ2", "skills that pre-approve tools", 170021, "rq2_asking", "pre-approval declared"),
    ("IV-B RQ2", "... share", "10.5%", "rq2_asking", "pre-approval declared share"),
    ("IV-B RQ2", "pre-approve every shell command", 90278, "rq2_asking", "pre-approval shell"),
    ("IV-B RQ2", "... share", "5.6%", "rq2_asking", "pre-approval shell share"),
    ("IV-B RQ2", "pre-approve scoped commands", 37556, "rq2_asking", "pre-approval scoped"),
    ("IV-B RQ2", "... share", "2.3%", "rq2_asking", "pre-approval scoped share"),
    ("IV-B RQ2", "outside actions pre-approved", 9230, "rq2_asking", "outside action pre-approved"),
    ("IV-B RQ2", "... share", "14.5%", "rq2_asking", "outside action pre-approved share"),
    ("Table IV", "skills with commit history", 400783, "rq2_asking", "skills with commit history"),
    ("Table IV", "agent-written", 129139, "rq2_asking", "agent-written"),
    ("IV-B RQ2", "agent-written share", "32.2%", "rq2_asking", "agent-written share"),
    ("Table IV", "Agent-written row", [129139, "7.0%", "90.3%", "1.01%"], "rq2_asking", "table IV Agent-written"),
    ("Table IV", "No agent trace row", [271644, "4.5%", "92.2%", "0.56%"], "rq2_asking", "table IV No agent trace"),
    ("Table IV", "OR outside action", "1.58", "rq2_asking", "authorship outside action: OR"),
    ("Table IV", "OR unguarded", "0.79", "rq2_asking", "authorship unguarded: OR"),
    ("Table IV", "OR no-approval", "1.81", "rq2_asking", "authorship no-approval: OR"),
    ("Table IV", "Python", [627125, "2.9%", "95.8%", "0.35%"], "rq2_asking", "table IV Python"),
    ("Table IV", "TypeScript", [284327, "4.6%", "93.7%", "0.57%"], "rq2_asking", "table IV TypeScript"),
    ("Table IV", "JavaScript", [135222, "3.2%", "94.2%", "0.36%"], "rq2_asking", "table IV JavaScript"),
    ("Table IV", "No detected language", [135156, "3.1%", "95.4%", "0.31%"], "rq2_asking", "table IV No detected language"),
    ("Table IV", "Shell", [120313, "7.1%", "92.3%", "1.16%"], "rq2_asking", "table IV Shell"),
    ("Table IV", "HTML", [97604, "3.5%", "95.0%", "0.44%"], "rq2_asking", "table IV HTML"),
    ("Table IV", "Rust", [31925, "6.4%", "93.8%", "0.73%"], "rq2_asking", "table IV Rust"),
    ("Table IV", "Go", [30014, "6.2%", "92.7%", "0.61%"], "rq2_asking", "table IV Go"),
    ("Table IV", "C#", [22348, "3.8%", "94.2%", "0.26%"], "rq2_asking", "table IV C#"),
    ("Table IV", "PowerShell", [13011, "3.6%", "96.0%", "0.27%"], "rq2_asking", "table IV PowerShell"),
    ("Table IV", "Cramer's V outside action", "0.067", "rq2_asking", "languages outside action: V"),
    ("Table IV", "Cramer's V unguarded", "0.055", "rq2_asking", "languages unguarded: V"),
    ("Table IV", "Cramer's V no-approval", "0.034", "rq2_asking", "languages no-approval: V"),
    ("Table V", "all skills: skills", 1624613, "rq3_copies", "All skills: skills"),
    ("Table V", "all skills: installations", 2795450, "rq3_copies", "All skills: installations"),
    ("Table V", "all skills: at least", "47.7%", "rq3_copies", "All skills: at least"),
    ("Table V", "all skills: at most", "57.1%", "rq3_copies", "All skills: at most"),
    ("Table V", "unguarded: skills", 59892, "rq3_copies", "Unguarded skills: skills"),
    ("Table V", "unguarded: installations", 93678, "rq3_copies", "Unguarded skills: installations"),
    ("Table V", "unguarded: at least", "40.1%", "rq3_copies", "Unguarded skills: at least"),
    ("Table V", "unguarded: at most", "49.7%", "rq3_copies", "Unguarded skills: at most"),
    ("IV-C RQ3", "unguarded: receiving repositories", 10029, "rq3_copies", "Unguarded skills: receiving repositories"),
    ("Table V", "no-approval: skills", 8054, "rq3_copies", "No-approval skills: skills"),
    ("Table V", "no-approval: installations", 12130, "rq3_copies", "No-approval skills: installations"),
    ("Table V", "no-approval: at least", "39.6%", "rq3_copies", "No-approval skills: at least"),
    ("Table V", "no-approval: at most", "52.2%", "rq3_copies", "No-approval skills: at most"),
    ("IV-C RQ3", "no-approval: receiving repositories", 1340, "rq3_copies", "No-approval skills: receiving repositories"),
    ("Table V", "edited copies of unguarded skills", 1117, "rq3_copies", "edited copies of unguarded skills", "copies"),
    ("Table V", "... manual-start added", "2.6%", "rq3_copies", "edited copies of unguarded skills", "manual-start added"),
    ("Table V", "... with pre-approvals", 177, "rq3_copies", "edited copies of unguarded skills", "with pre-approvals"),
    ("Table V", "... same pre-approvals", "78.5%", "rq3_copies", "edited copies of unguarded skills",
     "with pre-approvals: same"),
    ("IV-C RQ3", "... widened pre-approvals", "12.4%", "rq3_copies", "edited copies of unguarded skills",
     "with pre-approvals: widened"),
    ("IV-C RQ3", "... narrowed pre-approvals", "8.5%", "rq3_copies", "edited copies of unguarded skills",
     "with pre-approvals: narrowed"),
    ("Table V", "edited copies of no-approval skills", 165, "rq3_copies", "edited copies of no-approval skills", "copies"),
    ("Table V", "... manual-start added", "2.4%", "rq3_copies", "edited copies of no-approval skills", "manual-start added"),
    ("Table V", "... with pre-approvals", 165, "rq3_copies", "edited copies of no-approval skills", "with pre-approvals"),
    ("Table V", "... same pre-approvals", "77.0%", "rq3_copies", "edited copies of no-approval skills",
     "with pre-approvals: same"),
]
TABLE_I = [("Build, test & packages", "16.8%", "23.6%", "npm install"), ("Interpreters & scripts", "15.9%", "17.4%", "python3"),
           ("File & text utilities", "12.4%", "15.4%", "grep"), ("Version control", "9.4%", "15.2%", "git diff"),
           ("Network clients", "5.2%", "5.1%", "curl"), ("Code hosting", "3.6%", "6.4%", "gh pr view"),
           ("Cloud & online services", "2.1%", "2.1%", "membrane"), ("System & processes", "2.1%", "2.5%", "sleep"),
           ("Containers & orchestration", "1.7%", "2.3%", "docker compose"), ("AI agent CLIs", "1.1%", "1.1%", "claude"),
           ("Other tools", "0.9%", "1.2%", "openclaw"), ("Media & documents", "0.6%", "0.6%", "ffmpeg"),
           ("Browser automation", "0.6%", "1.0%", "playwright"), ("Security tools", "0.6%", "0.5%", "openssl"),
           ("Databases & migrations", "0.5%", "0.9%", "sqlite3")]
for t, all_, claude, top in TABLE_I:
    CHECKS.append(("Table I", t, [all_, claude, top], "rq1_commands", f"type {t}", ("all", "Claude Code", "most used")))


def actual(script, key, sub=None):
    v = R[script].get(key)
    if isinstance(sub, tuple):
        return [v[s] for s in sub] if v else None
    return v[sub] if (sub and v) else v


def main():
    failed, md = 0, ["| Paper | Number | Value | Produced by |", "|---|---|---|---|"]
    for where, what, expected, script, key, *sub in CHECKS:
        got = actual(script, key, sub[0] if sub else None)
        ok = got == expected
        failed += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {where:<18} {what:<42} paper: {expected!s:<28} computed: {got}")
        md.append(f"| {where} | {what} | {expected} | `{script}.py` ({key}) |")
    (RESULTS / "paper_numbers.md").write_text("\n".join(md) + "\n")
    print(f"\n{len(CHECKS) - failed} of {len(CHECKS)} numbers match the paper; written: results/paper_numbers.md")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
