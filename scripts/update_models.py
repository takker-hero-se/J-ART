#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Add newly released models to config.yaml as naked targets (run weekly by update-models.yml).

    python scripts/update_models.py --dry-run      # list what would be added
    python scripts/update_models.py                # append them to config.yaml

Source: the public OpenRouter model catalogue (no API key needed). Rules, chosen to keep the
weekly LIVE evaluation affordable and the leaderboard meaningful:
- only vendors in VENDORS, released within --window-days, accepting text input;
- variants are skipped (batch/free/preview/experimental/premium tiers/audio-image-only);
- prompt price at most --price-cap USD per million tokens;
- at most one model per vendor and --max-new models per run, newest first (on a tie the
  shorter id, i.e. the base model, wins);
- a model already in config.yaml (by direct or OpenRouter spelling) is never added twice.
New models are measured as "naked API" configurations through OpenRouter; hardened or guarded
variants are added by hand.
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.request
from datetime import date, datetime, timezone

import yaml

CATALOG_URL = "https://openrouter.ai/api/v1/models"
VENDORS = ("openai/", "anthropic/", "google/", "meta-llama/", "qwen/", "deepseek/", "mistralai/", "x-ai/", "z-ai/")
_VARIANT = re.compile(r"(:batch|:free|:beta|:extended|preview|-exp\b|-exp-|experimental|-prime\b|vision|omni|"
                      r"audio|image|tts|realtime|embed|search|guard|instruct-old)", re.I)
ANCHOR = "# ---------------------------------------------------------------------\n# ベース攻撃（MITRE ATLAS 準拠）"
SECTION = ("  # ===================================================================\n"
           "  # 自動追加（scripts/update_models.py, 毎週）— 新しく公開されたモデルを素のAPIで測る。\n"
           "  # ===================================================================\n")


def normalize(model_id: str) -> str:
    """Comparable name: vendor prefix dropped, dots as dashes, a trailing date snapshot removed
    (qwen3.8-max-0902 and deepseek-v4-pro-0813 are the models already tracked without the date)."""
    name = model_id.strip().lower().split("/")[-1].split(":")[0].replace(".", "-")
    return re.sub(r"-(\d{4}|\d{6}|\d{8})$", "", name)


def tracked_models(config_path: str) -> set:
    with open(config_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return {normalize(t["model"]) for t in cfg.get("targets", []) if t.get("model")}


def _price_per_million(m) -> float:
    try:
        return float((m.get("pricing") or {}).get("prompt") or 0) * 1_000_000
    except (TypeError, ValueError):
        return float("inf")


def select_new_models(catalog, tracked, *, now=None, max_new=3, window_days=45, price_cap=5.0):
    now = now if now is not None else time.time()
    seen = {normalize(t) for t in tracked}
    cands = []
    for m in catalog:
        mid = m.get("id", "")
        if not mid.startswith(VENDORS) or _VARIANT.search(mid):
            continue
        if "text" not in ((m.get("architecture") or {}).get("input_modalities") or []):
            continue
        if now - int(m.get("created") or 0) > window_days * 86400 or _price_per_million(m) > price_cap:
            continue
        if normalize(mid) in seen:
            continue
        cands.append(m)
    # newest day first; within a day the shorter id (the base model, not "-pro"/"-max" tiers) wins
    cands.sort(key=lambda m: (-(int(m.get("created") or 0) // 86400), len(m["id"]), m["id"]))
    picked, vendors = [], set()
    for m in cands:
        vendor = m["id"].split("/")[0]
        if vendor in vendors:
            continue
        picked.append(m)
        vendors.add(vendor)
        if len(picked) >= max_new:
            break
    return picked


def _label(m) -> str:
    name = (m.get("name") or m["id"].split("/")[-1]).split(":", 1)[-1].strip()
    return name.replace('"', "'")


def target_block(m, today=None) -> str:
    today = today or date.today().isoformat()
    slug = re.sub(r"[^a-z0-9]+", "-", normalize(m["id"])).strip("-")
    label = _label(m)
    return (
        f"  - id: openrouter-{slug}-naked  # auto-added {today} (OpenRouter released "
        f"{datetime.fromtimestamp(int(m.get('created') or 0), timezone.utc).date().isoformat()})\n"
        f'    label: "{label} / 素のAPI (OpenRouter)"\n'
        f'    label_en: "{label} / bare API (OpenRouter)"\n'
        "    provider: openai_compatible\n"
        '    base_url: "https://openrouter.ai/api/v1"\n'
        "    api_key_env: OPENROUTER_API_KEY\n"
        f'    model: "{m["id"]}"\n'
        "    prompt_strength: low\n"
        "    guardrail: none\n"
        "    rag: true\n\n"
    )


def apply(config_path: str, models, today=None):
    text = open(config_path, encoding="utf-8").read()
    tracked = {normalize(t) for t in tracked_models(config_path)}
    new = [m for m in models if normalize(m["id"]) not in tracked]
    if not new:
        return []
    assert text.count(ANCHOR) == 1, "attacks section anchor not found in config.yaml"
    blocks = "".join(target_block(m, today) for m in new)
    if SECTION not in text:
        blocks = SECTION + blocks
    i = text.index(ANCHOR)
    text = text[:i].rstrip("\n") + "\n\n" + blocks + text[i:]
    yaml.safe_load(text)  # never write an unparseable config
    with open(config_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return [m["id"] for m in new]


def fetch_catalog(url=CATALOG_URL):
    req = urllib.request.Request(url, headers={"User-Agent": "j-art-update-models/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)["data"]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max-new", type=int, default=int(os.environ.get("JART_MAX_NEW_MODELS", "3")))
    ap.add_argument("--window-days", type=int, default=45)
    ap.add_argument("--price-cap", type=float, default=5.0, help="max prompt price, USD per million tokens")
    args = ap.parse_args(argv)
    picked = select_new_models(fetch_catalog(), tracked_models(args.config), max_new=args.max_new,
                               window_days=args.window_days, price_cap=args.price_cap)
    for m in picked:
        print(f"candidate: {m['id']}  ({_label(m)}, ${_price_per_million(m):.2f}/M prompt)")
    if args.dry_run or not picked:
        print("no change" if not picked else "dry run: config.yaml not modified")
        return 0
    added = apply(args.config, picked)
    print("added: " + ", ".join(added))
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as f:
            f.write("added=" + ", ".join(added) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
