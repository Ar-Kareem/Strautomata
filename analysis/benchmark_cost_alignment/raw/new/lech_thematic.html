# LLM Thematic Generalization Benchmark V2

This benchmark tests whether large language models can infer a **specific latent theme** from a few examples, use anti-examples to reject the broader but wrong pattern, and then identify the **one true match** among close distractors.

Each item gives the model:
- **3 positive examples**
- **3 anti-examples** that fit a broader or adjacent pattern but not the exact one
- **8 candidates**, with exactly **1** hidden true match

Models score all 8 candidates. We then measure whether the correct candidate is ranked first, and how highly it tends to be ranked overall.

V2 uses **1,247 validated prompts** and adds stricter ambiguity filtering plus harder evaluation slices. The previous published release is being archived as V1.

Current V2 snapshot:
- **703**-item cross-family hard subset: at least two distinct non-suppressed full-coverage model buckets miss
- **881**-item conservative hard subset: at least one non-suppressed full-coverage model misses
- **1,247** validated prompts
- **366** items solved by every non-suppressed full-coverage model
- **11** items solved by no non-suppressed full-coverage model

---

## Headline Result: Cross-Family Hard Subset

![Cross-family hard subset inverse-rank leaderboard](images/04_model_bar_correct_rank_hard_subset_two_plus_wrong.png)

This is the main result.

The chart uses **inverse-rank score**, a higher-is-better transformation of the average rank assigned to the correct answer. It is easier to interpret than raw average rank and avoids the old problem where a random model would sit around the middle of the scale.

The subset contains **703** items where at least **two distinct non-suppressed full-coverage model buckets** miss the item. A case does not enter this subset just because two nearby variants from the same family fail; it needs broader model disagreement.

The table below includes every non-suppressed full-coverage model on this subset.

### Cross-family hard-subset leaderboard

| Rank | Model | Top-1 Accuracy | Inverse-Rank Score | Cases |
|---:|---|---:|---:|---:|
| 1 | Claude Opus 4.6 (high reasoning) | 90.0% | 80.6 | 703 |
| 2 | GPT-5.4 (xhigh reasoning) | 90.9% | 80.0 | 703 |
| 3 | Gemini 3.1 Pro Preview | 91.5% | 79.4 | 703 |
| 4 | GPT-5.4 (high reasoning) | 88.5% | 77.4 | 703 |
| 5 | Claude Sonnet 4.6 (high reasoning) | 88.5% | 76.3 | 703 |
| 6 | GPT-5.4 (medium reasoning) | 88.3% | 75.2 | 703 |
| 7 | Claude Opus 4.7 (high reasoning) | 86.8% | 72.8 | 703 |
| 8 | GLM-5.1 | 85.9% | 69.8 | 703 |
| 9 | Kimi K2.5 Thinking | 84.8% | 69.4 | 703 |
| 10 | Claude Opus 4.6 (no reasoning) | 84.1% | 68.8 | 703 |
| 11 | Claude Sonnet 4.6 (no reasoning) | 82.5% | 68.5 | 703 |
| 12 | Qwen3.5-397B-A17B | 82.4% | 65.1 | 703 |
| 13 | DeepSeek V3.2 | 81.8% | 65.0 | 703 |
| 14 | Grok 4.20 0309 (Reasoning) | 81.5% | 63.8 | 703 |
| 15 | Gemini 3.1 Flash-Lite Preview | 82.1% | 63.3 | 703 |
| 16 | GPT-5.4 Mini (xhigh reasoning) | 80.8% | 61.7 | 703 |
| 17 | Qwen 3.6 Plus | 81.5% | 59.5 | 703 |
| 18 | ByteDance Seed2.0 Pro | 77.0% | 57.1 | 703 |
| 19 | Gemma 4 31B Reasoning | 76.1% | 53.0 | 703 |
| 20 | Claude Opus 4.7 (no reasoning) | 71.6% | 52.6 | 703 |
| 21 | Qwen3.5-122B-A10B | 76.5% | 51.2 | 703 |
| 22 | Xiaomi MiMo V2 Pro | 68.8% | 45.9 | 703 |
| 23 | Qwen3.5-27B | 71.3% | 45.5 | 703 |
| 24 | Baidu Ernie 5.0 | 65.3% | 41.7 | 703 |
| 25 | Arcee Trinity Large Thinking | 66.1% | 41.6 | 703 |
| 26 | MiniMax-M2.7 | 63.4% | 39.3 | 703 |
| 27 | GPT-5.4 (no reasoning) | 44.0% | 27.1 | 703 |
| 28 | Mistral Large 3 | 34.0% | 23.0 | 703 |
| 29 | Grok 4.20 0309 (Non-Reasoning) | 33.4% | 22.0 | 703 |
| 30 | Mistral Medium 3.1 | 32.3% | 20.3 | 703 |

Main takeaway:
- the top three remain extremely tight: Claude Opus 4.6 (high reasoning), GPT-5.4 (xhigh reasoning), and Gemini 3.1 Pro Preview sit within **1.2 inverse-rank points** of one another
- the top six positions are unchanged from the previous V2 snapshot and remain dominated by Anthropic, OpenAI, and Google reasoning models
- Claude Opus 4.7 lands at **7th** with high reasoning, while Claude Opus 4.7 (no reasoning) lands at **20th** on this 703-case slice
- reasoning still matters a lot: GPT-5.4's `xhigh`, `high`, and `medium` variants all land in the top 6, while GPT-5.4 (no reasoning) drops to 26th
- recent panel additions such as GLM-5.1, Qwen3.5-122B-A10B, Qwen3.5-27B, Arcee Trinity Large Thinking, and MiniMax-M2.7 broaden the middle and lower-middle tiers rather than dislodging the frontier cluster

---

## Model-Behavior Correlation

![Hard subset model correlation heatmap](images/06_models_correlation_hard_subset_two_plus_wrong.png)

This heatmap compares model behavior at the item level on the same hard subset.

Models that tend to score the same prompts similarly cluster together, while more unusual models sit further away from the pack. This is useful because raw leaderboard position is only part of the story: two models can have similar overall scores while making different kinds of mistakes.

---


## Example Benchmark Item

Here is a representative V2-style example:

**Examples**
- a surveyor's leveling rod
- a fishpole microphone boom
- a submarine periscope housing

**Anti-examples**
- a coiled steel measuring tape
- a folding wooden carpenter's rule
- a retractable cord dog leash

**Correct candidate**
- a collapsible stainless steel drinking straw

**Theme**
- physical objects that extend and retract by sliding rigid, nested tubular segments along a single axis

This shows the core idea of the benchmark:
- the model must infer a **narrow mechanism**, not just a broad category like "things that extend"
- the anti-examples are deliberately close enough to tempt a broader but wrong rule
- the correct answer is only obvious if the model identifies the precise latent theme

---

## Method Summary

### 1. Theme generation

Multiple strong LLMs generate candidate themes from random seeds. These themes are meant to be narrow, specific, and checkable rather than broad trivia categories.

### 2. Examples and anti-examples

For each theme, models generate:
- true examples that fit the exact theme
- anti-examples that fit a broader or neighboring pattern but not the exact one

### 3. Double-checking

Generated examples and anti-examples are reviewed by other models. Weak or internally inconsistent items are removed.

### 4. Validation

The benchmark runs explicit validation prompts that ask models to:
- check whether the true candidate matches the stated theme
- infer alternate themes from the examples
- detect cases where the candidate pack is too ambiguous

V2 adds a stricter ambiguity / exclusivity screen here and now publishes both a conservative hard subset and a stricter cross-family hard subset.

### 5. Final pick task

Each benchmark prompt shows:
- 3 examples
- 3 anti-examples
- 8 candidates

Exactly one candidate is the hidden fourth true example. Models score all 8 candidates, and the results are turned into leaderboard metrics.

---

## Updates

- April 16, 2026: Claude Opus 4.7 (high reasoning), Claude Opus 4.7 (no reasoning), GLM-5.1, Qwen3.5-122B-A10B, Qwen3.5-27B, Arcee Trinity Large Thinking, and MiniMax-M2.7 added
- April 8, 2026: Claude Opus 4.6 (high reasoning), GPT-5.4 (high reasoning), GPT-5.4 Mini (xhigh reasoning), Qwen 3.6 Plus, Gemma 4 31B Reasoning, Xiaomi MiMo V2 Pro added
- March 16, 2026: V2



---

## Related Benchmarks

- [Sycophancy Benchmark](https://github.com/lechmazur/sycophancy/)
- [Writing Benchmark](https://github.com/lechmazur/writing/)
- [Translation Benchmark](https://github.com/lechmazur/translation/)
- [PACT: Multi-Round Bargaining Benchmark](https://github.com/lechmazur/pact/)
- [BAZAAR: Auction Market Benchmark](https://github.com/lechmazur/bazaar/)
- [Extended NYT Connections](https://github.com/lechmazur/nyt-connections/)
- [Step Game](https://github.com/lechmazur/step_game/)
- [Elimination Game](https://github.com/lechmazur/elimination_game/)
