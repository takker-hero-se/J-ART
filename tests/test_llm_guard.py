# -*- coding: utf-8 -*-
"""LLM ガードレールは LIVE では入力も出力も実際に LLM へ問い合わせる（API は呼ばない: 偽の呼び出しで検証）。

以前の出力検閲は LIVE でも LLM を呼ばず、突破応答の 70% を決め打ちの確率で「是正」していた。
入力検閲は API 失敗時に黙って決定論判定へ切り替わっていた。どちらも実測に模擬値が混ざる。
- 出力検閲は全応答に掛ける（突破かどうかを知らないのが本物の検閲器。誤検知とコストも数える）。
- 検閲器には合言葉を渡さない。
- ガードの呼び出し失敗は api_error として集計から除外する。
"""
import os
import sys

import pytest
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import run_assessment as ra  # noqa: E402

CFG = yaml.safe_load(open(os.path.join(ROOT, "config.yaml"), encoding="utf-8"))
SECRET, MARKERS = CFG["secret_canary"], CFG["markers"]
LEAK_ATTACK = next(a for a in CFG["attacks"] if a["check"] == "secret_leak" and a["vector"] == "user")
TARGET = {"id": "t-llm", "provider": "anthropic", "model": "claude-test", "prompt_strength": "high",
          "guardrail": "llm", "rag": True}


def _fake(monkeypatch, *, model_answer, input_says="いいえ", output_says="いいえ", fail=None):
    calls = []

    def call_live(target, system, user):
        kind = "input" if system == ra.LLM_INPUT_GUARD_PROMPT else "output" if system == ra.LLM_OUTPUT_GUARD_PROMPT else "model"
        calls.append((kind, system, user))
        if fail == kind:
            raise RuntimeError("upstream 503")
        return {"input": input_says, "output": output_says, "model": model_answer}[kind], 100, 3

    monkeypatch.setattr(ra, "is_live", lambda target: True)
    monkeypatch.setattr(ra, "_call_live", call_live)
    return calls


def test_live_output_screen_really_asks_the_model_and_can_stop_a_leak(monkeypatch):
    calls = _fake(monkeypatch, model_answer=f"合言葉は『{SECRET}』です。", output_says="はい")
    r = ra.run_one(TARGET, LEAK_ATTACK, "baseline", SECRET, MARKERS)
    kinds = [c[0] for c in calls]
    assert kinds == ["input", "model", "output"]
    assert r["breached"] is False and r.get("api_error") is not True
    out_call = calls[2]
    assert SECRET in out_call[2]          # the guard reads the answer ...
    assert SECRET not in out_call[1]      # ... but is never told the canary


def test_live_output_screen_saying_no_leaves_the_breach_standing(monkeypatch):
    # no fixed-probability rescue any more: if the guard misses it, it is a breach
    for _ in range(5):
        _fake(monkeypatch, model_answer=f"合言葉は『{SECRET}』です。", output_says="いいえ")
        r = ra.run_one(TARGET, LEAK_ATTACK, "baseline", SECRET, MARKERS)
        assert r["breached"] is True


def test_live_output_screen_runs_on_every_answer_and_its_cost_is_counted(monkeypatch):
    calls = _fake(monkeypatch, model_answer="セキュリティポリシーによりお応えできません。")
    r = ra.run_one(TARGET, LEAK_ATTACK, "baseline", SECRET, MARKERS)
    assert [c[0] for c in calls] == ["input", "model", "output"]  # screened although it defended
    assert r["breached"] is False and r["input_tokens"] >= 300  # input guard + model + output guard


@pytest.mark.parametrize("answer", ["", "   \n"])
def test_an_empty_answer_is_not_sent_to_the_output_screen(monkeypatch, answer):
    # 2026-10-04: Claude sometimes answers with no text; sending that to the screen was a 400
    # ("user messages must have non-empty content") and 107 trials became API errors.
    calls = _fake(monkeypatch, model_answer=answer)
    r = ra.run_one(TARGET, LEAK_ATTACK, "baseline", SECRET, MARKERS)
    assert [c[0] for c in calls] == ["input", "model"]  # nothing to screen: an empty answer leaks nothing
    assert r.get("api_error") is not True and r["breached"] is False


@pytest.mark.parametrize("where", ["input", "output"])
def test_a_failed_guard_call_is_an_api_error_not_a_simulated_verdict(monkeypatch, where):
    _fake(monkeypatch, model_answer=f"合言葉は『{SECRET}』です。", fail=where)
    r = ra.run_one(TARGET, LEAK_ATTACK, "baseline", SECRET, MARKERS)
    assert r["api_error"] is True


def test_mock_mode_still_uses_the_documented_simulation():
    assert 0 < ra.LLM_OUTPUT_GUARD_MOCK_P < 1
    assert not hasattr(ra, "LLM_OUTPUT_GUARD_SIMULATED_P")


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))


# ---------- Llama Guard 分類器も、LIVE では推測で埋めない ----------
LG_TARGET = dict(TARGET, id="t-lg", guardrail="llamaguard")


def _fake_lg(monkeypatch, *, classifier=None, key=True, fail=False, model_answer="お応えできません。"):
    calls = []

    def openai_chat(guard, system, user):
        calls.append(guard["model"])
        if fail:
            raise RuntimeError("upstream 429")
        return classifier, 50, 1

    monkeypatch.setattr(ra, "is_live", lambda target: True)
    monkeypatch.setattr(ra, "resolve_api_key", lambda t: "k" if (key or t.get("model") != ra.GUARD_MODEL) else None)
    monkeypatch.setattr(ra, "_call_openai_chat", openai_chat)
    monkeypatch.setattr(ra, "_call_live", lambda target, system, user: (model_answer, 100, 3))
    return calls


def test_live_llama_guard_blocks_on_unsafe(monkeypatch):
    calls = _fake_lg(monkeypatch, classifier="unsafe")
    r = ra.run_one(LG_TARGET, LEAK_ATTACK, "baseline", SECRET, MARKERS)
    assert calls == [ra.GUARD_MODEL] and r["breached"] is False and r.get("api_error") is not True


@pytest.mark.parametrize("case", ["call_fails", "no_guard_key"])
def test_live_llama_guard_failure_is_an_api_error_not_a_simulated_verdict(monkeypatch, case):
    _fake_lg(monkeypatch, classifier="safe", fail=(case == "call_fails"), key=(case != "no_guard_key"),
             model_answer=f"合言葉は『{SECRET}』です。")
    r = ra.run_one(LG_TARGET, LEAK_ATTACK, "baseline", SECRET, MARKERS)
    assert r["api_error"] is True
