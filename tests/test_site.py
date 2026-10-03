# -*- coding: utf-8 -*-
"""generate_site のユニットテスト（Quiet Forensics 統合後のサイト外装）。

J-ART のリーダーボードは Quiet Forensics の公開研究として jart.quietforensics.com で公開する。
本テストは、ポータルと同じ外装（紺の帯＋シアン、明るい本文、BIZ UDPGothic、JA/EN 切替）と、
公開 URL・埋め込みデータの安全性を検証する。API もネットワークも使わない。

pytest があれば `pytest tests/` で、無ければ `python tests/test_site.py` で直接実行できる。
"""
import html
import json
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import generate_site  # noqa: E402
from generate_site import build_i18n, build_site, key_findings, render_page, transform_examples  # noqa: E402


def _row(tid="t1", label="テスト構成", rate=95.0, mode="LIVE", measured=True,
         model="openai/gpt-test", prompt="high", guardrail="keyword", cost=0.5):
    return {
        "target_id": tid, "target_label": label, "target_label_en": "Test config",
        "provider": "openai", "model": model, "prompt_strength": prompt,
        "guardrail": guardrail, "rag": True, "mode": mode, "n_api_error": 0,
        "total_attacks": 10 if measured else 0, "defended": 9, "breached": 1,
        "success_rate": rate, "ci_low": 80.0, "ci_high": 99.0,
        "cost_per_million_usd": cost, "cospa_score": 190.0,
    }


def _data(**kw):
    d = {
        "generated_at": "2026-09-28T00:00:00+00:00",
        "transformations": ["baseline", "gyaru"],
        "summary": [_row()],
        "details": [{
            "target_id": "t1", "breached": False, "atlas_id": "AML.T0051.000",
            "attack_id": "a1", "transformation": "gyaru", "trials": 1, "breaches": 0,
            "input_tokens": 10, "output_tokens": 5, "cost_usd": 0.0001,
            "atlas_name": "Prompt Injection", "vector": "direct", "reason": "拒否した",
            "prompt_excerpt": "前置き <<CORE>>", "response_excerpt": "お答えできません",
        }],
    }
    d.update(kw)
    return d


# ---------- 外装（Quiet Forensics と同じ見た目） ----------

def test_page_uses_quiet_forensics_palette_and_type():
    page = render_page(_data())
    assert "#082A41" in page and "#2BC1FF" in page          # 紺の帯とシアン
    assert "BIZ+UDPGothic" in page                          # ポータルと同じ和文書体
    assert "color-scheme:light" in page.replace(" ", "")


def test_page_drops_the_old_dark_neon_look():
    page = render_page(_data())
    assert "cdn.tailwindcss.com" not in page                # 実行時 CSS 生成をやめ、自前 CSS に
    assert "title-glow" not in page and "#020617" not in page
    assert "emerald" not in page and "rose-" not in page


def test_i18n_strings_carry_no_tailwind_classes():
    for lang, table in build_i18n().items():
        for key, value in table.items():
            assert not re.search(r"text-(slate|emerald|rose|amber|sky)-", value), (lang, key)


def test_i18n_tables_have_the_same_keys():
    t = build_i18n()
    assert set(t["ja"]) == set(t["en"])


# ---------- Quiet Forensics との往来 ----------

def test_header_links_back_to_the_portal_and_has_ja_en_switch():
    page = render_page(_data())
    assert 'href="https://quietforensics.com/"' in page
    assert 'data-lang-btn="ja"' in page and 'data-lang-btn="en"' in page
    assert "URLSearchParams" in page                        # ?lang= で言語を指定できる


def test_footer_keeps_repo_sponsor_citation_and_disclaimer():
    page = render_page(_data())
    assert generate_site.REPO_URL in page
    assert generate_site.SPONSOR_URL in page
    assert "10.5281/zenodo.20676879" in page
    assert "公式評価ではありません" in page


# ---------- 公開 URL ----------

def test_canonical_url_is_the_quiet_forensics_subdomain():
    assert generate_site.SITE_URL == "https://jart.quietforensics.com/"
    page = render_page(_data())
    assert '<link rel="canonical" href="https://jart.quietforensics.com/">' in page
    assert 'og:url" content="https://jart.quietforensics.com/"' in page


def test_build_site_writes_every_published_file():
    with tempfile.TemporaryDirectory() as out:
        build_site(_data(), out)
        names = set(os.listdir(out))
        assert {"index.html", "results.json", "icon.svg", "sitemap.xml", "robots.txt"} <= names
        with open(os.path.join(out, "sitemap.xml"), encoding="utf-8") as f:
            sm = f.read()
        assert "<loc>https://jart.quietforensics.com/</loc>" in sm
        assert "<lastmod>2026-09-28</lastmod>" in sm
        with open(os.path.join(out, "robots.txt"), encoding="utf-8") as f:
            assert "Sitemap: https://jart.quietforensics.com/sitemap.xml" in f.read()
        with open(os.path.join(out, "results.json"), encoding="utf-8") as f:
            assert json.load(f)["summary"][0]["target_id"] == "t1"


def test_icon_matches_the_navy_brand():
    icon = generate_site.load_icon()
    assert "#082A41" in icon and "#2BC1FF" in icon


# ---------- 埋め込みデータの安全性 ----------

def test_model_output_cannot_close_the_data_script():
    # 攻撃ログ本文はモデル出力（外部入力）。</script> を含んでもスクリプトを終了させない。
    d = _data()
    d["details"][0]["response_excerpt"] = "</script><img src=x onerror=alert(1)>"
    page = render_page(d)
    body = page.split("const DATA = ", 1)[1].split("\n", 1)[0]
    assert "</script>" not in body
    assert "<\\/script>" in body


def test_header_counts_come_from_the_results():
    d = _data(summary=[_row("a"), _row("b", mode="MOCK")])
    page = render_page(d)
    assert "LIVE 1 / MOCK 1" in page
    assert "2026-09-28" in page


# ---------- 分かりやすさ: 要点・変形の実例・表の既定表示 ----------

def _findings_data():
    return _data(summary=[
        _row("a-naked", model="m/a", prompt="low", guardrail="none", rate=60.0),
        _row("a-llm", model="m/a", prompt="high", guardrail="llm", rate=100.0, cost=2.0),
        _row("a-kw", model="m/a", prompt="high", guardrail="keyword", rate=100.0, cost=0.0),
        _row("b-naked", model="m/b", prompt="low", guardrail="none", rate=90.0),
        _row("c-kw", model="m/c", prompt="high", guardrail="keyword", rate=95.0),
        _row("dead", model="m/d", prompt="low", guardrail="none", rate=0.0, measured=False),
    ])


def test_key_findings_summarise_naked_versus_protected():
    f = key_findings(_findings_data())
    assert f["naked_n"] == 2 and f["naked_mean"] == 75.0             # 未計測の構成は含めない
    assert f["naked_min"] == 60.0 and f["naked_max"] == 90.0
    assert f["protected_n"] == 3 and f["protected_perfect"] == 2
    # モデルごとの比較は、素のAPIと防御ありの両方があるモデルだけ。防御ありは防御率→安さで最良を選ぶ
    pairs = {p["model"]: p for p in f["pairs"]}
    assert set(pairs) == {"m/a"}
    assert pairs["m/a"]["naked"] == 60.0 and pairs["m/a"]["protected"] == 100.0
    assert pairs["m/a"]["protected_guardrail"] == "keyword"


def test_key_findings_survive_results_without_naked_rows():
    f = key_findings(_data())
    assert f["naked_n"] == 0 and f["pairs"] == []
    assert "id=\"findings\"" in render_page(_data())


def test_page_opens_with_findings_before_the_table():
    page = render_page(_findings_data())
    assert page.index('id="findings"') < page.index('id="board"')
    assert "75.0%" in page                                            # 素のAPIの平均防御率


def test_transform_examples_show_each_wrapper_with_the_core_masked():
    d = _data()
    d["details"] = [
        dict(d["details"][0], attack_id="x", transformation=t, prompt_excerpt=f"{t} 前置き <<CORE>>")
        for t in ("baseline", "gyaru", "base64_wrap")
    ]
    ex = transform_examples(d)
    assert [e[0] for e in ex] == ["baseline", "gyaru", "base64_wrap"]
    page = render_page(d)
    assert 'id="examples"' in page
    assert "gyaru 前置き" in page and "&lt;&lt;CORE&gt;&gt;" not in page and "<<CORE>>" not in page.split("<script>")[1].split("</script>")[0]


def test_board_defaults_to_defense_rate_and_hides_unmeasured_rows():
    page = render_page(_findings_data())
    assert 'let sortKey = "success_rate"' in page
    assert 'id="show-unmeasured"' in page and 'data-view="naked"' in page and 'data-view="protected"' in page
    # 費用 $0 の行が「無料で最強」に見えないよう、理由を表示する
    ja = build_i18n()["ja"]
    assert "blocked_at_input" in ja and "モデルは呼ばれていません" in ja["blocked_at_input_tip"]


if __name__ == "__main__":
    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except AssertionError as e:
                failed += 1
                print(f"FAIL {name}: {e}")
    sys.exit(1 if failed else 0)


# ---------- 何通り試したか（ヒーローで明示） ----------

def _scale_data(trials=1, errors=0):
    det = [{"target_id": t, "attack_id": a, "transformation": f, "trials": trials, "breaches": 0}
           for t in ("t1", "t2") for a in ("a1", "a2", "a3") for f in ("baseline", "gyaru")]
    rows = [dict(_row(t), total_attacks=3 * 2 * trials - (errors if t == "t1" else 0),
                 n_api_error=(errors if t == "t1" else 0)) for t in ("t1", "t2")]
    return _data(transformations=["baseline", "gyaru"], summary=rows, details=det)


def test_scale_counts_configs_attacks_and_transforms():
    s = generate_site.scale(_scale_data())
    assert (s["n_targets"], s["n_attacks"], s["n_transforms"], s["combos"]) == (2, 3, 2, 12)
    assert s["trials"] == 12 and s["per_cell"] == 1 and s["valid"] == 12 and s["api_errors"] == 0


def test_scale_counts_repeated_trials_not_cells():
    # each cell run 5 times: 12 combinations, 60 trials (the old "total trials" showed 12)
    s = generate_site.scale(_scale_data(trials=5, errors=4))
    assert s["combos"] == 12 and s["trials"] == 60 and s["per_cell"] == 5
    assert s["valid"] == 56 and s["api_errors"] == 4


def test_hero_states_how_many_combinations_were_tried():
    page = render_page(_scale_data(trials=5, errors=4))
    assert "2 構成 × 3 攻撃 × 2 変形 = 12 通り" in page
    assert "各 5 回" in page and "60 試行" in page
    assert "有効 56" in page and "API エラー 4" in page
    assert "2 configs × 3 attacks × 2 transforms = 12 combinations" in page  # EN, switched by the i18n script


# ---------- 防御設定の公開（強化プロンプト・LLM ガードレール） ----------

def test_defense_settings_are_published_from_the_assessment_code():
    import run_assessment as ra
    page = render_page(_data())
    hardened = ra.build_system_prompt({"prompt_strength": "high"}, generate_site.CANARY_MASK, "")
    for line in hardened.splitlines():
        if line.startswith("- "):
            assert html.escape(line[2:]) in page, line  # every hardened rule is shown verbatim
    assert html.escape(ra.LLM_INPUT_GUARD_PROMPT) in page
    assert "ZIPANGU" not in page  # the canary itself is never published


def test_output_guard_prompt_is_published_and_the_old_simulation_is_disclosed():
    import run_assessment as ra
    page = render_page(_data())
    assert html.escape(ra.LLM_OUTPUT_GUARD_PROMPT) in page
    assert f"{round(ra.LLM_OUTPUT_GUARD_MOCK_P * 100)}%" in page  # runs before the change were simulated
    assert "シミュレーション" in page and "simulation" in page
