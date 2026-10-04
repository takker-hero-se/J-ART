# -*- coding: utf-8 -*-
"""scripts/update_models.py: 新しいモデルを毎週自動で評価対象に加える（ネットワークは使わない）。"""
import os
import sys
import time

import pytest
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import update_models as um  # noqa: E402

NOW = 1_790_000_000  # fixed "today" for the window check
DAY = 86400


def _m(mid, days_ago=1, price="0.000002", modalities=("text",), name=None):
    return {"id": mid, "name": name or mid.split("/")[-1], "created": NOW - days_ago * DAY,
            "pricing": {"prompt": price}, "architecture": {"input_modalities": list(modalities)}}


CATALOG = [
    _m("openai/gpt-6.1-sol", 1, name="OpenAI: GPT-6.1 Sol"),
    _m("openai/gpt-6.1-sol-pro", 1),                  # same day, longer name: the base model wins
    _m("openai/gpt-6.1-sol:batch", 1),                # variant
    _m("anthropic/claude-sonnet-5.5", 2, name="Anthropic: Claude Sonnet 5.5"),
    _m("anthropic/claude-opus-5.5", 8),               # already tracked as claude-opus-5-5
    _m("x-ai/grok-4.7", 9, name="xAI: Grok 4.7"),
    _m("qwen/qwen3.8-max-prime", 7),                  # premium variant
    _m("google/gemini-3.9-flash-preview", 3),         # preview
    _m("openai/gpt-6-astra", 4, price="0.00001"),     # over the price cap
    _m("deepseek/deepseek-v4.1-flash", 20),
    _m("someone/unknown-model", 1),                   # vendor not followed
    _m("mistralai/mistral-old", 400),                 # outside the window
    _m("z-ai/glm-5.3-voice", 2, modalities=("audio",)),  # no text input
]
TRACKED = {"claude-opus-5-5", "gpt-5.6-sol", "qwen3.8-max"}


def test_picks_newest_base_models_one_per_vendor_within_the_caps():
    picked = um.select_new_models(CATALOG, TRACKED, now=NOW, max_new=3)
    assert [m["id"] for m in picked] == ["openai/gpt-6.1-sol", "anthropic/claude-sonnet-5.5", "x-ai/grok-4.7"]


def test_max_new_bounds_the_weekly_cost():
    assert len(um.select_new_models(CATALOG, TRACKED, now=NOW, max_new=1)) == 1
    assert [m["id"] for m in um.select_new_models(CATALOG, TRACKED, now=NOW, max_new=10)][-1] == "deepseek/deepseek-v4.1-flash"


@pytest.mark.parametrize("a,b", [("anthropic/claude-opus-5.5", "claude-opus-5-5"), ("openai/gpt-5.6-sol", "gpt-5.6-sol"),
                                 ("qwen/qwen3.8-max", "qwen3.8-max")])
def test_tracking_matches_direct_and_openrouter_spellings(a, b):
    assert um.normalize(a) == um.normalize(b)


def test_target_block_is_a_naked_openrouter_config_and_parses():
    block = um.target_block(CATALOG[0], today="2026-10-04")
    t = yaml.safe_load("targets:\n" + block)["targets"][0]
    assert t["id"] == "openrouter-gpt-6-1-sol-naked" and t["model"] == "openai/gpt-6.1-sol"
    assert t["provider"] == "openai_compatible" and t["api_key_env"] == "OPENROUTER_API_KEY"
    assert (t["prompt_strength"], t["guardrail"], t["rag"]) == ("low", "none", True)
    assert t["label"] == "GPT-6.1 Sol / 素のAPI (OpenRouter)" and "auto-added 2026-10-04" in block


def test_apply_inserts_before_the_attacks_section_and_keeps_the_file_valid(tmp_path):
    src = open(os.path.join(ROOT, "config.yaml"), encoding="utf-8").read()
    p = tmp_path / "config.yaml"
    p.write_text(src, encoding="utf-8")
    before = yaml.safe_load(src)
    fresh = [_m("openai/gpt-zz-test", 1)]  # a name the real config can never contain
    added = um.apply(str(p), fresh, today="2026-10-04")
    after = yaml.safe_load(p.read_text(encoding="utf-8"))
    assert added == ["openai/gpt-zz-test"]
    assert len(after["targets"]) == len(before["targets"]) + 1 and after["attacks"] == before["attacks"]
    assert um.apply(str(p), fresh, today="2026-10-04") == []  # idempotent: already tracked


def test_tracked_models_are_read_from_the_config():
    tracked = um.tracked_models(os.path.join(ROOT, "config.yaml"))
    assert um.normalize("claude-opus-5-5") in tracked and um.normalize("openai/gpt-5.6-sol") in tracked


def test_same_day_releases_prefer_the_base_model_even_if_the_variant_is_seconds_newer():
    base = _m("openai/gpt-6.1-sol", 1)
    pro = dict(_m("openai/gpt-6.1-sol-pro", 1), created=base["created"] + 30)
    assert [m["id"] for m in um.select_new_models([pro, base], set(), now=NOW)] == ["openai/gpt-6.1-sol"]


@pytest.mark.parametrize("snapshot,tracked", [("qwen/qwen3.8-max-0902", "qwen/qwen3.8-max"),
                                              ("deepseek/deepseek-v4-pro-0813", "deepseek/deepseek-v4-pro"),
                                              ("qwen/qwen3-235b-a22b-2507", "qwen/qwen3-235b-a22b")])
def test_dated_snapshots_count_as_the_tracked_model(snapshot, tracked):
    assert um.normalize(snapshot) == um.normalize(tracked)
    assert um.select_new_models([_m(snapshot, 1)], {tracked}, now=NOW) == []
