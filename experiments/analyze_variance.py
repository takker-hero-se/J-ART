# -*- coding: utf-8 -*-
"""統制した分散実験の結果を分析する（査読 C3 対応）。

C3 の指摘：旧 §4.3 は 58→0 の変化を「実行時刻のみ」に帰属したが、2回の実行で
構成集合も変わっていた（18→21）。本スクリプトは「構成を完全に固定したまま反復」
した結果のばらつきを定量化し、構成変更と実行時非決定性を切り分ける。

2つの使い方:
  (A) 1回の実行を JART_TRIALS=K で回し、各セルの K 反復ばらつきを見る:
      JART_TRIALS=5 python run_assessment.py --config config.yaml \
          --out experiments/var_run.json
      python experiments/analyze_variance.py experiments/var_run.json

  (B) 同一構成を別々の日に K 回実行し、実行間（時間/ルータ）のばらつきを見る:
      python experiments/analyze_variance.py run1.json run2.json run3.json ...
"""
import json
import os
import sys

# Windows の既定コンソール(cp932)でも非ASCII出力で落ちないよう UTF-8 に再設定。
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from run_assessment import wilson_ci  # noqa: E402


def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def within_run(data):
    """(A) 単一 K-反復実行内のセル別ばらつき。"""
    details = data.get("details", [])
    k = max((d.get("trials", 1) for d in details), default=1)
    print(f"=== 実行内ばらつき（1実行・{k}反復/セル, mode={data.get('mode')}） ===")
    if k < 2:
        print("[!] JART_TRIALS=1 で実行されています。反復ばらつきを見るには K>=2 で再実行してください。")
    unstable = [d for d in details if 0 < d.get("breaches", 0) < d.get("trials", 1)]
    print(f"総セル数: {len(details)}  / 反復内で結果が割れた（不安定）セル: {len(unstable)}")
    for d in sorted(unstable, key=lambda d: -d["breach_rate"])[:30]:
        print(f"  {d['target_id']:<22} {d['attack_id']:<22} {d['transformation']:<16} "
              f"突破 {d['breaches']}/{d['trials']} ({d['breach_rate']}%)")
    # 構成（target）単位の防御率と Wilson CI（n = K×セル数）。
    print("\n--- 構成別 防御率（n=K×セル, Wilson 95%CI） ---")
    for s in sorted(data.get("summary", []), key=lambda s: s["success_rate"]):
        print(f"  {s.get('target_label_en', s['target_id']):<40} "
              f"{s['success_rate']:>6.1f}%  CI[{s['ci_low']}–{s['ci_high']}]  "
              f"(n={s['total_attacks']})")


def across_runs(paths):
    """(B) 複数実行間の構成別防御率のばらつき（range/分散）。"""
    runs = [load(p) for p in paths]
    print(f"=== 実行間ばらつき（{len(runs)}回の独立実行） ===")
    # target_id -> 各実行の success_rate
    series = {}
    order = []
    for r in runs:
        for s in r.get("summary", []):
            tid = s["target_id"]
            if tid not in series:
                series[tid] = {"label": s.get("target_label_en", tid), "rates": [],
                               "def": 0, "tot": 0}
                order.append(tid)
            series[tid]["rates"].append(s["success_rate"])
            series[tid]["def"] += s["defended"]
            series[tid]["tot"] += s["total_attacks"]
    print(f"{'構成':<40} {'各実行の防御率%':<28} {'幅(range)':>10} {'統合CI':>16}")
    print("-" * 100)
    worst = None
    for tid in order:
        e = series[tid]
        rates = e["rates"]
        rng = max(rates) - min(rates)
        lo, hi = wilson_ci(e["def"], e["tot"])
        rates_s = " ".join(f"{x:.0f}" for x in rates)
        print(f"{e['label'][:39]:<40} {rates_s:<28} {rng:>9.1f}% [{lo:>5.1f}–{hi:>5.1f}]")
        if worst is None or rng > worst[1]:
            worst = (e["label"], rng, rates)
    if worst:
        print(f"\n[!] 最大のばらつき: 「{worst[0]}」 range={worst[1]:.1f}% rates={worst[2]}")
    print("[i] 構成を固定しても実行間で防御率が動くなら、それは実行時非決定性（時間/ルータ）"
          "に由来する——構成変更（C3の交絡）とは独立に定量化できる。")


def main(argv):
    paths = argv[1:]
    if not paths:
        print(__doc__)
        return 2
    for p in paths:
        if not os.path.exists(p):
            print(f"[!] 見つかりません: {p}")
            return 1
    if len(paths) == 1:
        within_run(load(paths[0]))
    else:
        across_runs(paths)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
