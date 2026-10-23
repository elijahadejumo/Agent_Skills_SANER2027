"""Definitions used across the research questions, and the statistics.

unrestricted shell  a pre-approval of every shell command: Bash or Bash(*)
scoped              a pre-approval of the commands that start with a given text, e.g.
                    Bash(git:*) or Bash(git diff *); stems() returns those texts
covered()           whether a skill's pre-approvals cover its outside action
agent-written       the commit that first added the skill names an AI agent
"""
import math
import re

from scipy.stats import chi2, chi2_contingency

UNRESTRICTED = re.compile(r"^Bash(\(\s*[\*:\s]*\))?$")
AGENT = re.compile(r"co-authored-by:[^\n]*(claude|cursor|copilot|codex|gemini|devin|aider|windsurf|cline|openhands|jules|kiro)"
                   r"|noreply@anthropic\.com|generated with \[?claude|claude\.(ai|com)/(code|claude-code)|cursoragent"
                   r"|copilot-swe-agent|chatgpt-codex|devin-ai|openai-codex", re.I)
BOT_AGENT = re.compile(r"copilot|claude|devin|codex|cursor|jules|openhands|gemini|kiro", re.I)


def agent_written(message, author, author_type):
    return bool(AGENT.search(message or "")) or (author_type == "Bot" and bool(BOT_AGENT.search(author or "")))


def stems(grants):
    """Command prefixes allowed by scoped shell pre-approvals: Bash(git:*) -> 'git'."""
    out = []
    for t in grants:
        if t.startswith("Bash(") and not UNRESTRICTED.match(t):
            for pat in t[5:-1].split(","):
                s = re.sub(r"[\s:*]+$", "", pat.strip()).lower()
                if s:
                    out.append(s)
    return out


def covered(outside_commands, grants, sends):
    """Would the skill's outside actions run without a permission prompt?"""
    if any(UNRESTRICTED.match(t) for t in grants):
        return True
    st = stems(grants)
    hit = lambda p: any(p == s or p.startswith(s + " ") or s.startswith(p + " ") for s in st)
    return any(hit(p) for p in outside_commands) or (sends and hit("curl"))


def two_by_two(a, b, c, d):
    """Chi-square test on [[a, b], [c, d]]: (chi2, p, phi = Cramer's V, odds ratio, 95% CI)."""
    n = a + b + c + d
    x2 = n * (a * d - b * c) ** 2 / ((a + b) * (c + d) * (a + c) * (b + d))
    odds = (a * d) / (b * c)
    se = math.sqrt(1 / a + 1 / b + 1 / c + 1 / d)
    return x2, chi2.sf(x2, 1), math.sqrt(x2 / n), odds, math.exp(math.log(odds) - 1.96 * se), math.exp(math.log(odds) + 1.96 * se)


def cramers_v(table):
    """Chi-square test across groups, table = [[yes, no], ...]: (Cramer's V, p)."""
    x2, p, _, _ = chi2_contingency(table)
    return math.sqrt(x2 / sum(map(sum, table))), p
