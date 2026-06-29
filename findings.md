## Project set-up structure

- File structure
    - Data  
        - advanced_stem_derivations.jsonl — adaption enhanced original dataset
        - claude_samples.jsonl — generated using Claude API with critique loop
        - stem_step_by_step_solutions.jsonl — combined pipeline (Claude + Adaption)
        - math_logic_samples.jsonl — original dataset
        - failed_instructions.txt — instructions that failed all 3 critique attempts
    - evals
        - harness.py — eval harness using deterministic rules and LLM judge
    - pipeline
        - generate.py — generation pipeline with critique loop
    - findings.md — technical writeup
    - reflections.md — tradeoffs, gaps, Adaption help and gaps
    - initial_eda.py — exploratory analysis on original dataset, run once
    - README.md — how to run this code

---

## Technical Writeup

### Diagnosis

The original dataset had 30 rows but only 6 unique instructions —
80% duplicates. All from the same domain, same prompt structure,
same monotone openings (26/30 thoughts started with "we need to").

Four responses overclaimed — presenting numerical verification
as formal proof for the Riemann Hypothesis.
LLM judge confirmed circular reasoning in the same responses.
No theatrical self-correction detected by phrase matching,
but phrase matching cannot confirm absence — LLM judge needed.

---

### Generation Pipeline

Two approaches were compared — not to find which is better
but to understand what each fixes and what it misses.
A combined pipeline was then tested as the strongest hypothesis.

**Claude pipeline:** 29 diverse instructions generated from scratch.
Two-step generation — detailed scratchpad prompt then full solution.
Each sample judged immediately after generation (critique loop).
Only samples passing overclaiming, circular reasoning,
and theatrical checks enter the dataset.
Temperature 0.7 — 0.5 produced monotone outputs.
Prove-type instructions deliberately limited to one well-established theorem.
Asking models to prove unsolvable problems forces overclaiming.

**Adaption on original:** Original dataset uploaded with thought as context.
Blueprint written directly from diagnosis findings with 1-shot example.
Deduplication, reasoning traces, hallucination mitigation enabled.
Length set to Detailed.

**Combined pipeline:** Claude samples uploaded to Adaption for enhancement.
Blueprint focused on depth and reasoning trace length
rather than fixing quality problems — input was already clean.
Note: Adaption scored Claude samples at 47th percentile before enhancement.
This is lower than expected given the input quality
and needs investigation before scaling this pipeline.

---

### Results

| | Original | Claude | Adaption | Claude + Adaption |
|--|---------|--------|---------|-------------------|
| Unique instructions | 6 | 29 | 30 | 29 |
| Duplicates | 24 | 0 | 0 | 0 |
| Overclaiming (LLM judge) | 4 | 0 | 0 | 0 |
| Circular reasoning | 4 | 0 | 0 | 0 |
| Theatrical (LLM judge) | 0 | 0 | 2 | 2 |
| Monotone openings | 26/30 | 0 | 0 | 0 |
| Avg response (chars) | 11,868 | 8,454 | 11,659 | 13,173 |
| Avg thought (chars) | 25,169 | 8,357 | 9,704 | 12,747 |

Combined pipeline produced the best response and thought lengths.
Adaption enhancement improved Claude's thought length by 52% (8,357 → 12,747)
and response length by 56% (8,454 → 13,173).

Both theatrical instances in combined pipeline were caught by LLM judge only —
phrase matching missed both.
Row 16: announced symmetry observation before any calculation showed it.
Row 19: "let me be careful" manufactured appearance of catching error.

Reasoning consistency check on 5 random samples:
3/5 consistent — thought genuinely led to response.
2/5 inconsistent — thought truncated mid-sentence, response did not follow.

Key finding: phrase matching caught 0 theatrical instances across all datasets.
LLM judge on 1,000 chars caught 1. Full response caught 3.
Truncated evaluation would have given Adaption a clean pass it did not deserve.

---

### Eval Harness

Runs on any dataset file — original, Claude, Adaption, or future batches.
Checks in order of cost:
1. Structural — duplicates, missing values, length distribution (free)
2. Phrase matching — overclaiming and theatrical keywords (free)
3. Monotone detection — opening phrase check (free)
4. LLM judge — prove-type rows get full check, all other rows checked for theatrical (paid)
5. Reasoning consistency — 5 random samples checked for thought-response coherence (paid)

Gap between what eval measures and what predicts training success:
- Structural checks are reliable
- Phrase matching is surface level and context blind
- LLM judge is probabilistic — temperature=0 improves but does not guarantee consistency
- No factual accuracy check — math could be wrong and pass all checks
- Reasoning consistency on 5 samples is a proxy not a guarantee
- Downstream training impact cannot be measured without fine-tuning

---

### Risks at scale and fixes

**Length collapse**
Current mitigation: scratchpad prompt, max_tokens=4000, Detailed in Adaption.
At scale: track length per batch, alert on 20% drop from pilot baseline.
Monitor thought separately — thought compression precedes response collapse.

**Critique loop cost**
At 10,000 samples worst case 90,000 API calls.
Fix: swap judge to claude-haiku (10x cheaper), phrase matching as free pre-filter,
cost cap per batch, parallel generation with asyncio.

**Theatrical in non-prove-type**
Current judge checks all rows for theatrical — prove-type gets full check.
At scale: majority vote across 3 judge runs to reduce false positives.

---

### What to resolve before scaling

- Investigate why Adaption scored Claude samples at 47th percentile
  before deciding to use combined pipeline at scale
- Run judge on all rows with majority vote
- Add semantic duplicate detection using embeddings
- Establish baseline pass rate from pilot to monitor drift
- Fine-tune on subset and measure reasoning benchmark
  to get real training signal proxy instead of proxy evals