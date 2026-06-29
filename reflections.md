## Reflections

**Tradeoffs**

Two-step generation compresses thought length.
Original averaged 25,168 chars, Claude generated 8,357.
Scratchpad prompt helped but did not close the gap.
Combined pipeline improved to 12,747 — still 50% shorter than original.

LLM judge runs on all rows for theatrical, prove-type gets full check.
Majority vote not implemented — single run may produce inconsistent verdicts.

Temperature tuned by observation not systematically.
0.5 was monotone, 0.7 produced variety. No ablation run.

---

**Where I got stuck**

Adaption column normalization took several iterations.
Output had both original and enhanced columns.
Harness kept picking up originals until load function was fixed.

---

**Did Claude and Adaption work well together?**

Partially. Length metrics improved significantly —
response length up 56%, thought length up 52% vs Claude alone.
But Adaption introduced 2 theatrical instances into otherwise clean Claude samples.
The input passed all quality checks. The output did not.
This suggests Adaption can degrade quality even when the source is clean.
The combined pipeline needs a post-enhancement filtering step
before output is usable for training.

Adaption also scored Claude samples at 47th percentile before enhancement —
lower than expected for clean, diverse input.
The scoring methodology is unclear and needs investigation before scaling.

Reasoning consistency failed on 2/5 sampled rows —
thought truncated mid-sentence, response did not follow.
This is a weak training signal regardless of surface quality checks passing.

---

**What another week would look like**

Run combined pipeline output through critique loop as a post-enhancement filter.
Run judge with majority vote across 3 runs to reduce false positives.
Investigate Adaption's percentile scoring on clean inputs.
Fine-tune on a subset and measure a reasoning benchmark
to get a real training signal proxy.
Add semantic duplicate detection using embeddings.

---

**Where Adaption helped**

Blueprint translated diagnosis findings directly into generation rules.
Quality improved from B to A, 33rd to 57.7th percentile on original dataset.
Length metrics improved significantly in combined pipeline.
Confirmed diagnosis findings independently.

---

**Where Adaption fell short**

Cannot fix source diversity — enhancement cannot invent what the source lacks.
Introduced theatrical self-correction into clean Claude samples —
enhancement degraded quality it should have preserved.
Annotation leak wrote internal evaluation strings into completions silently —
invisible without reading the full response.
Percentile scoring on clean input was unexpectedly low — methodology unclear.