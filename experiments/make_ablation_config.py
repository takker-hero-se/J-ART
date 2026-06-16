# -*- coding: utf-8 -*-
"""均衡アブレーション用の設定ファイルを生成する（査読 C2 対応）。

`config.yaml` の secret/markers/transformations/attacks をそのまま再利用し、
targets だけを「同一モデル × 構成因子の直積」に差し替える。これによりモデル能力を
固定したまま構成（プロンプト強度・ガードレール）の効果だけを取り出せる。

使い方:
  python experiments/make_ablation_config.py \
      --base-model gpt-4o-mini --provider openai \
      --out experiments/ablation.yaml

  # OpenAI互換(OSS)モデルの場合:
  python experiments/make_ablation_config.py \
      --base-model meta-llama/llama-4-scout --provider openai_compatible \
      --api-key-env OPENROUTER_API_KEY \
      --out experiments/ablation.yaml

生成後:
  python run_assessment.py --config experiments/ablation.yaml \
      --out experiments/ablation_results.json
  python experiments/analyze_ablation.py experiments/ablation_results.json
"""
import argparse
import os
import sys

import yaml

# 直積をとる構成因子。モデルは固定し、この2因子だけを動かす。
PROMPT_STRENGTHS = ["low", "high"]
GUARDRAILS = ["none", "keyword", "regex", "llm", "llamaguard"]

_JP_GR = {"none": "GRなし", "keyword": "キーワードGR", "regex": "正規化GR",
          "llm": "LLM-GR", "llamaguard": "LlamaGuard"}
_EN_GR = {"none": "no GR", "keyword": "keyword GR", "regex": "regex GR",
          "llm": "LLM GR", "llamaguard": "Llama Guard"}
_JP_PS = {"low": "素", "high": "強化プロンプト"}
_EN_PS = {"low": "naked", "high": "hardened"}


def build_targets(base_model, provider, api_key_env, base_url):
    targets = []
    for ps in PROMPT_STRENGTHS:
        for gr in GUARDRAILS:
            tid = f"abl-{ps}-{gr}"
            t = {
                "id": tid,
                "label": f"{base_model} / {_JP_PS[ps]} + {_JP_GR[gr]}",
                "label_en": f"{base_model} / {_EN_PS[ps]} + {_EN_GR[gr]}",
                "provider": provider,
                "model": base_model,
                "prompt_strength": ps,
                "guardrail": gr,
                "rag": True,
            }
            if provider == "openai_compatible":
                if api_key_env:
                    t["api_key_env"] = api_key_env
                if base_url:
                    t["base_url"] = base_url
            targets.append(t)
    return targets


def main():
    ap = argparse.ArgumentParser(description="均衡アブレーション設定の生成")
    ap.add_argument("--base-config", default="config.yaml",
                    help="secret/markers/transformations/attacks を借用する元設定")
    ap.add_argument("--base-model", required=True, help="固定する単一モデルID")
    ap.add_argument("--provider", default="openai",
                    choices=["openai", "anthropic", "gemini", "openai_compatible"])
    ap.add_argument("--api-key-env", default=None,
                    help="openai_compatible のときのAPIキー環境変数名")
    ap.add_argument("--base-url", default=None,
                    help="openai_compatible のときの互換エンドポイント")
    ap.add_argument("--out", default="experiments/ablation.yaml")
    args = ap.parse_args()

    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    base_path = args.base_config
    if not os.path.isabs(base_path):
        base_path = os.path.join(here, base_path)
    with open(base_path, "r", encoding="utf-8") as f:
        base = yaml.safe_load(f)

    cfg = {
        "app": "J-ART balanced ablation",
        "secret_canary": base["secret_canary"],
        "markers": base["markers"],
        "transformations": base.get("transformations"),
        "targets": build_targets(args.base_model, args.provider,
                                 args.api_key_env, args.base_url),
        "attacks": base["attacks"],
    }

    out_path = args.out
    if not os.path.isabs(out_path):
        out_path = os.path.join(here, out_path)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)

    n = len(cfg["targets"])
    print(f"[+] {n} 構成（{len(PROMPT_STRENGTHS)}プロンプト強度 × {len(GUARDRAILS)}ガード"
          f"レール、モデル={args.base_model} 固定）を {out_path} に書き出しました。")
    print("[i] 次に: python run_assessment.py --config "
          f"{args.out} --out experiments/ablation_results.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
