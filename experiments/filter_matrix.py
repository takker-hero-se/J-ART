# -*- coding: utf-8 -*-
"""変形 × フィルタの段の回避行列を作る（決定論、API 呼び出しなし、費用 0）。

各変形で 11 攻撃を書き換え、フィルタの各段が止める攻撃の数を数える。
  keyword     部分一致フィルタ
  regex       公開済みの正規化フィルタ（論文のキャンペーンで使ったもの。NFKC なし）
  regex_nfkc  regex + NFKC
  skeleton    regex_nfkc + 同形異字・異体の漢字・仮名の畳み込み

使い方:  python experiments/filter_matrix.py            # 表を表示し filter_matrix.json を書く
"""
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("JART_FORCE_MOCK", "1")

import run_assessment as R  # noqa: E402

MARKERS = {"injection": "[JART-PWNED]", "hijack": "[JART-HIJACKED]"}
LEVELS = ("keyword", "regex", "regex_nfkc", "skeleton")


def main():
    m = R.filter_evasion_matrix(MARKERS)
    base = m["baseline"]["keyword"]
    print("禁止語を含む攻撃: %d / %d（baseline で keyword フィルタが止める数）" % (base, m["baseline"]["n"]))
    print("%-18s %8s %8s %11s %9s" % (("変形",) + LEVELS))
    for name, row in m.items():
        print("%-18s %8d %8d %11d %9d" % ((name,) + tuple(row[k] for k in LEVELS)))
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "filter_matrix.json")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"markers": MARKERS, "levels": LEVELS, "attacks": len(R.CORE_PAYLOADS),
                   "banned_keywords": len(R.BANNED_KEYWORDS), "matrix": m}, f, ensure_ascii=False, indent=1)
    print("wrote", out)


if __name__ == "__main__":
    main()
