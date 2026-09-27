# -*- coding: utf-8 -*-
"""generate_site のユニットテスト（Quiet Forensics 統合後のサイト外装）。

J-ART のリーダーボードは Quiet Forensics の公開研究として jart.quietforensics.com で公開する。
本テストは、ポータルと同じ外装（紺の帯＋シアン、明るい本文、BIZ UDPGothic、JA/EN 切替）と、
公開 URL・埋め込みデータの安全性を検証する。API もネットワークも使わない。

pytest があれば `pytest tests/` で、無ければ `python tests/test_site.py` で直接実行できる。
"""
import json
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import generate_site  # noqa: E402
from generate_site import build_i18n, build_site, render_page  # noqa: E402


def _row(tid="t1", label="テスト構成", rate=95.0, mode="LIVE", measured=True):
    return {
        "target_id": tid, "target_label": label, "target_label_en": "Test config",
        "provider": "openai", "model": "openai/gpt-test", "prompt_strength": "high",
        "guardrail": "keyword", "rag": True, "mode": mode, "n_api_error": 0,
        "total_attacks": 10 if measured else 0, "defended": 9, "breached": 1,
        "success_rate": rate, "ci_low": 80.0, "ci_high": 99.0,
        "cost_per_million_usd": 0.5, "cospa_score": 190.0,
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
