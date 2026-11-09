# -*- coding: utf-8 -*-
"""Numbers for the Japanese prompt-injection talk, from experiments/live_latest.json.

Subsets (each trial counted once; cells with api_error excluded):
  naked     = prompt low + guardrail none, configurations with no api_error at all
  by guard  = every configuration, grouped by guardrail setting
Detection  = share of trials a guardrail blocked at the input, per transform group.
Usage: python experiments/slide_numbers.py
"""
import json, os, sys
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from run_assessment import wilson_ci  # noqa: E402

d = json.load(open(os.path.join(os.path.dirname(__file__), "live_latest.json"), encoding="utf-8"))
det = [x for x in d["details"] if not x.get("api_error")]
summ = {s["target_id"]: s for s in d["summary"]}
print("run", d["generated_at"], "clean trials", len(det))

naked_ids = sorted(t for t, s in summ.items() if s["prompt_strength"] == "low" and s["guardrail"] == "none" and s["n_api_error"] == 0)
nk = [x for x in det if x["target_id"] in naked_ids]
b = sum(x["breached"] for x in nk); n = len(nk); lo, hi = wilson_ci(n - b, n)
print(f"\n[naked] configs {len(naked_ids)}, trials {n}, breached {b} = {b/n*100:.1f}%  (defense CI {lo:.1f}-{hi:.1f})")

def rate(rows):
    b = sum(x["breached"] for x in rows); return b, len(rows), (b / len(rows) * 100 if rows else 0)

print("\n[naked] by transform")
for tr in ["double_tongue", "baseline", "polite_business", "vertical_newline", "gyaru", "leet_smuggle", "base64_wrap"]:
    b, n, r = rate([x for x in nk if x["transformation"] == tr]); print(f"  {tr:<18}{r:5.1f}%  {b}/{n}")
print("\n[naked] by attack (top)")
by = defaultdict(list)
for x in nk: by[(x["attack_id"], x["atlas_id"])].append(x)
for (a, at), rows in sorted(by.items(), key=lambda kv: -rate(kv[1])[2]):
    b, n, r = rate(rows); print(f"  {a:<26}{at:<15}{r:5.1f}%  {b}/{n}")

print("\n[naked] by model (77 trials each)")
for t in sorted(naked_ids, key=lambda t: -rate([x for x in nk if x['target_id'] == t])[2]):
    rows = [x for x in nk if x["target_id"] == t]; b, n, r = rate(rows); lo, hi = wilson_ci(b, n)
    print(f"  {summ[t]['model']:<34}{b:>3}/{n}  {r:5.1f}%  CI {lo:.1f}-{hi:.1f}")

print("\n[all configs] breach by guardrail (prompt strength mixed)")
for g in ["none", "keyword", "regex", "llamaguard", "llm"]:
    for p in ["low", "high"]:
        rows = [x for x in det if x["guardrail"] == g and summ[x["target_id"]]["prompt_strength"] == p]
        if rows:
            b, n, r = rate(rows); lo, hi = wilson_ci(b, n)
            print(f"  {g:<11}{p:<5}configs {len({x['target_id'] for x in rows}):>2}  {b:>4}/{n:<5}{r:5.1f}%  CI {lo:.1f}-{hi:.1f}")

OBF = ["vertical_newline", "gyaru", "base64_wrap", "leet_smuggle"]
CLEAR = ["baseline", "polite_business", "double_tongue"]
print("\n[input-block rate] share of trials the guardrail blocked before the model")
for g, key in [("keyword", "キーワードガードレール"), ("regex", "正規化フィルタ")]:
    for name, grp in [("obfuscated 4", OBF), ("verbatim 3", CLEAR)]:
        rows = [x for x in det if x["guardrail"] == g and x["transformation"] in grp]
        k = sum(1 for x in rows if key in (x.get("reason") or ""))
        print(f"  {g:<8}{name:<13}{k:>4}/{len(rows):<4}{k/len(rows)*100:5.1f}%")
    for tr in OBF + CLEAR:
        rows = [x for x in det if x["guardrail"] == g and x["transformation"] == tr]
        k = sum(1 for x in rows if key in (x.get("reason") or ""))
        print(f"      {tr:<18}{k:>3}/{len(rows):<3}")
