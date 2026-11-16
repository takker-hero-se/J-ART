# -*- coding: utf-8 -*-
"""決定論フィルタの誤検知を、正常な依頼の集合で数える（API 呼び出しなし、費用 0）。

入力は experiments/benign_requests.json。各依頼を、検索文脈を付けずにそのままフィルタに通す。
出力は、分類ごと・フィルタの段ごとに止めた件数と、止めた依頼の一覧である。

    python experiments/benign_fp.py        # 表を表示し benign_fp.json を書く
"""
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
os.environ.setdefault("JART_FORCE_MOCK", "1")

import run_assessment as R  # noqa: E402

LEVELS = ("keyword", "regex", "regex_nfkc", "skeleton")


def blocks(text):
    return {
        "keyword": R.keyword_guardrail_blocks(text),
        "regex": R.regex_guardrail_blocks(text, level=1),
        "regex_nfkc": R.regex_guardrail_blocks(text, level=2),
        "skeleton": R.regex_guardrail_blocks(text, level=3),
    }


def evaluate(categories):
    out = {"by_category": {}, "total": {k: 0 for k in LEVELS}, "n": 0, "blocked": []}
    for cat, items in categories.items():
        row = {k: 0 for k in LEVELS}
        for text in items:
            b = blocks(text)
            for k in LEVELS:
                row[k] += b[k]
            if any(b.values()):
                out["blocked"].append({"category": cat, "text": text,
                                       "first_level": next(k for k in LEVELS if b[k])})
        row["n"] = len(items)
        out["by_category"][cat] = row
        out["n"] += len(items)
        for k in LEVELS:
            out["total"][k] += row[k]
    return out


def main():
    data = json.load(open(os.path.join(HERE, "benign_requests.json"), encoding="utf-8"))
    res = evaluate(data["categories"])
    print("%-14s %4s %8s %6s %11s %9s" % (("分類", "n") + LEVELS))
    for cat, row in res["by_category"].items():
        print("%-14s %4d %8d %6d %11d %9d" % ((cat, row["n"]) + tuple(row[k] for k in LEVELS)))
    print("%-14s %4d %8d %6d %11d %9d" % (("計", res["n"]) + tuple(res["total"][k] for k in LEVELS)))
    for b in res["blocked"]:
        if b["first_level"] != "keyword":
            print("  %s で初めて止まる [%s] %s" % (b["first_level"], b["category"], b["text"].replace("\n", "／")))
    with open(os.path.join(HERE, "benign_fp.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
