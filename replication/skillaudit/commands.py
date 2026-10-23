"""Extracts the shell commands a skill tells the agent to run (RQ1).

Commands are read from code blocks labelled as shell (bash, sh, zsh, powershell, ...), from
unlabelled code blocks, and from inline code that starts with a common tool name and has at
least one argument. Table rows (reference lists) and lines that forbid a command ("never run
git push") are skipped. Combined commands are split at &&, ||, ; and |; prompts, helpers
(sudo, env), variable settings and package runners (npx) are removed; each command is kept
as its program plus subcommand (git push), or two levels for tools such as gh pr create.
Skills that send messages (Slack, Discord or Telegram APIs, sendmail) are flagged.

commands(body) returns (strict, unlabeled, sends): commands from shell-labelled blocks and
inline code, commands from unlabelled blocks, and whether the skill sends a message.
Unlabelled-block commands are kept only for known programs whose names are not ordinary
words (classes.census_commands).
"""
import re

FENCE_OPEN = re.compile(r"^\s*(```|~~~)\s*([\w+\-.]*)")
# unlabeled fences count too: outside-acting commands are unambiguous strings,
# and counting more usage keeps the over-privilege measure conservative
SHELL_LANGS = {"", "bash", "sh", "shell", "zsh", "console", "terminal", "shell-session", "shellsession", "fish",
               "powershell", "pwsh", "ps1", "cmd", "bat", "batch"}
INLINE = re.compile(r"`([^`\n]+)`")
SPLIT = re.compile(r"\s*(?:&&|\|\||;|\|)\s*")
FM = re.compile(r"\A\s*---[ \t]*\r?\n.*?\r?\n---[ \t]*(?:\r?\n|\Z)", re.S)
NEG = re.compile(r"\b(never|don't|do not|must not|should not|avoid|unless|blocked|forbidden|prohibited)\b", re.I)
SEND = re.compile(r"chat\.postMessage|hooks\.slack\.com/|discord(app)?\.com/api/webhooks|api\.telegram\.org/bot[^\s]*/send"
                  r"|\bsendmail\b|\bmail\s+-s\b", re.I)

DEPTH3 = {"gh", "glab", "aws", "az", "gcloud", "prisma", "supabase", "shopify", "eas", "php"}
DEPTH2 = {"git", "npm", "pnpm", "yarn", "bun", "docker", "kubectl", "helm", "terraform", "pulumi", "cargo", "pip",
          "pip3", "uv", "poetry", "go", "dotnet", "vercel", "netlify", "fly", "flyctl", "firebase", "wrangler",
          "heroku", "rails", "bundle", "make", "deno", "brew", "systemctl", "sam", "cdk", "serverless", "twine",
          "gem", "railway", "fastlane", "alembic", "flyway", "knex", "sequelize", "drizzle-kit", "mix", "composer",
          "artisan", "rake", "mvn", "gradle", "./gradlew", "swift", "xcodebuild", "expo", "turbo", "nx"}
LAUNCHERS = {"sudo", "time", "exec", "env", "command", "nohup"}
RUNNERS = {"npx", "bunx", "pnpx"}
INLINE_HEADS = DEPTH3 | DEPTH2 | {"python", "python3", "node", "bash", "sh", "curl", "wget", "ssh", "scp", "rsync",
                                  "psql", "mysql", "sqlite3", "redis-cli", "npx", "bunx", "pnpx", "rm", "mv", "cp"}
WORD = re.compile(r"^[a-z][\w:.\-]*$")


def prefix(segment):
    toks = [t.strip("'\"") for t in segment.split()]
    while toks and (toks[0] in LAUNCHERS or re.match(r"^\w+=", toks[0])):
        toks.pop(0)
    if toks and toks[0] in RUNNERS:
        toks.pop(0)
    if toks and toks[0] in ("pnpm", "yarn") and len(toks) > 1 and toks[1] in ("dlx", "exec"):
        toks = toks[2:]
    if not toks:
        return None
    head = toks[0].lower()
    if not re.match(r"^[a-z./][\w.\-/]*$", head):
        return None
    depth = 3 if head in DEPTH3 else 2 if head in DEPTH2 else 1
    words = [head] + [t.lower() for t in toks[1:] if WORD.match(t.lower())][:depth - 1]
    return " ".join(words)


def commands(body):
    """Command prefixes the skill tells the agent to run, split by where they appear
    (shell-labelled blocks and inline code vs unlabelled blocks), and whether it sends a message.
    Skips table rows (reference lists) and negated lines ("never run `git push`")."""
    strict, unlabeled, sends, lang, in_fence = set(), set(), False, "", False
    for line in body.splitlines():
        m = FENCE_OPEN.match(line)
        if m:
            if in_fence:
                in_fence = False
            else:
                in_fence, lang = True, m.group(2).lower()
            continue
        if line.lstrip().startswith("|") or NEG.search(line):
            continue
        if in_fence:
            if lang not in SHELL_LANGS:
                continue
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            sends = sends or bool(SEND.search(s))
            s = re.sub(r"^[$%]\s+", "", s)
            target = unlabeled if lang == "" else strict
            for seg in SPLIT.split(s):
                p = prefix(seg)
                if p:
                    target.add(p)
        else:
            for span in INLINE.findall(line):
                toks = span.split()
                head = toks[0].lower() if toks else ""
                # a single backticked word names a tool ("deploy to `vercel`"); a command has arguments
                if head in INLINE_HEADS and len(toks) >= 2:
                    sends = sends or bool(SEND.search(span))
                    p = prefix(span)
                    if p:
                        strict.add(p)
    return strict, unlabeled, sends
