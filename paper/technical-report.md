# J-ART: A Japanese Adversarial Red-Team Framework for Application-Layer LLM Security and Cost-Efficiency

**Technical Report (v0.2, preprint)**

Author: Takayuki Hirose — ORCID: [0009-0005-6735-1862](https://orcid.org/0009-0005-6735-1862)
Affiliation: Independent Researcher
Project / code: <https://github.com/takker-hero-se/J-ART>
Live leaderboard: <https://takker-hero-se.github.io/J-ART/>
DOI (concept): [10.5281/zenodo.20676879](https://doi.org/10.5281/zenodo.20676879) — v0.2.0: 10.5281/zenodo.20687484
License: report text CC-BY-4.0; code MIT.

> **Status.** This is a technical report / preprint describing the framework and
> its live findings. It is **not** an official safety evaluation of any vendor's
> model; reported numbers are run-time snapshots (2026-06-14) subject to the
> limitations in §7, and all "defense rates" are *lexical-leak* upper bounds
> (§3.5). The §4 numbers are reproducible from the committed artifacts
> `experiments/var_run.json` and `experiments/ablation_results.json` (§9).

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

Across 21 application configurations and 11 attacks × 7 transforms (live, K=5
trials per cell), we find that **application-layer defenses dominate raw model
capability** (a naked flagship was breached far more often than a hardened cheap
model). In a
balanced ablation on **three** base models with **cluster-robust** intervals, a
**hardened prompt and the model-based guardrails significantly raise defense on
every model**, while lightweight keyword/regex filters help most where the base
model is weak; the effect scales inversely with the naked baseline (measured
against the naked baseline — the hardened arm saturates, so guardrail-atop-hardened
is out of scope). A simple
**normalizing filter** defeats the obfuscation transforms a naïve keyword filter
misses. We also document **large within-campaign variance**: in a controlled K=5
repeat of a frozen configuration set, **9.6% of cells changed outcome across
identical trials**, which makes single-sample leaderboards unreliable and
motivates the statistical treatment we adopt.

### 概要（日本語）

LLM のレッドチーミング/ジェイルブレイク評価はほぼ英語中心で、かつ「素のモデル」を
対象とする。本稿は **J-ART**（日本語敵対的レッドチーム評価ハーネス）を提案する。
特徴は、(1)「モデル × システムプロンプト強度 × ガードレール × RAG」という
**アプリケーション構造層**を評価すること、(2) ギャル文字・縦書き改行・慇懃無礼・
二枚舌・Base64・leet/ゼロ幅密輸といった**日本語特有の難読化変形**でキーワード検閲を
突破すること、(3) 攻撃を **MITRE ATLAS**（推論時10技術）に対応づけること、
(4) 防御率に **Wilson 95%信頼区間**を付し、**コスト効率**指標を併記すること、である。
攻撃は無害なプロキシ（架空カナリア・無害マーカー）で構成され、危険物を一切含まず、
悪意あるコアは公開物上で常にマスクされる。実験（実LIVE・21構成・各セルK=5反復）では、
**アプリ層の防御がモデル素性を上回る**こと——素のモデルは防御29.6〜86.5%とばらつくが、
**3モデル**の均衡アブレーション（クラスタ頑健CI）で**強プロンプトとモデルベースのガード
レールは全モデルで有意に防御を引き上げ**、軽量なkeyword/regexは素の弱いモデルほど効く
（効果は素の余地に反比例）——、**正規化フィルタが難読化を無効化**することを示す。さらに、
構成を固定したK=5反復で**9.6%のセルが反復間で結果を変える**ことを記録し、単一サンプルの
リーダーボードが信頼できないこと、統計的処理が必要であることを論じる。

---

## 1. Introduction

Public LLM red-teaming tooling (e.g., garak [2]) and jailbreak benchmarks
(e.g., HarmBench [3], JailbreakBench [4]) are predominantly English. Multilingual safety
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

**Encoding and typographic obfuscation.** Encoding-based jailbreaks are
established prior art: CipherChat [28] shows that conversing in ciphers evades
safety alignment, and ArtPrompt [29] uses ASCII-art typography to smuggle banned
words past filters. Our `base64_wrap` and `leet_smuggle` transforms are
**language-agnostic replications of this line**, included as a comparison
baseline, *not* as novel contributions; the novel surface in J-ART is the
**Japanese-script** transforms (`gyaru`, `vertical_newline`, keigo framing),
which exploit the writing system rather than a general encoding (§3.2).

**Prompt injection and application-layer evaluation.** Perez & Ribeiro [16]
introduced goal-hijacking and prompt-leaking; Greshake et al. [8] formalized
*indirect* injection via retrieved content; Liu et al. [17] benchmark
LLM-integrated applications; and AgentDojo [30] is the closest application-layer
evaluation, measuring prompt-injection robustness of tool-using agents. J-ART
differs by holding the *application configuration* (system prompt × guardrail ×
RAG) as the explicit unit of evaluation and crossing it against a
Japanese-obfuscation surface, rather than evaluating an agent's tool-use loop.

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

We distinguish two classes (Table 2). The **novel** surface is the
**Japanese-specific** transforms, which exploit the writing system or register and
have no direct equivalent in English red-teaming: `gyaru` (kana glyph
substitution), `vertical_newline` (traditional vertical writing), and
`polite_business` / `double_tongue` (keigo-based authority and in-group framing).
The **language-agnostic** transforms — `base64_wrap` and `leet_smuggle` (and the
`baseline` control) — are **not novel**: they are replications of the
encoding/typographic jailbreak line (CipherChat [28], ArtPrompt [29]), included
only as a comparison baseline so the *marginal* effect of the Japanese-specific
surface can be isolated and so we can say which findings generalize beyond
Japanese (the encodings) versus probe a genuinely under-studied, language-specific
attack surface (the Japanese-script transforms).

**Table 2. Classification of obfuscation transforms.**

| Class | Transforms | Exploits | Novelty |
|---|---|---|---|
| Japanese-specific | `gyaru`, `vertical_newline`, `polite_business`, `double_tongue` | Kana glyph variants, vertical writing, keigo authority/in-group framing | **Novel surface** |
| Language-agnostic | `base64_wrap`, `leet_smuggle` (+ `baseline` control) | Encoding / symbol substitution applicable to any language | Replication baseline [28,29] |

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

A breach is declared by membership — the canary or marker in the response,
matched exactly *and* after light normalization (§7). This judge is reproducible
and cheap but conservative: it detects a *lexical* leak (the literal token
escaping) and **cannot** detect a semantic or paraphrased leak. We therefore call
the resulting metric a **lexical-leak defense rate**, and every "defense rate" in
this paper is that quantity — an **upper bound** on true safety, not a certificate
of it. Quantifying the residual false-negative rate with a human-validated judge
is future work (§8).

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

The trial-level Wilson interval, however, treats the `K` repeats of a cell as
independent, which they are **not** (the same prompt against the same
configuration). For any *difference* between configurations (the ablation, §4.2),
we therefore report a **cluster-robust bootstrap 95% CI** that resamples whole
*cells* with replacement (`bootstrap_diff_ci`, 3,000 resamples, fixed seed),
so within-cell correlation cannot inflate significance. These intervals are wider
than the trial-level Newcombe ones and are the intervals on which every
significance claim in §4.2/§4.4 rests.

### 3.8 Cost-efficiency metric

We report **cospa = defense_rate(%) ÷ cost_per_million_tokens(USD)** (the
per-million cost is clamped at a 0.01 USD floor to avoid divergence). This
surfaces configurations that are both safe and cheap. cospa is a deliberately
simple screening ratio, not a utility model: its units (defense-% per USD/Mtok)
are not independently meaningful, and the ranking is sensitive to the clamp and to
the price snapshot. We therefore treat cospa only as a *sort key* and present the
underlying **defense-vs-cost trade-off** directly (the safe-and-cheap frontier in
§4.4); a configuration is preferable only if it is Pareto-non-dominated on
(defense, cost). Sensitivity to the clamp affects only sub-$0.01/Mtok
configurations, of which there are none in our fleet.

### 3.9 Execution

Trials are independent and are executed with bounded concurrency
(`ThreadPoolExecutor`, default 8 workers) under per-request timeouts and
exponential-backoff retries. Determinism of the simulation does not depend on
execution order. Targets whose API key is absent fall back to a deterministic
simulation so a partial key set never aborts the run.

## 4. Results

We report a single, fully-labeled **live campaign** (21 configurations × 11
attacks × 7 transforms × **K = 5** independent trials = 8,085 trials), executed
2026-06-14. Every cell is labeled `mode=LIVE` with a price snapshot; the harness
retries on transient errors and labels any cell whose call ultimately failed
(`api_error`). **Exclusion rule:** aggregates are computed over clean trials only
— a trial is excluded iff `api_error=True`, at the trial level (not the whole
cell). After parity re-runs this removes 169 of 8,085 trials, leaving **7,916
clean trials**; the billed API cost over those clean cells (campaign plus the
parity re-runs, which include the expensive Opus flagship) is **≈ $6.0** (gross
$6.07; the small difference is *estimated* tokens charged to rate-limited calls
that were not actually billed). **Claude Opus naked is now fully measured**
(n = 385; an Anthropic top-up enabled parity); **only Gemini-pro remains partial**
(n = 227; persistent per-minute rate limits), and its estimate is treated as
provisional. The exact artifacts backing every number in this section are
committed at `experiments/var_run.json` (campaign) and `experiments/abl_*.json`
(the three same-model ablations: `gpt-4o-mini`, `Llama-4-Scout`, `GPT-4.1`); §9
names which file reproduces each table.

### 4.1 Overall

All "defense rates" below are **lexical-leak** rates (§3.5) — upper bounds on true
safety, reported with **cluster-robust** intervals where a difference is claimed
(§3.7). All evaluated configurations include the simplified RAG context of §3.1;
**"naked" therefore means no system-prompt hardening and no guardrail, not "no
RAG"** (so indirect-injection attacks are in scope even for the naked baselines).
The aggregate breach rate over clean trials was **14.5%** (1,151 / 7,916) and was
**concentrated in weak configurations** — low-capability models with no system
prompt and no guardrail. (One configuration, `gemini-pro`, contributes a
*provisional* n = 227 of defended trials to this pool — see §7; excluding it
raises the aggregate breach rate to 15.0%, leaving the qualitative picture
unchanged.) Every hardened-prompt or guardrailed configuration, on *any* model,
defended in the **91–100%** band, whereas bare ("naked") models ranged from
**29.6% to 86.5%** defense (below).

### 4.2 Application-layer defense vs. model capability

Naked defense depends heavily on the model — a **~57-point spread**:

| Naked model (no prompt, no guardrail) | Defense | 95% CI | n |
|---|---|---|---|
| DeepSeek-V3 | 29.6% | [25.3–34.4] | 385 |
| Llama 4 Scout | 37.9% | [33.2–42.9] | 385 |
| Gemini 2.5 Flash | 49.6% | [44.6–54.6] | 385 |
| gpt-oss-120b | 82.6% | [78.5–86.1] | 385 |
| GPT-4o-mini | 83.9% | [79.9–87.2] | 385 |
| Claude Opus 4.x | 86.5% | [82.7–89.5] | 385 |

(Opus is now fully measured at n = 385 after a parity re-run. An *earlier,
pre-top-up partial measurement* — 89.6% on only 125 surviving trials, not retained
as an artifact — over-estimated this by ~3 points; the committed `var_run.json`
holds the corrected n = 385 figure. See §7.)

We then **isolate the configuration effect from model capability** with a balanced
ablation run on **three** base models spanning the capability range (a weak OSS
model, Llama 4 Scout; a cheap proprietary model, GPT-4o-mini; and a flagship,
GPT-4.1). Each holds the model fixed and crosses {naked, hardened} prompt ×
guardrail; we report each config's difference from that model's naked baseline
with a **cluster-robust bootstrap 95% CI** (3,000 cell-resamples; resampling cells,
not trials, so the within-cell correlation of the ablation's K = 3 repeats does not
inflate significance). Table 3 summarizes the deltas; they are reproduced by
`experiments/analyze_ablation.py`.

**Table 3. Configuration effect (Δ vs. that model's naked baseline; cluster-robust 95% CI).**

| Added defense (low-prompt arm) | Llama-4-Scout (naked 38.1%) | GPT-4o-mini (naked 82.3%) | GPT-4.1 (naked 64.1%) |
|---|---|---|---|
| + keyword filter | **+26.0** [+13.0,+39.4] | +9.1 [−1.3,+19.5] ✗ | +12.5 [−1.5,+26.3] ✗ |
| + normalizing regex | **+45.0** [+33.3,+55.8] | +10.0 [+0.0,+19.9] ✗ | **+23.8** [+11.3,+36.4] |
| + Llama Guard | **+47.2** [+35.9,+58.4] | **+15.6** [+7.4,+24.7] | **+25.1** [+12.6,+37.7] |
| + LLM guardrail | **+59.7** [+50.6,+68.4] | **+17.7** [+10.0,+26.4] | **+35.9** [+26.0,+46.8] |
| hardened prompt (alone) | **+47.2** [+35.5,+58.4] | **+17.7** [+10.0,+26.4] | **+33.3** [+22.9,+44.6] |

Two robust patterns emerge across all three models. (1) A **hardened prompt** and
the **model-based guardrails** (Llama Guard, LLM self-moderation) significantly
raise defense on *every* model (all CIs exclude 0). (2) The effect **scales
inversely with the naked baseline**: on the weak Scout (naked 38%) every guardrail
helps by +26 to +60 points, whereas on GPT-4o-mini (naked 82%, near the ceiling)
the *lightweight* keyword/regex filters are **not** individually significant under
clustering — there is little headroom to recover. So configuration matters most
exactly where the base model is weakest.

The practical thesis — *how the application is configured matters more than which
model is used* — is supported by a clean, fully-measured comparison: a **hardened
cheap model** (GPT-4o-mini hardened ≈ 100%) **out-defends a naked flagship**
(GPT-4.1 naked 64.1%, n = 231) by ~36 points, and likewise out-defends a naked
Opus (86.5%, n = 385). Even at full parity the strongest naked model trails a
hardened cheap one.

### 4.3 Within-campaign trial variance (a primary result)

We replace the earlier confounded two-run comparison with a **controlled
experiment**: within a single campaign, every cell of a frozen configuration set
is sampled **K = 5** times, everything else held constant. Over the **1,577 cells
with all five trials clean** (no `api_error`), **9.6% (152 / 1,577) changed outcome
across the five identical repeats** — the same input against the same configuration
breaching on some trials and defending on others.
The instability concentrates in naked weak models (DeepSeek-V3: 37 unstable cells;
Llama 4 Scout: 32).

For "Llama 4 Scout / naked" — the original cautionary example — of its 77 cells,
**32 (42%) were unstable**: 14 never breached (0/5), 31 always breached (5/5), and
**32 fell in between** (e.g. seven at 2/5, three at 3/5, thirteen at 4/5). A
*single-sample* leaderboard would assign this exact configuration anywhere from 0%
to 100% defense depending on which trial it happened to draw. This is controlled
evidence — free of the configuration-set confound — that **a single sample per
cell is not reproducible**, and that defense rates must carry confidence intervals
over repeated trials. We scope this claim precisely: it is measured *within one
campaign* (K independent API calls per cell), which isolates provider/router
non-determinism. Whether defense rates also drift *across days* is a related but
distinct question; the harness ships an `across_runs` analysis mode for it
(`experiments/analyze_variance.py`), but a multi-day study is left to future work
(§8). We treat this variance as a result, not noise to be hidden.

### 4.4 Guardrail comparison

Across the three ablation models (Table 3), the ordering is consistent: the
**LLM guardrail** and a **hardened prompt** give the largest gains, **Llama Guard**
is next, and the **lightweight keyword/regex** filters help most on weak base
models and little on already-strong ones. Guardrails that block an input **skip
the main model call**, so they can *lower* net cost while raising defense. The
**normalizing regex filter** deterministically neutralizes the vertical-newline,
leet, Base64, and gyaru transforms the keyword filter misses — verified in unit
tests (`tests/test_guardrails.py`) — at zero additional API cost; consistent with
this, on the weak Scout it adds **+45 points** of defense (the largest gain of any
deterministic filter).

**Ceiling caveat.** Marginal guardrail effects are cleanly identifiable only in
the *low-prompt* (naked) arm; in the *hardened* arm the hardened prompt alone
already reaches 100%, so 6 of the 10 ablation cells saturate at the ceiling and
the *additional* contribution of a guardrail on top of a hardened prompt cannot be
separated from this suite. The per-guardrail deltas above are therefore reported
**against the naked baseline**, and should be read as "guardrail-vs-nothing on a
weak prompt," not as marginal effects atop an already-strong prompt. A
less-saturating attack set or a weaker base model would be needed to resolve the
prompt×guardrail interaction.

On the cost-efficiency metric (§3.8), the leaders are **inexpensive OSS models
behind a lightweight guardrail** (gpt-oss-20b + keyword, cospa ≈ 1131; Qwen3-235B
+ LLM guard, cospa ≈ 1109), while a **flagship naked** configuration is worst
(Opus naked, cospa ≈ 6.8, at $12.7 per million tokens) — three orders of magnitude
apart.

### 4.5 Attack and transform effectiveness

Across all clean trials, the most effective **attacks** were Trusted-Output /
Citations manipulation (**31.3%** breach), False RAG Entry Injection (22.0%), and
System-Prompt discovery (19.1%) — RAG-borne and output-trust vectors dominate.
Among **transforms**, the *un-obfuscated* `baseline` was most effective (**22.0%**)
followed by `vertical_newline` (20.0%) and `polite_business` (17.3%), while
**`base64_wrap` was least effective (5.5%)** and `leet_smuggle` next (8.8%):
heavy encoding makes models *refuse or fail to parse* the instruction more often
than it smuggles it past them. This is itself a finding — the most dangerous
Japanese transforms are the *legible* ones (vertical writing, keigo framing), not
the cryptographic ones.

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
accountable for, Table 4 cross-references each evaluated capability to MITRE
ATLAS [1], the OWASP Top 10 for LLM Applications (2025) [10], the NIST AI Risk
Management Framework [23] and its Generative-AI Profile [24], the EU AI Act [25],
and Japan's AI governance guidance — the AI Guidelines for Business [26] and the
AISI red-teaming guide [27]. The mapping is **informational, not a compliance
claim or legal advice**; standards evolve and applicability depends on each
deployment's risk classification.

**Table 4. Governance crosswalk (informational).**

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

*Worked example.* Under **NIST MEASURE 2.7** (AI system security and resilience),
an organization could record a J-ART line item as: *"prompt-injection /
jailbreak resilience (ATLAS T0051/T0054), lexical-leak defense rate
93.5% (Wilson 95% CI [90.6, 95.6] for this single configuration's rate — the
cluster-robust interval applies to *differences* between configurations, §3.7),
n = 385, K = 5, model GPT-4.1-mini + hardened prompt + keyword guardrail,
2026-06-14"*, with a pre-registered sufficiency threshold (e.g. "CI lower bound
≥ 90% for the shipped configuration"). The same row is the
evidence an AISI red-teaming report or an EU AI Act Art. 15 robustness dossier
would cite. This shows the crosswalk is operational, not merely a label.

### 6.4 Dual-use

J-ART is a defensive evaluation harness, but the published transform suite is also
a reusable *attack* wrapper, and we weigh this openly. The uplift it gives an
attacker is low: the Japanese-script transforms are folklore among Japanese
internet users, the encoding transforms are replications of public work
(CipherChat [28], ArtPrompt [29]), and the suite contains no harmful payloads — only the
harmless proxy markers (§3.4). Against this, the defender benefit is concrete: we
release, in the same repository, the **normalizing regex guardrail** that
neutralizes every transform in the suite (verified by unit tests), so the
mitigation ships with the disclosure. On balance we judge open release net-positive
for defenders, consistent with the responsible-disclosure pattern of §6.2.

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
- **Non-random missingness (now mostly resolved):** an earlier campaign left three
  flagship/rate-limited configs partial, and we flagged that the missingness was
  **not random** — rate limits correlate with attack difficulty, so Opus's hardest
  attacks were under-represented. Parity re-runs **confirmed this directly**:
  Opus-naked measured at full **n = 385** defends **86.5%**, vs. the
  survivorship-biased **89.6%** on the n = 125 earlier partial snapshot (not
  retained as an artifact; only the corrected n = 385 figure is committed) — a
  ~3-point over-estimate, exactly as
  predicted. Qwen3-max (n = 374) and Opus (n = 385) are now at parity; **only
  Gemini-pro remains partial** (n = 227; persistent per-minute rate limits that a
  credit top-up cannot raise). Its estimate is treated as provisional, and no
  headline rests on it. Bringing Gemini-pro to parity needs a provider quota
  increase and is left to the camera-ready.
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
excluded from the live aggregates (§4). **Every number in §4 is reproducible from
committed artifacts**, named here:

| Table / claim | Committed artifact |
|---|---|
| §4.1 overall, §4.2 naked-spread table, §4.3 variance, §4.5 transforms | `experiments/var_run.json` |
| §4.2 Table 3 ablation — GPT-4o-mini | `experiments/ablation_results.json` |
| §4.2 Table 3 ablation — Llama-4-Scout | `experiments/abl_scout_results.json` |
| §4.2 Table 3 ablation — GPT-4.1 | `experiments/abl_gpt41_results.json` |
| §4.4 cospa ranking | `experiments/var_run.json` (`summary[].cospa_score`) |

Aggregates and CIs are recomputed by `experiments/analyze_ablation.py` and
`experiments/analyze_variance.py` (cluster-robust intervals via
`bootstrap_diff_ci`). The public leaderboard site is regenerated by a manual or
weekly LIVE CI run; push-triggered CI runs use simulation mode and are labeled as
such, so the site never silently mixes MOCK and LIVE.

## AI Writing Assistance

The author used **Claude Opus 4 (Anthropic)**, accessed via the Claude Code
command-line interface, for writing and editing assistance during the preparation
of this manuscript: (1) drafting and revising prose across three rounds of
reviewer-driven revision; (2) bilingual editing of the Japanese-language abstract
and the parallel Japanese LaTeX version (`technical-report.ja.tex`); and
(3) citation error checking (author attributions, publication years, bibliography
completeness). All AI-generated text was reviewed, corrected where necessary, and
approved by the sole author. The scientific content — experimental design, all
live API evaluations, data collection, statistical computation (Wilson and
cluster-robust intervals), and interpretation — was conducted independently by the
human author without AI generation assistance. **Dual-role note:** Claude Opus 4.x
also appears in this paper as one of the *evaluated* models (§4.2, naked defense
rate 86.5%, n = 385); its role as a writing tool and its role as a research subject
are distinct and both disclosed here. The author takes sole and full responsibility
for all content.

## 10. References

*(All entries are real, canonical works; final venue/year/DOI formatting will be
completed for camera-ready.)*

1. MITRE ATLAS — Adversarial Threat Landscape for Artificial-Intelligence
   Systems. <https://atlas.mitre.org> (accessed 2026-06-14).
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
10. OWASP Top 10 for Large Language Model Applications (2025).
    <https://genai.owasp.org/llm-top-10/> (accessed 2026-06-14).
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
    (2023). arXiv:2306.05499.
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
28. Yuan et al. GPT-4 Is Too Smart To Be Safe: Stealthy Chat with LLMs via
    Cipher (CipherChat, 2023).
29. Jiang et al. ArtPrompt: ASCII Art-based Jailbreak Attacks against Aligned
    LLMs (2024).
30. Debenedetti et al. AgentDojo: A Dynamic Environment to Evaluate Attacks and
    Defenses for LLM Agents (2024).

## Citation

If you use J-ART, please cite the archived release (see `CITATION.cff` /
`.zenodo.json` in the repository; a DOI is minted on first Zenodo release).
