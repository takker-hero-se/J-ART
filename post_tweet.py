#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
J-ART - 週次リーダーボード更新を X (旧Twitter) に自動投稿するスクリプト
=================================================================
results.json のサマリーから見出し（構成数・防御率トップ）を組み立て、1件だけ投稿する。

  python post_tweet.py --results results.json
  python post_tweet.py --results results.json --dry-run   # 投稿せず本文だけ確認

投稿の仕組み（OAuth 1.0a 署名、X と同じ文字数の数え方、エラー処理）は Quiet Forensics 共通の
qf_common/qf_x.py（原本は security-biz/qf-common、同期コピー）を使う。標準ライブラリだけで動く。
X_API_KEY / X_API_SECRET / X_ACCESS_TOKEN / X_ACCESS_SECRET のいずれかが無い場合は
投稿せず本文を表示して終了する（未設定でもCIを壊さない）。
=================================================================
"""

import argparse
import json
import sys
from datetime import datetime, timezone

from qf_common import qf_x

# 公開サイト（GitHub Pages）の正規 URL。generate_site.py の SITE_URL と揃える。
SITE_URL = "https://jart.quietforensics.com/"


def compose_tweet(results: dict) -> str:
    summary = results.get("summary", [])
    generated_at = results.get("generated_at", "")
    date_str = generated_at[:10] if generated_at else datetime.now(timezone.utc).strftime("%Y-%m-%d")

    scored = [t for t in summary if t.get("total_attacks")]
    top = max(scored, key=lambda t: t.get("success_rate", 0), default=None)

    lines = [
        f"J-ART 週次更新 ({date_str})",
        f"{len(summary)}構成を日本語レッドチームで実LIVE評価。",
    ]
    if top is not None:
        label = top.get("target_label_en") or top.get("target_label") or top.get("target_id", "")
        lines.append(f"防御率トップ: {label} {top.get('success_rate', 0):.1f}%")
    # X は日本語を 1 文字 2 として数える。URL は残し、本文だけを切り詰める。
    return qf_x.fit("\n".join(lines), url=SITE_URL)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", default="results.json")
    parser.add_argument("--dry-run", action="store_true", help="投稿せず本文だけ表示する")
    args = parser.parse_args(argv)

    with open(args.results, encoding="utf-8") as f:
        results = json.load(f)

    result = qf_x.post(compose_tweet(results), dry_run=args.dry_run)
    if not result.posted:
        print(f"[post_tweet] 投稿をスキップしました（{result.skipped_reason}）。")
        print("--- 投稿予定の本文 ---")
        print(result.text)
        return 0
    print(f"[post_tweet] 投稿しました（id={result.tweet_id}）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
