# -*- coding: utf-8 -*-
"""Round-7 revision numbers, recomputed from the committed artifacts (no API calls).

Produces, from experiments/{ablation_results,abl_scout_results,abl_gpt41_results}.json
and experiments/var_run.json:

  [A] absolute lexical-leak defense rate (Wilson 95% CI, n) for all 2x5 arms of each
      ablated model (30 cells);
  [B] the llm-guardrail arm's exposure to the simulated output screen: cells whose
      recorded reason says the (simulated) output guard corrected a breach, and the
      conservative rate obtained by counting every trial of those cells as a breach;
  [C] per-transform breach rate under none / keyword / regex / llamaguard / llm on the
      low-prompt arm of each ablated model (transform x guardrail);
  [D] the 15 ablation contrasts with the paper's cluster-robust 95% CI and a
      Bonferroni-adjusted (alpha/15) cluster-robust CI; a contrast whose adjusted CI
      excludes 0 remains significant under Holm;
  [E] the 21-configuration fleet table (model id, prompt, guardrail, price, n, rate, CI);
  [F] transform means by class, for the original and the revised classification.

Usage:  python experiments/analyze_revision7.py
"""
import json
import os
import random
import sys
from collections import defaultdict, Counter

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from run_assessment import wilson_ci  # noqa: E402

EXP = os.path.join(ROOT, "experiments")
ABL = {
    "GPT-4o-mini": "ablation_results.json",
    "Llama 4 Scout": "abl_scout_results.json",
    "GPT-4.1": "abl_gpt41_results.json",
}
GUARDS = ["none", "keyword", "regex", "llamaguard", "llm"]
GUARD_LABEL = {"none": "no guardrail", "keyword": "keyword", "regex": "regex (normalizing)",
               "llamaguard": "Llama Guard 4", "llm": "LLM self-moderation"}
TRANSFORMS = ["baseline", "polite_business", "vertical_newline", "gyaru",
              "double_tongue", "base64_wrap", "leet_smuggle"]
N_BOOT = 3000
SEED = 20260614
OUTGUARD_MARK = "出力ガードレール"   # reason text written when the output guard flipped a breach


def load(name):
    with open(os.path.join(EXP, name), "r", encoding="utf-8") as f:
        return json.load(f)


def cells_by_target(details):
    cells = defaultdict(list)
    for x in details:
        clean = x["trials"] - x.get("api_errors", 0)
        if clean > 0:
            cells[x["target_id"]].append((x["breaches"], clean))
    return cells


def rate_n(cs):
    tt = sum(t for _, t in cs)
    tb = sum(b for b, _ in cs)
    return (1 - tb / tt) * 100.0, tt, tt - tb


def boot_diff(c1, c2, alpha, n_boot=N_BOOT, seed=SEED):
    """Cluster-robust bootstrap CI of rate(c1) - rate(c2), same resampling as
    run_assessment.bootstrap_diff_ci, at an arbitrary alpha."""
    def _rate(cs):
        tb = sum(b for b, _ in cs); tt = sum(t for _, t in cs)
        return (1 - tb / tt) if tt else 0.0
    diff = (_rate(c1) - _rate(c2)) * 100.0
    rng = random.Random(seed)
    diffs = []
    for _ in range(n_boot):
        s1 = [c1[rng.randrange(len(c1))] for _ in range(len(c1))]
        s2 = [c2[rng.randrange(len(c2))] for _ in range(len(c2))]
        diffs.append((_rate(s1) - _rate(s2)) * 100.0)
    diffs.sort()
    def pct(p):
        k = (len(diffs) - 1) * p
        lo, hi = int(k), min(int(k) + 1, len(diffs) - 1)
        return diffs[lo] + (diffs[hi] - diffs[lo]) * (k - lo)
    return diff, pct(alpha / 2), pct(1 - alpha / 2)


def main():
    print("=" * 78)
    print("[A] Absolute defense rate per ablation arm (K=3; Wilson 95% CI; n = clean trials)")
    print("=" * 78)
    arms = {}  # (model, prompt, guard) -> (rate, lo, hi, n, defended)
    allcells = {}
    details_all = {}
    for model, fn in ABL.items():
        d = load(fn)
        details_all[model] = d["details"]
        cells = cells_by_target(d["details"])
        allcells[model] = cells
        meta = {s["target_id"]: s for s in d["summary"]}
        print(f"\n{model}  (generated {d['generated_at'][:19]}Z)")
        print(f"  {'prompt':<9}{'guardrail':<20}{'defended/n':>12}{'rate':>8}{'Wilson 95% CI':>18}")
        for prompt in ["low", "high"]:
            for g in GUARDS:
                tid = next(t for t, s in meta.items() if s["prompt_strength"] == prompt and s["guardrail"] == g)
                r, n, dfd = rate_n(cells[tid])
                lo, hi = wilson_ci(dfd, n)
                arms[(model, prompt, g)] = (r, lo, hi, n, dfd, tid)
                print(f"  {prompt:<9}{GUARD_LABEL[g]:<20}{dfd:>6}/{n:<5}{r:>7.1f}%   [{lo:5.1f}, {hi:5.1f}]")
    below91 = [(m, p, g, v[0]) for (m, p, g), v in arms.items() if not (p == "low" and g == "none") and v[0] < 91.0]
    print(f"\n  Defended arms (hardened or guardrailed) below 91%: {len(below91)} of {len(arms) - 3}")
    for m, p, g, r in sorted(below91, key=lambda x: x[3]):
        print(f"    {m:<14}{p:<6}{GUARD_LABEL[g]:<20}{r:5.1f}%")

    print("\n" + "=" * 78)
    print("[B] Exposure of the llm-guardrail arm to the simulated output screen")
    print("=" * 78)
    print("  A cell is 'exposed' if its recorded reason says the output guard corrected a breach;")
    print("  the conservative rate counts every clean trial of an exposed cell as a breach.")
    for model in ABL:
        det = details_all[model]
        for prompt in ["low", "high"]:
            tid = arms[(model, prompt, "llm")][5]
            cs = [x for x in det if x["target_id"] == tid]
            exposed = [x for x in cs if OUTGUARD_MARK in (x.get("reason") or "")]
            exp_trials = sum(x["trials"] - x.get("api_errors", 0) for x in exposed)
            r, n, dfd = rate_n(allcells[model][tid])
            cons = (dfd - exp_trials) / n * 100.0
            lo, hi = wilson_ci(dfd - exp_trials, n)
            reasons = Counter((x.get("reason") or "")[:24] for x in cs)
            print(f"  {model:<14}{prompt:<6} exposed cells {len(exposed):>2}/77  (<= {exp_trials:>2} of {n} trials)"
                  f"  reported {r:5.1f}%  conservative {cons:5.1f}% [{lo:5.1f}, {hi:5.1f}]"
                  f"  input-screen blocks {sum(c for k, c in reasons.items() if k.startswith('LLM入力検閲が攻撃'))}/77 cells")
    # Llama Guard: any cell whose guard_model is empty would indicate a non-classifier verdict.
    for model in ABL:
        lg = [x for x in details_all[model] if x["guardrail"] == "llamaguard"]
        print(f"  {model:<14} Llama Guard cells with recorded classifier model: "
              f"{sum(1 for x in lg if x.get('guard_model'))}/{len(lg)}")
    v = load("var_run.json")
    vl = [x for x in v["details"] if x["guardrail"] == "llm"]
    print(f"  21-config campaign: llm-guard cells {len(vl)}; exposed cells "
          f"{sum(1 for x in vl if OUTGUARD_MARK in (x.get('reason') or ''))}")

    print("\n" + "=" * 78)
    print("[C] Transform x guardrail: breach rate (%) on the low-prompt arm (K=3, 11 attacks x 3)")
    print("=" * 78)
    for model in ABL:
        det = details_all[model]
        print(f"\n{model:<14}" + "".join(f"{GUARD_LABEL[g][:14]:>16}" for g in GUARDS))
        for tr in TRANSFORMS:
            row = []
            for g in GUARDS:
                tid = arms[(model, "low", g)][5]
                cs = [x for x in det if x["target_id"] == tid and x["transformation"] == tr]
                tt = sum(x["trials"] - x.get("api_errors", 0) for x in cs)
                tb = sum(x["breaches"] for x in cs)
                row.append(f"{tb / tt * 100:6.1f} ({tb:2d}/{tt:2d})")
            print(f"  {tr:<16}" + "".join(f"{c:>16}" for c in row))

    print("\n" + "=" * 78)
    print("[D] 15 ablation contrasts vs. the low+none baseline: 95% and Bonferroni (alpha/15) cluster CIs")
    print("=" * 78)
    alpha_b = 0.05 / 15
    for model in ABL:
        base = allcells[model][arms[(model, "low", "none")][5]]
        print(f"\n{model}")
        for prompt, g in [("low", "keyword"), ("low", "regex"), ("low", "llamaguard"), ("low", "llm"), ("high", "none")]:
            cs = allcells[model][arms[(model, prompt, g)][5]]
            d95, lo95, hi95 = boot_diff(cs, base, 0.05)
            dB, loB, hiB = boot_diff(cs, base, alpha_b)
            holm = "significant under Holm" if loB > 0 else "NOT significant after correction"
            print(f"  {prompt:<5}{GUARD_LABEL[g]:<20} Δ={d95:+5.1f}  95%[{lo95:+5.1f},{hi95:+5.1f}]"
                  f"  Bonf[{loB:+5.1f},{hiB:+5.1f}]  {holm}")

    print("\n" + "=" * 78)
    print("[E] 21-configuration campaign (K=5; var_run.json generated "
          f"{v['generated_at'][:19]}Z; parity re-runs merged)")
    print("=" * 78)
    prices = {}
    for x in v["details"]:
        prices.setdefault(x["target_id"], x.get("price_per_million"))
    print(f"  {'target_id':<26}{'model id':<30}{'prompt':<6}{'guard':<11}{'$in':>6}{'$out':>6}{'n':>5}{'err':>5}{'rate':>7}{'Wilson CI':>16}")
    for s in sorted(v["summary"], key=lambda s: -s["success_rate"]):
        p = prices.get(s["target_id"]) or {}
        print(f"  {s['target_id']:<26}{s['model']:<30}{s['prompt_strength']:<6}{s['guardrail']:<11}"
              f"{p.get('in', 0):>6}{p.get('out', 0):>6}{s['total_attacks']:>5}{s['n_api_error']:>5}"
              f"{s['success_rate']:>6.1f}%  [{s['ci_low']:5.1f}, {s['ci_high']:5.1f}]")
    hard = [s for s in v["summary"] if not (s["prompt_strength"] == "low" and s["guardrail"] == "none")]
    print(f"\n  defended configurations: {len(hard)}; min {min(s['success_rate'] for s in hard):.1f}% "
          f"({min(hard, key=lambda s: s['success_rate'])['target_id']}); "
          f"hardened-prompt configurations: {sum(1 for s in hard if s['prompt_strength']=='high')}, "
          f"min {min(s['success_rate'] for s in hard if s['prompt_strength']=='high'):.1f}%")

    print("\n" + "=" * 78)
    print("[F] Transform breach rate over the campaign and class means")
    print("=" * 78)
    tr_rate = {}
    for tr in TRANSFORMS:
        cs = [x for x in v["details"] if x["transformation"] == tr]
        tt = sum(x["trials"] - x.get("api_errors", 0) for x in cs)
        tb = sum(x["breaches"] for x in cs)
        tr_rate[tr] = tb / tt * 100
        print(f"  {tr:<18}{tr_rate[tr]:5.1f}%  ({tb}/{tt})")
    def mean(ts):
        return sum(tr_rate[t] for t in ts) / len(ts)
    print(f"  original classes: Japanese-specific (gyaru, vertical_newline, polite_business, double_tongue) "
          f"= {mean(['gyaru','vertical_newline','polite_business','double_tongue']):.1f}%; "
          f"language-agnostic encodings (base64, leet) = {mean(['base64_wrap','leet_smuggle']):.1f}%")
    print(f"  revised classes: Japanese-script/register (gyaru, polite_business) = {mean(['gyaru','polite_business']):.1f}%; "
          f"layout/pretext, language-agnostic in mechanism (vertical_newline, double_tongue) = "
          f"{mean(['vertical_newline','double_tongue']):.1f}%; encodings = {mean(['base64_wrap','leet_smuggle']):.1f}%; "
          f"legible non-encoded (all four) = {mean(['gyaru','polite_business','vertical_newline','double_tongue']):.1f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
