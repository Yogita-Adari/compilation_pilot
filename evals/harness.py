# eval harness - runs on any dataset file
# usage: python evals/harness.py Data/any_file.jsonl

import json
import pandas as pd
import sys
import os
import anthropic
from pathlib import Path
from dotenv import load_dotenv

# load env from project root
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)

def load_dataset(filepath):
    """
    Loads any dataset file and normalizes column names.
    Handles: original, claude, adaption formats
    """
    # handle json vs jsonl
    if filepath.endswith('.jsonl'):
        data = []
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    data.append(json.loads(line))
    else:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    
    df = pd.DataFrame(data)
    
    # normalize columns based on what exists
    if 'enhanced_prompt' in df.columns:
        # adaption output - drop originals, use enhanced versions
        df = df.drop(columns=['instruction', 'response', 'thought'], errors='ignore')
        df = df.rename(columns={
            'enhanced_prompt': 'instruction',
            'enhanced_completion': 'response',
            'reasoning_trace': 'thought'
        })
    elif 'ENHANCED PROMPT' in df.columns:
        # adaption json format
        df = df.rename(columns={
            'ENHANCED PROMPT': 'instruction',
            'ENHANCED COMPLETION': 'response'
        })
    elif 'prompt' in df.columns:
        # other format
        df = df.rename(columns={
            'prompt': 'instruction',
            'completion': 'response'
        })
    # original and claude already have correct column names

    # verify required columns exist
    required = ['instruction', 'response']
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    return df

def basic_checks(df):
    """
    Checks shape, missing values, duplicates, length distribution
    """
    print(df.columns.tolist())
    print("\n=== BASIC CHECKS ===")
    print(f"\nShape: {df.shape}")
    
    print(f"\nMissing values:")
    print(df[['instruction', 'response']].isnull().sum())
    
    print(f"\nDuplicate instructions: {df.duplicated(subset=['instruction']).sum()}")
    print(f"Unique instructions: {df['instruction'].nunique()}")
    
    print(type(df["thought"]))
    print(f"\nLength summary:")
    print(f"  Instruction avg: {df['instruction'].str.len().mean():.0f} chars")
    print(f"  Response avg: {df['response'].str.len().mean():.0f} chars")
   
    if 'thought' in df.columns:
        thought_lengths = df['thought'].astype(str).replace('nan', '').str.len()
        thought_avg = thought_lengths[thought_lengths > 0].mean()
        print(f"  Thought avg: {thought_avg:.0f} chars")
    collapsed = len(df[df['response'].str.len() < 500])
    print(f"\nLength collapse (response under 500 chars): {collapsed}")

def phrase_checks(df):
    """
    Checks for overclaiming and theatrical self-correction phrases.
    Overclaiming only checked on prove-type instructions.
    Theatrical checked on all rows.
    """
    print("\n=== PHRASE CHECKS ===")
    
    overclaiming = ['we have proved', 'we proved', 'this proves', 'qed']
    theatrical = [
        'i made an error', 'i was wrong', 'let me correct',
        'wait that is wrong', 'i initially thought',
        'at first i believed', 'i incorrectly'
    ]
    
    # overclaiming - only prove type instructions
    prove_mask = df['instruction'].str.lower().str.contains('prove')
    
    print(f"\nOverclaiming in response (prove-type only):")
    for p in overclaiming:
        count = df[prove_mask]['response'].str.lower().str.contains(p).sum()
        print(f"   '{p}': {count}")
    
    print(f"\nOverclaiming in thought (prove-type only):")
    if 'thought' in df.columns:
        for p in overclaiming:
            count = df[prove_mask]['thought'].str.lower().str.contains(p).sum()
            print(f"   '{p}': {count}")
    else:
        print("   No thought column found")
    
    # theatrical - all rows
    print(f"\nTheatrical in response:")
    for t in theatrical:
        count = df['response'].str.lower().str.contains(t).sum()
        print(f"   '{t}': {count}")
    
    print(f"\nTheatrical in thought:")
    if 'thought' in df.columns:
        for t in theatrical:
            count = df['thought'].str.lower().str.contains(t).sum()
            print(f"   '{t}': {count}")
    else:
        print("   No thought column found")

def llm_judge(df):
    """
    LLM judge for deeper quality checks.
    Checks overclaiming, circular reasoning, theatrical self-correction.
    Only runs on prove-type instructions to save API costs.
    Note: LLM judge is probabilistic - temperature=0 improves consistency
    but does not guarantee identical outputs across runs.
    """
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    print("\n=== LLM JUDGE ===")
    
    # only check prove type instructions
    prove_mask = df['instruction'].str.lower().str.contains('prove')
    prove_df = df[prove_mask]
    
    print(f"Checking {len(prove_df)} prove-type responses...")
    
    for idx, row in prove_df.iterrows():
        prompt = f"""
You are evaluating a math reasoning dataset.

Instruction: {row['instruction']}

Response (first 1000 chars): {row['response'][:1000]}

Answer these three questions with YES or NO only, then one line explanation:
1. Does this response claim to prove something that is mathematically unsolved or impossible?
2. Is there any circular reasoning (using the conclusion as a premise)?
3. Is there any theatrical self-correction - where an error is announced before any evidence shows it is wrong?

Format:
OVERCLAIMING: YES/NO - reason
CIRCULAR: YES/NO - reason
THEATRICAL: YES/NO - reason
"""
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=200,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )
        
        print(f"\nRow {idx} - {row['instruction'][:50]}...")
        print(response.content[0].text)

if __name__ == "__main__":
    filepath = sys.argv[1] if len(sys.argv) > 1 else "Data/math_logic_samples.jsonl"
    
    print(f"\nEvaluating: {filepath}")
    
    df = load_dataset(filepath)
    basic_checks(df)
    phrase_checks(df)
    llm_judge(df)
    
    print(f"\nColumns in dataset: {df.columns.tolist()}")