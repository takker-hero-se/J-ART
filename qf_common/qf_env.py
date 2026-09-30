"""Shared settings for every Quiet Forensics project: the environment first, then qf-common/.env.

ORIGINAL: security-biz/qf-common/python/qf_env.py - projects hold a synced copy; do not edit it there.

    from qf_common import qf_env
    token = qf_env.get("X_ACCESS_TOKEN")

- Locally, shared values (X keys, ...) live once in security-biz/qf-common/.env, which git ignores
  and qf_sync never copies. The file is found by walking up from the working directory (and from
  this module) to a folder that has qf-common/.env beside it; QF_ENV_FILE names another file.
- In CI and on Cloud Run there is no such file: the platform's secrets arrive as environment
  variables, which always win. An empty variable counts as unset.
- Values are never logged or printed here.
"""
from __future__ import annotations

import os
import re
from collections.abc import Iterable
from pathlib import Path

_LINE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$")


def read_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        m = _LINE.match(raw)
        if not m:
            continue
        v = m.group(2)
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1]
        values[m.group(1)] = v
    return values


def find_shared_env(start: Path | None = None) -> Path | None:
    explicit = os.environ.get("QF_ENV_FILE")
    if explicit:
        p = Path(explicit)
        return p if p.is_file() else None
    # an explicit start is searched alone (tests, callers that know their project); otherwise the
    # working directory, then this module's own location
    starts = [Path(start)] if start else [Path.cwd(), Path(__file__).resolve().parent]
    for s in starts:
        s = s.resolve()
        for d in (s, *s.parents):
            for cand in (d / "qf-common" / ".env", d / ".env" if d.name == "qf-common" else None):
                if cand is not None and cand.is_file():
                    return cand
    return None


def values(keys: Iterable[str], start: Path | None = None) -> dict[str, str | None]:
    keys = list(keys)
    out: dict[str, str | None] = {k: (os.environ.get(k) or None) for k in keys}
    if any(v is None for v in out.values()):
        path = find_shared_env(start)
        shared = read_env_file(path) if path else {}
        for k in keys:
            if out[k] is None:
                out[k] = shared.get(k) or None
    return out


def get(key: str, start: Path | None = None) -> str | None:
    return values([key], start)[key]
