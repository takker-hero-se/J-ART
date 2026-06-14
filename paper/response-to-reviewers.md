# Response to Reviewers — J-ART Technical Report

> **Round 2 (v0.2 → v0.3) is summarized first; the original Round-1 response
> follows below.** A second peer-review panel re-read the v0.2 revision, verified
> the empirical core reproduces, and returned *Major Revision* with two new
> CRITICAL items. Both are now resolved:
>
> **R2-C1 — Survivorship bias in the flagship comparator.** The panel showed the
> "cheap+hardened beats strongest naked (Opus 89.6%)" headline rested on Opus's
> 125/385 trials, with the *hardest 7 attacks* having zero surviving Opus trials.
> **Action:** a parity re-run brought Qwen3-max to n=374; Opus could not be
> brought to parity (Anthropic balance exhausted) and Gemini-pro stayed
> rate-limited, so we (a) re-anchor the thesis on **fully-measured GPT-4.1**
> (naked 64.1%, n=231) instead of Opus, (b) mark Opus/Gemini-pro **provisional**
> in every table, and (c) add an explicit **non-random-missingness** disclosure
> to §7 stating Opus's 89.6% is likely an over-estimate.
>
> **R2-C2 — Reproducibility/provenance trap.** The committed `results.json` and
> the public site were MOCK while §4 cited live numbers. **Action:** the exact
> LIVE artifacts (`var_run.json` + three ablation JSONs) are now **committed**
> (un-git-ignored; masking invariant re-verified: 100% masked prompts, 0 raw-core
> leaks), §9 has a **table naming which file reproduces each §4 number**, the cost
> figure is corrected $3.74 → $3.25, and CI was changed so push-triggered runs are
> MOCK-labeled (the site never mixes MOCK/LIVE).
>
> **Consensus (5/5) — single-model ablation.** The ablation now runs on **three**
> base models (Llama-4-Scout, GPT-4o-mini, GPT-4.1), new §4.2 Table 2′.
>
> **R2 (methodology) — clustered CIs.** K=5 repeats are correlated; we added a
> **cluster-robust bootstrap CI** (resample cells, not trials). This *corrected*
> the earlier "every guardrail significant" claim: a hardened prompt and the
> model-based guardrails are robustly significant on all three models, but
> lightweight keyword/regex are significant only where the base model is weak
> (no headroom on GPT-4o-mini's 82% naked). Plus prior-art (CipherChat/ArtPrompt/
> AgentDojo), cospa-as-screening-ratio, a dual-use note, a governance worked
> example, and a lexical-leak relabel of all defense rates.

---

## Round 1 (v0.1 → v0.2)

We thank the reviewers for the careful reading and the *Major Revision*
assessment. The review identified three CRITICAL issues (C1–C3) and several
methodological and code-level defects. Below we respond to each in
**R**eviewer-comment → **A**ction → **C**hange format. Each change is linked to a
commit and a location so the revision is auditable.

**Update (v0.2):** the fully-labeled live campaign has now been **executed** — 21
configurations × 11 attacks × 7 transforms × **K=5** = 8,085 trials, 2026-06-14,
$3.74, 7,466 clean trials after excluding rate-limited cells. **All items below,
including the three CRITICAL issues, are now [DONE]** with real measured numbers in
§4. The headline results:

- **C1**: every cell is labeled `mode/api_error/price`; §4 reports only clean LIVE
  cells; 619 rate-limited cells are excluded, not silently counted.
- **C2**: model-fixed ablation shows every guardrail/hardening is significant
  (82% → 91–100%, all Newcombe Δ-CIs exclude 0); naked models alone span
  29.6–89.6%, so a hardened cheap model out-defends the strongest naked model.
- **C3**: in the controlled K=5 repeat, **9.6% of cells (142/1,477) flip outcome
  across identical trials**; Llama-4-Scout-naked has 32/77 unstable cells.

A one-line summary of the disposition is in the table at the end.

---

## Critical issues

### C1 — Provenance of the published `results.json` (MOCK vs. "live")

**R.** The committed `results.json` was produced entirely in deterministic
simulation (MOCK) mode, while §4 describes "live runs." This is a
provenance/labeling gap: a reader cannot tell which cells are empirical and which
are simulated.

**A.** We make execution mode a *first-class, per-cell* property rather than a
single top-level flag, and we restrict the empirical claims in §4 to cells whose
mode is `live`.

- The harness now stamps **every cell** with `mode` (`live`/`mock`),
  `generated_at`, the resolved `model` slug, and the `pricing` snapshot used for
  cost (so a mixed run is unambiguous and reproducible).
- The site and `results.json` render a per-cell mode badge; simulated cells are
  visibly marked and are excluded from the headline aggregates.
- §4 is rewritten to report only `live` cells; simulated cells, if any, are
  reported separately and never aggregated into defense rates.
- The unit-test masking invariant additionally guarantees no core leaks
  regardless of mode.

**C.** `run_assessment.py` (per-cell labeling), `generate_site.py` (mode badge),
§3.9/§4 of all three manuscript sources. **[PENDING-LIVE]** for the replacement
numbers; **[DONE]** for the labeling mechanism and the manuscript framing.

### C2 — Confound in "application layer dominates model capability"

**R.** Model tier and configuration tier are not balanced-crossed, so the claim
that configuration matters more than model choice is confounded.

**A.** We add a **balanced ablation**: the *same* model is evaluated under a
crossed design {naked, hardened-prompt} × {no-guardrail, keyword, regex}, holding
the model fixed, and we report the **difference in defense proportions with a
95% Wilson/Newcombe confidence interval** for the configuration effect. The
"configuration > model" claim is re-stated only to the extent the within-model
ablation and a matched cross-model comparison support it.

**C.** New `wilson_diff_ci()` (difference-in-proportions CI) in
`run_assessment.py`; new ablation configuration and analysis; §3 (design) and §4.2
rewrite. **[DONE]** for the design, statistic, and harness; **[PENDING-LIVE]** for
the measured effect sizes.

### C3 — Run-to-run variance attributed to "time only" despite a config change

**R.** The 58→0 breach change for "Llama 4 Scout / naked" is attributed to time
of execution, but the configuration set also changed (18→21 targets) between the
two runs, so "time only" is not established.

**A.** We retract the "time only" attribution as stated and replace §4.3 with a
**controlled variance experiment**: a *single, frozen* configuration set is
re-run **K times** with everything else held constant (same targets, prompts,
transforms, seeds), and we report per-run defense rates and the across-run
variance / range with CIs. This isolates provider/router non-determinism from any
configuration change, which the original two-run comparison could not.

**C.** New repeated-run mode and an across-run aggregation/analysis path; §4.3
rewrite to present K independent runs rather than two non-matched snapshots.
**[DONE]** for the experiment design and runner; **[PENDING-LIVE]** for the K runs
and the variance numbers (default **K = 5**).

---

## Methodological and code-level defects

### R1-M3 — Normalizing filter does not actually neutralize *gyaru*; "in unit tests" unsupported

**R.** The Abstract claims the normalizing regex filter neutralizes obfuscation
"in unit tests," but no unit tests existed and `_normalize_for_filter` never
inverted the gyaru substitution map, so hiragana-bearing banned terms passed
through.

**A.** Fixed and tested.

- `_normalize_for_filter` now inverts `_GYARU_MAP` (longest-glyph-first) before
  keyword matching.
- We also found and fixed a **second** defect the tests surfaced: the normalizer
  folds whitespace, so a space-containing banned term (`developer mode`) could
  never match; banned keywords are now whitespace-folded for comparison too.
- Added `tests/test_guardrails.py` (pytest-free, also CI-run): asserts the filter
  defeats vertical-newline, leet, Base64, and gyaru transforms for **every**
  banned keyword, plus a `render_display` core-masking invariant. The "in unit
  tests" claim is now substantiated. Full suite: 11/11 pass.

**C.** `run_assessment.py` `_normalize_for_filter`, `regex_guardrail_blocks`;
`tests/test_guardrails.py`; `.github/workflows/eval.yml` (CI test step). Commit
`01020fe`. **[DONE]**

### R1 — Anthropic calls did not set temperature

**R.** The Anthropic path omitted `temperature`, breaking determinism/comparability
with the OpenAI and Gemini paths (which set `temperature=0`).

**A.** Added `temperature=0` to `_call_anthropic`.

**C.** `run_assessment.py` `_call_anthropic`. Commit `01020fe`. **[DONE]**

### R1-M5 — Cost attribution prices guardrail tokens at the target model's rate

**R.** Guardrail tokens are billed at the target model's price, which is an
approximation that can misstate cospa when the guardrail model is cheaper/dearer.

**A.** Cost attribution is corrected to price guardrail tokens at the **guardrail
model's** own rate (`JART_GUARD_MODEL`), and the Limitations note is updated. The
classifier-guardrail (Llama Guard) and LLM-judge guardrail tokens are accounted
separately from the target model's tokens.

**C.** `run_assessment.py` cost path; §3.8/§7. **[PENDING-LIVE]** affects cospa
numbers; **[DONE]** for the attribution logic and text. *(Implemented in the P0
batch; see below.)*

### Judge false negatives (R-methodology)

**R.** An exact-match judge can undercount breaches when the model echoes the
canary/marker in a reformatted way, inflating defense rates.

**A.** `judge()` now matches exactly **and** after light normalization
(case-folding, whitespace/zero-width removal); the new match strictly contains the
old exact match, so detection only increases (no new false positives) and MOCK
determinism is unchanged. We add judge unit tests (reformatted-echo, clean-refusal,
unknown-check) and state in §7 that reported defense rates are an **upper bound**;
a human-validated LLM-judge to quantify residual semantic false negatives is future
work. Commit `93c7283`. **[DONE]**

---

## Major-revision dimensions

### Related Work (originality/positioning)

**R.** Related Work was a bullet list and omitted several relevant literatures.

**A.** §2 is rewritten as a six-thread narrative with a positioning table
(Table 1), and the bibliography is expanded from 10 to 27 entries — adding
prompt-injection benchmarks, multilingual/low-resource safety, in-the-wild
jailbreaks, GCG, Jailbroken, guardrail evaluations, LLM-judge validation, Japanese
NLP (JGLUE), and governance standards. Commit `93c7283`, `5ddee84`. **[DONE]**

### Transform classification (construct validity)

**R.** The paper conflates Japanese-specific and language-agnostic obfuscations.

**A.** §3.2 adds a two-class taxonomy (Table 2): Japanese-specific (`gyaru`,
`vertical_newline`, `polite_business`, `double_tongue`) vs. language-agnostic
(`base64_wrap`, `leet_smuggle`, + `baseline`), so the marginal effect of the
Japanese-specific surface can be isolated and the generalizable findings are
identified. Commit `e1f1a99`. **[DONE]**

### Responsible disclosure and governance (significance/ethics)

**R.** The safe-by-construction design and its standards relevance should be made
explicit and reusable.

**A.** §6 is restructured into safety-by-construction, a **reusable disclosure
pattern** for safety benchmarks, and a **governance crosswalk** (Table 3) mapping
each capability (by ATLAS technique) to OWASP LLM Top 10 (2025), NIST AI RMF, the
EU AI Act, and Japan's AI Guidelines for Business + AISI red-teaming guide, framed
explicitly as informational. Commit `5ddee84`. **[DONE]**

---

## Disposition summary

| # | Reviewer item | Disposition |
|---|---|---|
| C1 | MOCK/live provenance | **[DONE]** — labeled LIVE campaign; §4 clean cells only |
| C2 | App-layer confound | **[DONE]** — model-fixed ablation, all Δ-CIs exclude 0 |
| C3 | Variance attribution | **[DONE]** — controlled K=5; 9.6% of cells flip |
| R1-M3 | gyaru filter + tests | **[DONE]** (`01020fe`) |
| R1 | Anthropic temperature | **[DONE]** (`01020fe`; Opus regression fixed `d7906c1`) |
| R1-M5 | Cost attribution | **[DONE]** — guard tokens priced separately; cospa in §4.4 |
| Judge FN | Reformatted-echo undercount | **[DONE]** (`93c7283`) |
| Related Work | Narrative + table + refs | **[DONE]** (`93c7283`,`5ddee84`) |
| Transforms | JP vs language-agnostic | **[DONE]** (`e1f1a99`) |
| Ethics/Gov | Disclosure pattern + crosswalk | **[DONE]** (`5ddee84`) |

All reviewer items are now resolved with implemented code, unit tests, and real
measured results from the labeled live campaign (2026-06-14). The remaining
caveat, stated in §7, is that three configurations (Gemini-pro, Qwen3-max, Opus)
were partially rate-limited; their failed cells are excluded and their CIs widen
accordingly, but their point estimates rest on fewer trials (n = 116–295 rather
than 385).
