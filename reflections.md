### Claude — final run

29/30 samples generated — 30th not attempted due to API credit limit.
All 29 passed critique loop on first or second attempt.
failed_instructions.txt empty.
Zero failure modes across all checks.
Thought and response length balanced — 8,357 vs 8,454 chars.
Only 1 prove-type instruction — deliberate design choice.
Asking models to prove unsolvable problems forces overclaiming.
Avoiding it removes the root cause not just the symptom.

---

### Adaption — final run

Phrase matching passed completely — looked clean on surface checks.
LLM judge found 2 theatrical responses phrase matching missed entirely.
Both involved pre-scripted self-correction —
errors announced before any mathematical evidence motivated them.

2 responses contained "checking full response" mid-sentence.
This is an annotation Adaption writes internally during its own evaluation.
It survived into the final output.
Training on these would teach the model to insert evaluation annotations
into its own reasoning — invisible to anyone not reading the full response.

Phrase matching missed it.
LLM judge at 1,000 chars missed it.
Full response evaluation caught it.

## Reflections

**Tradeoffs**

Two-step generation compresses thought length.
Original averaged 25,168 chars, Claude generated 8,357.
Scratchpad prompt helped but did not close the gap.

LLM judge scoped to prove-type only to control cost.
Non-prove-type instructions go unchecked.

Adaption run on original dataset not Claude samples.
Stronger pipeline would be Claude for diversity, Adaption for quality.
The comparison was more informative for the pilot than a combined pipeline.

Temperature tuned by observation not systematically.
0.5 was monotone, 0.7 produced variety. No ablation run.

---

**Where I got stuck**

Adaption column normalization took several iterations.
Output had both original and enhanced columns.
Harness kept picking up originals until load function was fixed for adaption ai dataset.

---

**What another week would look like**

Feed Claude samples into Adaption as a combined pipeline.
Run judge on all rows not just prove-type.
Fine-tune on a subset and measure a reasoning benchmark to get a real training signal proxy.

---

**Where Adaption helped**

Blueprint translated diagnosis findings directly into generation rules.
Quality improved from B to A, 33rd to 57.7th percentile.
Confirmed diagnosis findings independently.

---

**Where Adaption fell short**

Cannot fix source diversity — enhancement cannot invent what the source data does not have.
Annotation leak wrote internal evaluation strings into completions silently — invisible without reading the full response.