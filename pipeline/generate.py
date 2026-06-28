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
    "Derive the Black-Scholes equation for option pricing. Show each assumption and how it leads to the final PDE."
]

def generate_sample(instruction):
    # step 1 - generate thought
    thought_response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        temperature=0.7,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Think through this step by step before answering: {instruction}"
        }]
    )
    thought = thought_response.content[0].text

    # step 2 - generate response using thought as context
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
    
    # create file if not exists
    open(output_file, 'a').close()
    
    print(f"Generating {len(INSTRUCTIONS)} samples...")
    print(f"Saving to: {output_file}")
    
    for i, instruction in enumerate(INSTRUCTIONS):
        print(f"\nGenerating {i+1}/{len(INSTRUCTIONS)}: {instruction[:50]}...")
        
        try:
            thought, response = generate_sample(instruction)
            save_sample(instruction, thought, response, output_file)
            print(f"   Saved — thought: {len(thought)} chars, response: {len(response)} chars")
        except Exception as e:
            print(f"   Failed: {e}")
    
    print(f"\nDone. {len(INSTRUCTIONS)} samples saved to {output_file}")