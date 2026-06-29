## Reflections

**Tradeoffs**

Two-step generation compresses thought length.
Original averaged 25,168 chars, Claude generated 8,357.
Scratchpad prompt helped but did not close the gap.
Combined pipeline improved this to 12,747 — still short of original.

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

**What another week would look like**

Investigate why Adaption scored Claude samples at 47th percentile before enhancement.
Run judge with majority vote across 3 runs to reduce false positives.
Fine-tune on a subset and measure a reasoning benchmark
to get a real training signal proxy.
Add semantic duplicate detection using embeddings.

---

**Where Adaption helped**

Blueprint translated diagnosis findings directly into generation rules.
Quality improved from B to A, 33rd to 57.7th percentile on original dataset.
Combined pipeline improved thought length by 52% and response length by 56%.
Confirmed diagnosis findings independently.

---

**Where Adaption fell short**

Cannot fix source diversity — enhancement cannot invent what the source lacks.
Scored Claude samples at 47th percentile before enhancement —
lower than expected given input quality, needs investigation before scaling.
Annotation leak wrote internal evaluation strings into completions silently —
invisible without reading the full response.