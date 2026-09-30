"""Post one update to X (Twitter) - shared by every Quiet Forensics project. Standard library only.

ORIGINAL: security-biz/qf-common/python/qf_x.py - projects hold a synced copy; do not edit it there.

    from qf_x import fit, post
    result = post(fit("週次更新 ...", url="https://jart.quietforensics.com/"))

- Credentials come from X_API_KEY / X_API_SECRET / X_ACCESS_TOKEN / X_ACCESS_SECRET (OAuth 1.0a
  user context), looked up by qf_env: the environment first, then the shared qf-common/.env. Without all four, or with dry_run=True, nothing is sent and the text is returned:
  a CI run without secrets never fails and never posts.
- Length is counted the way X counts it (twitter-text v3): CJK and most non-Latin characters weigh
  2, any http(s) URL weighs 23, the limit is 280. Plain len() lets a Japanese post through that X
  then rejects.
- Messages never contain a secret. Posting is an outward action: the caller decides when to post;
  nothing here retries or schedules.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import re
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

try:  # synced as a package (qf_common.qf_x) or imported as a top-level module
    from . import qf_env
except ImportError:
    import qf_env  # type: ignore[no-redef]

ENDPOINT = "https://api.x.com/2/tweets"
MAX_WEIGHT = 280
URL_WEIGHT = 23
ENV_KEYS = ("X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_SECRET")

# twitter-text v3: code points in these ranges weigh 1, everything else 2
_LIGHT = ((0, 4351), (8192, 8205), (8208, 8223), (8242, 8247))
_URL = re.compile(r"https?://[^\s]+")


class XPostError(RuntimeError):
    pass


@dataclass(frozen=True)
class Credentials:
    consumer_key: str
    consumer_secret: str
    access_token: str
    access_secret: str

    @classmethod
    def from_env(cls, env: Mapping[str, str | None]) -> Credentials | None:
        values = [env.get(k) or "" for k in ENV_KEYS]
        return cls(*values) if all(values) else None

    def __repr__(self) -> str:  # never print secrets, even by accident
        return f"Credentials(consumer_key={self.consumer_key!r}, access_token={self.access_token!r}, secrets=***)"


@dataclass(frozen=True)
class PostResult:
    text: str
    posted: bool
    tweet_id: str | None = None
    skipped_reason: str | None = None


# ---------------------------------------------------------------- length
def _char_weight(ch: str) -> int:
    cp = ord(ch)
    return 1 if any(lo <= cp <= hi for lo, hi in _LIGHT) else 2


def weighted_length(text: str) -> int:
    total, pos = 0, 0
    for m in _URL.finditer(text):
        total += sum(_char_weight(c) for c in text[pos:m.start()]) + URL_WEIGHT
        pos = m.end()
    return total + sum(_char_weight(c) for c in text[pos:])


def fits(text: str) -> bool:
    return weighted_length(text) <= MAX_WEIGHT


def fit(body: str, url: str | None = None) -> str:
    """`body` (+ newline + `url`) within the limit; the body is cut with "…", the URL is never cut."""
    tail = f"\n{url}" if url else ""
    if fits(body + tail):
        return body + tail
    budget = MAX_WEIGHT - weighted_length(tail) - _char_weight("…")  # the ellipsis itself weighs 2
    out, used = [], 0
    for ch in body:
        w = _char_weight(ch)
        if used + w > budget:
            break
        out.append(ch)
        used += w
    return "".join(out).rstrip() + "…" + tail


# ---------------------------------------------------------------- OAuth 1.0a
def _q(s: str) -> str:
    return urllib.parse.quote(s, safe="-._~")


def signature(method: str, url: str, params: Mapping[str, str], consumer_secret: str, token_secret: str) -> str:
    pairs = sorted((_q(k), _q(v)) for k, v in params.items())
    base = "&".join([method.upper(), _q(url), _q("&".join(f"{k}={v}" for k, v in pairs))])
    key = f"{_q(consumer_secret)}&{_q(token_secret)}"
    return base64.b64encode(hmac.new(key.encode(), base.encode(), hashlib.sha1).digest()).decode()


def authorization_header(method: str, url: str, creds: Credentials | None, *, nonce: str | None = None, timestamp: str | None = None) -> str:
    if creds is None:
        raise XPostError("no X credentials")
    oauth = {
        "oauth_consumer_key": creds.consumer_key,
        "oauth_nonce": nonce or secrets.token_hex(16),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": timestamp or str(int(time.time())),
        "oauth_token": creds.access_token,
        "oauth_version": "1.0",
    }
    # a JSON body is not part of the signature base; only the oauth_* parameters (and a query string) are
    oauth["oauth_signature"] = signature(method, url, oauth, creds.consumer_secret, creds.access_secret)
    return "OAuth " + ", ".join(f'{_q(k)}="{_q(v)}"' for k, v in sorted(oauth.items()))


# ---------------------------------------------------------------- post
def post(
    text: str,
    *,
    env: Mapping[str, str | None] | None = None,
    dry_run: bool = False,
    opener: Callable[..., Any] = urllib.request.urlopen,
    timeout: float = 20.0,
) -> PostResult:
    if not fits(text):
        raise XPostError(f"text weighs {weighted_length(text)}, over the {MAX_WEIGHT} limit - shorten it with fit()")
    if dry_run:
        return PostResult(text=text, posted=False, skipped_reason="dry run")
    creds = Credentials.from_env(qf_env.values(ENV_KEYS) if env is None else env)
    if creds is None:
        return PostResult(text=text, posted=False, skipped_reason="X credentials not set (" + ", ".join(ENV_KEYS) + ")")
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps({"text": text}, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={"Authorization": authorization_header("POST", ENDPOINT, creds), "Content-Type": "application/json"},
    )
    try:
        with opener(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = str(json.loads(exc.read().decode("utf-8") or "{}").get("title") or "")
        except (ValueError, AttributeError):
            pass
        raise XPostError(f"X API HTTP {exc.code}{': ' + detail if detail else ''}") from None
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise XPostError(f"X API network error: {type(exc).__name__}") from None
    tweet_id = (body.get("data") or {}).get("id") if isinstance(body, dict) else None
    if not tweet_id:
        raise XPostError("X API returned an unexpected response (no data.id)")
    return PostResult(text=text, posted=True, tweet_id=str(tweet_id))
