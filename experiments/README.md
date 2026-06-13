# J-ART experiments — reviewer-response (P0)

This directory holds the harness and analysis scaffolding for the three
measurement experiments that substantively close reviewer issues **C1–C3**. The
code, statistics, and configuration are in place; the only remaining step is
executing one labeled live campaign and pasting the resulting numbers into §4.

All experiments reuse the canonical `secret_canary`, `markers`, `transformations`,
and `attacks` from `../config.yaml`, so they stay in sync with the main suite.

## C1 — Provenance labels (no separate run needed)

`run_assessment.py` now stamps every cell with `mode` (`LIVE`/`MOCK`),
`api_error`, the resolved `model`, a `price_per_million` snapshot, and separate
`guard_*` token/`guard_model` fields. `summarize()` drops `api_error` cells from
defense-rate and cost aggregates (`n_api_error` is retained). §4 reports only
`LIVE` cells.

## C2 — Balanced ablation (configuration effect, model held fixed)

Generate a crossed design for a **single fixed model** — {naked, hardened}
prompt × {none, keyword, regex, llm, llamaguard} guardrail (10 configs) — then
test each config against the naked baseline with a difference-in-proportions
(Newcombe 95%) CI.

```bash
python experiments/make_ablation_config.py \
    --base-model gpt-4o-mini --provider openai \
    --out experiments/ablation.yaml
python run_assessment.py --config experiments/ablation.yaml \
    --out experiments/ablation_results.json
python experiments/analyze_ablation.py experiments/ablation_results.json
```

A config whose Δ CI excludes 0 is a configuration effect that holds **with the
model fixed**, separating it from model capability (C2). For OSS models add
`--provider openai_compatible --api-key-env OPENROUTER_API_KEY`.

## C3 — Controlled variance experiment (frozen config, repeated)

The original §4.3 compared two runs whose *config set also changed* (18→21), so
"time only" was not isolated. Freeze the config and repeat.

**(A) Within-run, K repeats per cell** (captures provider/router non-determinism
for an identical config in one invocation):

```bash
JART_TRIALS=5 python run_assessment.py --config config.yaml \
    --out experiments/var_run.json
python experiments/analyze_variance.py experiments/var_run.json
```

**(B) Across separate runs** (captures day-to-day / routing drift — run on
different days, then aggregate):

```bash
python experiments/analyze_variance.py run1.json run2.json run3.json
```

`analyze_variance.py` reports per-config defense-rate CIs and flags cells whose
outcome splits across repeats; the across-runs mode reports the per-config range.

## Cost estimate (live)

From MOCK token accounting priced at real per-model rates, one full pass over all
21 configs (1,617 cells) is **≈ $0.55** if every config runs live. So:

| Experiment | Scale | Rough live cost* |
|---|---|---|
| Variance, K=5 over full suite | 5 × 1,617 cells | ~$3 (≤ ~$10 worst case) |
| Balanced ablation (1 model, K=3) | 3 × 770 cells | ~$0.5 |
| Single labeled pass (K=1) | 1,617 cells | ~$0.55 |

\* Upper-bound assuming **all** configs live; actual spend is lower for any config
whose key is absent (those fall back to MOCK and are labeled as such). Live
responses can be longer than the MOCK stand-ins, so treat these as order-of-
magnitude figures and keep a small buffer.

## Notes

- Determinism: MOCK results are reproducible from `_frac`/`_seed`; the
  cost-attribution fix (guardrail tokens priced at `JART_GUARD_MODEL`'s own rate)
  changes cost numbers deliberately (reviewer R1-M5).
- Generated artifacts (`ablation.yaml`, `*_results.json`, `var_run*.json`) are
  git-ignored; regenerate them with the commands above.
