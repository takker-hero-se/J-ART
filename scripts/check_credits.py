#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Detect exhausted API credits after an evaluation and fail, so GitHub e-mails the owner.

    python scripts/check_credits.py --results results.json

- Counts trials whose API error says the billing account is out of credit (Anthropic "credit
  balance is too low", OpenAI "no credits remaining" / insufficient_quota, OpenRouter 402
  "insufficient credits"). Rate limits are not credit problems and are ignored.
- If OPENROUTER_API_KEY is set, also reads the OpenRouter balance and warns below --threshold USD.
- Writes a summary with top-up links (to GITHUB_STEP_SUMMARY when present) and exits 1 when
  anything needs topping up. Run it as its own job: a failure must not block publishing.
"""
import argparse
import json
import os
import re
import sys
import urllib.request

TOP_UP = {
    "anthropic": ("Anthropic", "https://console.anthropic.com/settings/billing"),
    "openai": ("OpenAI", "https://platform.openai.com/settings/organization/billing"),
    "openrouter": ("OpenRouter", "https://openrouter.ai/settings/credits"),
    "google": ("Google AI (Gemini)", "https://aistudio.google.com/apikey"),
}
_CREDIT = re.compile(r"credit balance is too low|no credits remaining|insufficient[_ ]quota|insufficient credits|"
                     r"requires more credits|exceeded your current quota|billing", re.I)
_ACCOUNT = {"anthropic": "anthropic", "openai": "openai", "openai_compatible": "openrouter", "gemini": "google"}


def exhausted(results) -> dict:
    found = {}
    for d in results.get("details", []):
        if not (d.get("api_error") or d.get("api_errors")):
            continue
        if _CREDIT.search(d.get("response_excerpt") or ""):
            acct = _ACCOUNT.get(d.get("provider"), d.get("provider") or "unknown")
            found[acct] = found.get(acct, 0) + 1
    return found


def balance_problem(balance, threshold=5.0) -> bool:
    return balance is not None and balance < threshold


def openrouter_balance():
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        return None
    req = urllib.request.Request("https://openrouter.ai/api/v1/credits", headers={"Authorization": f"Bearer {key}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r).get("data") or {}
        return float(data.get("total_credits", 0)) - float(data.get("total_usage", 0))
    except Exception as e:  # noqa: BLE001 - an unknown balance is reported as unknown, not as a problem
        print(f"OpenRouter balance unavailable: {type(e).__name__}")
        return None


def report(found, balance=None, threshold=5.0) -> str:
    lines = ["## J-ART: API credits need attention", ""]
    for acct, n in sorted(found.items()):
        name, url = TOP_UP.get(acct, (acct, ""))
        lines.append(f"- **{name}**: {n} trials failed for lack of credit. Top up: {url}")
    if balance_problem(balance, threshold):
        lines.append(f"- **OpenRouter** balance is ${balance:.2f} (below ${threshold:.2f}). Top up: {TOP_UP['openrouter'][1]}")
    lines += ["", "Trials that failed are excluded from the leaderboard; rerun the evaluation after topping up "
              "(Actions → Eval & Deploy → Run workflow)."]
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results", default="results.json")
    ap.add_argument("--threshold", type=float, default=float(os.environ.get("JART_CREDIT_THRESHOLD", "5")))
    args = ap.parse_args(argv)
    try:
        with open(args.results, encoding="utf-8") as f:
            results = json.load(f)
    except FileNotFoundError:
        results = {}
    found = exhausted(results)
    balance = openrouter_balance()
    if not found and not balance_problem(balance, args.threshold):
        print("credits OK" + (f" (OpenRouter ${balance:.2f})" if balance is not None else ""))
        return 0
    text = report(found, balance, args.threshold)
    print(text)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write(text + "\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
