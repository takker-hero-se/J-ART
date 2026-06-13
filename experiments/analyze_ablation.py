# -*- coding: utf-8 -*-
"""均衡アブレーション結果から構成効果を差の比率CIで検定する（査読 C2 対応）。

同一モデルを固定した直積デザインの results.json を読み、各ハードン構成と
「素（low + GRなし）」基準との防御率差を Newcombe 95%CI で報告する。CIが0を
跨がなければ、その構成効果はモデルを固定した上で統計的に有意である。

使い方:
  python experiments/analyze_ablation.py experiments/ablation_results.json
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from run_assessment import wilson_ci, wilson_diff_ci  # noqa: E402


def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    data = load(argv[1])
    summ = data.get("summary", [])
    if not summ:
        print("[!] summary が空です。")
        return 1

    # 各 summary は (defended, total) を持つ。基準＝最も素な構成（low + none）。
    def cfg_key(s):
        return (s.get("prompt_strength"), s.get("guardrail"))

    by_key = {cfg_key(s): s for s in summ}
    baseline = by_key.get(("low", "none")) or min(
        summ, key=lambda s: s["success_rate"])
    b_def, b_tot = baseline["defended"], baseline["total_attacks"]

    model = summ[0].get("model", "?")
    print(f"=== 均衡アブレーション（モデル固定: {model}） ===")
    print(f"基準構成: {baseline['target_label_en']}  "
          f"防御 {b_def}/{b_tot} = {baseline['success_rate']}% "
          f"CI[{baseline['ci_low']}–{baseline['ci_high']}]\n")
    print(f"{'構成':<40} {'防御率%':>8} {'95%CI':>16}  {'Δ(vs基準)':>10} {'差の95%CI':>18}  判定")
    print("-" * 110)

    # 防御率昇順で表示（弱い構成→強い構成）。
    for s in sorted(summ, key=lambda s: s["success_rate"]):
        d, t = s["defended"], s["total_attacks"]
        lo, hi = wilson_ci(d, t)
        diff, dlo, dhi = wilson_diff_ci(d, t, b_def, b_tot)
        if s is baseline:
            verdict = "（基準）"
        elif dlo > 0:
            verdict = "有意に改善"
        elif dhi < 0:
            verdict = "有意に悪化"
        else:
            verdict = "有意差なし"
        label = s.get("target_label_en", s["target_id"])[:39]
        print(f"{label:<40} {s['success_rate']:>7.1f}% "
              f"[{lo:>5.1f}–{hi:>5.1f}]  {diff:>+9.1f}% "
              f"[{dlo:>+6.1f},{dhi:>+6.1f}]  {verdict}")

    print("\n[i] 差の95%CIが0を含まなければ、モデルを固定した上で構成効果は有意。")
    print("[i] これによりモデル能力と構成効果の交絡（C2）を切り分ける。")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
