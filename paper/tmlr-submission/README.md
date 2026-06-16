# TMLR submission package (anonymized)

This folder contains the **double-blind, TMLR-formatted** version of the J-ART
paper, ready to submit to **Transactions on Machine Learning Research** via
OpenReview. It is derived from `../technical-report.tex` with all
author-identifying information removed.

## Files
- `main.tex` — the anonymized manuscript (TMLR style, inline references).
- `main.pdf` — the **compiled, verified** 9-page submission PDF (ready to upload).
- `tmlr.sty`, `tmlr.bst`, `fancyhdr.sty`, `math_commands.tex` — the **official TMLR
  style files** (bundled from <https://github.com/JmlrOrg/tmlr-style-file>, BSD),
  so this folder compiles as-is.
- `SUBMISSION-FORM.md` — copy-paste answers for the OpenReview submission form.

## What was anonymized (vs. the public preprint)
- Author name, ORCID, affiliation → `Anonymous authors` (TMLR hides these
  automatically in submission mode).
- GitHub URLs (`github.com/<user>/J-ART`), the live-leaderboard URL, and the
  Zenodo DOIs → removed; §9 now says code/artifacts are in an **anonymized
  repository**, released upon acceptance, and the site URL is withheld.
- Title subtitle "Technical Report (v0.2, preprint)" and the preprint status
  block → removed/neutralized.
- The **AI Assistance Disclosure** section is kept (TMLR requires disclosure of LLM
  use) and contains no identifying information.

## How to compile (self-contained — already verified)
The official TMLR style files are bundled here, so no template hunting is needed.

1. **Overleaf.** Create a new project → *Upload Project* → upload **this whole
   folder** (a zip of `tmlr-submission/`). Set the compiler to **pdfLaTeX** and
   compile `main.tex`. (Or just upload/submit the bundled `main.pdf` directly.)
2. **Local.** `pdflatex main.tex` (run twice for references). Already confirmed to
   produce a clean 9-page `main.pdf` with numbered citations.

Submission mode (the default, `\usepackage{tmlr}`) prints "Under review as a
submission to TMLR" and hides authors. **For the camera-ready only**, switch to
`\usepackage[accepted]{tmlr}` and restore the author block + code/Zenodo links.

**Citations.** `tmlr.sty` loads natbib (author-year); since this paper's prose uses
numbered references, `main.tex` sets `\setcitestyle{numbers,square}` and uses
`\citep{...}`, rendering "[n]". If you prefer TMLR's default author-year style for
the camera-ready, remove that line and convert the inline `thebibliography` to a
`.bib` file.

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
