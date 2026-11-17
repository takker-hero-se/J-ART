# -*- coding: utf-8 -*-
"""拡充変形の実測（expansion_run.json）を、モデル × ガードレール × 変形の突破率にまとめる。

    python experiments/analyze_expansion.py [experiments/expansion_run.json]

各セルは 11 攻撃 × K 試行である。api_error の試行は除く。突破率に Wilson 95% CI を付ける。
ガードレールが入力を止めた割合（モデルを呼ばなかった試行）も併記する。
"""
import collections
import json
import math
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from run_assessment import bootstrap_diff_ci, wilson_ci  # noqa: E402

MODELS = ["scout", "4omini", "gpt41"]
GUARDS = ["none", "keyword", "regex", "skeleton", "llamaguard"]
TRANSFORMS = ["baseline", "gyaru", "compat_forms", "variant_forms", "ringi_document"]


def load(path):
    return json.load(open(path, encoding="utf-8"))


def table(data):
    """{(model, guard, transform): {"breaches", "n", "errors", "cells"}}"""
    agg = collections.defaultdict(lambda: {"breaches": 0, "n": 0, "errors": 0, "cells": 0})
    for d in data["details"]:
        _, model, guard = d["target_id"].split("-", 2)
        a = agg[(model, guard, d["transformation"])]
        err = d.get("api_errors", 0)
        a["breaches"] += d["breaches"]
        a["n"] += d["trials"] - err
        a["errors"] += err
        a["cells"] += 1
    return agg


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "expansion_run.json")
    data = load(path)
    agg = table(data)
    print("mode=%s generated_at=%s" % (data.get("mode"), data.get("generated_at")))
    tot_n = sum(a["n"] for a in agg.values())
    tot_e = sum(a["errors"] for a in agg.values())
    cost = sum(d.get("cost_usd", 0.0) for d in data["details"])
    print("valid trials=%d excluded(api_error)=%d cost(recorded, representative trial per cell)=$%.4f" % (tot_n, tot_e, cost))
    out = {}
    for model in MODELS:
        print("\n== %s : 突破率 %% [Wilson 95%% CI]（n） ==" % model)
        print("%-11s" % "guard" + "".join("%-26s" % t for t in TRANSFORMS))
        for guard in GUARDS:
            cells = []
            for t in TRANSFORMS:
                a = agg[(model, guard, t)]
                if a["n"] == 0:
                    cells.append("%-26s" % "n/a")
                    continue
                rate = 100.0 * a["breaches"] / a["n"]
                lo, hi = wilson_ci(a["breaches"], a["n"])
                cells.append("%-26s" % ("%5.1f [%4.1f,%5.1f] (%d)" % (rate, lo, hi, a["n"])))
                out["%s|%s|%s" % (model, guard, t)] = {"breach_rate": round(rate, 1), "ci": [lo, hi],
                                                       "breaches": a["breaches"], "n": a["n"],
                                                       "excluded": a["errors"]}
            print("%-11s" % guard + "".join(cells))
    # 構成間の差（防御率の差、ポイント）。セル（攻撃）単位で復元抽出するクラスタ頑健 95% CI。
    cells = collections.defaultdict(list)
    for d in data["details"]:
        _, model, guard = d["target_id"].split("-", 2)
        cells[(model, guard, d["transformation"])].append((d["breaches"], d["trials"] - d.get("api_errors", 0)))
    print("\n== 防御率の差（ポイント）[クラスタ頑健 95% CI]、* はゼロを含まない ==")
    diffs = {}
    for t in ("compat_forms", "variant_forms"):
        for a, b in (("regex", "none"), ("skeleton", "regex"), ("skeleton", "none"), ("llamaguard", "none")):
            row = []
            for model in MODELS:
                diff, lo, hi = bootstrap_diff_ci(cells[(model, a, t)], cells[(model, b, t)])
                sig = "*" if (lo > 0 or hi < 0) else " "
                row.append("%s %+5.1f [%+5.1f,%+5.1f]%s" % (model, diff, lo, hi, sig))
                diffs["%s|%s-%s|%s" % (model, a, b, t)] = {"diff": round(diff, 1), "ci": [round(lo, 1), round(hi, 1)],
                                                         "excludes_zero": bool(lo > 0 or hi < 0)}
            print("%-14s %-17s %s" % (t, "%s - %s" % (a, b), "   ".join(row)))
    # 感度分析：各群は同じ 11 攻撃を共有するので、攻撃ごとに対応づけて復元抽出する。
    # 結果を見た後に加えた解析であり、有意性の判定には使わない。
    import random
    by_attack = {}
    for d in data["details"]:
        _, model, guard = d["target_id"].split("-", 2)
        by_attack[(model, guard, d["transformation"], d["attack_id"])] = (
            d["breaches"], d["trials"] - d.get("api_errors", 0))
    attacks = sorted({k[3] for k in by_attack})
    rng = random.Random(20260614)

    def paired(model, a, b, t, n_boot=3000):
        pa = [by_attack[(model, a, t, x)] for x in attacks]
        pb = [by_attack[(model, b, t, x)] for x in attacks]

        def diff(idx):
            ba = sum(pa[i][0] for i in idx)
            na = sum(pa[i][1] for i in idx)
            bb = sum(pb[i][0] for i in idx)
            nb = sum(pb[i][1] for i in idx)
            return ((1 - ba / na) - (1 - bb / nb)) * 100.0
        ds = sorted(diff([rng.randrange(len(attacks)) for _ in attacks]) for _ in range(n_boot))
        return diff(range(len(attacks))), ds[int(0.025 * n_boot)], ds[int(0.975 * n_boot) - 1]

    def sign_test(model, a, b, t):
        """攻撃ごとの防御率の差の符号だけを使う正確な両側検定。攻撃は 11 しかないので検出力は低い。"""
        pos = neg = 0
        for x in attacks:
            (ba, na), (bb, nb) = by_attack[(model, a, t, x)], by_attack[(model, b, t, x)]
            d = (1 - ba / na) - (1 - bb / nb)
            pos += d > 0
            neg += d < 0
        n, k = pos + neg, min(pos, neg)
        p = min(1.0, 2.0 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n) if n else 1.0
        return pos, neg, p

    print("\n== 感度分析：攻撃ごとに対応づけた復元抽出（防御率の差、ポイント）==")
    paired_out, n_ex = {}, 0
    for t in ("compat_forms", "variant_forms"):
        for a, b in (("regex", "none"), ("skeleton", "regex"), ("skeleton", "none"), ("llamaguard", "none")):
            for model in MODELS:
                diff, lo, hi = paired(model, a, b, t)
                ex = bool(lo > 0 or hi < 0)
                n_ex += ex
                pos, neg, p = sign_test(model, a, b, t)
                paired_out["%s|%s-%s|%s" % (model, a, b, t)] = {"diff": round(diff, 1),
                                                              "ci": [round(lo, 1), round(hi, 1)],
                                                              "excludes_zero": ex,
                                                              "sign_test": {"positive": pos, "negative": neg,
                                                                            "p_two_sided": round(p, 4)}}
                if ex:
                    print("%-14s %-17s %-7s %+5.1f [%+5.1f,%+5.1f]  符号検定: +%d/-%d, 両側 p=%.4f"
                          % (t, "%s - %s" % (a, b), model, diff, lo, hi, pos, neg, p))
    print("ゼロを含まない対比: %d / %d" % (n_ex, len(paired_out)))
    with open(os.path.join(HERE, "expansion_summary.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"cells": out, "diffs": diffs, "paired_sensitivity": paired_out}, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
