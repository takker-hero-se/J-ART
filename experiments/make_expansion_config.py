# -*- coding: utf-8 -*-
"""2026-11 の拡充変形を測る設定（expansion.yaml）を、既存のアブレーション設定から作る。

3 モデル（Llama 4 Scout、GPT-4o-mini、GPT-4.1）の素プロンプトに、ガードレール
none / keyword / regex / skeleton / llamaguard を付けた 15 構成で、基準と拡充変形を測る。
モデルの指定（provider、api_key_env など）は 6 月のアブレーションの設定をそのまま引き継ぐ。

    python experiments/make_expansion_config.py
    JART_TRIALS=3 python run_assessment.py --config experiments/expansion.yaml --out experiments/expansion_run.json
"""
import copy
import os

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCES = [("scout", "abl_scout.yaml"), ("4omini", "ablation.yaml"), ("gpt41", "abl_gpt41.yaml")]
GUARDS = ["none", "keyword", "regex", "skeleton", "llamaguard"]
TRANSFORMS = ["baseline", "gyaru", "compat_forms", "variant_forms", "ringi_document"]
GUARD_JA = {"none": "GRなし", "keyword": "キーワードGR", "regex": "正規化GR",
            "skeleton": "スケルトンGR", "llamaguard": "LlamaGuard"}


def main():
    out = None
    targets = []
    for short, fname in SOURCES:
        cfg = yaml.safe_load(open(os.path.join(HERE, fname), encoding="utf-8"))
        if out is None:
            out = {k: v for k, v in cfg.items() if k not in ("targets", "transformations")}
            out["app"] = "J-ART transform expansion (2026-11)"
        base = next(t for t in cfg["targets"] if t["id"] == "abl-low-none")
        for g in GUARDS:
            t = copy.deepcopy(base)
            t["id"] = "exp-%s-%s" % (short, g)
            t["guardrail"] = g
            t["label"] = "%s / 素 + %s" % (base["model"], GUARD_JA[g])
            t["label_en"] = "%s / naked + %s" % (base["model"], g)
            targets.append(t)
    out["transformations"] = TRANSFORMS
    out["targets"] = targets
    path = os.path.join(HERE, "expansion.yaml")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        yaml.safe_dump(out, f, allow_unicode=True, sort_keys=False)
    print("wrote", path, len(targets), "targets x", len(TRANSFORMS), "transforms")


if __name__ == "__main__":
    main()
