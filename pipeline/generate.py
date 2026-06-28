import anthropic
import json
import os
import sys
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """
You are a mathematical reasoning assistant generating training data.

WHAT TO DO:
1. Show every step of the thinking process in full detail
2. Show full working - every calculation, every logical step, 
   every assumption stated explicitly
3. If you realize a genuine error during working, correct it 
   and explain exactly which step was wrong and why

WHAT NEVER TO DO:
1. Never summarize - if a step can be explained further, explain it
2. Never claim to prove something that cannot be proven
3. Never use the conclusion as a premise
4. Never change what you are proving or deriving mid-response
5. Never fabricate an error just to show self-correction
6. Never start with 'We need to prove/derive/solve'
"""

INSTRUCTIONS = [
    "Derive the steady-state temperature distribution in a spherical shell with inner radius r1 and outer radius r2, where thermal conductivity varies as k(r) = k0/r. Show all boundary condition applications.",
    "Work through the derivation of the velocity profile for a Bingham plastic fluid flowing between two parallel plates. Show where the yield stress creates a plug flow region.",
    "Derive the equations of motion for a double pendulum using the Lagrangian approach. Show how the coupled differential equations arise.",
    "Work through the Gram-Schmidt orthogonalization process for a set of three linearly independent vectors in R3. Show each projection step explicitly.",
    "Solve the heat equation on a finite rod with mixed boundary conditions: fixed temperature at one end, insulated at the other. Show the separation of variables steps.",
    "Evaluate the contour integral of f(z) = 1/(z^2+1) around a semicircular contour in the upper half plane. Show how the residue theorem applies.",
    "Derive the maximum likelihood estimator for the parameters of a Gaussian mixture model with two components. Show the E-step and M-step explicitly.",
    "Work through the proof that there are infinitely many primes using Euclid's argument. Then show how the same logic extends to primes of the form 4k+3.",
    "Derive the KKT conditions for a constrained optimization problem with two inequality constraints. Show a worked example with explicit calculations.",
    "Work through Dijkstra's shortest path algorithm on a weighted graph with 6 nodes. Show the priority queue state at each step.",
    "Derive the Fourier series representation of a square wave. Show the calculation of each coefficient and discuss the Gibbs phenomenon.",
    "Derive the error term for Simpson's rule numerical integration. Show how the error depends on the fourth derivative and step size.",
    "Work through the derivation of the channel capacity formula for a binary symmetric channel. Show how Shannon entropy leads to the capacity bound.",
    "Prove that every subgroup of a cyclic group is cyclic. Work through the proof constructively showing how the generator of the subgroup is found.",
    "Derive the Black-Scholes equation for option pricing. Show each assumption and how it leads to the final PDE.",
    "Derive the Euler-Lagrange equation from the principle of stationary action. Show how it applies to a simple harmonic oscillator.",
    "Work through the derivation of the normal distribution from the central limit theorem. Show each step of the convergence argument.",
    "Derive the convolution theorem for Fourier transforms. Show how it simplifies the computation of convolutions.",
    "Work through the proof of Bayes theorem from first principles. Show a worked example with explicit probability calculations.",
    "Derive the equations of motion for a charged particle in crossed electric and magnetic fields. Show the cyclotron frequency calculation.",
    "Work through the Cholesky decomposition of a 3x3 positive definite matrix. Show each step of the factorization explicitly.",
    "Derive the Green's function for the one-dimensional Poisson equation. Show how boundary conditions determine the solution.",
    "Work through the simplex method on a linear programming problem with three variables and four constraints. Show the tableau at each pivot.",
    "Derive the Navier-Stokes equations from conservation of momentum for a Newtonian fluid. Show each term's physical meaning.",
    "Work through the proof of the Cauchy integral formula. Show how it follows from Green's theorem.",
    "Derive the partition function for a two-level quantum system. Show how thermodynamic quantities follow from it.",
    "Work through the derivation of the Kalman filter update equations. Show the geometric interpretation of the gain matrix.",
    "Derive the singular value decomposition of a 2x2 matrix. Show the geometric interpretation of each factor.",
    "Work through the proof of the prime number theorem using the Chebyshev psi function. Show each bound explicitly.",
    "Derive the equations governing heat transfer in a fin of variable cross-section. Show how the efficiency depends on the Biot number."
]

def judge_sample(instruction, response):
    prompt = f"""
You are evaluating a math reasoning dataset sample.

Instruction: {instruction}

Response: {response[:3000]}

Answer YES or NO for each, then one line reason:
1. Does this response claim to prove something mathematically unsolved or impossible?
2. Is there circular reasoning (conclusion used as premise)?
3. Is there theatrical self-correction (error announced before any evidence)?

Format exactly:
OVERCLAIMING: YES/NO - reason
CIRCULAR: YES/NO - reason
THEATRICAL: YES/NO - reason
"""
    result = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=150,
        temperature=0,
        messages=[{"role": "user", "content": prompt}]
    )
    text = result.content[0].text
    passed = "OVERCLAIMING: YES" not in text and "CIRCULAR: YES" not in text and "THEATRICAL: YES" not in text
    return passed, text

def generate_sample(instruction):
    thought_response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        temperature=0.7,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"""Before solving this problem, write a detailed scratchpad showing:
- Your interpretation of the problem and any ambiguities
- Your planned approach and why you chose it
- Any alternative approaches you considered and rejected
- Step by step working including every calculation
- Any mistakes you catch during working and why they are wrong
- Your confidence in each step

Problem: {instruction}"""
        }]
    )
    thought = thought_response.content[0].text

    final_response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        temperature=0.7,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"{instruction}\n\nHere is my thinking so far:\n{thought}\n\nNow write the full solution."
        }]
    )
    return thought, final_response.content[0].text

def generate_with_critique(instruction, max_retries=3):
    for attempt in range(max_retries):
        thought, response = generate_sample(instruction)
        passed, verdict = judge_sample(instruction, response)
        if passed:
            return thought, response, attempt + 1
        print(f"   attempt {attempt + 1} failed — retrying")
        print(f"   reason: {verdict}")
    return None, None, max_retries

def save_sample(instruction, thought, response, filepath):
    sample = {
        "instruction": instruction,
        "thought": thought,
        "response": response
    }
    with open(filepath, 'a', encoding='utf-8') as f:
        f.write(json.dumps(sample) + '\n')

if __name__ == "__main__":
    output_file = sys.argv[1] if len(sys.argv) > 1 else "Data/claude_samples.jsonl"
    failed_log = "Data/failed_instructions.txt"

    open(output_file, 'a').close()

    print(f"generating {len(INSTRUCTIONS)} samples")
    print(f"saving to {output_file}")

    passed = 0
    failed = 0

    for i, instruction in enumerate(INSTRUCTIONS):
        print(f"\n{i+1}/{len(INSTRUCTIONS)}: {instruction[:60]}...")

        thought, response, attempts = generate_with_critique(instruction)

        if thought is None:
            print(f"   failed after {attempts} attempts — skipping")
            with open(failed_log, 'a') as f:
                f.write(instruction + '\n')
            failed += 1
        else:
            save_sample(instruction, thought, response, output_file)
            print(f"   saved on attempt {attempts} — thought: {len(thought)} chars, response: {len(response)} chars")
            passed += 1

    print(f"\ndone — {passed} passed, {failed} failed")
    print(f"saved to {output_file}")