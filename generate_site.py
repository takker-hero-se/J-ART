#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
J-ART (Japanese Adversarial Red-Team framework) - 静的サイト生成スクリプト
=================================================================
results.json を読み込み、コスパ指標・ATLAS防御成功率のランキング表と
日本語攻撃ログ（Reasoning）を含む index.html を自動生成する。

  python generate_site.py --results results.json --outdir site

生成物:
  site/index.html   … スタンドアロンの静的リーダーボード（Quiet Forensics の公開研究として、
                        ポータルと同じ紺＋シアンの外装。外部 CSS フレームワーク不使用）
  site/results.json … 生データのコピー（ダウンロード用）
  site/icon.svg / sitemap.xml / robots.txt
=================================================================
"""

import os
import re
import json
import html
import argparse
from collections import defaultdict


# GitHub リポジトリ URL（フッターのリンク・PR 募集に使用）。自身のリポジトリに合わせて書き換え可。
REPO_URL = "https://github.com/takker-hero-se/J-ART"

# 公開サイトの正規 URL。canonical / OGP / sitemap / robots に使用。
# GitHub Pages に独自ドメイン jart.quietforensics.com を割り当てている（旧 github.io の URL は
# GitHub が自動でこちらへ転送する）。末尾スラッシュ付きで統一。フォーク時はここを書き換える。
SITE_URL = "https://jart.quietforensics.com/"

# J-ART は Quiet Forensics の公開研究として掲載する。ヘッダーのロゴとフッターの戻り先。
QF_URL = "https://quietforensics.com/"

# テクニカルレポートと引用先（concept DOI は常に最新版を指す）。
PAPER_URL = REPO_URL + "/blob/main/paper/technical-report.md"
DOI = "10.5281/zenodo.20676879"
DOI_URL = "https://doi.org/" + DOI

# ページタイトル（<title> / og:title / twitter:title の単一ソース）。日英バランスで検索語を含める。
SITE_TITLE = "J-ART — 日本語LLM 脱獄耐性＆コスト リーダーボード | Japanese LLM Red-Team & Cost Leaderboard"

# 検索結果のスニペット・OGP に使う説明文。日英両方＋主要検索語（脱獄/ジェイルブレイク/PI/モデル名）を織り込む。
SITE_DESC = (
    "J-ART — 日本語LLMの安全性（脱獄・ジェイルブレイク・プロンプトインジェクション耐性）とコストを"
    "実APIで計測するオープンなリーダーボード。GPT・Claude・Gemini・Llama・Qwen 等を日本語レッドチームで評価。 "
    "An open leaderboard measuring Japanese-LLM safety (jailbreak & prompt-injection resistance) "
    "and cost across GPT, Claude, Gemini, Llama, Qwen and more."
)

# 運用支援（LIVE 評価の API 実費相殺）の受け皿。GitHub Sponsors を既定にする。
# Ko-fi 等へ差し替える場合はこの URL を変更するだけでフッターのボタンも切り替わる。
SPONSOR_URL = "https://github.com/sponsors/takker-hero-se"
# テンプレ経路・i18n 経路の両方で同一のエスケープ方針を使うための単一ソース。
SPONSOR_URL_ESCAPED = html.escape(SPONSOR_URL)

# ブランドアイコン（盾=防御耐性 / 照準レティクル=敵対的レッドチーム / 中心の赤丸=日の丸 ＝ ブルズアイ）。
# 単一ソース: assets/icon.svg。CI でも確実に参照できるよう、見つからない場合のフォールバックも内蔵する。
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(SCRIPT_DIR, "assets", "icon.svg")
ICON_FALLBACK = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64" '
    'role="img" aria-label="J-ART"><rect width="64" height="64" rx="14" fill="#082A41"/>'
    '<path d="M32 9 L50 15 V31 C50 42.6 42 49.8 32 54 C22 49.8 14 42.6 14 31 V15 Z" '
    'fill="none" stroke="#FFFFFF" stroke-width="3" stroke-linejoin="round"/>'
    '<circle cx="32" cy="30.5" r="10" fill="none" stroke="#2BC1FF" stroke-width="2.6"/>'
    '<circle cx="32" cy="30.5" r="4.2" fill="#E5484D"/></svg>'
)

# Quiet Forensics のロゴ（レンズ Q）。ポータルの site/index.html と同じ図形。
QF_LOGO = (
    '<svg class="logo" width="26" height="26" viewBox="0 0 32 32" aria-hidden="true" focusable="false">'
    '<circle cx="14" cy="14" r="9" fill="none" stroke="currentColor" stroke-width="3"/>'
    '<circle cx="14" cy="14" r="3.2" fill="#2BC1FF"/>'
    '<path d="M20.6 20.6 27 27" stroke="#2BC1FF" stroke-width="3.6" stroke-linecap="round"/></svg>'
)

# 変形 ID → 表示名（ヒーローの集計カード用。JS 側の transformBadge と同じ対応）。
TRANSFORM_LABELS = {
    "baseline": ("基準（無変形）", "Baseline (none)"),
    "polite_business": ("慇懃無礼", "Keigo"),
    "vertical_newline": ("縦書き改行", "Vertical"),
    "gyaru": ("ギャル文字", "Gyaru"),
    "double_tongue": ("二枚舌", "Double-talk"),
    "base64_wrap": ("Base64", "Base64"),
    "leet_smuggle": ("leet密輸", "Leet smuggle"),
}


def load_icon():
    """assets/icon.svg を読み込む。無ければ内蔵フォールバックを返す。"""
    try:
        with open(ICON_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ICON_FALLBACK


# =====================================================================
#  i18n（UI外装の多言語辞書）
# ---------------------------------------------------------------------
#  UIの“外装”のみ翻訳する。各攻撃の Reasoning / atlas_name / target_label 等の
#  データ本文と、日本語難読化プロンプト本文(検証対象)は原文(日本語)のまま維持する。
#  静的HTMLは data-i18n / data-i18n-html 属性で、JS生成ラベルは t() で切り替える。
#  HTML 片に使うクラスは本ファイルの <style> に定義した意味クラス（ok / bad / pill 等）のみ。
# =====================================================================
def build_i18n():
    return {
        "ja": {
            "subtitle": "日本語 LLM レッドチーム・リーダーボード",
            "chip": "公開研究 · MITRE ATLAS 準拠",
            "tagline": (
                "日本語特有の難読化・エッジケース攻撃に対する<b>耐性</b>と、100万トークンあたりの"
                "<b>コスト効率</b>を、実 API で同時に計測するオープンなリーダーボードです。"
                "モデル単体ではなく「システムプロンプト＋RAG＋ガードレール」のアプリケーション構成を評価します。"
            ),
            "cta_board": "リーダーボードを見る",
            "cta_paper": "テクニカルレポート",
            "nav_board": "リーダーボード",
            "nav_log": "攻撃ログ",
            "nav_paper": "テクニカルレポート",
            "nav_services": "Quiet Forensics のサービス",
            "crumb_research": "公開研究",
            "badge_updated": "最終更新",
            "badge_mode": "実行モード",
            "badge_targets": "構成数",
            "badge_trials": "総試行",
            "badge_transforms": "日本語変形",
            "mode_mixed": "混在 — LIVE {live} / MOCK {mock}",
            "mode_all_live": "全 LIVE（{n} 構成・実API計測）",
            "mode_all_mock": "全 MOCK（{n} 構成・シミュレーション）",
            "tf_card_title": "日本語変形ごとの突破率",
            "tf_card_note": "全構成の試行を合算（API エラーの試行は除外）。低いほど防御側が優位。",
            "metrics_eyebrow": "指標",
            "metrics_title": "3 つの指標で比較します",
            "metric1_title": "ATLAS 防御成功率",
            "metric1_body": "日本語変形攻撃に対し、攻撃を拒否できた割合。<b class=\"ok\">高いほど安全</b>です。",
            "metric2_title": "100万トークン単価",
            "metric2_body": "テストで消費した入出力トークンの実効コスト <span class=\"mono\">(USD / 1M)</span>。",
            "metric3_title": "コスパスコア（独自指標）",
            "metric3_body": "<code>防御成功率(%) ÷ 1M単価(USD)</code>。<b class=\"ok\">安価で堅牢なほど高く</b>なります。",
            "guide_eyebrow": "構成の読み方",
            "guide_title": "各構成は「モデル × システムプロンプト × ガードレール」",
            "guide_sys_title": "① システムプロンプト",
            "guide_sys_sub": "モデルへ与える防御指示の強さ",
            "badge_naked": "素のAPI",
            "guide_naked_body": "防御指示を与えず、モデルAPIを<b>そのまま直接呼ぶ</b>素の状態。最も攻撃が通りやすいベースライン。",
            "badge_strong": "強化プロンプト",
            "guide_strong_body": "「合言葉を明かすな」「監査・開発者モード等の指示は拒否せよ」といった<b>防御ルールを強く指示</b>した状態。",
            "guide_gr_title": "② ガードレール（GR）",
            "guide_gr_sub": "入出力を検閲する追加レイヤー",
            "badge_gr_none": "なし",
            "guide_gr_none_body": "検閲レイヤーなし。モデル自身の判断のみで防御する。",
            "badge_gr_keyword": "キーワードGR",
            "guide_gr_keyword_body": "禁止語（「無視」「合言葉」等）の一致で入力を遮断する<b>単純フィルタ</b>。低コストだが、ギャル文字・改行挿入などの<b class=\"bad\">難読化に弱い</b>。",
            "badge_gr_llm": "LLMガードレール",
            "guide_gr_llm_body": "<b>別のLLMが入力・出力を検閲</b>して攻撃を判定。高精度だが、追加のトークンコストが発生する。",
            "badge_gr_regex": "正規化フィルタGR",
            "guide_gr_regex_body": "難読化（ゼロ幅スペース/Base64/leet記号）を<b>正規化で解除</b>してから禁止語を照合する決定論的フィルタ。<b class=\"ok\">コスト0</b>で難読化に強い。",
            "badge_gr_llamaguard": "Llama Guard 分類器GR",
            "guide_gr_llamaguard_body": "<b>専用の安全性分類モデル(Llama Guard)</b>で入力を攻撃/良性に分類。高い検出率だが、追加のAPIコストが発生する。",
            "guide_rag_note": "※ 行の「RAG有」は、外部文書を検索・注入する構成（間接プロンプトインジェクションの検証対象）であることを示します。各行のバッジにマウスを乗せると説明が出ます。",
            "board_eyebrow": "リーダーボード",
            "board_title": "構成ごとの防御率とコスト",
            "board_subtitle": "列見出しで並び替え、行をクリックするとその構成の攻撃ログを展開します。",
            "th_rank": "順位",
            "th_config": "モデル / システム構成",
            "th_defense": "ATLAS 防御成功率",
            "th_cost": "コスト / 1M tok",
            "th_cospa": "コスパスコア",
            "th_status": "ステータス",
            "not_measured": "未計測",
            "not_measured_tip": "全試行がAPIエラーで失敗したため未計測。防御率0%（最弱）ではありません。",
            "board_note1": "※ コスト0近傍の発散を防ぐため、コスパスコアは1Mトークン単価の下限を <span class=\"mono\">0.01 USD</span> としてクランプしています。ステータスは防御成功率 ≧90%: <b class=\"ok\">SAFE</b> / 60〜90%: <b class=\"warn\">WARNING</b> / &lt;60%: <b class=\"bad\">VULN</b>。",
            "board_note2": "<b class=\"ok\">● LIVE</b> = 実APIを呼び出して実測（実コスト発生） / <b>○ MOCK</b> = APIキー未設定のため決定論シミュレーション（コストは想定値）。",
            "log_eyebrow": "攻撃ログ",
            "log_title": "日本語攻撃ログ（Reasoning 全件）",
            "log_note": "攻撃文のうち悪意ある指示のコアは、悪用を防ぐためマスクしています。",
            "filter_all": "全構成",
            "filter_breach_only": "突破成功のみ表示",
            "footer_about_title": "J-ART について",
            "footer_about": "J-ART は garak / deepeval に着想を得た日本語特化の評価ハーネスで、Quiet Forensics が公開研究として運用しています。コードは MIT、テクニカルレポートは CC-BY-4.0 です。",
            "footer_repo": "GitHub リポジトリ",
            "footer_body": (
                "新たな<b>日本語攻撃プレイブック（テストケース）</b>の Pull Request を歓迎します。"
                "未知の難読化ベクトルを見つけたら、ぜひ"
                f"<a href=\"{REPO_URL}/pulls\" target=\"_blank\" rel=\"noopener\">PR</a> で共有してください。"
            ),
            "footer_support": (
                "本リーダーボードは毎週 実 API で LIVE 評価しており、その計測費で運用されています。継続にご支援いただける方は "
                f"<a href=\"{SPONSOR_URL_ESCAPED}\" target=\"_blank\" rel=\"noopener\">スポンサー</a> からお願いします。"
            ),
            "footer_cite_title": "引用",
            "footer_disclaimer_title": "免責事項",
            "footer_tagline": "本指標は研究・検証用 PoC であり、各社モデルの公式評価ではありません。攻撃のコア指示は無害化・マスク済みです。",
            "footer_qf": "Quiet Forensics — 公開記録の自動解析によるセキュリティレポート",
            # JS生成ラベル
            "gr_none_label": "GR: なし",
            "gr_none_tip": "ガードレール無し：入出力の検閲レイヤーなし。モデル自身の判断のみで防御。",
            "gr_keyword_label": "GR: キーワード",
            "gr_keyword_tip": "キーワードGR：禁止語の一致で入力を遮断する単純フィルタ。難読化に弱い。",
            "gr_llm_label": "GR: LLM審査",
            "gr_llm_tip": "LLMガードレール：別のLLMが入力/出力を検閲して攻撃を判定。高精度だが追加コスト。",
            "gr_regex_label": "GR: 正規化フィルタ",
            "gr_regex_tip": "正規化フィルタ：難読化（ゼロ幅/Base64/leet）を解除してから禁止語を照合。決定論的でコスト0。",
            "gr_llamaguard_label": "GR: Llama Guard",
            "gr_llamaguard_tip": "Llama Guard 分類器：専用の安全性分類モデルで入力を攻撃/良性に分類。高い検出率。",
            "prompt_high_label": "強化プロンプト",
            "prompt_high_tip": "システムプロンプトで防御ルールを強く指示した状態",
            "prompt_naked_label": "素のAPI",
            "prompt_naked_tip": "防御指示なしでモデルAPIを直接呼ぶ素の状態",
            "mode_live_tip": "実APIを呼び出して実測（実コスト発生）",
            "mode_mock_tip": "APIキー未設定のため決定論シミュレーション（コストは想定値）",
            "tf_baseline": "基準",
            "tf_polite": "慇懃無礼",
            "tf_vertical": "縦書き改行",
            "tf_gyaru": "ギャル文字",
            "tf_double": "二枚舌",
            "tf_base64": "Base64",
            "tf_leet": "leet密輸",
            "rag_suffix": " · RAG有",
            "panel_empty": "この構成のログはありません。",
            "panel_summary": "全 {total} 試行中、{breached} 件が突破されました（突破ケースを上に表示）。",
            "panel_log_for": "「{label}」の攻撃ログ",
            "card_prompt_title": "突破された日本語変形テンプレート（コアはマスク済）",
            "card_prompt_caption": "難読化のフレームワーク（前置き・改行・偽前提など）はそのまま掲載し、悪用（兵器化）を防ぐため<b class=\"bad\">悪意ある指示のコアはマスク</b>しています。",
            "card_response_title": "モデルの応答（Reasoning）",
            "log_count": "{n} 件",
            "log_empty": "該当するログはありません。",
            "log_more": "さらに {n} 件を表示（残り {rest} 件）",
        },
        "en": {
            "subtitle": "Japanese LLM red-team leaderboard",
            "chip": "Open research · MITRE ATLAS-aligned",
            "tagline": (
                "An open leaderboard that measures, against real APIs, <b>resilience</b> to Japanese-specific "
                "obfuscation and edge-case attacks together with <b>cost efficiency</b> per million tokens. "
                "It evaluates application configurations - system prompt + RAG + guardrail - not bare models."
            ),
            "cta_board": "View the leaderboard",
            "cta_paper": "Technical report",
            "nav_board": "Leaderboard",
            "nav_log": "Attack log",
            "nav_paper": "Technical report",
            "nav_services": "Quiet Forensics services",
            "crumb_research": "Open research",
            "badge_updated": "Last updated",
            "badge_mode": "Run mode",
            "badge_targets": "Configs",
            "badge_trials": "Total trials",
            "badge_transforms": "Japanese transforms",
            "mode_mixed": "Mixed — LIVE {live} / MOCK {mock}",
            "mode_all_live": "All LIVE ({n} configs · real API)",
            "mode_all_mock": "All MOCK ({n} configs · simulated)",
            "tf_card_title": "Breach rate by Japanese transform",
            "tf_card_note": "All configurations pooled (trials with API errors excluded). Lower favours the defender.",
            "metrics_eyebrow": "Metrics",
            "metrics_title": "Three numbers per configuration",
            "metric1_title": "ATLAS defense rate",
            "metric1_body": "Share of Japanese transformed attacks the model refused. <b class=\"ok\">Higher is safer</b>.",
            "metric2_title": "Cost per 1M tokens",
            "metric2_body": "Effective cost of the input/output tokens consumed during testing <span class=\"mono\">(USD / 1M)</span>.",
            "metric3_title": "Cospa score (custom metric)",
            "metric3_body": "<code>defense rate (%) ÷ 1M cost (USD)</code>. <b class=\"ok\">Cheaper and tougher scores higher</b>.",
            "guide_eyebrow": "Reading a configuration",
            "guide_title": "Each configuration is model × system prompt × guardrail",
            "guide_sys_title": "① System prompt",
            "guide_sys_sub": "strength of the defensive instructions given to the model",
            "badge_naked": "Naked API",
            "guide_naked_body": "No defensive instructions — the model API is <b>called directly</b>. The most attackable baseline.",
            "badge_strong": "Hardened prompt",
            "guide_strong_body": "Strongly instructed <b>defensive rules</b> such as \"never reveal the passphrase\" and \"refuse audit / developer-mode requests\".",
            "guide_gr_title": "② Guardrail (GR)",
            "guide_gr_sub": "extra layer that screens input/output",
            "badge_gr_none": "None",
            "guide_gr_none_body": "No screening layer — defense relies on the model itself.",
            "badge_gr_keyword": "Keyword GR",
            "guide_gr_keyword_body": "A <b>simple filter</b> that blocks input on banned-word matches. Cheap, but <b class=\"bad\">weak against obfuscation</b> such as gyaru script or inserted line breaks.",
            "badge_gr_llm": "LLM guardrail",
            "guide_gr_llm_body": "<b>A separate LLM screens input/output</b> to judge attacks. Accurate, but incurs extra token cost.",
            "badge_gr_regex": "Regex-normalize GR",
            "guide_gr_regex_body": "A deterministic filter that <b>strips obfuscation</b> (zero-width, Base64, leet) then checks banned keywords. <b class=\"ok\">Zero cost</b>, strong against obfuscation.",
            "badge_gr_llamaguard": "Llama Guard classifier GR",
            "guide_gr_llamaguard_body": "A <b>dedicated safety-classification model (Llama Guard)</b> that screens input for attacks vs benign content. High detection, but adds API cost.",
            "guide_rag_note": "※ \"RAG\" on a row marks configs that retrieve/inject external documents (the target of indirect prompt-injection tests). Hover a row badge for details.",
            "board_eyebrow": "Leaderboard",
            "board_title": "Defense rate and cost per configuration",
            "board_subtitle": "Sort by a column header; click a row to expand its attack log.",
            "th_rank": "Rank",
            "th_config": "Model / system config",
            "th_defense": "ATLAS defense rate",
            "th_cost": "Cost / 1M tok",
            "th_cospa": "Cospa score",
            "th_status": "Status",
            "not_measured": "not measured",
            "not_measured_tip": "Every trial failed with an API error, so this configuration is unmeasured — this is not a 0% defense rate.",
            "board_note1": "※ To avoid divergence near zero cost, the cospa score clamps the 1M-token cost floor to <span class=\"mono\">0.01 USD</span>. Status: defense rate ≧90% <b class=\"ok\">SAFE</b> / 60–90% <b class=\"warn\">WARNING</b> / &lt;60% <b class=\"bad\">VULN</b>.",
            "board_note2": "<b class=\"ok\">● LIVE</b> = real API calls, actually measured (real cost) / <b>○ MOCK</b> = deterministic simulation when the API key is unset (estimated cost).",
            "log_eyebrow": "Attack log",
            "log_title": "Japanese attack log (all reasoning)",
            "log_note": "The malicious core of every attack is masked to prevent misuse.",
            "filter_all": "All configs",
            "filter_breach_only": "Show breaches only",
            "footer_about_title": "About J-ART",
            "footer_about": "J-ART is a Japanese-focused evaluation harness inspired by garak / deepeval, run by Quiet Forensics as open research. Code is MIT; the technical report is CC-BY-4.0.",
            "footer_repo": "GitHub repository",
            "footer_body": (
                "Pull requests adding new <b>Japanese attack playbooks (test cases)</b> are welcome. "
                "If you find an unknown obfuscation vector, please share it via a "
                f"<a href=\"{REPO_URL}/pulls\" target=\"_blank\" rel=\"noopener\">PR</a>."
            ),
            "footer_support": (
                "This leaderboard runs a weekly LIVE evaluation against real APIs, funded by those measurement costs. "
                f"If you would like to help keep it running, please consider becoming a <a href=\"{SPONSOR_URL_ESCAPED}\" target=\"_blank\" rel=\"noopener\">sponsor</a>."
            ),
            "footer_cite_title": "Citation",
            "footer_disclaimer_title": "Disclaimer",
            "footer_tagline": "These metrics are a research PoC, not an official evaluation of any vendor model. Attack cores are neutralised and masked.",
            "footer_qf": "Quiet Forensics — Automated security reports from public records",
            # JS-rendered labels
            "gr_none_label": "GR: None",
            "gr_none_tip": "No guardrail: no input/output screening layer; defense relies on the model alone.",
            "gr_keyword_label": "GR: Keyword",
            "gr_keyword_tip": "Keyword GR: a simple filter that blocks input on banned-word matches; weak against obfuscation.",
            "gr_llm_label": "GR: LLM review",
            "gr_llm_tip": "LLM guardrail: a separate LLM screens input/output to judge attacks; accurate but adds cost.",
            "gr_regex_label": "GR: Regex-normalize",
            "gr_regex_tip": "Regex-normalize filter: strips obfuscation (zero-width/Base64/leet) then checks banned keywords; deterministic, zero cost.",
            "gr_llamaguard_label": "GR: Llama Guard",
            "gr_llamaguard_tip": "Llama Guard classifier: a dedicated safety-classification model that screens input; high detection rate.",
            "prompt_high_label": "Hardened",
            "prompt_high_tip": "System prompt strongly instructs defensive rules.",
            "prompt_naked_label": "Naked API",
            "prompt_naked_tip": "Model API called directly with no defensive instructions.",
            "mode_live_tip": "Real API calls, actually measured (real cost).",
            "mode_mock_tip": "Deterministic simulation when the API key is unset (estimated cost).",
            "tf_baseline": "Baseline",
            "tf_polite": "Keigo",
            "tf_vertical": "Vertical",
            "tf_gyaru": "Gyaru",
            "tf_double": "Double-talk",
            "tf_base64": "Base64",
            "tf_leet": "Leet smuggle",
            "rag_suffix": " · RAG",
            "panel_empty": "No logs for this configuration.",
            "panel_summary": "{breached} of {total} trials breached (breaches shown first).",
            "panel_log_for": "Attack log for \"{label}\"",
            "card_prompt_title": "Breached Japanese transform template (core masked)",
            "card_prompt_caption": "The obfuscation framework (preamble, line breaks, false premises) is shown verbatim; to prevent weaponization the <b class=\"bad\">malicious instruction core is masked</b>.",
            "card_response_title": "Model response (reasoning)",
            "log_count": "{n} entries",
            "log_empty": "No matching logs.",
            "log_more": "Show {n} more ({rest} remaining)",
        },
    }


# =====================================================================
#  ページテンプレート
# ---------------------------------------------------------------------
#  %%name%% の差し込み口を render_page() が 1 回だけ置換する（置換後の値は再走査しない）。
#  str.format を使わないので、CSS / JS の波括弧はそのまま書ける。
#  外装は Quiet Forensics ポータル（crypto-intel-agent/site/assets/qf.css）と同じトークン。
# =====================================================================
PAGE_TEMPLATE = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>%%site_title%%</title>
<meta name="description" content="%%site_desc%%">
<meta name="robots" content="index,follow">
<!-- Google Search Console 所有権確認（削除するとサイトマップ送信等が失効するため残す） -->
<meta name="google-site-verification" content="qREgRC0nh7MwmvSxbPYoF9CVZkwpJgQug1rJ1FYakcs">

<link rel="canonical" href="%%site_url%%">
<!-- Open Graph（SNS 共有・一部検索エンジンの理解補助） -->
<meta property="og:type" content="website">
<meta property="og:site_name" content="J-ART by Quiet Forensics">
<meta property="og:title" content="%%site_title%%">
<meta property="og:description" content="%%site_desc%%">
<meta property="og:url" content="%%site_url%%">
<meta property="og:image" content="%%site_url%%icon.svg">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="%%site_title%%">
<meta name="twitter:description" content="%%site_desc%%">
<meta name="twitter:image" content="%%site_url%%icon.svg">
<link rel="icon" type="image/svg+xml" href="icon.svg">
<link rel="apple-touch-icon" href="icon.svg">
<meta name="theme-color" content="#082A41">
<script type="application/ld+json">%%jsonld%%</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=BIZ+UDPGothic:wght@400;700&family=Noto+Sans+JP:wght@400;500;700&family=JetBrains+Mono:wght@400;500&display=swap">
<script>
/* 初回描画前に言語を決める（ちらつき防止）。優先順: ?lang= > 保存した選択 > ブラウザの言語 > en。 */
(function(){var l=null;try{var q=new URLSearchParams(location.search).get('lang');if(q==='ja'||q==='en')l=q;}catch(e){}
if(!l){try{var s=localStorage.getItem('jart_lang');if(s==='ja'||s==='en')l=s;}catch(e){}}
if(!l){try{var ls=navigator.languages||[navigator.language||''];for(var i=0;i<ls.length;i++){if(ls[i]&&ls[i].toLowerCase().indexOf('ja')===0){l='ja';break;}}}catch(e){}}
l=l||'en';document.documentElement.setAttribute('data-lang',l);document.documentElement.lang=l;})();
</script>
<style>
:root{
  --ground:#FFFFFF; --alt:#F3F8FD; --surface:#FFFFFF; --ink:#0B2236; --body-ink:#2F4254; --muted:#4F6275; --faint:#6B7C8D; --line:#D7E6F4; --line-2:#C3D6E8;
  --accent:#0077B6; --accent-hover:#005F92; --accent-soft:#E6F4FD; --accent-soft-ink:#005F92;
  --ok:#15803D; --ok-soft:#E7F7EC; --warn:#B45309; --warn-soft:#FFF8EB; --warn-line:#F2C879; --bad:#B91C1C; --bad-soft:#FDECEC; --bad-line:#F4C2C2;
  --violet:#6D28D9; --violet-soft:#F1EBFD;
  --navy:#082A41; --navy-2:#0B3A5A; --cyan:#2BC1FF; --cyan-hover:#6FD6FF; --on-navy-muted:#C5D8E8; --on-navy-faint:#9FB6C9;
  --shadow:0 16px 48px -8px rgba(11,18,32,.10); --shadow-sm:0 1px 2px rgba(11,18,32,.06);
  --sans:"Inter","BIZ UDPGothic","Noto Sans JP","Hiragino Kaku Gothic ProN","Yu Gothic",system-ui,sans-serif;
  --mono:"JetBrains Mono",ui-monospace,SFMono-Regular,Menlo,monospace;
  color-scheme:light;
}
html:not([data-lang="en"]) [lang="en"]{display:none !important}
html[data-lang="en"] [lang="ja"]{display:none !important}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--ground);color:var(--ink);font-family:var(--sans);font-size:16px;line-height:1.85;-webkit-font-smoothing:antialiased}
html[data-lang="ja"] body{letter-spacing:.02em}
a{color:var(--accent);text-decoration:none}
a:hover{color:var(--accent-hover)}
h1,h2,h3{margin:0;line-height:1.3;letter-spacing:-.01em;color:var(--ink)}
h2{font-size:clamp(1.375rem,2.4vw,2rem);font-weight:700}
h3{font-size:1.0625rem;font-weight:700}
p{margin:0}
code,.mono{font-family:var(--mono);font-size:.9em}
b{font-weight:700;color:var(--ink)}
.ok{color:var(--ok)} .warn{color:var(--warn)} .bad{color:var(--bad)}
.wrap{max-width:1160px;margin:0 auto;padding:0 24px}
.eyebrow{font-size:.8125rem;font-weight:600;color:var(--accent);letter-spacing:.02em;margin:0 0 10px}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;padding:12px 22px;border-radius:8px;font-weight:600;font-size:.9375rem;border:1px solid transparent;transition:background .15s,border-color .15s,color .15s}
.btn-primary{background:var(--cyan);color:var(--navy)}
.btn-primary:hover{background:var(--cyan-hover);color:var(--navy)}
.btn-ghost{background:transparent;color:#fff;border-color:rgba(255,255,255,.45)}
.btn-ghost:hover{border-color:#fff;color:#fff}
.btn-sm{padding:9px 16px;font-size:.875rem}

/* nav（ポータルと同じ紺の帯） */
.nav{position:sticky;top:0;z-index:20;background:var(--navy)}
.nav .wrap{display:flex;align-items:center;justify-content:space-between;gap:20px;height:64px}
.brand{display:inline-flex;align-items:center;gap:10px;color:#fff;font-weight:600;font-size:1.0625rem;letter-spacing:-.01em;white-space:nowrap}
.brand:hover{color:#fff}
.brand .logo{flex:none;display:block}
.brand .sep{color:var(--on-navy-faint);font-weight:400}
.brand .prod{color:var(--cyan)}
.nav ul{list-style:none;margin:0;padding:0;display:flex;gap:26px}
.nav ul a{color:#D6E6F3;font-weight:500;font-size:.9rem}
.nav ul a:hover{color:#fff}
.nav-right{display:flex;align-items:center;gap:14px}
.lang{display:inline-flex;padding:3px;border-radius:8px;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.18)}
.lang button{appearance:none;border:0;background:transparent;color:var(--on-navy-muted);font:inherit;font-size:.8125rem;font-weight:600;letter-spacing:.06em;padding:5px 11px;border-radius:6px;cursor:pointer}
.lang button[aria-pressed="true"]{background:#fff;color:var(--navy);box-shadow:var(--shadow-sm)}

/* hero */
.hero{background:linear-gradient(180deg,var(--navy) 0%,var(--navy-2) 100%);color:#fff;padding:64px 0 56px}
.hero .grid{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,.9fr);gap:56px;align-items:center}
.crumbs{font-size:.8125rem;color:var(--on-navy-faint);margin-bottom:14px}
.crumbs a{color:var(--on-navy-faint)}
.crumbs a:hover{color:#fff}
.chip{display:inline-flex;align-items:center;gap:8px;padding:5px 12px 5px 10px;border-radius:999px;background:rgba(43,193,255,.14);color:#8FDDFF;font-size:.8125rem;font-weight:500}
.chip::before{content:"";width:6px;height:6px;border-radius:50%;background:var(--cyan)}
.hero h1{margin-top:18px;color:#fff;display:flex;align-items:center;gap:16px;font-size:clamp(2.25rem,4vw,3.25rem);font-weight:700;line-height:1.1}
.hero h1 svg{width:56px;height:56px;flex:none}
.hero .sub{display:block;margin-top:10px;font-size:clamp(1.125rem,2vw,1.5rem);color:#fff;font-weight:700}
.hero .lead{margin-top:18px;color:var(--on-navy-muted);font-size:1.0625rem;max-width:620px}
.hero .lead b{color:#fff}
.cta{display:flex;flex-wrap:wrap;gap:12px;margin-top:26px}
.facts{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px;margin-top:40px}
.fact{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.14);border-radius:10px;padding:12px 14px;min-width:0}
.fact dt{font-size:.75rem;color:var(--on-navy-faint);font-weight:500}
.fact dd{margin:4px 0 0;font-weight:600;color:#fff;font-size:.875rem;overflow-wrap:anywhere;line-height:1.5}
.tfcard{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.16);border-radius:16px;padding:22px 24px}
.tfcard h2{font-size:.875rem;color:#8FDDFF;font-weight:600;margin-bottom:14px;letter-spacing:.01em}
.tfrow{display:grid;grid-template-columns:7.5em minmax(0,1fr) 3.6em;gap:12px;align-items:center;font-size:.875rem;padding:5px 0}
.tfrow .n{color:var(--on-navy-muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tfrow .track{height:8px;border-radius:999px;background:rgba(255,255,255,.12);overflow:hidden}
.tfrow .track i{display:block;height:100%;background:var(--cyan);border-radius:999px}
.tfrow .v{text-align:right;font-family:var(--mono);color:#fff;font-size:.8125rem}
.tfcard .note{margin-top:12px;font-size:.75rem;color:var(--on-navy-faint);line-height:1.6}

/* sections */
.block{padding:72px 0}
.block.alt{background:var(--alt);border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
.sec-head{max-width:760px;margin-bottom:28px}
.sec-head p.sub{margin-top:10px;color:var(--muted)}
.cards3{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px}
.cards2{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:24px}
.card .n{font-weight:600;font-size:.8125rem;color:var(--accent)}
.card h3{margin-top:6px}
.card h3 small{font-weight:400;color:var(--faint);font-size:.8125rem;margin-left:8px}
.card p{margin-top:8px;font-size:.9rem;color:var(--muted);line-height:1.75}
.defs{list-style:none;margin:14px 0 0;padding:0;display:grid;gap:12px}
.defs li{display:flex;gap:12px;align-items:flex-start;font-size:.875rem;color:var(--muted);line-height:1.7}
.defs li .pill{flex:none;margin-top:2px}
.note{font-size:.8125rem;color:var(--faint);margin-top:12px;line-height:1.7}

/* pills */
.pill{display:inline-flex;align-items:center;gap:5px;padding:2px 9px;border-radius:999px;font-size:.75rem;font-weight:500;white-space:nowrap;border:1px solid var(--line);background:var(--alt);color:var(--body-ink);line-height:1.6}
.pill[title]{cursor:help}
.p-live,.p-llm{background:var(--ok-soft);color:var(--ok);border-color:transparent}
.p-mock,.p-naked,.p-nodata{background:var(--alt);color:var(--muted)}
.p-high,.p-llamaguard{background:var(--accent-soft);color:var(--accent-soft-ink);border-color:transparent}
.p-none{background:var(--bad-soft);color:var(--bad);border-color:transparent}
.p-keyword{background:var(--warn-soft);color:var(--warn);border-color:var(--warn-line)}
.p-regex{background:var(--violet-soft);color:var(--violet);border-color:transparent}
.st{font-weight:700;letter-spacing:.04em}
.st::before{content:"";width:6px;height:6px;border-radius:50%;background:currentColor}
.st-safe{background:var(--ok-soft);color:var(--ok);border-color:transparent}
.st-warn{background:var(--warn-soft);color:var(--warn);border-color:var(--warn-line)}
.st-vuln{background:var(--bad-soft);color:var(--bad);border-color:var(--bad-line)}

/* leaderboard */
.tablewrap{overflow-x:auto;background:var(--surface);border:1px solid var(--line);border-radius:12px;box-shadow:var(--shadow)}
table.board{width:100%;min-width:760px;border-collapse:collapse;font-size:.875rem}
.board th{text-align:left;font-weight:500;color:var(--faint);font-size:.8125rem;padding:12px 16px;background:var(--alt);border-bottom:1px solid var(--line);white-space:nowrap}
.board th.r,.board td.r{text-align:right}
.board th.c,.board td.c{text-align:center}
.board td{padding:14px 16px;border-bottom:1px solid var(--line);vertical-align:middle;color:var(--body-ink)}
th.sortable{cursor:pointer;user-select:none}
th.sortable:hover{color:var(--ink)}
.arrow::after{content:" ⇅";opacity:.35;font-size:.8em}
.arrow.asc::after{content:" ▲";opacity:1;color:var(--accent)}
.arrow.desc::after{content:" ▼";opacity:1;color:var(--accent)}
tr.board-row{cursor:pointer;transition:background .15s}
tr.board-row:hover{background:#F8FBFE}
tr.board-row.is-open{background:var(--accent-soft)}
.rank{font-family:var(--mono);color:var(--faint);font-weight:600}
.rank.top{display:inline-grid;place-items:center;width:28px;height:28px;border-radius:50%;background:var(--navy);color:#fff;font-size:.8125rem}
.board td.cfgcell{min-width:320px}
.cfg{font-weight:600;color:var(--ink)}
.more{margin-top:14px;font:inherit;font-size:.875rem;font-weight:600;color:var(--accent);background:var(--surface);border:1px solid var(--line-2);border-radius:8px;padding:9px 16px;cursor:pointer}
.more:hover{border-color:var(--accent)}
.badges{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px}
.model{margin-top:6px;font-size:.8125rem;color:var(--faint)}
.model .mono{color:var(--muted)}
.rate{display:flex;align-items:center;justify-content:flex-end;gap:10px;flex-wrap:wrap}
.bar{width:96px;height:6px;border-radius:999px;background:var(--line);overflow:hidden}
.bar i{display:block;height:100%;border-radius:999px}
.bar .i-ok{background:var(--ok)} .bar .i-warn{background:var(--warn)} .bar .i-bad{background:var(--bad)}
.pct{font-variant-numeric:tabular-nums;font-weight:700;min-width:3.6em;text-align:right}
.ci{font-size:.75rem;color:var(--faint);font-family:var(--mono)}
.prov{font-size:.75rem;color:var(--warn)}
.num{font-family:var(--mono);font-variant-numeric:tabular-nums}
.cospa{font-size:1.0625rem;font-weight:700;color:var(--ink);font-variant-numeric:tabular-nums}
.chev{width:16px;height:16px;color:var(--faint);transition:transform .25s ease}
tr.is-open .chev{transform:rotate(90deg);color:var(--accent)}
.acc-row>td{padding:0 !important;border:0 !important}
.acc-wrap{display:grid;grid-template-rows:0fr;transition:grid-template-rows .28s cubic-bezier(.4,0,.2,1)}
tr.is-open+tr.acc-row .acc-wrap{grid-template-rows:1fr}
tr.is-open+tr.acc-row>td{border-bottom:1px solid var(--line) !important}
.acc-inner{overflow:hidden}
.panel{padding:20px 24px;background:var(--alt);display:grid;gap:10px}
.panel-title{font-weight:700;color:var(--ink);font-size:.9375rem}
.panel-sum{font-size:.8125rem;color:var(--muted)}

/* attack log */
.filters{display:flex;flex-wrap:wrap;gap:14px;align-items:center;margin-bottom:16px;font-size:.875rem}
.filters select{font:inherit;font-size:.875rem;color:var(--ink);background:var(--surface);border:1px solid var(--line-2);border-radius:8px;padding:8px 12px;max-width:100%}
.filters select:focus{outline:2px solid var(--accent);outline-offset:1px}
.filters label{display:inline-flex;align-items:center;gap:8px;cursor:pointer;color:var(--body-ink)}
.filters input{accent-color:var(--bad);width:16px;height:16px}
.count{font-family:var(--mono);color:var(--faint);font-size:.8125rem}
.logs{display:grid;gap:10px}
details.logc{background:var(--surface);border:1px solid var(--line);border-radius:10px}
details.logc.breached{border-color:var(--bad-line);border-left:3px solid var(--bad)}
details.logc>summary{list-style:none;cursor:pointer;padding:12px 16px;display:flex;flex-wrap:wrap;align-items:center;gap:8px;border-radius:10px}
details.logc>summary::-webkit-details-marker{display:none}
details.logc>summary:hover{background:#F8FBFE}
.verdict{font-size:.75rem;font-weight:700;letter-spacing:.04em;padding:2px 9px;border-radius:6px;color:#fff}
.v-breached{background:var(--bad)} .v-defended{background:var(--ok)}
.meta{font-family:var(--mono);font-size:.75rem;color:var(--faint)}
.meta.end{margin-left:auto}
.logbody{padding:0 16px 16px;display:grid;gap:12px;font-size:.875rem}
details[open] .logbody{animation:fadeIn .25s ease both}
@keyframes fadeIn{from{opacity:0;transform:translateY(-4px)}to{opacity:1;transform:none}}
.kv b{color:var(--accent);font-weight:600;margin-right:6px}
.kv .dim{color:var(--faint)}
.lbl{font-size:.75rem;font-weight:600;color:var(--muted);margin-bottom:4px}
.cap{font-size:.75rem;color:var(--faint);margin-bottom:6px;line-height:1.6}
pre.code{margin:0;white-space:pre-wrap;word-break:break-word;font-family:var(--mono);font-size:.8125rem;line-height:1.7;background:var(--alt);border:1px solid var(--line);border-radius:8px;padding:12px 14px;color:var(--body-ink);max-height:18rem;overflow:auto}
pre.code.resp-bad{background:var(--bad-soft);border-color:var(--bad-line);color:#7F1D1D}
pre.code.resp-ok{background:var(--ok-soft);border-color:transparent;color:#14532D}

/* footer（ポータルと同じ濃紺） */
footer{background:#061F31;color:#A9B3C2;padding:56px 0 40px;font-size:.875rem}
footer a{color:#8FDDFF}
footer a:hover{color:#fff}
footer b{color:#fff}
footer .cols{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:32px}
footer h3{color:#fff;font-size:.875rem;margin-bottom:10px}
footer p{line-height:1.75}
footer p+p{margin-top:10px}
footer pre{margin:0;white-space:pre-wrap;word-break:break-all;font-family:var(--mono);font-size:.75rem;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.12);border-radius:8px;padding:10px 12px;color:#C5D8E8}
footer .models{margin-top:28px;font-size:.75rem;color:#7F93A6;line-height:1.7}
footer .bottom{display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap;margin-top:32px;padding-top:24px;border-top:1px solid rgba(255,255,255,.1)}
footer .brand{font-size:.9375rem}
footer .brand .logo{width:22px;height:22px}
footer .gh{display:inline-flex;align-items:center;gap:8px;font-weight:600}
footer .gh svg{width:18px;height:18px;fill:currentColor}

@media (max-width:1100px){.nav ul{display:none}}
@media (max-width:960px){
  .hero .grid,.cards2,footer .cols{grid-template-columns:1fr}
  .cards3{grid-template-columns:1fr}
  .facts{grid-template-columns:repeat(2,minmax(0,1fr))}
}
@media (max-width:640px){
  .wrap{padding:0 16px}
  .nav .wrap{gap:10px}
  .nav .btn-primary{display:none}
  .brand .qfname{display:none}
  .hero{padding:44px 0 40px}
  .hero h1 svg{width:44px;height:44px}
  .block{padding:52px 0}
  .cta .btn{width:100%}
  .tfcard{padding:18px}
  .tfrow{grid-template-columns:6.5em minmax(0,1fr) 3.4em;gap:8px}
  .panel{padding:16px}
}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}.acc-wrap,.chev{transition:none}details[open] .logbody{animation:none}}
</style>
%%analytics%%
</head>
<body>
<nav class="nav" aria-label="Site">
  <div class="wrap">
    <a class="brand" href="%%qf_url%%">%%qf_logo%%<span class="qfname">Quiet Forensics</span><span class="sep">/</span><span class="prod">J-ART</span></a>
    <ul>
      <li><a href="#board" data-i18n="nav_board">リーダーボード</a></li>
      <li><a href="#log" data-i18n="nav_log">攻撃ログ</a></li>
      <li><a href="%%paper_url%%" target="_blank" rel="noopener" data-i18n="nav_paper">テクニカルレポート</a></li>
      <li><a href="%%repo_url%%" target="_blank" rel="noopener">GitHub</a></li>
    </ul>
    <div class="nav-right">
      <div class="lang" role="group" aria-label="Language / 言語">
        <button type="button" data-lang-btn="ja" aria-pressed="true">JA</button>
        <button type="button" data-lang-btn="en" aria-pressed="false">EN</button>
      </div>
      <a class="btn btn-primary btn-sm" href="%%qf_url%%#services" data-i18n="nav_services">Quiet Forensics のサービス</a>
    </div>
  </div>
</nav>

<header class="hero" id="top">
  <div class="wrap">
    <div class="grid">
      <div>
        <p class="crumbs"><a href="%%qf_url%%">Quiet Forensics</a> › <span data-i18n="crumb_research">公開研究</span> › J-ART</p>
        <span class="chip" data-i18n="chip">公開研究 · MITRE ATLAS 準拠</span>
        <h1>%%header_icon%%<span>J-ART</span></h1>
        <span class="sub" data-i18n="subtitle">日本語 LLM レッドチーム・リーダーボード</span>
        <p class="lead" data-i18n-html="tagline">%%ja.tagline%%</p>
        <div class="cta">
          <a class="btn btn-primary" href="#board" data-i18n="cta_board">リーダーボードを見る</a>
          <a class="btn btn-ghost" href="%%paper_url%%" target="_blank" rel="noopener" data-i18n="cta_paper">テクニカルレポート</a>
        </div>
      </div>
      %%tf_card%%
    </div>
    <dl class="facts">
      <div class="fact"><dt data-i18n="badge_updated">最終更新</dt><dd class="mono">%%generated_at%%</dd></div>
      <div class="fact"><dt data-i18n="badge_mode">実行モード</dt><dd id="mode-badge-label">%%mode%%</dd></div>
      <div class="fact"><dt data-i18n="badge_targets">構成数</dt><dd class="mono">%%n_targets%%</dd></div>
      <div class="fact"><dt data-i18n="badge_trials">総試行</dt><dd class="mono">%%n_details%%</dd></div>
      <div class="fact"><dt data-i18n="badge_transforms">日本語変形</dt><dd class="mono">%%n_transforms%%</dd></div>
    </dl>
  </div>
</header>

<section class="block">
  <div class="wrap">
    <div class="sec-head">
      <p class="eyebrow" data-i18n="metrics_eyebrow">指標</p>
      <h2 data-i18n="metrics_title">3 つの指標で比較します</h2>
    </div>
    <div class="cards3">
      <div class="card"><span class="n">01</span><h3 data-i18n="metric1_title">ATLAS 防御成功率</h3><p data-i18n-html="metric1_body">%%ja.metric1_body%%</p></div>
      <div class="card"><span class="n">02</span><h3 data-i18n="metric2_title">100万トークン単価</h3><p data-i18n-html="metric2_body">%%ja.metric2_body%%</p></div>
      <div class="card"><span class="n">03</span><h3 data-i18n="metric3_title">コスパスコア（独自指標）</h3><p data-i18n-html="metric3_body">%%ja.metric3_body%%</p></div>
    </div>
  </div>
</section>

<section class="block alt">
  <div class="wrap">
    <div class="sec-head">
      <p class="eyebrow" data-i18n="guide_eyebrow">構成の読み方</p>
      <h2 data-i18n="guide_title">各構成は「モデル × システムプロンプト × ガードレール」</h2>
    </div>
    <div class="cards2">
      <div class="card">
        <h3><span data-i18n="guide_sys_title">① システムプロンプト</span><small data-i18n="guide_sys_sub">モデルへ与える防御指示の強さ</small></h3>
        <ul class="defs">
          <li><span class="pill p-naked" data-i18n="badge_naked">素のAPI</span><span data-i18n-html="guide_naked_body">%%ja.guide_naked_body%%</span></li>
          <li><span class="pill p-high" data-i18n="badge_strong">強化プロンプト</span><span data-i18n-html="guide_strong_body">%%ja.guide_strong_body%%</span></li>
        </ul>
      </div>
      <div class="card">
        <h3><span data-i18n="guide_gr_title">② ガードレール（GR）</span><small data-i18n="guide_gr_sub">入出力を検閲する追加レイヤー</small></h3>
        <ul class="defs">
          <li><span class="pill p-none" data-i18n="badge_gr_none">なし</span><span data-i18n-html="guide_gr_none_body">%%ja.guide_gr_none_body%%</span></li>
          <li><span class="pill p-keyword" data-i18n="badge_gr_keyword">キーワードGR</span><span data-i18n-html="guide_gr_keyword_body">%%ja.guide_gr_keyword_body%%</span></li>
          <li><span class="pill p-llm" data-i18n="badge_gr_llm">LLMガードレール</span><span data-i18n-html="guide_gr_llm_body">%%ja.guide_gr_llm_body%%</span></li>
          <li><span class="pill p-regex" data-i18n="badge_gr_regex">正規化フィルタGR</span><span data-i18n-html="guide_gr_regex_body">%%ja.guide_gr_regex_body%%</span></li>
          <li><span class="pill p-llamaguard" data-i18n="badge_gr_llamaguard">Llama Guard 分類器GR</span><span data-i18n-html="guide_gr_llamaguard_body">%%ja.guide_gr_llamaguard_body%%</span></li>
        </ul>
      </div>
    </div>
    <p class="note" data-i18n-html="guide_rag_note">%%ja.guide_rag_note%%</p>
  </div>
</section>

<section class="block" id="board">
  <div class="wrap">
    <div class="sec-head">
      <p class="eyebrow" data-i18n="board_eyebrow">リーダーボード</p>
      <h2 data-i18n="board_title">構成ごとの防御率とコスト</h2>
      <p class="sub" data-i18n="board_subtitle">列見出しで並び替え、行をクリックするとその構成の攻撃ログを展開します。</p>
    </div>
    <div class="tablewrap">
      <table class="board">
        <thead>
          <tr>
            <th class="c" data-i18n="th_rank">順位</th>
            <th class="sortable arrow" data-key="target_label" data-type="str" data-i18n="th_config">モデル / システム構成</th>
            <th class="r sortable arrow" data-key="success_rate" data-type="num" data-i18n="th_defense">ATLAS 防御成功率</th>
            <th class="r sortable arrow" data-key="cost_per_million_usd" data-type="num" data-i18n="th_cost">コスト / 1M tok</th>
            <th class="r sortable arrow desc" data-key="cospa_score" data-type="num" data-i18n="th_cospa">コスパスコア</th>
            <th class="c" data-i18n="th_status">ステータス</th>
            <th class="c"></th>
          </tr>
        </thead>
        <tbody id="board-body"></tbody>
      </table>
    </div>
    <p class="note" data-i18n-html="board_note1">%%ja.board_note1%%</p>
    <p class="note" style="margin-top:4px" data-i18n-html="board_note2">%%ja.board_note2%%</p>
  </div>
</section>

<section class="block alt" id="log">
  <div class="wrap">
    <div class="sec-head">
      <p class="eyebrow" data-i18n="log_eyebrow">攻撃ログ</p>
      <h2 data-i18n="log_title">日本語攻撃ログ（Reasoning 全件）</h2>
      <p class="sub" data-i18n="log_note">攻撃文のうち悪意ある指示のコアは、悪用を防ぐためマスクしています。</p>
    </div>
    <div class="filters">
      <select id="filter-target" aria-label="config"></select>
      <label><input type="checkbox" id="filter-breach"> <span data-i18n="filter_breach_only">突破成功のみ表示</span></label>
      <span id="log-count" class="count"></span>
    </div>
    <div id="log-list" class="logs"></div>
  </div>
</section>

<footer>
  <div class="wrap">
    <div class="cols">
      <div>
        <h3 data-i18n="footer_about_title">J-ART について</h3>
        <p data-i18n="footer_about">%%ja.footer_about%%</p>
        <p><a class="gh" href="%%repo_url%%" target="_blank" rel="noopener"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8Z"/></svg><span data-i18n="footer_repo">GitHub リポジトリ</span></a></p>
        <p data-i18n-html="footer_body">%%ja.footer_body%%</p>
        <p data-i18n-html="footer_support">%%ja.footer_support%%</p>
      </div>
      <div>
        <h3 data-i18n="footer_cite_title">引用</h3>
        <p>DOI: <a href="%%doi_url%%" target="_blank" rel="noopener">%%doi%%</a></p>
        <pre>@software{hirose_jart_2026,
  title = {J-ART: A Japanese Adversarial Red-Team Framework for Application-Layer LLM Security and Cost-Efficiency},
  author = {Hirose, Takayuki},
  year = {2026},
  doi = {%%doi%%}
}</pre>
      </div>
      <div>
        <h3 data-i18n="footer_disclaimer_title">免責事項</h3>
        <p data-i18n="footer_tagline">本指標は研究・検証用 PoC であり、各社モデルの公式評価ではありません。攻撃のコア指示は無害化・マスク済みです。</p>
        <p><a href="%%qf_url%%" data-i18n="footer_qf">Quiet Forensics — 公開記録の自動解析によるセキュリティレポート</a></p>
      </div>
    </div>
    <!-- クロール可能なモデル一覧（ランキング表は JS 注入のため、検索到達性の担保として静的にも列挙） -->
    <p class="models">%%seo_models%%</p>
    <div class="bottom">
      <a class="brand" href="%%qf_url%%">%%qf_logo%%Quiet Forensics</a>
      <span>© 2026 Quiet Forensics · J-ART (MIT)</span>
    </div>
  </div>
</footer>

<script>
const DATA = %%data_json%%
const I18N = %%i18n_json%%;

// ---------- i18n（UI外装のみ。データ本文・日本語攻撃プロンプトは原文維持） ----------
let LANG = document.documentElement.getAttribute("data-lang") === "ja" ? "ja" : "en";
function t(key) {
  const L = I18N[LANG] || I18N.ja;
  if (L && L[key] != null) return L[key];
  return (I18N.ja && I18N.ja[key] != null) ? I18N.ja[key] : key;
}
// 構成名は UI 表示なので言語に応じて切替（EN時は target_label_en があれば使用）
function labelOf(o) {
  return (LANG === "en" && o.target_label_en) ? o.target_label_en : o.target_label;
}
function modeText() {
  const s = DATA.summary || [];
  const live = s.filter(function(x) { return x.mode === "LIVE"; }).length;
  const mock = s.filter(function(x) { return x.mode === "MOCK"; }).length;
  if (live && mock) return t("mode_mixed").replace("{live}", live).replace("{mock}", mock);
  if (live) return t("mode_all_live").replace("{n}", live);
  return t("mode_all_mock").replace("{n}", mock);
}
function applyI18n(lang) {
  LANG = lang;
  try { localStorage.setItem("jart_lang", lang); } catch (e) {}
  document.documentElement.lang = lang;
  document.documentElement.setAttribute("data-lang", lang);
  document.querySelectorAll("[data-i18n]").forEach(function(el) {
    const v = (I18N[lang] || {})[el.getAttribute("data-i18n")];
    if (v != null) el.textContent = v;
  });
  document.querySelectorAll("[data-i18n-html]").forEach(function(el) {
    const v = (I18N[lang] || {})[el.getAttribute("data-i18n-html")];
    if (v != null) el.innerHTML = v;
  });
  document.querySelectorAll("[data-lang-btn]").forEach(function(b) {
    b.setAttribute("aria-pressed", String(b.getAttribute("data-lang-btn") === lang));
  });
  const lbl = document.getElementById("mode-badge-label");
  if (lbl) lbl.textContent = modeText();
  buildFilter();
  renderBoard();
  renderLog();
}

// ---------- helpers ----------
function esc(s) { const d=document.createElement("div"); d.textContent=s==null?"":String(s); return d.innerHTML; }
function fmtUSD(x) { return "$" + Number(x).toLocaleString("en-US", {maximumFractionDigits: 4}); }
function pill(cls, label, tip) {
  return `<span class="pill ${cls}"${tip ? ` title="${esc(tip)}"` : ""}>${esc(label)}</span>`;
}

function guardrailBadge(g) {
  const m = {
    none:       ["p-none", "gr_none_label", "gr_none_tip"],
    keyword:    ["p-keyword", "gr_keyword_label", "gr_keyword_tip"],
    llm:        ["p-llm", "gr_llm_label", "gr_llm_tip"],
    regex:      ["p-regex", "gr_regex_label", "gr_regex_tip"],
    llamaguard: ["p-llamaguard", "gr_llamaguard_label", "gr_llamaguard_tip"]
  };
  const e = m[g];
  return e ? pill(e[0], t(e[1]), t(e[2])) : pill("", g, "");
}

// システムプロンプト強度バッジ（素のAPI / 強化プロンプト）
function promptBadge(s) {
  if (s === "high") return pill("p-high", t("prompt_high_label"), t("prompt_high_tip"));
  return pill("p-naked", t("prompt_naked_label"), t("prompt_naked_tip"));
}

// 有効試行が1件でもあるか（measured は新しい results.json のみ持つため後方互換をとる）
function isMeasured(s) {
  return (s.measured !== false) && (s.total_attacks == null || s.total_attacks > 0);
}
// 防御成功率 → SAFE / WARNING / VULN
function statusOf(r) {
  if (r >= 90) return {label:"SAFE", cls:"st-safe", tone:"ok"};
  if (r >= 60) return {label:"WARNING", cls:"st-warn", tone:"warn"};
  return {label:"VULN", cls:"st-vuln", tone:"bad"};
}
function statusBadge(r) {
  const s = statusOf(r);
  return `<span class="pill st ${s.cls}">${s.label}</span>`;
}
function noDataBadge() {
  return pill("p-nodata", "NO DATA", t("not_measured_tip"));
}

function rateBar(s) {
  // 全セルがAPIエラーだった構成は「未計測」。0%（＝最弱）と誤読させないため N/A を出す。
  if (!isMeasured(s))
    return `<div class="rate"><span class="pct" style="color:var(--faint)">N/A</span><span class="ci">${esc(t("not_measured"))}</span></div>`;
  const r = s.success_rate;
  const tone = statusOf(r).tone;
  const ci = (s.ci_low != null && s.ci_high != null)
    ? `<span class="ci">CI[${Number(s.ci_low).toFixed(1)}–${Number(s.ci_high).toFixed(1)}]</span>`
    : "";
  // 部分データ（レート制限等で試行が除外された）構成は暫定として明示する。
  const prov = (s.n_api_error && s.n_api_error > 0)
    ? `<span class="prov" title="provisional: ${s.n_api_error} trials excluded (API error); non-random missingness — see paper §7">⚠ n=${s.total_attacks}/${s.n_planned || (s.total_attacks + s.n_api_error)}</span>`
    : "";
  return `<div class="rate"><div class="bar"><i class="i-${tone}" style="width:${r}%"></i></div>
      <span class="pct ${tone}">${r.toFixed(1)}%</span>${ci}${prov}</div>`;
}

function transformBadge(name) {
  const m = {baseline:"tf_baseline", polite_business:"tf_polite", vertical_newline:"tf_vertical",
             gyaru:"tf_gyaru", double_tongue:"tf_double", base64_wrap:"tf_base64", leet_smuggle:"tf_leet"};
  return pill("", m[name] ? t(m[name]) : name, "");
}

// LIVE（実API計測）/ MOCK（決定論シミュレーション）の識別バッジ
function modeBadge(m) {
  if (m === "LIVE") return pill("p-live", "● LIVE", t("mode_live_tip"));
  return pill("p-mock", "○ MOCK", t("mode_mock_tip"));
}

// 行内アコーディオンの中身（その構成の攻撃ログ。突破を上位に）
function panelContent(targetId) {
  let rows = DATA.details.filter(d => d.target_id === targetId)
                         .sort((a,b) => (b.breached?1:0) - (a.breached?1:0));
  if (!rows.length) return `<p class="panel-sum">${esc(t("panel_empty"))}</p>`;
  const breached = rows.filter(d => d.breached).length;
  const totalTrials = rows.reduce((s,d) => s + (d.trials||1), 0);
  const summary = t("panel_summary").replace("{total}", totalTrials).replace("{breached}", breached);
  return `<div class="panel-sum">${esc(summary)}</div>` + rows.map(d => logCard(d)).join("");
}

// 安全マスク: 悪意あるコアは run_assessment.py 側で既に伏字化済みだが、
// 万一プレースホルダ(CORE_SLOT)が残っていても画面では必ずマスクへ置換する二重防御。
const CORE_SLOT = "<<CORE>>";
const CORE_MASK = "[ 悪意ある指示のコア（安全のためマスク済） ]";
function maskCore(s) {
  return (s || "").split(CORE_SLOT).join(CORE_MASK);
}

// 個別の攻撃ログカード（<details>）
function logCard(d) {
  return `
    <details class="logc${d.breached ? " breached" : ""}">
      <summary>
        <span class="verdict ${d.breached ? "v-breached" : "v-defended"}">${d.breached ? "BREACHED" : "DEFENDED"}</span>
        <span class="meta">${esc(d.atlas_id)}</span>
        <span class="meta">${esc(d.attack_id)}</span>
        ${transformBadge(d.transformation)}
        <span class="meta end">${d.trials>1 ? d.breaches+"/"+d.trials+" breached · " : ""}in ${d.input_tokens} / out ${d.output_tokens} tok · ${fmtUSD(d.cost_usd)}</span>
      </summary>
      <div class="logbody">
        <div class="kv"><b>ATLAS</b>${esc(d.atlas_name)} <span class="dim">(vector: ${esc(d.vector)})</span></div>
        <div class="kv"><b>Reasoning</b>${esc(d.reason)}</div>
        <div>
          <div class="lbl">${esc(t("card_prompt_title"))}</div>
          <div class="cap">${t("card_prompt_caption")}</div>
          <pre class="code">${esc(maskCore(d.prompt_excerpt))}</pre>
        </div>
        <div>
          <div class="lbl">${esc(t("card_response_title"))}</div>
          <pre class="code ${d.breached ? "resp-bad" : "resp-ok"}">${esc(maskCore(d.response_excerpt))}</pre>
        </div>
      </div>
    </details>`;
}

// ---------- Leaderboard ----------
let board = DATA.summary.slice();
let sortKey = "cospa_score", sortType = "num", sortDir = -1;

function renderBoard() {
  // 未計測（全セルAPIエラー）の構成は順位を付けず、常に表の末尾へ回す。
  const ranked = board.filter(isMeasured);
  const unranked = board.filter(function(s) { return !isMeasured(s); });
  ranked.sort((a,b) => {
    let av=a[sortKey], bv=b[sortKey];
    if (sortType==="str") return String(av).localeCompare(String(bv))*sortDir;
    return (av-bv)*sortDir;
  });
  const body = document.getElementById("board-body");
  body.innerHTML = ranked.concat(unranked).map((s,i) => {
    const rankBadge = !isMeasured(s)
      ? `<span class="rank">—</span>`
      : `<span class="rank${i < 3 ? " top" : ""}">${i+1}</span>`;
    const sub = `${esc(s.provider)}${s.rag ? esc(t("rag_suffix")) : ""}`;
    return `
    <tr class="board-row" data-tid="${esc(s.target_id)}" tabindex="0" aria-expanded="false">
      <td class="c" style="width:64px">${rankBadge}</td>
      <td class="cfgcell">
        <div class="cfg">${esc(labelOf(s))}</div>
        <div class="badges">${isMeasured(s) ? modeBadge(s.mode) : noDataBadge()} ${promptBadge(s.prompt_strength)} ${guardrailBadge(s.guardrail)}</div>
        <div class="model"><span class="mono">${esc(s.model)}</span> · ${sub}</div>
      </td>
      <td class="r">${rateBar(s)}</td>
      <td class="r num">${fmtUSD(s.cost_per_million_usd)}</td>
      <td class="r"><span class="cospa">${Number(s.cospa_score).toLocaleString()}</span></td>
      <td class="c">${isMeasured(s) ? statusBadge(s.success_rate) : noDataBadge()}</td>
      <td class="c"><svg class="chev" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M7 5l6 5-6 5" stroke-linecap="round" stroke-linejoin="round"/></svg></td>
    </tr>
    <tr class="acc-row">
      <td colspan="7">
        <div class="acc-wrap"><div class="acc-inner">
          <div class="panel">
            <div class="panel-title">${esc(t("panel_log_for").replace("{label}", labelOf(s)))}</div>
            <div class="panel-body" data-tid="${esc(s.target_id)}"></div>
          </div>
        </div></div>
      </td>
    </tr>`;
  }).join("");

  // 行クリック / Enter・Space でアコーディオン開閉
  body.querySelectorAll("tr.board-row").forEach(tr => {
    const toggle = () => {
      // 攻撃ログは初めて開いたときに描画する（全行分を先に作ると初期表示が重い）。
      const pb = tr.nextElementSibling.querySelector(".panel-body");
      if (pb && !pb.dataset.done) { pb.innerHTML = panelContent(pb.dataset.tid); pb.dataset.done = "1"; }
      tr.classList.toggle("is-open");
      tr.setAttribute("aria-expanded", String(tr.classList.contains("is-open")));
    };
    tr.addEventListener("click", (e) => {
      if (e.target.closest("details")) return; // 内側のdetailsクリックは無視
      toggle();
    });
    tr.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggle(); }
    });
  });
}

document.querySelectorAll("th.sortable").forEach(th => {
  th.addEventListener("click", () => {
    const key = th.dataset.key, type = th.dataset.type;
    if (sortKey===key) sortDir*=-1; else { sortDir = (type==="num"?-1:1); }
    sortKey=key; sortType=type;
    document.querySelectorAll("th.sortable").forEach(x=>x.classList.remove("asc","desc"));
    th.classList.add(sortDir===1?"asc":"desc");
    renderBoard();
  });
});

// ---------- 全攻撃ログ（フィルタ付き） ----------
const sel = document.getElementById("filter-target");
function buildFilter() {
  const cur = sel.value;
  sel.innerHTML = `<option value="">${esc(t("filter_all"))}</option>` +
    DATA.summary.map(s=>`<option value="${esc(s.target_id)}">${esc(labelOf(s))}</option>`).join("");
  sel.value = cur;
}

// ログ一覧は PAGE 件ずつ描画する（全件 3,000 超を一度に DOM 化しない）。
const PAGE = 200;
let shown = PAGE;
function renderLog(keep) {
  if (keep !== true) shown = PAGE;
  const tgt = sel.value;
  const onlyBreach = document.getElementById("filter-breach").checked;
  let rows = DATA.details.filter(d => (!tgt || d.target_id===tgt) && (!onlyBreach || d.breached));
  document.getElementById("log-count").textContent = t("log_count").replace("{n}", rows.length);
  const rest = rows.length - shown;
  document.getElementById("log-list").innerHTML =
    (rows.slice(0, shown).map(d => logCard(d)).join("") || `<p class="note">${esc(t("log_empty"))}</p>`) +
    (rest > 0 ? `<button type="button" class="more" id="log-more">${esc(t("log_more").replace("{n}", Math.min(rest, PAGE)).replace("{rest}", rest))}</button>` : "");
  const more = document.getElementById("log-more");
  if (more) more.addEventListener("click", function() { shown += PAGE; renderLog(true); });
}

sel.addEventListener("change", renderLog);
document.getElementById("filter-breach").addEventListener("change", renderLog);
document.querySelectorAll("[data-lang-btn]").forEach(function(b) {
  b.addEventListener("click", function() { applyI18n(b.getAttribute("data-lang-btn")); });
});

// 初期描画（言語適用 → フィルタ構築 → ボード/ログ描画を内部で実行）
applyI18n(LANG);
</script>
</body>
</html>
"""


def _script_json(obj):
    """<script> 内へ埋め込む JSON。モデル出力に </script> や <!-- があっても要素を閉じさせない。"""
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/").replace("<!--", "<\\!--")


def _fmt_generated_at(s):
    """'2026-08-23T18:31:19.1+00:00' → '2026-08-23 18:31 UTC'。形式が違えばそのまま返す。"""
    m = re.match(r"^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2})", s or "")
    return f"{m.group(1)} {m.group(2)} UTC" if m else (s or "")


def transform_breach_rates(data):
    """日本語変形ごとの突破率（全構成合算、API エラー試行は除外）。表示順は config の変形順。

    LIVE の試行が 1 件でもあれば LIVE のみで集計し、MOCK の想定値を混ぜない。
    戻り値: [(transform_id, breaches, trials), ...]（trials 0 の変形は除く）。
    """
    details = data.get("details", [])
    live_only = any(d.get("mode") == "LIVE" for d in details)
    agg = defaultdict(lambda: [0, 0])
    for d in details:
        if d.get("api_error") or (live_only and d.get("mode") != "LIVE"):
            continue
        trials = d.get("trials") or 1
        breaches = d.get("breaches")
        if breaches is None:
            breaches = trials if d.get("breached") else 0
        agg[d.get("transformation", "")][0] += breaches
        agg[d.get("transformation", "")][1] += trials
    order = list(data.get("transformations", [])) + sorted(k for k in agg if k not in data.get("transformations", []))
    return [(k, agg[k][0], agg[k][1]) for k in order if agg.get(k, [0, 0])[1] > 0]


def _tf_card(data):
    """ヒーロー右側の集計カード（変形別の突破率バー）。データが無ければ空文字。"""
    rows = transform_breach_rates(data)
    if not rows:
        return ""
    top = max(b / t for _, b, t in rows) or 1.0
    out = []
    for key, b, t in rows:
        ja, en = TRANSFORM_LABELS.get(key, (key, key))
        rate = 100.0 * b / t
        width = 100.0 * (b / t) / top
        out.append(
            f'<div class="tfrow"><span class="n"><span lang="ja">{html.escape(ja)}</span>'
            f'<span lang="en">{html.escape(en)}</span></span>'
            f'<span class="track"><i style="width:{width:.1f}%"></i></span>'
            f'<span class="v">{rate:.1f}%</span></div>'
        )
    return (
        '<aside class="tfcard" aria-labelledby="tf-title">'
        '<h2 id="tf-title" data-i18n="tf_card_title">日本語変形ごとの突破率</h2>'
        + "".join(out)
        + '<p class="note" data-i18n="tf_card_note">全構成の試行を合算（API エラーの試行は除外）。低いほど防御側が優位。</p>'
        "</aside>"
    )


def render_page(data, analytics=""):
    """results.json の内容から index.html の文字列を作る（ファイル I/O なし）。"""
    summary = data.get("summary", [])

    # 構成ごとの LIVE / MOCK 内訳を集計し、ヘッダーに混在状況を明示する（JS が言語に合わせて置き換える）
    n_live = sum(1 for s in summary if s.get("mode") == "LIVE")
    n_mock = sum(1 for s in summary if s.get("mode") == "MOCK")
    if n_live and n_mock:
        mode_label = f"混在 — LIVE {n_live} / MOCK {n_mock}"
    elif n_live:
        mode_label = f"全 LIVE（{n_live} 構成・実API計測）"
    else:
        mode_label = f"全 MOCK（{n_mock} 構成・シミュレーション）"

    # SEO: クロール可能なモデル一覧。ランキング表は JS 注入のため、評価対象のモデル名を静的にも列挙して
    # 「GPT-4.1 安全性」「Claude 脱獄」等の検索到達性を確保する。model 例: "openai/gpt-oss-20b"。
    seen_models = []
    for row in summary:
        m = (row.get("model") or "").split("/")[-1].strip()
        if m and m not in seen_models:
            seen_models.append(m)
    n_tf = len(data.get("transformations", []))
    seo_models = html.escape(
        f"評価対象モデル / Evaluated models: {', '.join(seen_models)}. "
        f"{len(summary)} 構成 × {n_tf} 種の日本語変形攻撃"
        f"（脱獄・ジェイルブレイク・プロンプトインジェクション）で計測。"
    )

    # 構造化データ（schema.org Dataset）。検索エンジンが研究成果物として解釈しやすくする。
    jsonld = _script_json(
        {
            "@context": "https://schema.org",
            "@type": "Dataset",
            "name": "J-ART: Japanese Adversarial Red-Team leaderboard",
            "description": SITE_DESC,
            "url": SITE_URL,
            "license": "https://opensource.org/licenses/MIT",
            "creator": {"@type": "Organization", "name": "Quiet Forensics", "url": QF_URL},
            "isBasedOn": REPO_URL,
            "identifier": DOI_URL,
            "keywords": [
                "LLM", "AI safety", "red teaming", "Japanese", "日本語",
                "jailbreak", "脱獄", "prompt injection", "プロンプトインジェクション",
                "leaderboard", "adversarial", "benchmark",
                "GPT", "Claude", "Gemini", "Llama", "Qwen",
            ],
        }
    )

    # ヘッダーのアイコンはサイズを CSS で決めるため、固定 width/height を外してインライン埋め込み。
    header_icon = load_icon().replace('width="64" height="64"', 'aria-hidden="true"', 1)

    values = {
        "site_title": html.escape(SITE_TITLE),
        "site_desc": html.escape(SITE_DESC),
        "site_url": html.escape(SITE_URL),
        "qf_url": html.escape(QF_URL),
        "qf_logo": QF_LOGO,
        "paper_url": html.escape(PAPER_URL),
        "repo_url": html.escape(REPO_URL),
        "doi": html.escape(DOI),
        "doi_url": html.escape(DOI_URL),
        "header_icon": header_icon,
        "tf_card": _tf_card(data),
        "generated_at": html.escape(_fmt_generated_at(data.get("generated_at", ""))),
        "mode": html.escape(mode_label),
        "n_targets": str(len(summary)),
        "n_details": f"{len(data.get('details', [])):,}",
        "n_transforms": str(n_tf),
        "seo_models": seo_models,
        "jsonld": jsonld,
        "analytics": analytics,
        "data_json": _script_json(data) + ";",
        "i18n_json": _script_json(build_i18n()),
    }
    # 1 回の走査で差し込む（差し込んだ値の中の %%...%% は再置換しない）。
    ja = build_i18n()["ja"]

    def fill(m):
        # %%ja.key%% は JS 無効時・クローラ向けの日本語初期値（i18n は HTML 片なのでエスケープしない）。
        return ja[m.group(2)] if m.group(1) else values[m.group(2)]

    return re.sub(r"%%(ja\.)?(\w+)%%", fill, PAGE_TEMPLATE)


def _analytics_tag():
    """アクセス解析（GoatCounter）。サイトコードは環境変数 JART_GOATCOUNTER_CODE で注入する。

    - 未設定なら HTML コメントのみ（＝タグを出力せず、ローカルビルドやフォークを壊さない）。
    - 値は素のコード（例: "j-art"）でも、完全な count エンドポイント URL でも可。
    - Cookie レス・IP非保存の軽量解析。GitHub Pages は生ログを出さないため、これで訪問数を可視化する。
    """
    gc_code = os.environ.get("JART_GOATCOUNTER_CODE", "").strip()
    if not gc_code:
        return "<!-- analytics disabled: set JART_GOATCOUNTER_CODE to enable GoatCounter -->"
    gc_endpoint = gc_code if "://" in gc_code else f"https://{gc_code}.goatcounter.com/count"
    return (
        f'<script data-goatcounter="{html.escape(gc_endpoint)}"\n'
        f'        async src="//gc.zgo.at/count.js"></script>'
    )


def build_site(data, outdir):
    """outdir へ公開ファイル一式（index.html / results.json / icon.svg / sitemap.xml / robots.txt）を書く。"""
    os.makedirs(outdir, exist_ok=True)

    with open(os.path.join(outdir, "icon.svg"), "w", encoding="utf-8") as f:
        f.write(load_icon())

    index_path = os.path.join(outdir, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(render_page(data, analytics=_analytics_tag()))

    # 生データもダウンロード可能なように配置
    with open(os.path.join(outdir, "results.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # sitemap.xml … クローラに公開 URL を提示。lastmod は生成日を YYYY-MM-DD で流用。
    lastmod = data.get("generated_at", "")[:10]
    lastmod_tag = f"\n    <lastmod>{html.escape(lastmod)}</lastmod>" if len(lastmod) == 10 and lastmod[4] == "-" else ""
    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"  <url>\n    <loc>{html.escape(SITE_URL)}</loc>{lastmod_tag}\n"
        "    <changefreq>weekly</changefreq>\n    <priority>1.0</priority>\n  </url>\n"
        "</urlset>\n"
    )
    with open(os.path.join(outdir, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(sitemap)

    # robots.txt … 全クロール許可 + sitemap の所在を明示。
    robots = f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}sitemap.xml\n"
    with open(os.path.join(outdir, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(robots)

    return index_path


def main():
    ap = argparse.ArgumentParser(description="J-ART (Japanese Adversarial Red-Team framework) - site generator")
    ap.add_argument("--results", default="results.json")
    ap.add_argument("--outdir", default="site")
    args = ap.parse_args()

    with open(args.results, "r", encoding="utf-8") as f:
        data = json.load(f)

    index_path = build_site(data, args.outdir)
    print(f"[+] 生成完了: {index_path}")


if __name__ == "__main__":
    main()
