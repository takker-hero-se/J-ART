# Response to Reviewers — J-ART (revision)

Format: **R** = reviewer concern · **A** = author response · **C** = change made.
Severity tags from the editorial decision (2 CRITICAL, several MAJOR/MINOR).

We thank the reviewers. The panel found the contributions and reproducibility
solid but judged the **headline framing** ("configuration dominates model
capability") to outrun the evidence. We have **de-escalated the central claim to
what the data support** and added the missing construct-validity caveats,
citations, and an auditable ATLAS mapping. No reported number changed; the
repositioning is in framing and scope.

---

## CRITICAL

### C1 — "Configuration dominates model" rests on a naked-vs-hardened (defended-vs-undefended) comparison; "naked flagship" is a strawman (Devil's Advocate; echoed by EIC, R3)
- **A:** We agree the phrase over-reached. The defensible, evidence-backed finding
  is that **configuration collapses the large naked spread** (29.6–86.5% → a
  91–100% band on all three ablated models), i.e. model choice matters far less
  *once configured*. We now state explicitly that "naked" is a **zero-defense lower
  bound** (not a deployment baseline), that the gap is "configured vs. unconfigured"
  rather than a like-for-like model contest, and that part of the inverse-scaling is
  a **ceiling artifact**. A deployment-realistic minimal-prompt baseline is named as
  future work.
- **C:** Abstract and §4 ("Application-layer configuration vs. model capability")
  rewritten; "dominate" removed throughout; scope limited to "the three ablated
  models at K=3."

### C2 — The lexical-leak judge cannot separate genuine refusal from marker-suppression; the bias correlates with the treatment (Devil's Advocate; echoed by R1, R3)
- **A:** We accept this as a genuine construct-validity threat and now state it
  prominently. **We ran a preliminary semantic-judge audit** (60 defended cells, an
  LLM judge; manual review found ~4 of 6 flags genuine): the lexical-leak looseness
  is **~7–10 points**, and — importantly — **concentrated in the encoding
  transforms**, because the exact-match, attack-specific judge misses (i) markers
  emitted in leet form (e.g. `[J@RT-PWN3D]`) and (ii) a canary leaked during a
  non-leakage attack. The upper bound is thus now *empirically bounded*, not unknown,
  and we identify the concrete mechanism.
- **C:** §4 + the "Deterministic judge" limitation now report the audit result and
  mechanism; the abstract says rates "cannot fully separate genuine refusal from
  marker-suppression"; M1 caveats that the encoding transforms' low scores are partly
  a judge artifact. Audit tooling committed (`experiments/audit_semantic_judge.py`,
  `audit_results.json`).
- **Remaining:** a human-validated audit and a **stricter judge** (canary-checked
  across all attacks, leet-reversed before matching) that would *lower*
  encoding-transform defense rates — future work. No headline depends on the
  absolute level.

---

## MAJOR

### M1 — The "Japanese-specific" / "hard-to-translate" claim is asserted, not measured (R3; R2; DA)
- **A:** Agree. We now report per-transform rates by class and note the
  Japanese-specific transforms retain more potency (~16%) than the language-agnostic
  encodings (~7%), **but** caution this is partly a *legibility* effect that is not
  strictly Japanese-specific (vertical_newline is typographic; keigo framing overlaps
  with language-agnostic role-play), and that we do **not** isolate the marginal
  effect of the Japanese-specific surface. Claim softened to "a Japanese obfuscation
  surface worth cataloguing," not "Japanese script is more dangerous."
- **C:** §4 transform-effectiveness paragraph rewritten with the class split + caveat.

### M2 — cospa elevates obfuscation-fragile keyword filters (R3; DA)
- **A:** Agree. cospa is now used only behind a **sufficiency gate**: rank only
  configs whose defense-rate CI lower bound clears a user-set floor, then sort by
  cost ("cheapest *sufficiently safe*"); a high cospa from a lightweight keyword
  filter must not be read as obfuscation-robust.
- **C:** §3 cost-metric paragraph updated.

### M3 — Missing key references (R2)
- **A:** Added. Crescendo is now cited where we use the word "crescendo"; many-shot,
  AutoDAN, and Boucher "Bad Characters" (nearest prior art to gyaru/zero-width) added
  and distinguished.
- **C:** Bibliography +4 entries; cited in §2 (encoding) and §7 (single-turn,
  fixed-suite).

### M4 — ATLAS mapping not auditable; version unspecified (R2)
- **A:** Added the matrix access date (2026-06) and made the 9-technique count
  explicit (the two T0051 sub-techniques count as two). All IDs were re-verified
  against the live ATLAS matrix; the non-existent AML.T0071 from the prior draft was
  removed and false-RAG-entry folded into AML.T0070 (RAG Poisoning).
- **C:** §3 attack-suite sentence + governance table updated.

### M5 — Reproducibility artifacts not bundled to reviewers; biased n=125 snapshot not retained (EIC; R1)
- **A:** The anonymized code + the four committed JSON artifacts are provided as
  OpenReview supplementary material (self-contained, author-free). For the biased
  n=125 snapshot: we acknowledge it was not retained; we will commit a per-cell
  before/after table so the ~3-point survivorship correction is auditable rather than
  asserted.
- **C:** Supplementary zip refreshed; §7 wording clarified. (Per-cell snapshot table:
  committed for the next upload.)

---

## MINOR (addressed)
- **Abstract K=5 vs K=3:** abstract now separates the descriptive live K=5 campaign
  from the inferential K=3 ablation. (EIC, R1)
- **152 vs 153 unstable cells:** `analyze_variance.py` now restricts to all-K-clean
  cells and prints **152/1577 (9.6%)**, matching §4. (R1)
- **Within-campaign variance cause:** attribution softened from "router
  non-determinism" to "provider stochasticity (sampling temperature and/or
  routing)"; we note p≈0.5 cells flip often at K=5 by chance. (DA)
- **"No weaponizable content" vs reusable wrapper:** changed to "no weaponizable
  **payloads**"; dual-use paragraph now states the normalizer defends only the
  *fixed published* transforms, not adaptive obfuscation. (R2, R3)
- **Governance worked example:** the 93.5% line now carries an inline qualifier
  (lexical-leak upper bound, harmless single-turn proxy; pair with semantic/human
  evaluation before compliance reliance). Crosswalk caption notes Article refs are
  illustrative of the obligation *area*. (R3, EIC)
- **Single-turn ↔ thesis:** §7 now states the 91–100% band is a single-turn ceiling
  and the configuration-collapse finding is only *hypothesized* for multi-turn. (R3)
- **Attack-strength upper bound:** §7 now notes defense rates are also an upper bound
  w.r.t. attack strength (adaptive PAIR/TAP/AutoDAN/GCG would lower them). (R2)
- **Redundant guardrails atop hardening:** now stated openly (not hidden as "out of
  scope"). (DA)
- **Table 1 "Public":** J-ART marked "On accept." (EIC)

---

## Items requiring new experiments (declared, not fabricated)
1. **Semantic-judge audit** of defended responses (bounds C2). — committed.
2. **Deployment-realistic minimal-prompt baseline** (strengthens C1 beyond
   reframing). — future work.
3. **Retain/commit the n=125 biased snapshot** as a per-cell table (M5). — next upload.

We did **not** fabricate any of these; the revision instead de-escalates the claims
so that none of the paper's current conclusions depends on them.

---

## Round-6 calibration (post re-review)

A second simulated review of the revised manuscript downgraded both prior CRITICALs
to resolved/substantially-resolved and surfaced calibration items, addressed here:

- **cospa "sufficiency gate" was described but not implemented in the harness** (a
  paper-vs-artifact mismatch). Fixed by **accurately rewording**: the gate is now
  stated as a *recommended methodology, not the harness default*; the leaderboard
  reports raw cospa (with CIs) and the practitioner applies the gate. (No false
  claim of an unimplemented feature.)
- **The "~7–10 points" audit figure was over-stated for N=60.** Now reported with
  its binomial CI (6/60, Wilson 95% CI [4.7%, 20.1%]; ~4/6 genuine), framed as an
  *existence proof of single-digit-to-low-double-digit looseness, not a calibrated
  correction*, with the LLM-judge circularity named and the manual adjudication
  committed to `audit_results.json`. We also note the headline configuration-collapse
  result (hardened/guardrail arms) is comparatively unaffected by the
  encoding-localized looseness.
- **M1 "legible beats cryptographic"** softened from "finds" to "*suggests*", with an
  explicit statement that the two explanations are not separated and the surviving
  gap is unquantified (*provisional*).
- **ATLAS auditability:** added a one-line 11-attack→9-technique mapping note (both
  RAG attacks realize T0070; the two PI vectors realize the two T0051 sub-techniques).
- **AutoDAN** disambiguated (Liu et al., ICLR 2024, arXiv:2310.04451).

Remaining (genuinely needs new work, not review-fixable): a deployment-realistic
minimal-prompt baseline (to move C1 from "well-disclosed limitation" to "removed"),
and a powered, human-validated judge audit + stricter-judge re-measurement.
