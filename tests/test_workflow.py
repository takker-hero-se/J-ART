# -*- coding: utf-8 -*-
"""eval.yml の公開ポリシー: 計測したものはすべて公開し、push で古い結果に戻さない。

以前は push のたびに論文用の成果物（2026-06 の21構成）を公開しており、毎週の定期実行で
全構成（2026-09-27 時点で49構成）を測っても、次の push で21構成に戻っていた。
定期・手動の LIVE 結果は experiments/live_latest.json に保存し、push はそれを公開する。
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WF = open(os.path.join(ROOT, ".github", "workflows", "eval.yml"), encoding="utf-8").read()
LATEST = os.path.join(ROOT, "experiments", "live_latest.json")


def _step(name):
    m = re.search(r"- name: " + re.escape(name) + r"\n(.*?)(?=\n      - name: |\n  [a-z]+:\n|\Z)", WF, re.S)
    assert m, name
    return m.group(1)


def test_push_publishes_the_latest_live_run_and_falls_back_to_the_paper_artifact():
    publish = _step("Publish results")
    assert "experiments/live_latest.json" in publish
    i_latest, i_paper = publish.index("experiments/live_latest.json"), publish.index("experiments/var_run.json")
    assert i_latest < i_paper  # the latest LIVE run first, the paper campaign only as a fallback


def test_scheduled_and_manual_live_runs_are_kept_in_the_repository():
    keep = _step("Keep the LIVE results in the repository")
    assert "github.event_name != 'push'" in keep
    assert "force_mock != 'true'" in keep  # a forced MOCK run never overwrites measured data
    assert "cp results.json experiments/live_latest.json" in keep
    assert "git push" in keep


def test_the_evaluate_job_may_write_contents_but_nothing_else_widened():
    job = WF.split("\n  evaluate:\n", 1)[1].split("\n  deploy:\n", 1)[0]
    perms = re.search(r"permissions:\n((?:\s{6}\S.*\n)+)", job).group(1)
    assert "contents: write" in perms and "pages: write" in perms


def test_the_seeded_latest_run_is_all_live():
    with open(LATEST, encoding="utf-8") as f:
        data = json.load(f)
    modes = {t.get("mode") for t in data["summary"]}
    assert modes == {"LIVE"} and len(data["summary"]) > 21


if __name__ == "__main__":
    import sys

    import pytest
    sys.exit(pytest.main([__file__, "-q"]))


def test_new_models_are_added_weekly_before_the_evaluation():
    wf = open(os.path.join(ROOT, ".github", "workflows", "update-models.yml"), encoding="utf-8").read()
    assert 'cron: "0 16 * * 6"' in wf          # Sunday 01:00 JST, a day before the Monday 03:00 JST evaluation
    assert "workflow_dispatch" in wf and "contents: write" in wf
    assert "python scripts/update_models.py" in wf
    assert "pytest" in wf.split("python scripts/update_models.py", 1)[1]  # tests run before the commit
    assert "git push" in wf
