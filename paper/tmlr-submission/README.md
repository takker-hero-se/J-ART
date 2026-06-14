# TMLR submission package (anonymized)

This folder contains the **double-blind, TMLR-formatted** version of the J-ART
paper, ready to submit to **Transactions on Machine Learning Research** via
OpenReview. It is derived from `../technical-report.tex` with all
author-identifying information removed.

## Files
- `main.tex` — the anonymized manuscript (TMLR style, inline references).

## What was anonymized (vs. the public preprint)
- Author name, ORCID, affiliation → `Anonymous authors` (TMLR hides these
  automatically in submission mode).
- GitHub URLs (`github.com/<user>/J-ART`), the live-leaderboard URL, and the
  Zenodo DOIs → removed; §9 now says code/artifacts are in an **anonymized
  repository**, released upon acceptance, and the site URL is withheld.
- Title subtitle "Technical Report (v0.2, preprint)" and the preprint status
  block → removed/neutralized.
- The **AI Writing Assistance** section is kept (TMLR requires disclosure of LLM
  use) and contains no identifying information.

## How to compile (you need the official TMLR style)
`main.tex` uses `\usepackage{tmlr}`, which is **not** bundled here. Two options:

1. **Overleaf (easiest).** Open the official *Transactions on Machine Learning
   Research (TMLR)* template on Overleaf, then replace its `main.tex` with this
   file's content and compile (pdfLaTeX).
2. **Local.** Download the TMLR template from <https://jmlr.org/tmlr/> (Author
   instructions → LaTeX style files), put `tmlr.sty`, `tmlr.bst`, and
   `fancyhdr.sty` next to `main.tex`, then `pdflatex main`.

Submission mode (the default, `\usepackage{tmlr}`) prints "Under review as a
submission to TMLR" and hides authors. **For the camera-ready only**, switch to
`\usepackage[accepted]{tmlr}` and restore the author block + the code/Zenodo links.

## Anonymous code/artifacts for reviewers
TMLR is double-blind, so do **not** link the public GitHub/Zenodo. Instead:
- Mirror the repo to an anonymizing proxy, e.g. **<https://anonymous.4open.science>**
  (point it at the GitHub repo), and cite that anonymous URL in the submission
  form / a footnote, **or**
- Upload a stripped, author-free zip of the code + the four `*.json` artifacts as
  OpenReview supplementary material.

## Submit (OpenReview)
1. Create/log in at <https://openreview.net>, find the **TMLR** venue.
2. New submission → upload the compiled `main.pdf`.
3. Fill the form: title, abstract, **anonymous** author list, keywords, the
   anonymous code link, and the TMLR checklist (claims supported, limitations
   stated, compute/reproducibility, LLM-use disclosure — all already addressed in
   the paper: §7 limitations, §3.5 lexical-leak bound, §9 reproducibility, AI
   Writing Assistance section).
4. TMLR criteria are **correctness + "some audience would be interested"**, not
   novelty — keep claims tightly scoped to what the artifacts support.

## Camera-ready (after acceptance)
- `\usepackage[accepted]{tmlr}`; restore author/affiliation/ORCID.
- Replace the anonymized-repository wording in §9 with the real GitHub + Zenodo
  DOIs; restore the live-leaderboard URL.
- Verify all 30 references' venue/year/DOI.
