## Results

### Adaption Enhancement

The original dataset was uploaded to Adaption with all three columns mapped:
instruction as prompt, thought as context, response as completion.

Mapping thought as context was a deliberate decision.
The thought column contains the reasoning trace —
the most important signal for this project goal.
Giving Adaption access to it meant enhancements would be
informed by the existing reasoning, not just the surface prompt and answer.

A blueprint was written based directly on the issues found in diagnosis:
- no duplicate instructions
- no overclaiming for unsolvable problems
- no circular reasoning
- no monotone openings
- consistent depth throughout
- self-correction only when a genuine contradiction is found

A 1-shot example was included showing bad vs good response
so Adaption had a concrete target not just abstract rules.

Length was set to Detailed to prevent compression.
Deduplication, reasoning traces, and hallucination mitigation were all enabled.

Adaption evaluated the original dataset at B grade, 33rd percentile.
After enhancement: A grade, 57.7th percentile — 6.7% improvement.

---

### Why compare Claude and Adaption

The core question was not which tool is better.
The question was: what does each approach fix, what does it miss,
and what does that tell us about generation at scale.

Adaption works by enhancing existing data.
It can improve quality of what is already there
but it cannot invent diversity that does not exist in the source.
Starting from 6 unique instructions, Adaption produced 30 unique enhanced versions —
but all 30 are still variations of the same 6 mathematical topics.

Claude generates from scratch.
Given a list of 30 diverse instructions it produces 30 independent samples
with no structural relationship to each other.
This produces genuine diversity but without the quality controls Adaption applies.

Running both and comparing them through the same eval harness
reveals something neither approach shows alone:
- Adaption fixed structural problems but introduced theatrical self-correction
- Claude fixed diversity but compressed reasoning traces
- Neither alone produces the ideal dataset

The comparison also stress-tested the eval harness.
Running identical checks on three structurally different datasets
confirmed which checks are reliable, which are too shallow,
and where an LLM judge catches what phrase matching misses.

---

### Harness results across three datasets

Original dataset:
- 24 duplicate instructions
- 4 overclaiming responses confirmed by LLM judge
- 4 circular reasoning responses confirmed by LLM judge
- 26/30 thoughts and 16/30 responses with monotone openings
- No theatrical self-correction by phrase matching or LLM judge
- No length collapse

Claude generated dataset:
- 0 duplicates across 30 unique instructions
- 0 overclaiming by phrase matching and LLM judge
- 0 circular reasoning
- 0 monotone openings
- 0 theatrical self-correction
- Thought column compressed — avg 5,625 chars vs 25,168 in original
- Response avg shorter — 8,505 vs 11,867

Adaption enhanced dataset:
- 0 duplicates across 30 unique instructions
- 0 overclaiming by phrase matching and LLM judge
- 0 circular reasoning
- 0 monotone openings
- 2 theatrical responses found by LLM judge — missed by phrase matching -- initially LLM was only checking 400 chars but later full response was checked.
- Most consistent response length — std 2,094 vs 5,496 in original
- Thought avg 9,704 — shorter than original but longer than Claude
- 2 responses contained "checking full response" annotation
  suggesting Adaption's internal evaluation process leaked into generated completions
  this would not have been caught without full response LLM evaluation

---

### Key finding

Phrase matching caught 0 theatrical instances across all three datasets.
LLM judge on first 1,000 chars caught 1.
LLM judge on full response caught 3.

This directly validates the decision to run full response evaluation
despite the higher cost.
Truncated evaluation would have missed 2 out of 3 theatrical instances
and given Adaption a clean pass it did not deserve.

The annotation leak in Adaption output is also worth flagging.
It suggests that Adaption's internal review pipeline
writes annotations into the response during evaluation
and those annotations can survive into the final output.
Training on these would teach the model to annotate its own responses
which is not the behavior this dataset is trying to produce.

# Claude generated dataset -- with critique loop : final run
- 29/30 samples generated — stopped at 29 due to API credit limit- 
- failed_instructions.txt empty — no instructions failed all 3 attempts
- 30th instruction not attempted due to API credit limit
- 0 duplicates
- 0 overclaiming
- 0 circular reasoning  
- 0 theatrical self-correction
- 0 monotone openings
- No length collapse
- Thought avg: 8,357 chars — improved from first run (5,625)
  detailed scratchpad prompt produced longer reasoning traces
- Response avg: 8,454 chars
- Thought and response now similar length — more balanced than original
- Only 1 prove-type instruction — deliberate design choice
  avoids forcing model to prove unsolvable problems

# Adaption AI generated dataset -- final run

30 rows, 0 duplicates, 30 unique instructions.
Phrase matching passed completely — 0 overclaiming, 0 theatrical, 0 monotone.
Looked clean on surface checks.

LLM judge on 10 prove-type rows found 2 theatrical responses
that phrase matching missed entirely.
Both involved pre-scripted self-correction —
errors announced before any mathematical evidence motivated them.

More significant: 2 responses contained the string "checking full response"
mid-sentence inside the generated completion.
This is an annotation Adaption writes internally during its own evaluation process.
It survived into the final output.

Training on these responses would teach the model
to insert evaluation annotations into its own reasoning traces —
behavior that has nothing to do with mathematical reasoning
and would be invisible to anyone not reading the full response.

Phrase matching would never catch this.
Truncated LLM evaluation at 1,000 chars missed it.
Full response evaluation caught it.

This is the clearest example in the pilot of why surface evals are not enough
and why the gap between what an eval measures and what actually matters
is worth taking seriously.

# Tradeoffs
Two-step generation compresses thought length.
Original thoughts averaged 25,168 chars, Claude generated averaged 8,357.
Scratchpad prompt helped but did not close the gap.
Single-pass extended thinking would likely do better but wasn't explored.

LLM judge scoped to prove-type only to control cost.
Non-prove-type instructions go unchecked.
Full coverage wasn't feasible within credit budget.

Adaption was run on original dataset not Claude samples.
Stronger pipeline would be Claude for diversity, Adaption for quality.
Not done due to time — but the comparison was more informative for the pilot.

Temperature tuned by observation not systematically.
0.5 was monotone, 0.7 produced variety. No ablation run.

**Where I got stuck**
Adaption column normalization took several iterations.
Output had both original and enhanced columns.
Harness kept picking up originals until load function was fixed to drop them.

**What another week would look like**
Feed Claude samples into Adaption as a combined pipeline.
Run judge on all rows not just prove-type.
Add semantic duplicate detection using embeddings.
Fine-tune on a subset and measure reasoning benchmark
to get a real training signal proxy.

**Where Adaption helped**
Blueprint translated diagnosis findings directly into generation rules.
Quality score confirmed diagnosis independently.

**Where Adaption fell short**

Cannot fix source diversity — 6 unique inputs produced 30 variations
but all within the same narrow domain.
Output is JSON not JSONL — conversion needed before use.
Annotation leak wrote internal evaluation strings into completions silently.