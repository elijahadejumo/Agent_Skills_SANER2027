"""Reads a skill's YAML header: the manual-start option and the pre-approved tools.

manual_start(fm)  True when the header sets disable-model-invocation: true (or yes)
pre_approvals(fm) the entries of allowed-tools (or allowed_tools), as written, e.g.
                  ["Read", "Bash(git:*)"]; lists and space- or comma-separated strings are accepted
"""
import re

import yaml

LOADER = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
FM = re.compile(r"\A\s*---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)(.*)\Z", re.S)
TOOL_TOKEN = re.compile(r"[A-Za-z_][\w\-]*(?:\([^)]*\))?")


def front_matter(content):
    """(header as a dict or None, body)."""
    m = FM.match(content.lstrip("﻿"))
    if not m:
        return None, content
    try:
        fm = yaml.load(m.group(1), Loader=LOADER)
        return (fm if isinstance(fm, dict) else None), m.group(2)
    except yaml.YAMLError:
        return None, m.group(2)


def manual_start(fm):
    return str((fm or {}).get("disable-model-invocation", "")).strip().lower() in ("true", "yes")


def pre_approvals(fm):
    value = (fm or {}).get("allowed-tools") or (fm or {}).get("allowed_tools")
    items = value if isinstance(value, list) else ([value] if value else [])
    return [t for it in items for t in TOOL_TOKEN.findall(str(it))]
