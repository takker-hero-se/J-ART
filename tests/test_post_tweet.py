# -*- coding: utf-8 -*-
"""post_tweet のユニットテスト（週次リーダーボード更新の X 投稿）。

投稿そのもの（OAuth 署名・文字数の数え方・エラー処理）は Quiet Forensics 共通の
qf_common.qf_x が担い、ここでは J-ART 固有の本文組み立てと、認証情報がないときに
投稿しないことを確かめる。ネットワークには出ない。
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import post_tweet  # noqa: E402
from qf_common import qf_x  # noqa: E402


def _results(n=3, top_rate=97.5, label_en="Claude Opus 5 + high"):
    summary = [{"target_id": f"t{i}", "target_label": f"構成{i}", "target_label_en": f"config {i}",
                "total_attacks": 100, "success_rate": 80.0 + i} for i in range(n - 1)]
    summary.append({"target_id": "top", "target_label": "トップ", "target_label_en": label_en,
                    "total_attacks": 100, "success_rate": top_rate})
    summary.append({"target_id": "unmeasured", "total_attacks": 0, "success_rate": 100.0})  # not measured: never the top
    return {"generated_at": "2026-09-28T00:00:00Z", "summary": summary}


def test_compose_names_the_date_the_count_the_top_and_the_site():
    text = post_tweet.compose_tweet(_results())
    assert "J-ART 週次更新 (2026-09-28)" in text
    assert "4構成" in text and "Claude Opus 5 + high 97.5%" in text
    assert text.endswith(post_tweet.SITE_URL)
    assert qf_x.fits(text)


def test_compose_stays_within_x_limit_for_a_long_japanese_label():
    text = post_tweet.compose_tweet(_results(label_en="長い構成名" * 60))
    assert qf_x.fits(text) and text.endswith("\n" + post_tweet.SITE_URL) and "…" in text


def test_compose_without_measured_targets_has_no_top_line():
    text = post_tweet.compose_tweet({"generated_at": "2026-09-28T00:00:00Z", "summary": [{"target_id": "x", "total_attacks": 0}]})
    assert "防御率トップ" not in text and text.endswith(post_tweet.SITE_URL)


def test_main_without_credentials_prints_and_does_not_post(tmp_path, monkeypatch, capsys):
    path = tmp_path / "results.json"
    path.write_text(json.dumps(_results()), encoding="utf-8")
    for k in qf_x.ENV_KEYS:
        monkeypatch.delenv(k, raising=False)
    # without this, qf_env would fall back to the real security-biz/qf-common/.env and this test
    # would post for real once the keys are filled in there
    monkeypatch.setenv("QF_ENV_FILE", str(tmp_path / "no-shared.env"))
    called = []
    monkeypatch.setattr(qf_x.urllib.request, "urlopen", lambda *a, **k: called.append(a))
    assert post_tweet.main(["--results", str(path)]) == 0
    out = capsys.readouterr().out
    assert "スキップ" in out and "J-ART 週次更新" in out and called == []


def test_the_shared_env_file_is_where_local_keys_come_from(tmp_path, monkeypatch):
    shared = tmp_path / "shared.env"
    shared.write_text("".join(f"{k}=v\n" for k in qf_x.ENV_KEYS), encoding="utf-8")
    monkeypatch.setenv("QF_ENV_FILE", str(shared))
    for k in qf_x.ENV_KEYS:
        monkeypatch.delenv(k, raising=False)
    assert qf_x.Credentials.from_env(qf_x.qf_env.values(qf_x.ENV_KEYS)) is not None


def test_main_dry_run_never_posts_even_with_credentials(tmp_path, monkeypatch, capsys):
    path = tmp_path / "results.json"
    path.write_text(json.dumps(_results()), encoding="utf-8")
    for k in qf_x.ENV_KEYS:
        monkeypatch.setenv(k, "x")
    called = []
    monkeypatch.setattr(qf_x.urllib.request, "urlopen", lambda *a, **k: called.append(a))
    assert post_tweet.main(["--results", str(path), "--dry-run"]) == 0
    assert called == [] and "dry run" in capsys.readouterr().out


if __name__ == "__main__":  # pytest が無い環境でも直接実行できる（他のテストと同じ流儀）
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
