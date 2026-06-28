# Calibration Pilot

## Setup

```bash
git clone https://github.com/Yogita-Adari/compilation_pilot.git
cd compilation_pilot
pip install anthropic pandas python-dotenv
```

Create a `.env` file in the project root: ANTHROPIC KEY GOES HERE

---

## Data

Three datasets are in `Data/`:
- `math_logic_samples.jsonl` — original dataset provided
- `claude_samples.jsonl` — generated using Claude API with critique loop
- `advanced_stem_derivations.jsonl` — Adaption enhanced dataset
- `failed_instructions.txt` — instructions that failed all 3 critique loop attempts

---

## Run the eval harness

Runs on any dataset file:

```bash
python evals/harness.py Data/math_logic_samples.jsonl
python evals/harness.py Data/claude_samples.jsonl
python evals/harness.py Data/advanced_stem_derivations.jsonl
```

Checks performed:
- Duplicate instructions
- Length distribution and collapse detection
- Overclaiming and theatrical phrase matching
- Monotone opening detection
- LLM judge on prove-type responses

Handles multiple file formats — original jsonl, claude jsonl, and Adaption json output.
Column normalization is automatic.

---

## Run the generation pipeline

```bash
python pipeline/generate.py
```

Generates 30 samples with critique loop.
Each sample is judged immediately after generation.
Only samples passing overclaiming, circular reasoning, and theatrical checks are saved.
Failed instructions logged to `Data/failed_instructions.txt`.
Output saved to `Data/claude_samples.jsonl` by default.

Custom output file:
```bash
python pipeline/generate.py Data/my_output.jsonl
```

---

## Run initial EDA

One-time exploratory analysis on the original dataset:
```bash
python initial_eda.py
```

---

## Writeup and Reflections

- `findings.md` — technical writeup: diagnosis, generation pipeline, eval design, results
- `reflections.md` — tradeoffs, where got stuck, what's next, Adaption help and gaps