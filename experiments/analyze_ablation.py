# -*- coding: utf-8 -*-
"""均衡アブレーション結果から構成効果を検定する（査読 C2 / クラスタCI 対応）。

同一モデルを固定した直積デザインの results.json を読み、各構成と「素（low + GRなし）」
基準との防御率差を報告する。K反復はセル内で相関するため、差の信頼区間は**セル単位の
クラスタ頑健ブートストラップ**（`bootstrap_diff_ci`、既定3000再標本・固定シード）で算出する
——これが論文 §4.2 Table 2′ に印字された区間と一致する。比較用に試行レベルの Newcombe CI
（`wilson_diff_ci`）も併記する。

api_error は**試行単位**で除外する（セル丸ごと除外しない）：各セルの clean = trials − api_errors。

使い方:
  python experiments/analyze_ablation.py experiments/abl_gpt41_results.json
"""
import json
import os
import sys
from collections import defaultdict

# Windows の既定コンソール(cp932)でも非ASCII出力で落ちないよう UTF-8 に再設定。
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from run_assessment import wilson_ci, wilson_diff_ci, bootstrap_diff_ci  # noqa: E402

N_BOOT = 3000  # 論文 §3.7 と一致させる


def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    data = load(argv[1])
    det = data.get("details", [])
    summ = data.get("summary", [])
    if not det:
        print("[!] details が空です。")
        return 1

    # target_id -> セル群 (breaches, clean_trials)。clean = trials - api_errors（試行単位）。
    cells = defaultdict(list)
    for x in det:
        clean = x["trials"] - x.get("api_errors", 0)
        if clean > 0:
            cells[x["target_id"]].append((x["breaches"], clean))

    def rate_n(cs):
        tt = sum(t for _, t in cs)
        return (1 - sum(b for b, _ in cs) / tt) * 100.0, tt

    # 基準＝low+none（無ければ最小防御率の構成）。
    sumby = {s["target_id"]: s for s in summ}
    base = next((s for s in summ if s.get("prompt_strength") == "low"
                 and s["guardrail"] == "none"),
                min(summ, key=lambda s: s["success_rate"]))
    base_id = base["target_id"]
    base_cells = cells[base_id]
    b_rate, b_n = rate_n(base_cells)

    model = summ[0].get("model", "?")
    k = max(x["trials"] for x in det)
    print(f"=== 均衡アブレーション（モデル固定: {model}, K={k}） ===")
    print(f"基準構成: {base.get('target_label_en', base_id)}  "
          f"防御 {b_rate:.1f}% n={b_n}\n")
    print(f"{'構成':<34} {'防御率%':>7} {'Δ(素比)':>8} "
          f"{'クラスタ95%CI':>20} {'Newcombe95%CI':>18}  判定")
    print("-" * 104)

    b_def_tr = round(b_rate / 100 * b_n)  # Newcombe 用の defended/total（試行レベル）

    for s in sorted(summ, key=lambda s: s["success_rate"]):
        tid = s["target_id"]
        if tid not in cells:
            continue
        rate, n = rate_n(cells[tid])
        # クラスタ頑健（セル再標本）— Table 2′ の区間
        cd, clo, chi = bootstrap_diff_ci(cells[tid], base_cells, n_boot=N_BOOT)
        # 試行レベル Newcombe（参考）
        d_tr = round(rate / 100 * n)
        wd, wlo, whi = wilson_diff_ci(d_tr, n, b_def_tr, b_n)
        if tid == base_id:
            verdict = "（基準）"
        elif clo > 0:
            verdict = "有意に改善"
        elif chi < 0:
            verdict = "有意に悪化"
        else:
            verdict = "有意差なし(クラスタ)"
        label = s.get("target_label_en", tid)[:33]
        print(f"{label:<34} {rate:>6.1f}% {cd:>+7.1f} "
              f"[{clo:>+6.1f},{chi:>+6.1f}] [{wlo:>+6.1f},{whi:>+6.1f}]  {verdict}")

    print(f"\n[i] 判定は**クラスタ頑健CI**（セル単位ブートストラップ, n_boot={N_BOOT}）に基づく"
          "——これが論文 §4.2 Table 2′ の区間。")
    print("[i] Newcombe(試行レベル)は K反復を独立扱いするため過小評価で、参考表示。")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
