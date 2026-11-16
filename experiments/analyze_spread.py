# -*- coding: utf-8 -*-
"""Cross-model spread of the defense rate in each ablation arm (three models, K=3): spread with a cell-bootstrap
95% interval, its reduction against the bare arm, the breach rates and their max/min ratio.
Run from the repository root:  python experiments/analyze_spread.py
"""
import collections
import json
import random
import sys

sys.stdout.reconfigure(encoding="utf-8")
files = {"scout": "experiments/abl_scout_results.json", "4omini": "experiments/ablation_results.json",
         "gpt41": "experiments/abl_gpt41_results.json"}
cells = collections.defaultdict(list)          # (arm, model) -> [(breaches, n), ...] one per cell
for m, f in files.items():
    for c in json.load(open(f, encoding="utf-8"))["details"]:
        cells[(c["target_id"], m)].append((c["breaches"], c["trials"] - c.get("api_errors", 0)))


def rate(cs):
    return 100.0 * (1 - sum(b for b, _ in cs) / sum(n for _, n in cs))


def spread(arm, pick=None):
    rs = []
    for m in files:
        cs = cells[(arm, m)]
        if pick is not None:
            cs = [cs[i] for i in pick[m]]
        rs.append(rate(cs))
    return max(rs) - min(rs)


rng = random.Random(20260614)
arms = sorted({a for a, _ in cells})
N = 3000
draws = []
for _ in range(N):
    draws.append({(a, m): [rng.randrange(len(cells[(a, m)])) for _ in cells[(a, m)]] for a in arms for m in files})
base = "abl-low-none"
for a in arms:
    s = spread(a)
    ss = sorted(spread(a, {m: d[(a, m)] for m in files}) for d in draws)
    red = sorted(spread(base, {m: d[(base, m)] for m in files}) - spread(a, {m: d[(a, m)] for m in files}) for d in draws)
    br = [100 - rate(cells[(a, m)]) for m in files]
    ratio = (max(br) / min(br)) if min(br) > 0 else float("inf")
    print("%-20s spread %5.1f [%5.1f,%5.1f]  reduction vs bare %5.1f [%5.1f,%5.1f]  breach %s  max/min %.1f"
          % (a, s, ss[int(.025 * N)], ss[int(.975 * N) - 1], spread(base) - s, red[int(.025 * N)], red[int(.975 * N) - 1],
             "/".join("%.1f" % x for x in br), ratio))
