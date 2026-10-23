"""Step 0: read the GitSkills dataset once and build data/paper.db.

The dataset (agent_skills_release.db) is opened read-only. It lists every SKILL.md file found
on GitHub; files with identical text share a fingerprint (file_sha, the Git blob hash), and the
text of each distinct skill is stored once, on its representative row (dedup_primary = 1).

paper.db holds three tables:
  skills         one row per distinct skill (fingerprint), with what the analyses need:
                 folder class, repository, valid header, commit history and agent trace,
                 name and description, manual-start option, pre-approvals, and the
                 commands the skill tells the agent to run
  installations  one row per SKILL.md file: repository, fingerprint, folder class, path
  repos          stars and main language of each repository

Usage:  python step0_extract.py            (about 5 minutes with 8 processes)
"""
import sqlite3
import time
from multiprocessing import Pool
from pathlib import Path

from skillaudit.commands import FM, commands
from skillaudit.frontmatter import front_matter, manual_start, pre_approvals
from skillaudit.paths import PAPER_DB, dataset_uri
from skillaudit.rules import agent_written

COLUMNS = ("repo_full_name, path, location_class, file_sha, dedup_primary, frontmatter_valid, history_fetched, "
           "has_scripts, first_commit_at, last_commit_at, first_commit_author, first_commit_author_type, "
           "substr(first_commit_message, 1, 3000), name, description, content")


def work(chunk):
    lo, hi = chunk
    con = sqlite3.connect(dataset_uri(), uri=True)
    skills, installs = [], []
    for (repo, path, loc, sha, primary, fm_valid, history, scripts, first, last, author, author_type, message,
         name, desc, content) in con.execute(f"SELECT {COLUMNS} FROM artifacts WHERE rowid BETWEEN ? AND ?", (lo, hi)):
        installs.append((repo, sha, loc, path))
        if not primary:
            continue
        content = (content or "").lstrip("﻿")
        fm, _ = front_matter(content)
        strict, unlabeled, sends = commands(FM.sub("", content, count=1))
        skills.append((sha, loc, repo, int(fm_valid or 0), int(history or 0), first or "", last or "",
                       int(agent_written(message, author, author_type)) if history else 0, name or "", desc or "",
                       int(manual_start(fm)), "\t".join(pre_approvals(fm)), scripts,
                       ",".join(sorted(strict)), ",".join(sorted(unlabeled)), int(sends)))
    con.close()
    return skills, installs


def main():
    Path(PAPER_DB).parent.mkdir(parents=True, exist_ok=True)
    src = sqlite3.connect(dataset_uri(), uri=True)
    top = src.execute("SELECT MAX(rowid) FROM artifacts").fetchone()[0]
    repos = src.execute("SELECT full_name, COALESCE(stars, 0), NULLIF(language, '') FROM repos").fetchall()
    src.close()

    out = sqlite3.connect(PAPER_DB)
    out.executescript("""
        DROP TABLE IF EXISTS skills; DROP TABLE IF EXISTS installations; DROP TABLE IF EXISTS repos;
        CREATE TABLE skills(sha TEXT PRIMARY KEY, loc TEXT, repo TEXT, fm_valid INT, history INT, first_at TEXT,
                            last_at TEXT, agent INT, name TEXT, description TEXT, manual_start INT, grants TEXT,
                            has_scripts INT, cmds_strict TEXT, cmds_unlabeled TEXT, sends INT);
        CREATE TABLE installations(repo TEXT, sha TEXT, loc TEXT, path TEXT);
        CREATE TABLE repos(full_name TEXT PRIMARY KEY, stars INT, language TEXT);
    """)
    out.executemany("INSERT INTO repos VALUES (?,?,?)", repos)
    step = top // 128 + 1
    chunks = [(i, min(i + step - 1, top)) for i in range(1, top + 1, step)]
    t0 = time.time()
    with Pool(8) as pool:
        for done, (skills, installs) in enumerate(pool.imap_unordered(work, chunks), 1):
            out.executemany("INSERT INTO skills VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", skills)
            out.executemany("INSERT INTO installations VALUES (?,?,?,?)", installs)
            out.commit()
            if done % 16 == 0:
                print(f"  {done}/{len(chunks)} chunks ({time.time() - t0:.0f}s)", flush=True)
    out.execute("CREATE INDEX ix_installations_sha ON installations(sha)")
    out.commit()
    n_skills = out.execute("SELECT count(*) FROM skills").fetchone()[0]
    n_files = out.execute("SELECT count(*) FROM installations").fetchone()[0]
    print(f"done in {time.time() - t0:.0f}s: {n_skills:,} distinct skills, {n_files:,} files -> {PAPER_DB}")


if __name__ == "__main__":
    main()
