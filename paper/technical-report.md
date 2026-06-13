# J-ART: A Japanese Adversarial Red-Team Framework for Application-Layer LLM Security and Cost-Efficiency

**Technical Report (v0.1, preprint)**

Author: Takayuki Hirose — ORCID: [0009-0005-6735-1862](https://orcid.org/0009-0005-6735-1862)
Affiliation: Independent Researcher
Project / code: <https://github.com/takker-hero-se/J-ART>
Live leaderboard: <https://takker-hero-se.github.io/J-ART/>
DOI (concept): [10.5281/zenodo.20676879](https://doi.org/10.5281/zenodo.20676879) — v0.1.0: 10.5281/zenodo.20676880
License: report text CC-BY-4.0; code MIT.

> **Status.** This is a preliminary technical report / preprint describing a
> proof-of-concept framework and exploratory findings. It is **not** an official
> safety evaluation of any vendor's model. Numbers are run-time snapshots and
> are subject to the limitations in §7. References (§10) are indicative and
> their bibliographic details should be verified before formal submission.

---

## Abstract

Most open red-teaming and jailbreak benchmarks for large language models (LLMs)
are English-centric and evaluate *bare models*. We present **J-ART** (Japanese
Adversarial Red-Team framework), an open, reproducible harness that (i) evaluates
the **application-structure layer** — `model × system-prompt strength × guardrail
× retrieval (RAG)` — rather than bare models; (ii) applies **Japanese-specific
obfuscation transforms** (gyaru-moji character substitution, vertical/newline
splitting, keigo "polite-coercion" framing, double-talk false premises, Base64,
and leet/zero-width smuggling) that defeat naïve keyword filters; (iii) grounds
attacks in **MITRE ATLAS** (10 inference-time techniques); and (iv) reports a
**cost-efficiency** metric alongside a defense rate with **Wilson 95% confidence
intervals**. Attacks use *harmless proxy markers* (a fictitious canary and
benign output markers) so the framework contains **no weaponizable content**, and
the malicious "core" of each attack is masked in all published artifacts.

Across 18–21 application configurations and 11 attacks × 7 transforms, we find
that **application-layer defenses dominate raw model capability** (a flagship
model with no system prompt or guardrail was breached more often than a small,
cheap model behind a hardened prompt and a keyword guardrail), that a dedicated
**input classifier (Llama Guard) eliminated all observed breaches** for a weak
configuration at lower net cost, and that a simple **normalizing filter** defeats
the obfuscation transforms that a naïve keyword filter misses. We also document
**large run-to-run variance** for identical configurations served via a model
router (one configuration moved from 58 breaches to 0 breaches between two runs),
which we argue makes single-sample leaderboards unreliable and motivates the
statistical treatment we adopt.

### 概要（日本語）

LLM のレッドチーミング/ジェイルブレイク評価はほぼ英語中心で、かつ「素のモデル」を
対象とする。本稿は **J-ART**（日本語敵対的レッドチーム評価ハーネス）を提案する。
特徴は、(1)「モデル × システムプロンプト強度 × ガードレール × RAG」という
**アプリケーション構造層**を評価すること、(2) ギャル文字・縦書き改行・慇懃無礼・
二枚舌・Base64・leet/ゼロ幅密輸といった**日本語特有の難読化変形**でキーワード検閲を
突破すること、(3) 攻撃を **MITRE ATLAS**（推論時10技術）に対応づけること、
(4) 防御率に **Wilson 95%信頼区間**を付し、**コスト効率**指標を併記すること、である。
攻撃は無害なプロキシ（架空カナリア・無害マーカー）で構成され、危険物を一切含まず、
悪意あるコアは公開物上で常にマスクされる。実験では、**アプリ層の防御がモデル素性を
上回る**こと、**専用入力分類器（Llama Guard）が弱構成の突破を全て遮断**したこと、
**正規化フィルタが難読化を無効化**することを示す。さらに、同一構成でも実行間で大きく
ばらつく（ある構成が58突破→0突破に変動）ことを記録し、単一サンプルのリーダーボードが
信頼できないこと、統計的処理が必要であることを論じる。

---

## 1. Introduction

Public LLM red-teaming tooling (e.g., garak) and jailbreak benchmarks
(e.g., HarmBench, JailbreakBench) are predominantly English. Multilingual safety
work has shown that *translating* prompts into low-resource languages can bypass
safety training, but **language-specific obfuscation** — exploiting a language's
own scripts, typography, and register — remains comparatively underexplored, and
Japanese in particular offers a rich obfuscation surface (multiple scripts,
full-width/zero-width characters, vertical writing, and highly conventionalized
polite registers).

Two further gaps motivate J-ART:

1. **Bare-model vs. deployed-system evaluation.** Practitioners do not deploy
   bare models; they deploy a model *plus* a system prompt, *plus* one or more
   guardrails, often *plus* retrieval. The security-relevant unit is the
   **application configuration**, not the model. J-ART evaluates configurations.

2. **Security *and* cost, jointly.** Defenses cost tokens (LLM-as-judge
   guardrails) or latency. We report a **cost-efficiency** score so that
   "cheapest sufficiently-safe configuration" is directly readable.

Our contributions are: (a) a Japanese obfuscation transform suite; (b) an
application-layer, MITRE-ATLAS-grounded evaluation harness with a safe
proxy-marker methodology; (c) a guardrail comparison including a normalizing
filter and a model-based classifier; (d) a statistically-reported leaderboard
(Wilson CIs, optional repeated trials) with a cost-efficiency metric; and
(e) an empirical observation of large router-induced run-to-run variance.

## 2. Related Work

J-ART sits at the intersection of six lines of work. We summarize each and then
position J-ART against them in Table 1.

**Adversarial red-teaming tooling.** garak [2] scans a *model* with a library of
known vulnerability probes. Such scanners target the model in isolation; J-ART
instead treats the deployed *application configuration* — model × system prompt ×
guardrail × RAG — as the unit under test.

**Jailbreak and harmful-behavior benchmarks.** AdvBench / GCG [11], Jailbroken
[12], HarmBench [3], JailbreakBench [4], and the in-the-wild "Do Anything Now"
corpus [13] standardize *which* harmful behaviors to elicit and *how* to score
them, predominantly in English and at the model layer. J-ART reuses the
*evaluation-harness* idea but replaces harmful elicitation with a safe
proxy-marker objective (§3.4) so the suite can be released publicly.

**Automated attack generation.** PAIR [6] and TAP [7] iteratively optimize
jailbreak prompts against a target. J-ART deliberately uses a *fixed, auditable*
transform suite rather than an optimizer, trading attack strength for
reproducibility and safe public disclosure.

**Multilingual and low-resource safety.** Deng et al. [14] and Yong et al. [5]
show that alignment degrades when prompts are *translated* into low-resource
languages, and Wang et al. [15] examine cross-lingual safety generalization.
These study *translation across* languages; J-ART studies *intra-language
orthographic obfuscation* specific to Japanese — gyaru-moji glyph substitution,
vertical/newline writing, keigo framing, and kana/kanji encoding — which persists
even though Japanese is itself high-resource.

**Prompt injection.** Perez & Ribeiro [16] introduced goal-hijacking and
prompt-leaking; Greshake et al. [8] formalized *indirect* injection via retrieved
content; Liu et al. [17] provide a benchmark for LLM-integrated applications.
J-ART evaluates these threats as a function of the *application configuration*
(system prompt × guardrail × RAG) rather than the bare model.

**Guardrails and input classifiers.** Llama Guard [9] and its successors, NeMo
Guardrails [18], and the OpenAI Moderation API [19] provide model- or rule-based
filtering. J-ART treats the guardrail as a *swappable configuration variable* and
measures the marginal defense each adds, including a deterministic *normalizing*
filter we show defeats the obfuscations a naive keyword filter misses (§4.4).

**LLM-as-judge validation.** Zheng et al. [20] and the survey of Gu et al. [21]
document the agreement and systematic biases of LLM judges. J-ART avoids an LLM
judge for its *primary* outcome, using a deterministic canary/marker check (§3.5)
so judge variance does not enter the headline metric.

**Japanese NLP resources and taxonomies.** General Japanese benchmarks such as
JGLUE [22] cover natural-language understanding, but to our knowledge no open,
reproducible *adversarial-safety* benchmark targets Japanese-specific obfuscation
— the gap J-ART addresses. We map attacks to MITRE ATLAS [1] and cross-reference
the OWASP Top 10 for LLM Applications [10].

**Table 1. Positioning of J-ART relative to representative prior work.**

| Work | Language focus | Unit of evaluation | Obfuscation surface | Cost axis | Swappable guardrail/RAG | Safe public release |
|---|---|---|---|---|---|---|
| garak [2] | English | Model | Probe library | No | No | Yes |
| HarmBench / JailbreakBench [3,4] | English | Model | Suffixes / templates | No | No | Yes |
| PAIR / TAP [6,7] | English | Model | Optimized prompts | No | No | Partial |
| Multilingual jailbreaks [5,14,15] | Low-resource (translation) | Model | Cross-lingual translation | No | No | Yes |
| Llama Guard / NeMo [9,18] | English-centric | Classifier | — | No | n/a | Yes |
| **J-ART (this work)** | **Japanese (intra-language)** | **App config (model×prompt×guard×RAG)** | **gyaru / vertical / keigo / encoding** | **Yes (cospa)** | **Yes** | **Yes (proxy markers)** |

In short, J-ART is distinguished by combining a *Japanese intra-language
obfuscation* surface, an *application-configuration* unit of evaluation, a
*cost-efficiency* axis, and a *safe proxy-marker* methodology in a single
reproducible harness. *(Bibliographic details are indicative; see §10.)*

## 3. Methodology

### 3.1 Application-structure layer

Each evaluated **target** is a configuration:
`provider/model × prompt_strength ∈ {naked(low), hardened(high)} × guardrail ∈
{none, keyword, regex, llm, llamaguard} × rag ∈ {true,false}`. A simplified RAG
context (benign corporate documents, optionally poisoned for indirect-injection
attacks) and a system prompt containing a secret **canary** are assembled per
trial.

### 3.2 Japanese obfuscation transforms

Each base attack is rendered through one of seven transforms: `baseline`
(none), `polite_business` (keigo authority framing), `vertical_newline`
(one-character-per-line vertical writing), `gyaru` (gyaru-moji glyph
substitution + zero-width spaces), `double_tongue` (false sandbox/authorization
premise), `base64_wrap` (Base64-encoded instruction), and `leet_smuggle` (leet
symbol substitution + zero-width spaces). Transforms are designed to preserve
human legibility while breaking substring-matching filters.

We distinguish two classes (Table 2). **Japanese-specific** transforms exploit
properties of the Japanese writing system or register and have no direct
equivalent in, say, English red-teaming: `gyaru` (kana glyph substitution),
`vertical_newline` (traditional vertical writing), and `polite_business` /
`double_tongue` (keigo-based authority and in-group framing). **Language-agnostic**
transforms — `base64_wrap` and `leet_smuggle` (and the `baseline` control) —
apply to any language and are included as a comparison baseline so that the
marginal effect of the Japanese-specific surface can be isolated. This separation
also clarifies which findings are expected to generalize beyond Japanese (the
language-agnostic encodings) and which probe a genuinely under-studied,
language-specific attack surface.

**Table 2. Classification of obfuscation transforms.**

| Class | Transforms | Exploits |
|---|---|---|
| Japanese-specific | `gyaru`, `vertical_newline`, `polite_business`, `double_tongue` | Kana glyph variants, vertical writing, keigo authority/in-group framing |
| Language-agnostic | `base64_wrap`, `leet_smuggle` (+ `baseline` control) | Encoding / symbol substitution applicable to any language |

### 3.3 Attack suite and MITRE ATLAS mapping

Eleven attacks cover ten inference-time ATLAS techniques: Direct/Indirect Prompt
Injection (AML.T0051.000/.001), LLM Jailbreak (AML.T0054), LLM Data Leakage
(AML.T0057), LLM Prompt Self-Replication (AML.T0061), Trusted-Output/Citations
manipulation (AML.T0067.000), LLM Prompt Obfuscation (AML.T0068), System-Prompt
discovery (AML.T0069.002), RAG Poisoning (AML.T0070), and False RAG Entry
Injection (AML.T0071). Vectors are `user` (direct) or `rag` (indirect).

### 3.4 Harmless proxy markers and safety-by-construction

To avoid producing weaponizable content, attacks target **harmless proxies**: a
fictitious canary passphrase embedded in the system prompt (data-leakage
attacks) and benign string markers `[JART-PWNED]` / `[JART-HIJACKED]`
(injection / control-hijack attacks). The malicious instruction **core** of each
attack is defined in code, kept out of configuration files, and **masked** (the
core is replaced by a redaction placeholder) in `results.json` and the public
site; only the obfuscation *framework* is shown, so developers can study the
structure without a usable recipe. A defense-in-depth client-side mask is also
applied at render time.

### 3.5 Deterministic judge

A breach is declared by exact membership: the canary in the response
(`secret_leak`), or the marker in the response (`marker_injection` /
`marker_hijack`). This judge is reproducible and cheap but conservative (it can
miss semantically-equivalent leaks); see §7.

### 3.6 Guardrails

Five guardrail settings are compared: **none**; **keyword** (banned-substring
match — fast, weak to obfuscation); **regex** (a *normalizing* filter that strips
zero-width characters, reverses leet substitutions, folds whitespace, and
Base64-decodes long tokens *before* keyword matching — deterministic, zero extra
API cost); **llm** (the target model self-moderates input, and additionally
screens output); and **llamaguard** (a dedicated safety-classification model —
Llama Guard 4 via a model router — classifies the input as attack/benign, with a
graceful fallback on failure).

### 3.7 Statistical treatment

Each model's defense rate is reported with a **Wilson 95% confidence interval**
computed over its trial count. Optionally, each cell `(target, attack,
transform)` is repeated `N` times (`JART_TRIALS`, default 1); details aggregate
per cell with a per-cell breach rate, while summary statistics and CIs use the
trial-level sample. In simulation mode each repeated trial is an independent
Bernoulli draw, which (as a sanity check) narrows the CI as `N` grows
(e.g., interval width 15.1 → 7.5 points from `N`=1 to `N`=3 for one configuration).

### 3.8 Cost-efficiency metric

We report **cospa = defense_rate(%) ÷ cost_per_million_tokens(USD)** (the
per-million cost is clamped at a 0.01 USD floor to avoid divergence). This
surfaces configurations that are both safe and cheap.

### 3.9 Execution

Trials are independent and are executed with bounded concurrency
(`ThreadPoolExecutor`, default 8 workers) under per-request timeouts and
exponential-backoff retries. Determinism of the simulation does not depend on
execution order. Targets whose API key is absent fall back to a deterministic
simulation so a partial key set never aborts the run.

## 4. Results

We summarize two live runs (run A: 18 configurations, 1,386 cells; run B: 21
configurations, 1,617 cells), one trial per cell.

### 4.1 Overall

Breach rates were low in aggregate (run A: 108/1,386 = 7.8%; run B: 36/1,617 =
2.2%) and concentrated in **weak configurations** (naked, low-strength models),
while hardened-prompt-plus-guardrail configurations defended at or near 100%.

### 4.2 Application-layer defense vs. model capability

In run A, a flagship model with **no system prompt and no guardrail** was
breached 10 times (87.0% defense), whereas a small, inexpensive model behind a
**hardened prompt + keyword guardrail** defended at 96%+. This is suggestive of
the practical thesis that *how the application is configured matters more than
which model is used* — but the two configurations differ in **both** model and
application layer, so the comparison alone is confounded.

To isolate the configuration effect we add a **balanced ablation** that holds the
*model fixed* and crosses {naked, hardened} prompt × {none, keyword, regex, llm,
llamaguard} guardrail, reporting each config's defense-rate difference from the
naked baseline with a Newcombe 95% CI (`experiments/`, `wilson_diff_ci`). The
configuration-dominance claim is stated only to the extent this within-model
ablation supports it on labeled live data; the definitive effect sizes are part
of the live campaign described in §9.

### 4.3 Run-to-run variance (a primary result)

The configuration "Llama 4 Scout / naked" produced **58 breaches (24.7% defense)**
in run A and **0 breaches (100% defense)** in run B. We initially attributed this
to execution time alone; we **retract that specific attribution**, because the
configuration *set* also changed between the two runs (18→21 targets), so the two
snapshots are not a controlled comparison. The proper test is a **controlled
variance experiment**: freeze a single configuration set and re-run it *K* times
(default K=5) with everything else held constant, reporting per-config defense
rates and the across-run range/variance with CIs (`experiments/analyze_variance.py`).
The qualitative point stands and motivates the design — **single-sample LLM
leaderboards should not be read as reproducible**, and defense rates must carry
confidence intervals and, ideally, repeated trials — but the quantified variance
is reported from the controlled experiment in the live campaign (§9), not from the
two non-matched snapshots. We treat this variance as a result, not noise to be
hidden.

### 4.4 Guardrail comparison

In run B, "GPT-4o-mini / naked" was breached 14 times (81.8% defense,
CI[71.8–88.8]); the **same model behind a Llama-Guard input classifier** was
breached **0 times** (100% defense, CI[95.2–100]) at lower net cost, because
blocked inputs skip the main model call. The **normalizing regex filter**, in
unit tests, deterministically neutralizes the vertical-newline, leet, Base64,
and gyaru transforms that the keyword filter misses, at zero additional API
cost; in run B its weak-model baselines did not breach, so its live preventive
effect was not separable in that snapshot (see §7).

### 4.5 Attack and transform effectiveness

In run A, the most effective attacks were Trusted-Output/Citations manipulation,
False RAG Entry Injection, and indirect RAG exfiltration; the most effective
transforms were vertical-newline, baseline, and polite-business, while
**Base64** was least effective (models frequently declined to act on encoded
instructions). The newly-added ATLAS techniques accounted for a large share of
breaches, indicating the expanded taxonomy contributes signal.

## 5. The Leaderboard Artifact

The harness emits `results.json` and a self-contained static site (sortable
leaderboard, per-configuration attack logs with masked prompts, JP/EN UI with
environment-based auto-selection, per-model defense-rate CIs, and per-cell breach
rates). The site is continuously deployed.

## 6. Ethics and Responsible Disclosure

### 6.1 Safety by construction

J-ART is designed to be safe by construction. (1) Attacks target a **fictitious
canary** and **benign markers**, never real harmful capabilities; no
weaponizable content exists in the code, the data, or the published site.
(2) The malicious instruction **core** is masked in all artifacts; only the
obfuscation framework is shown. (3) Models are referred to for research
comparison only; results are run-time snapshots, not certifications. The
intended use is to help developers harden their *own* deployments.

### 6.2 A reusable disclosure pattern for safety benchmarks

We argue the design above is a transferable *pattern* for publishing adversarial
safety benchmarks without releasing operational attacks, and we state it
generally so other languages and threat models can reuse it:

1. **Harmless proxy objective.** Replace any genuinely harmful target with a
   neutral, machine-checkable success signal — here a fictitious canary string
   and benign injection/hijack markers — so a "breach" is *measurable* but
   *inert*. The objective, not the wrapper, is what makes a suite safe to release.
2. **Core/framework split with masking.** Separate each attack into a reusable
   *obfuscation framework* (publishable; it carries the research signal) and an
   *operational core* (the specific malicious instruction). Publish the framework,
   mask the core in every artifact (`results.json`, the site, logs), and keep the
   harmless cores defined only in code, never in public data.
3. **Determinism without weaponization.** Provide a deterministic offline mode so
   results are reproducible from the repository alone, without re-running live
   attacks or distributing a working exploit corpus.
4. **Audit the masking, not just assert it.** A unit-test invariant checks that no
   core (raw or obfuscated) ever reaches a published artifact (see
   `tests/test_guardrails.py`), turning "we masked it" into a checked property.

This pattern lets the *methodology* and *aggregate findings* be fully open while
the *attack payloads* stay withheld — the disclosure posture we recommend for
language-specific red-team datasets generally.

### 6.3 Governance crosswalk

To help practitioners connect J-ART's coverage to the controls they are already
accountable for, Table 3 cross-references each evaluated capability to MITRE
ATLAS, the OWASP Top 10 for LLM Applications (2025), the NIST AI Risk Management
Framework, the EU AI Act, and Japan's AI governance guidance. The mapping is
**informational, not a compliance claim or legal advice**; standards evolve and
applicability depends on each deployment's risk classification.

**Table 3. Governance crosswalk (informational).**

| J-ART capability (ATLAS) | OWASP LLM Top 10 (2025) | NIST AI RMF | EU AI Act | Japan guidance |
|---|---|---|---|---|
| Direct / indirect prompt injection, jailbreak (T0051, T0054) | LLM01 Prompt Injection | MEASURE 2.7 (security & resilience) | Art. 15 (robustness/cybersecurity); Art. 55 (adversarial testing of systemic-risk GPAI) | AISI red-teaming guide; AI Guidelines for Business |
| Canary / data leakage (T0057) | LLM02 Sensitive Information Disclosure | MEASURE 2.7; MAP 5.1 | Art. 15; Art. 10 (data governance) | AI Guidelines for Business (safety/security) |
| System-prompt discovery (T0069.002) | LLM07 System Prompt Leakage | MEASURE 2.7 | Art. 15 | AISI red-teaming guide |
| RAG poisoning / false RAG entry (T0070, T0071) | LLM08 Vector & Embedding Weaknesses; LLM01 | MEASURE 2.7; MANAGE 2.2 | Art. 15; Art. 10 | AISI red-teaming guide |
| Trusted-output / citation manipulation (T0067.000) | LLM09 Misinformation; LLM05 Improper Output Handling | MEASURE 2.6 (safety) | Art. 50 (transparency) | AI Guidelines for Business |
| Prompt obfuscation / self-replication (T0068, T0061) | LLM01 | MEASURE 2.7 | Art. 55 | AISI red-teaming guide |

Operationally, J-ART is best understood as a **MEASURE**-stage activity in the
NIST AI RMF (recurring adversarial measurement of a deployed configuration) whose
outputs feed an organization's **MANAGE** decisions (which configuration to ship).

## 7. Limitations

- **Proxy markers, not harm:** we measure instruction-violation / leakage proxies
  rather than real-world harm.
- **Deterministic judge:** the judge matches the canary/marker exactly *and*
  after light normalization (case-folding, whitespace/zero-width removal), so a
  reformatted echo (e.g. a vertically split or spaced canary) is now counted as a
  breach (see `tests/test_guardrails.py`). It still cannot detect *semantic* or
  paraphrased leakage, so reported defense rates are an **upper bound**;
  quantifying the residual false-negative rate via a human-validated LLM-judge is
  future work.
- **Single-turn:** multi-turn / crescendo attacks are not yet modeled.
- **Sample size:** a handcrafted suite (11 attacks × 7 transforms); default
  `N`=1 per cell.
- **Provider non-determinism / router variance:** see §4.3; results are
  snapshots and depend on routing and model versions at run time.
- **Cost attribution:** guardrail tokens are now priced at the *guardrail
  model's* own rate (the classifier `JART_GUARD_MODEL` for `llamaguard`; the
  target model itself for the `llm` guardrail, which it genuinely calls), reported
  separately from target-model tokens. Remaining approximation: token *counts* in
  simulation mode are estimated, and provider-side overhead (system-prompt
  caching, tool tokens) is not modeled.
- **Simulation mode** is a deterministic stand-in for missing keys and must not
  be read as empirical model behavior.

## 8. Future Work

LLM-judge with human-validated agreement; multi-turn and adaptive (PAIR/TAP-style)
attacks; larger and partially human-curated attack sets; additional ATLAS
techniques (cost-exhaustion, model extraction); per-provider concurrency and
incremental caching with longitudinal trend tracking; and dropping simulation
mode for a purely empirical, repeated-trial statistical report.

## 9. Reproducibility

Code, configuration, and the deployment workflow are public. The harness is
deterministic in simulation mode; live results depend on provider routing and
model versions at run time and should be reported with the run date and model
identifiers. See the repository for exact model identifiers and pricing used.

Each cell carries provenance labels — `mode` (`LIVE`/`MOCK`), `api_error`, the
resolved model, and a `price_per_million` snapshot — and simulated cells are
excluded from the live aggregates (§4). The reviewer-response experiments for
§4.2 (balanced ablation) and §4.3 (controlled variance) are scripted under
`experiments/` with their statistics (`wilson_diff_ci`) and a cost estimate; the
**labeled live campaign** that fills in the definitive numbers is a single
repeated, fully-labeled run of that scaffolding.

## 10. References (indicative — verify bibliographic details before submission)

1. MITRE ATLAS — Adversarial Threat Landscape for Artificial-Intelligence
   Systems. atlas.mitre.org
2. Derczynski et al. garak: A Framework for Security Probing Large Language
   Models (NVIDIA, 2024).
3. Mazeika et al. HarmBench: A Standardized Evaluation Framework for Automated
   Red Teaming and Robust Refusal (2024).
4. Chao et al. JailbreakBench: An Open Robustness Benchmark for Jailbreaking
   Large Language Models (2024).
5. Yong, Menghini, Bach. Low-Resource Languages Jailbreak GPT-4 (2023).
6. Chao et al. Jailbreaking Black-Box LLMs in Twenty Queries (PAIR, 2023).
7. Mehrotra et al. Tree of Attacks: Jailbreaking Black-Box LLMs Automatically
   (TAP, 2024).
8. Greshake et al. Not What You've Signed Up For: Compromising Real-World
   LLM-Integrated Applications with Indirect Prompt Injection (2023).
9. Inan et al. Llama Guard: LLM-Based Input-Output Safeguard for
   Human-AI Conversations (Meta, 2023).
10. OWASP Top 10 for Large Language Model Applications.
11. Zou et al. Universal and Transferable Adversarial Attacks on Aligned
    Language Models (AdvBench / GCG, 2023).
12. Wei, Haghtalab, Steinhardt. Jailbroken: How Does LLM Safety Training Fail?
    (2023).
13. Shen et al. "Do Anything Now": Characterizing and Evaluating In-the-Wild
    Jailbreak Prompts on Large Language Models (2024).
14. Deng et al. Multilingual Jailbreak Challenges in Large Language Models
    (2024).
15. Wang et al. All Languages Matter: On the Multilingual Safety of Large
    Language Models (2024).
16. Perez & Ribeiro. Ignore Previous Prompt: Attack Techniques for Language
    Models (2022).
17. Liu et al. Prompt Injection Attack against LLM-Integrated Applications
    (2024).
18. Rebedea et al. NeMo Guardrails: A Toolkit for Controllable and Safe LLM
    Applications with Programmable Rails (2023).
19. Markov et al. A Holistic Approach to Undesired Content Detection in the
    Real World (OpenAI Moderation, 2023).
20. Zheng et al. Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena (2023).
21. Gu et al. A Survey on LLM-as-a-Judge (2024).
22. Kurihara et al. JGLUE: Japanese General Language Understanding Evaluation
    (2022).
23. NIST. AI Risk Management Framework (AI RMF 1.0), NIST AI 100-1 (2023).
24. NIST. Artificial Intelligence Risk Management Framework: Generative AI
    Profile, NIST AI 600-1 (2024).
25. European Union. Regulation (EU) 2024/1689 (Artificial Intelligence Act),
    Official Journal of the EU (2024).
26. METI / MIC (Japan). AI Guidelines for Business (AI事業者ガイドライン),
    Ver. 1.0 (2024).
27. Japan AI Safety Institute (AISI). Guide to Red Teaming Methodology on AI
    Safety (2024).

## Citation

If you use J-ART, please cite the archived release (see `CITATION.cff` /
`.zenodo.json` in the repository; a DOI is minted on first Zenodo release).
