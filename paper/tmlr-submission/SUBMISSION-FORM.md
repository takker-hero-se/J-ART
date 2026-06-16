# TMLR / OpenReview submission form — copy-paste answers

Use these when filling the TMLR submission on OpenReview. Keep the manuscript
anonymous (`main.tex` with `\usepackage{tmlr}`); restore identity only for the
camera-ready.

## Title
J-ART: A Japanese Adversarial Red-Team Framework for Application-Layer LLM Security and Cost-Efficiency

## TL;DR (one sentence)
A reproducible, Japanese-specific red-team harness that evaluates the application-configuration layer (model × prompt × guardrail × RAG) of LLM deployments, showing — with live K=5 data and cluster-robust intervals — that configuration matters more than model choice.

## Keywords
LLM security; red teaming; jailbreak; prompt injection; guardrails; Japanese NLP; MITRE ATLAS; reproducibility; benchmark; cost efficiency

## Abstract
(Paste the plain-text abstract from the paper / README; it is already anonymized.)

## Authors
Anonymous (double-blind). Do **not** enter real names until the camera-ready.

## Standard TMLR declarations

- **Prior/concurrent publication.** This work is available as a **public preprint**
  (software + report) with a DOI. TMLR permits preprints. Note for the AE: the
  preprint is non-anonymous and de-anonymizable by searching the title; we have not
  actively de-anonymized the submission and ask reviewers not to seek the authors'
  identity, per TMLR policy. (Be honest here — declare the preprint exists.)
- **Code and data availability.** All code and the committed LIVE result artifacts
  (`var_run.json` + three ablation JSONs) are provided for review via an
  **anonymized repository** (e.g. anonymous.4open.science) linked in the submission;
  they will be released under MIT (code) / CC-BY-4.0 (report) upon acceptance.
- **Reproducibility.** Every Section 4 number reproduces from the committed
  artifacts; `analyze_ablation.py` / `analyze_variance.py` recompute the
  cluster-robust intervals; 16 unit tests pass (Section 9).
- **Limitations.** Stated explicitly in Section 7 (lexical-leak upper bound,
  single-turn, synthetic suite, one rate-limited config still provisional,
  proxy markers vs. real harm).
- **Ethics / responsible disclosure.** Section 6: harmless proxy markers, no
  weaponizable content, masked attack cores (unit-test-audited), a reusable
  safe-disclosure pattern, a governance crosswalk, and a dual-use discussion.
- **LLM usage.** Disclosed in the "AI Assistance Disclosure" section (writing **and
  code-implementation** assistance, including the statistical-analysis scripts; the
  human author directed all methodological choices, verified all results, and is
  responsible for all claims and analysis).

## Submission checklist mapping
| TMLR expectation | Where addressed |
|---|---|
| Claims supported by evidence | §4 + committed artifacts; CIs are cluster-robust |
| Limitations discussed | §7 |
| Reproducibility (code/data/seeds) | §9; seeded bootstrap; committed JSON artifacts |
| Compute/cost reported | §4 (≈$6.0), §3.8 cost metric |
| Ethics / dual-use | §6 (incl. dual-use paragraph) |
| LLM-use disclosure | "AI Assistance Disclosure" section (writing + code) |

## What I (author) still need to do
1. Compile `main.tex` with the official `tmlr.sty` (Overleaf "TMLR" template) → `main.pdf`.
2. Create the anonymized code mirror (anonymous.4open.science → the GitHub repo) and
   copy its URL into the submission form (and/or attach an author-free zip as
   supplementary material).
3. Submit on openreview.net (TMLR venue): upload `main.pdf`, paste Title/Abstract/
   TL;DR/Keywords, fill the declarations above.
