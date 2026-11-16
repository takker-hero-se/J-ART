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

## Running live locally

CI installs `requirements.txt`; a bare local checkout does **not** have the
provider SDKs, and without them every live call silently falls back to MOCK
(`No module named 'openai'` is caught and treated as an error/fallback). Before a
local live run:

```bash
pip install -r requirements.txt   # openai, anthropic, google-generativeai, pyyaml
```

Keys are read from the process environment (the harness does not auto-load
`.env`). Export them first, e.g. `set -a; . ./.env; set +a`, or pass them inline.
Targets whose key is absent are evaluated in MOCK and labeled `mode=MOCK`.

## Transform expansion (2026-11): NFKC-reversible vs. NFKC-resistant Japanese rewrites

Nine transforms were added to `run_assessment.py`. They rewrite kana and kanji only and never touch
ASCII, so the markers and the canary stay intact for the lexical judge.

| Transform | What it rewrites | Undone by NFKC |
|---|---|---|
| `halfwidth_kana` | katakana to half-width kana | yes |
| `dakuten_split` | voiced kana to base + combining mark (U+3099 / U+309A) | yes |
| `kanji_compat` | kanji to Kangxi radicals / CJK compatibility ideographs | yes |
| `compat_forms` | the three above combined | yes |
| `kana_swap` | hiragana and katakana exchanged | no |
| `kana_homoglyph` | katakana and look-alike kanji exchanged (ロ/口, カ/力, ...) | no |
| `kanji_variant` | Japanese forms to simplified / traditional forms (無視 to 无视) | no |
| `variant_forms` | the three above combined | no |
| `ringi_document` | pretext only: the core wrapped in a ringi (approval document) form | core intact |

The normalizing filter is staged: `regex_guardrail_blocks(text, level)` with level 1 = the published
`regex` guardrail (unchanged, no NFKC), level 2 = level 1 + NFKC, level 3 = level 2 + skeleton
matching (variant kanji, look-alikes and kana folded). Level 3 is selectable as `guardrail: skeleton`.

```bash
python experiments/filter_matrix.py     # deterministic: attacks blocked per transform and filter level -> filter_matrix.json
python experiments/benign_fp.py         # deterministic: false positives on 80 benign requests -> benign_fp.json
python experiments/make_expansion_config.py
JART_TRIALS=3 python run_assessment.py --config experiments/expansion.yaml --out experiments/expansion_run.json
python experiments/analyze_expansion.py # model x guardrail x transform breach rates -> expansion_summary.json
```

`expansion_run.json` is the LIVE run of 2026-11-16 (UTC): three bare models x five guardrails x five
transforms x 11 attacks, K=3, 2,472 valid trials, 3 excluded. `benign_requests.json` was written by
hand for this check and is not real traffic; the `hard_negative` and `boundary` categories were
built to expose a mechanism, so the counts are not a false-positive rate.

## Notes

- Determinism: MOCK results are reproducible from `_frac`/`_seed`; the
  cost-attribution fix (guardrail tokens priced at `JART_GUARD_MODEL`'s own rate)
  changes cost numbers deliberately (reviewer R1-M5).
- Generated artifacts (`ablation.yaml`, `*_results.json`, `var_run*.json`) are
  git-ignored; regenerate them with the commands above.
