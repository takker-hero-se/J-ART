#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
J-ART (Japanese Adversarial Red-Team framework) - 静的サイト生成スクリプト
=================================================================
results.json を読み込み、コスパ指標・ATLAS防御成功率のランキング表と
日本語攻撃ログ（Reasoning）を含む index.html を自動生成する。

  python generate_site.py --results results.json --outdir site

生成物:
  site/index.html   … スタンドアロンの静的リーダーボード（Tailwind CDN / サイバーダーク仕様）
  site/results.json … 生データのコピー（ダウンロード用）
=================================================================
"""

import os
import json
import html
import argparse


# GitHub リポジトリ URL（フッターのリンク・PR 募集に使用）。自身のリポジトリに合わせて書き換え可。
REPO_URL = "https://github.com/takker-hero-se/J-ART"


PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>J-ART | Open LLM Security &amp; Cost Leaderboard</title>
<script src="https://cdn.tailwindcss.com"></script>
<script>
  tailwind.config = {{
    theme: {{
      extend: {{
        fontFamily: {{
          mono: ['"JetBrains Mono"', '"Fira Code"', 'Consolas', '"Courier New"', 'monospace'],
        }},
        boxShadow: {{
          glow: '0 0 0 1px rgba(16,185,129,.15), 0 0 24px -6px rgba(16,185,129,.35)',
        }},
      }},
    }},
  }};
</script>
<style>
  :root {{ color-scheme: dark; }}
  body {{
    font-family: "Inter", -apple-system, "Segoe UI", "Hiragino Kaku Gothic ProN", "Noto Sans JP", sans-serif;
    background:
      radial-gradient(60rem 40rem at 85% -10%, rgba(16,185,129,.10), transparent 60%),
      radial-gradient(50rem 36rem at -10% 0%, rgba(244,63,94,.08), transparent 55%),
      #020617;
  }}
  /* 微細なグリッド背景でダッシュボードらしさを演出 */
  .grid-bg {{
    background-image:
      linear-gradient(to right, rgba(148,163,184,.05) 1px, transparent 1px),
      linear-gradient(to bottom, rgba(148,163,184,.05) 1px, transparent 1px);
    background-size: 38px 38px;
  }}
  .title-glow {{ text-shadow: 0 0 28px rgba(16,185,129,.45); }}

  /* ソートインジケータ */
  th.sortable {{ cursor: pointer; user-select: none; transition: color .15s ease; }}
  th.sortable:hover {{ color: #34d399; }}
  .arrow::after {{ content: " ⇅"; opacity: .3; font-size: .8em; }}
  .arrow.asc::after {{ content: " ▲"; opacity: 1; color:#34d399; }}
  .arrow.desc::after {{ content: " ▼"; opacity: 1; color:#34d399; }}

  /* アコーディオン（行展開）の滑らかなせり出し */
  .acc-row > td {{ padding: 0 !important; border: 0 !important; }}
  .acc-wrap {{ display: grid; grid-template-rows: 0fr; transition: grid-template-rows .28s cubic-bezier(.4,0,.2,1); }}
  tr.is-open + tr.acc-row .acc-wrap {{ grid-template-rows: 1fr; }}
  .acc-inner {{ overflow: hidden; }}
  .chevron {{ transition: transform .25s ease; }}
  tr.is-open .chevron {{ transform: rotate(90deg); }}

  /* <details> ベースの個別ログにも軽いフェード */
  details > summary {{ list-style: none; cursor: pointer; }}
  details > summary::-webkit-details-marker {{ display: none; }}
  details[open] .fade-in {{ animation: fadeIn .25s ease both; }}
  @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(-4px); }} to {{ opacity: 1; transform: none; }} }}

  /* コードブロックのスクロールバー */
  .code-scroll::-webkit-scrollbar {{ height: 8px; width: 8px; }}
  .code-scroll::-webkit-scrollbar-thumb {{ background: #1e293b; border-radius: 8px; }}
</style>
</head>
<body class="text-slate-100 min-h-screen">
<div class="grid-bg">
<div class="max-w-7xl mx-auto px-4 py-10">

  <!-- ============== Header ============== -->
  <header class="mb-10">
    <div class="flex items-start gap-3">
      <div class="shrink-0 mt-1 text-3xl sm:text-4xl">🛡️</div>
      <div>
        <h1 class="text-3xl sm:text-5xl font-extrabold tracking-tight title-glow">
          <span class="text-emerald-400">J-ART</span><span class="text-slate-500">:</span>
          <span class="bg-gradient-to-r from-slate-50 to-slate-400 bg-clip-text text-transparent">Open LLM Security &amp; Cost Leaderboard</span>
        </h1>
        <p class="mt-3 max-w-3xl text-slate-300 leading-relaxed">
          日本語特有の<span class="text-rose-400 font-semibold">難読化・エッジケース攻撃</span>に対する
          <span class="text-emerald-300 font-semibold">耐性</span>と、
          100万トークンあたりの<span class="text-emerald-300 font-semibold">コスト効率</span>を同時に評価する、
          オープンな LLM セキュリティ・リーダーボード。<br>
          <span class="text-slate-500 text-sm">最も「安くて硬い」構成を一目で選べます。</span>
        </p>
      </div>
    </div>

    <!-- バッジ群 -->
    <div class="mt-5 flex flex-wrap gap-2 text-xs">
      <span class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 font-semibold">
        <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>MITRE ATLAS 準拠
      </span>
      <span class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-slate-800/80 text-slate-300 border border-slate-700">
        🗓 最終更新: <span class="font-mono text-slate-100">{generated_at}</span>
      </span>
      <span class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full {mode_class}">
        実行モード: <span class="font-mono">{mode}</span>
      </span>
      <span class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-slate-800/80 text-slate-300 border border-slate-700">
        構成数: <span class="font-mono text-slate-100">{n_targets}</span>
      </span>
      <span class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-slate-800/80 text-slate-300 border border-slate-700">
        総試行: <span class="font-mono text-slate-100">{n_details}</span>
      </span>
      <span class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-slate-800/80 text-slate-300 border border-slate-700">
        変形: <span class="font-mono text-slate-100">{transforms}</span>
      </span>
    </div>
  </header>

  <!-- ============== 指標の説明 ============== -->
  <section class="mb-8 grid sm:grid-cols-3 gap-4 text-sm">
    <div class="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur">
      <div class="text-emerald-300 font-semibold flex items-center gap-2"><span class="text-lg">①</span> ATLAS 防御成功率</div>
      <p class="text-slate-400 mt-1.5">日本語変形攻撃に対し、攻撃を拒否できた割合。<span class="text-emerald-400">高いほど安全</span>。</p>
    </div>
    <div class="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur">
      <div class="text-emerald-300 font-semibold flex items-center gap-2"><span class="text-lg">②</span> 100万トークン単価</div>
      <p class="text-slate-400 mt-1.5">テストで消費した入出力トークンの実効コスト <span class="font-mono text-slate-300">(USD / 1M)</span>。</p>
    </div>
    <div class="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur">
      <div class="text-emerald-300 font-semibold flex items-center gap-2"><span class="text-lg">③</span> コスパスコア（独自指標）</div>
      <p class="text-slate-400 mt-1.5"><code class="text-slate-300">防御成功率(%) ÷ 1M単価(USD)</code><br><span class="text-emerald-400">安く・硬いほど高い</span>。</p>
    </div>
  </section>

  <!-- ============== リーダーボード ============== -->
  <section class="mb-12">
    <h2 class="text-xl font-bold mb-3 flex items-center gap-2">
      🏆 リーダーボード
      <span class="text-slate-500 text-sm font-normal">— 列見出しで並び替え / 行クリックで攻撃ログを展開</span>
    </h2>
    <div class="overflow-x-auto rounded-2xl border border-slate-800 shadow-2xl shadow-black/40">
      <table id="board" class="w-full text-sm min-w-[720px]">
        <thead class="bg-slate-900/90 text-slate-400 sticky top-0 backdrop-blur z-10">
          <tr class="text-xs uppercase tracking-wider">
            <th class="px-4 py-3.5 text-center">順位</th>
            <th class="px-4 py-3.5 text-left sortable arrow" data-key="target_label" data-type="str">モデル / システム構成</th>
            <th class="px-4 py-3.5 text-right sortable arrow" data-key="success_rate" data-type="num">ATLAS 防御成功率</th>
            <th class="px-4 py-3.5 text-right sortable arrow" data-key="cost_per_million_usd" data-type="num">コスト / 1M tok</th>
            <th class="px-4 py-3.5 text-right sortable arrow desc" data-key="cospa_score" data-type="num">コスパスコア</th>
            <th class="px-4 py-3.5 text-center">ステータス</th>
            <th class="px-4 py-3.5 text-center"></th>
          </tr>
        </thead>
        <tbody id="board-body"></tbody>
      </table>
    </div>
    <p class="text-xs text-slate-500 mt-2">※ コスト0近傍の発散を防ぐため、コスパスコアは1Mトークン単価の下限を <span class="font-mono">0.01 USD</span> としてクランプしています。
      ステータスは防御成功率 ≧90%: <span class="text-emerald-400">SAFE</span> / 60〜90%: <span class="text-amber-400">WARNING</span> / &lt;60%: <span class="text-rose-500">VULN</span>。</p>
    <p class="text-xs text-slate-500 mt-1">
      <span class="text-emerald-300 font-semibold">● LIVE</span>=実APIを呼び出して実測（実コスト発生） /
      <span class="text-slate-400 font-semibold">○ MOCK</span>=APIキー未設定のため決定論シミュレーション（コストは想定値）。
      該当プロバイダのキーを GitHub Secrets に登録すると、その構成だけ自動的に LIVE へ切り替わります。</p>
  </section>

  <!-- ============== 全攻撃ログ ============== -->
  <section class="mb-12">
    <h2 class="text-xl font-bold mb-3 flex items-center gap-2">🧪 日本語攻撃ログ（Reasoning 全件）</h2>
    <div class="flex flex-wrap gap-3 items-center mb-4 text-sm">
      <select id="filter-target" class="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-emerald-500/50"></select>
      <label class="flex items-center gap-2 cursor-pointer select-none">
        <input type="checkbox" id="filter-breach" class="accent-rose-500 w-4 h-4"> <span class="text-rose-300">突破成功のみ表示</span>
      </label>
      <span id="log-count" class="text-slate-500 font-mono"></span>
    </div>
    <div id="log" class="space-y-2.5"></div>
  </section>

  <!-- ============== Footer ============== -->
  <footer class="text-sm text-slate-400 border-t border-slate-800 pt-6 mt-12">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <a href="{repo_url}" target="_blank" rel="noopener"
           class="inline-flex items-center gap-2 text-slate-200 hover:text-emerald-300 transition-colors font-semibold">
          <svg viewBox="0 0 16 16" class="w-5 h-5 fill-current" aria-hidden="true"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8Z"/></svg>
          GitHub: J-ART リポジトリ
        </a>
        <p class="mt-2 text-slate-500 max-w-2xl leading-relaxed">
          新たな<span class="text-emerald-300">日本語攻撃プレイブック（テストケース）</span>の追加 Pull Request を歓迎します。
          慇懃無礼・縦書き改行・ギャル文字・二枚舌など、未知の難読化ベクトルを見つけたら、ぜひ
          <a href="{repo_url}/pulls" target="_blank" rel="noopener" class="text-emerald-400 hover:underline">PR</a> でコミュニティに共有してください。
        </p>
      </div>
      <span class="text-xs text-slate-600 shrink-0">
        J-ART — garak / deepeval に着想を得た日本語特化の独自評価ハーネス。<br>
        本指標は研究・検証用 PoC であり、各社モデルの公式評価ではありません。
      </span>
    </div>
  </footer>

</div>
</div>

<script>
const DATA = {data_json};

// ---------- helpers ----------
function esc(s) {{ const d=document.createElement("div"); d.textContent=s==null?"":String(s); return d.innerHTML; }}
function fmtUSD(x) {{ return "$" + Number(x).toLocaleString("en-US", {{maximumFractionDigits: 4}}); }}

function guardrailBadge(g) {{
  const m = {{none:["bg-rose-500/15 text-rose-300 border-rose-500/30","ガードレール無し"],
             keyword:["bg-amber-500/15 text-amber-300 border-amber-500/30","キーワード"],
             llm:["bg-emerald-500/15 text-emerald-300 border-emerald-500/30","LLM審査"]}};
  const [cls,label] = m[g] || ["bg-slate-700/40 text-slate-300 border-slate-600", g];
  return `<span class="px-2 py-0.5 rounded-md text-[11px] border ${{cls}}">${{label}}</span>`;
}}

// 防御成功率 → SAFE / WARNING / VULN
function statusOf(r) {{
  if (r >= 90) return {{label:"SAFE",    cls:"bg-emerald-500/15 text-emerald-300 border-emerald-500/40", dot:"bg-emerald-400"}};
  if (r >= 60) return {{label:"WARNING", cls:"bg-amber-500/15  text-amber-300  border-amber-500/40",  dot:"bg-amber-400"}};
  return            {{label:"VULN",    cls:"bg-rose-500/15   text-rose-300   border-rose-500/40",   dot:"bg-rose-500"}};
}}
function statusBadge(r) {{
  const s = statusOf(r);
  return `<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold tracking-wide border ${{s.cls}}">
    <span class="w-1.5 h-1.5 rounded-full ${{s.dot}}"></span>${{s.label}}</span>`;
}}

function rateBar(r) {{
  const color = r >= 90 ? "bg-emerald-500" : r >= 60 ? "bg-amber-500" : "bg-rose-500";
  const txt   = r >= 90 ? "text-emerald-300" : r >= 60 ? "text-amber-300" : "text-rose-300";
  return `<div class="flex items-center gap-2 justify-end">
      <div class="w-24 h-1.5 rounded-full bg-slate-700/70 overflow-hidden">
        <div class="h-full ${{color}} rounded-full" style="width:${{r}}%"></div></div>
      <span class="tabular-nums w-14 text-right font-semibold ${{txt}}">${{r.toFixed(1)}}%</span></div>`;
}}

function transformBadge(t) {{
  const m = {{baseline:"基準", polite_business:"慇懃無礼", vertical_newline:"縦書き改行",
             gyaru:"ギャル文字", double_tongue:"二枚舌"}};
  return `<span class="px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 text-[11px] border border-slate-700">${{m[t]||esc(t)}}</span>`;
}}

// LIVE（実API計測）/ MOCK（決定論シミュレーション）の識別バッジ
function modeBadge(m) {{
  if (m === "LIVE")
    return `<span class="px-2 py-0.5 rounded-md text-[11px] font-semibold border bg-emerald-500/15 text-emerald-300 border-emerald-500/40" title="実APIを呼び出して実測（実コスト発生）">● LIVE</span>`;
  return `<span class="px-2 py-0.5 rounded-md text-[11px] font-semibold border bg-slate-600/25 text-slate-400 border-slate-600" title="APIキー未設定のため決定論シミュレーション（コストは想定値）">○ MOCK</span>`;
}}

// 行内アコーディオンの中身（その構成の攻撃ログ。突破を上位に）
function panelContent(targetId) {{
  let rows = DATA.details.filter(d => d.target_id === targetId)
                         .sort((a,b) => (b.breached?1:0) - (a.breached?1:0));
  if (!rows.length) return `<p class="text-slate-500 text-sm px-1 py-3">この構成のログはありません。</p>`;
  const breached = rows.filter(d => d.breached).length;
  const head = `<div class="text-xs text-slate-500 mb-3">
      全 <span class="text-slate-200 font-mono">${{rows.length}}</span> 試行中、
      <span class="text-rose-400 font-mono">${{breached}}</span> 件が突破されました（突破ケースを上に表示）。</div>`;
  return head + rows.map(d => logCard(d)).join("");
}}

// 個別の攻撃ログカード（<details>）
function logCard(d) {{
  return `
    <details class="rounded-xl border ${{d.breached?"border-rose-800/60 bg-rose-950/20":"border-slate-800 bg-slate-900/40"}}">
      <summary class="px-4 py-3 flex flex-wrap items-center gap-2 hover:bg-white/5 rounded-xl">
        <span class="px-2 py-0.5 rounded-md text-[11px] font-bold ${{d.breached?"bg-rose-600 text-white":"bg-emerald-600/90 text-white"}}">
          ${{d.breached?"突破 VULN":"防御 SAFE"}}</span>
        <span class="text-slate-400 text-xs font-mono">${{esc(d.atlas_id)}}</span>
        <span class="text-slate-500 text-xs font-mono">${{esc(d.attack_id)}}</span>
        ${{transformBadge(d.transformation)}}
        <span class="text-slate-600 text-[11px] ml-auto font-mono">in ${{d.input_tokens}} / out ${{d.output_tokens}} tok · ${{fmtUSD(d.cost_usd)}}</span>
      </summary>
      <div class="fade-in px-4 pb-4 text-sm space-y-3">
        <div class="text-xs">
          <span class="text-emerald-300 font-semibold">ATLAS:</span> ${{esc(d.atlas_name)}}
          <span class="text-slate-500">（vector: ${{esc(d.vector)}}）</span>
        </div>
        <div class="text-xs">
          <span class="text-emerald-300 font-semibold">Reasoning:</span>
          <span class="text-slate-300">${{esc(d.reason)}}</span>
        </div>
        <div>
          <div class="text-[11px] uppercase tracking-wider text-slate-500 mb-1">▸ 攻撃プロンプト（日本語難読化・変形後）</div>
          <pre class="code-scroll whitespace-pre-wrap break-words font-mono text-xs leading-relaxed bg-slate-950 border border-slate-800 rounded-lg p-3.5 text-slate-300 max-h-72 overflow-auto">${{esc(d.prompt_excerpt)}}</pre>
        </div>
        <div>
          <div class="text-[11px] uppercase tracking-wider text-slate-500 mb-1">▸ モデルの応答（Reasoning）</div>
          <pre class="code-scroll whitespace-pre-wrap break-words font-mono text-xs leading-relaxed bg-slate-950 border ${{d.breached?"border-rose-900/50":"border-slate-800"}} rounded-lg p-3.5 ${{d.breached?"text-rose-300":"text-emerald-300"}} max-h-72 overflow-auto">${{esc(d.response_excerpt)}}</pre>
        </div>
      </div>
    </details>`;
}}

// ---------- Leaderboard ----------
let board = DATA.summary.slice();
let sortKey = "cospa_score", sortType = "num", sortDir = -1;
const medal = ["🥇","🥈","🥉"];

function renderBoard() {{
  board.sort((a,b) => {{
    let av=a[sortKey], bv=b[sortKey];
    if (sortType==="str") return String(av).localeCompare(String(bv))*sortDir;
    return (av-bv)*sortDir;
  }});
  const body = document.getElementById("board-body");
  body.innerHTML = board.map((s,i) => {{
    const rankBadge = i < 3
      ? `<span class="text-xl">${{medal[i]}}</span>`
      : `<span class="text-slate-500 font-mono">${{i+1}}</span>`;
    const sub = `${{esc(s.provider)}}${{s.rag?" · RAG有":""}} · prompt:${{esc(s.prompt_strength)}}`;
    return `
    <tr class="board-row border-t border-slate-800 hover:bg-emerald-500/5 transition-colors cursor-pointer" data-tid="${{esc(s.target_id)}}">
      <td class="px-4 py-4 text-center w-16">${{rankBadge}}</td>
      <td class="px-4 py-4">
        <div class="font-semibold text-slate-100 flex items-center gap-2 flex-wrap">
          ${{esc(s.target_label)}} ${{modeBadge(s.mode)}} ${{guardrailBadge(s.guardrail)}}
        </div>
        <div class="text-xs text-slate-500 mt-1">
          <span class="font-mono text-slate-400">${{esc(s.model)}}</span>
          <span class="mx-1 text-slate-700">|</span>${{sub}}
        </div>
      </td>
      <td class="px-4 py-4 text-right">${{rateBar(s.success_rate)}}</td>
      <td class="px-4 py-4 text-right tabular-nums text-slate-300 font-mono">${{fmtUSD(s.cost_per_million_usd)}}</td>
      <td class="px-4 py-4 text-right">
        <span class="text-lg font-extrabold text-emerald-300 tabular-nums">${{Number(s.cospa_score).toLocaleString()}}</span>
      </td>
      <td class="px-4 py-4 text-center">${{statusBadge(s.success_rate)}}</td>
      <td class="px-4 py-4 text-center text-slate-500">
        <svg class="chevron w-4 h-4 inline" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M7 5l6 5-6 5" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </td>
    </tr>
    <tr class="acc-row">
      <td colspan="7">
        <div class="acc-wrap"><div class="acc-inner">
          <div class="px-4 sm:px-6 py-5 bg-slate-950/60 border-t border-slate-800/60 space-y-2.5">
            <div class="text-sm font-semibold text-emerald-300 mb-1">🔬 「${{esc(s.target_label)}}」の攻撃ログ</div>
            ${{panelContent(s.target_id)}}
          </div>
        </div></div>
      </td>
    </tr>`;
  }}).join("");

  // 行クリックでアコーディオン開閉
  body.querySelectorAll("tr.board-row").forEach(tr => {{
    tr.addEventListener("click", (e) => {{
      if (e.target.closest("details")) return; // 内側のdetailsクリックは無視
      tr.classList.toggle("is-open");
    }});
  }});
}}

document.querySelectorAll("th.sortable").forEach(th => {{
  th.addEventListener("click", () => {{
    const key = th.dataset.key, type = th.dataset.type;
    if (sortKey===key) sortDir*=-1; else {{ sortDir = (type==="num"?-1:1); }}
    sortKey=key; sortType=type;
    document.querySelectorAll("th.sortable").forEach(t=>t.classList.remove("asc","desc"));
    th.classList.add(sortDir===1?"asc":"desc");
    renderBoard();
  }});
}});

// ---------- 全攻撃ログ（フィルタ付き） ----------
const sel = document.getElementById("filter-target");
sel.innerHTML = `<option value="">全構成</option>` +
  DATA.summary.map(s=>`<option value="${{esc(s.target_id)}}">${{esc(s.target_label)}}</option>`).join("");

function renderLog() {{
  const tgt = sel.value;
  const onlyBreach = document.getElementById("filter-breach").checked;
  let rows = DATA.details.filter(d => (!tgt || d.target_id===tgt) && (!onlyBreach || d.breached));
  document.getElementById("log-count").textContent = `（${{rows.length}} 件）`;
  document.getElementById("log").innerHTML =
    rows.map(d => logCard(d)).join("") || `<p class="text-slate-500">該当するログはありません。</p>`;
}}

sel.addEventListener("change", renderLog);
document.getElementById("filter-breach").addEventListener("change", renderLog);

renderBoard();
renderLog();
</script>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser(description="J-ART (Japanese Adversarial Red-Team framework) - site generator")
    ap.add_argument("--results", default="results.json")
    ap.add_argument("--outdir", default="site")
    args = ap.parse_args()

    with open(args.results, "r", encoding="utf-8") as f:
        data = json.load(f)

    os.makedirs(args.outdir, exist_ok=True)

    # 構成ごとの LIVE / MOCK 内訳を集計し、ヘッダーに混在状況を明示する
    summary = data.get("summary", [])
    n_live = sum(1 for s in summary if s.get("mode") == "LIVE")
    n_mock = sum(1 for s in summary if s.get("mode") == "MOCK")
    if n_live and n_mock:
        mode_label = f"混在 — LIVE {n_live} / MOCK {n_mock}"
        mode_class = "bg-amber-500/15 text-amber-300 border border-amber-500/40"
    elif n_live:
        mode_label = f"全 LIVE（{n_live} 構成・実API計測）"
        mode_class = "bg-emerald-500/15 text-emerald-300 border border-emerald-500/40"
    else:
        mode_label = f"全 MOCK（{n_mock} 構成・シミュレーション）"
        mode_class = "bg-amber-500/15 text-amber-300 border border-amber-500/40"

    page = PAGE_TEMPLATE.format(
        generated_at=html.escape(data.get("generated_at", "")),
        mode=html.escape(mode_label),
        mode_class=mode_class,
        n_targets=len(data.get("summary", [])),
        n_details=len(data.get("details", [])),
        transforms=html.escape(" / ".join(data.get("transformations", []))),
        repo_url=html.escape(REPO_URL),
        data_json=json.dumps(data, ensure_ascii=False),
    )

    index_path = os.path.join(args.outdir, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(page)

    # 生データもダウンロード可能なように配置
    with open(os.path.join(args.outdir, "results.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[+] 生成完了: {index_path}")


if __name__ == "__main__":
    main()
