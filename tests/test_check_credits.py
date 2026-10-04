# -*- coding: utf-8 -*-
"""scripts/check_credits.py: クレジット切れを検出して失敗させる（GitHub の失敗メールで知らせる）。"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import check_credits as cc  # noqa: E402


def _err(provider, msg, model="m"):
    return {"provider": provider, "model": model, "api_error": True, "response_excerpt": f"[API呼び出し失敗: {msg}]"}


RESULTS = {"details": [
    _err("anthropic", "Error code: 400 - {'error': {'message': 'Your credit balance is too low to access the Anthropic API.'}}"),
    _err("anthropic", "Error code: 400 - {'error': {'message': 'Your credit balance is too low to access the Anthropic API.'}}"),
    _err("openai", "Error code: 429 - {'error': {'message': 'You have no credits remaining. Add credits to continue'}}"),
    _err("openai_compatible", "Error code: 402 - {'error': {'message': 'Insufficient credits. Add more using https://openrouter.ai/settings/credits'}}", "x-ai/grok-4.7"),
    _err("openai_compatible", "Error code: 429 - {'error': {'message': 'Provider returned error', 'metadata': {'raw': 'is temporarily rate-limited'}}}"),
    {"provider": "gemini", "model": "gemini-3.8-flash", "api_error": False, "response_excerpt": "ok"},
]}


def test_credit_errors_are_counted_per_billing_account_and_rate_limits_are_not():
    found = cc.exhausted(RESULTS)
    assert found == {"anthropic": 2, "openai": 1, "openrouter": 1}


def test_low_openrouter_balance_is_flagged_at_the_threshold_boundary():
    assert cc.balance_problem(4.99, threshold=5.0) is True
    assert cc.balance_problem(5.0, threshold=5.0) is False
    assert cc.balance_problem(None, threshold=5.0) is False  # balance unknown: nothing to report


def test_report_names_each_account_with_its_top_up_url():
    text = cc.report({"anthropic": 2, "openrouter": 1}, balance=3.2, threshold=5.0)
    assert "https://console.anthropic.com/settings/billing" in text
    assert "https://openrouter.ai/settings/credits" in text and "$3.20" in text
    assert "openai" not in text.lower().replace("openrouter", "")


def test_exit_code_fails_only_when_there_is_something_to_fix(tmp_path, monkeypatch):
    import json
    ok = tmp_path / "ok.json"
    ok.write_text(json.dumps({"details": [RESULTS["details"][-1]]}), encoding="utf-8")
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(RESULTS), encoding="utf-8")
    monkeypatch.setattr(cc, "openrouter_balance", lambda: None)
    assert cc.main(["--results", str(ok)]) == 0
    assert cc.main(["--results", str(bad)]) == 1
    monkeypatch.setattr(cc, "openrouter_balance", lambda: 1.0)
    assert cc.main(["--results", str(ok)]) == 1  # low balance alone is worth a warning mail


def test_missing_results_file_is_not_a_credit_problem(tmp_path, monkeypatch):
    monkeypatch.setattr(cc, "openrouter_balance", lambda: None)
    assert cc.main(["--results", str(tmp_path / "none.json")]) == 0
