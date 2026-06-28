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
    Dataset statistics and length collapse detection.
    """

    print("\n BASIC CHECKS ")

    print(f"\nShape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")

    print("\nMissing values:")
    print(df[["instruction", "response"]].isnull().sum())

    print(f"\nDuplicate instructions: {df.duplicated(subset=['instruction']).sum()}")
    print(f"Unique instructions: {df['instruction'].nunique()}")

    instruction_lengths = df["instruction"].fillna("").astype(str).str.len()
    response_lengths = df["response"].fillna("").astype(str).str.len()

    print("\nInstruction length")
    print(instruction_lengths.describe(percentiles=[0.1,0.25,0.5,0.75,0.9]))

    print("\nResponse length")
    print(response_lengths.describe(percentiles=[0.1,0.25,0.5,0.75,0.9]))

    if "thought" in df.columns:
        thought_lengths = (
            df["thought"]
            .fillna("")
            .astype(str)
            .str.len()
        )

        print("\nThought length")
        print(thought_lengths.describe(percentiles=[0.1,0.25,0.5,0.75,0.9]))

    print("\nLength collapse")
    print(f"<500 chars  : {(response_lengths < 500).sum()}")
    print(f"<1000 chars : {(response_lengths < 1000).sum()}")
    print(f"<2000 chars : {(response_lengths < 2000).sum()}")

def phrase_checks(df):
    print("\noverclaiming, Theatrics, Circular reasoning")
    
    overclaiming = [
        "we have proved",
        "we proved",
        "this proves",
        "qed",
        "the theorem is proved",
        "the claim is proved",
        "thus we conclude",
        "therefore we conclude"
    ]

    theatrical = [
        "i made an error",
        "i was wrong",
        "let me correct",
        "wait that is wrong",
        "i initially thought",
        "at first i believed",
        "i incorrectly",
        "i realized my mistake",
        "that approach was flawed",
        "this argument fails",
        "let me start over"
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
def monotone_check(df):
    print("MONOTONE OPENINGS")
    
    monotone_phrases = [
        'we need to prove',
        'we need to derive', 
        'we need to solve',
        'we are asked',
        'we need to'
    ]
    
    print("\nThought openings:")
    for p in monotone_phrases:
        count = df['thought'].str.lower().str[:50].str.startswith(p).sum() if 'thought' in df.columns else 'no thought column'
        print(f"   '{p}': {count}")
    
    print("\nResponse openings:")
    for p in monotone_phrases:
        count = df['response'].str.lower().str[:50].str.startswith(p).sum()
        print(f"   '{p}': {count}")
def llm_judge(df):
    """
    LLM judge for deeper quality checks.
    Checks overclaiming, circular reasoning, theatrical self-correction.
    Only runs on prove-type instructions to save API costs.
    Note: LLM judge is probabilistic - temperature=0 improved consistency
    but does not guarantee identical outputs across runs.
    """

    
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    print("\n LLM JUDGE")
    
    # only check prove type instructions --cost effective for pilot
    prove_mask = df['instruction'].str.lower().str.contains('prove')
    prove_df = df[prove_mask]
    
    print(f"Checking {len(prove_df)} prove-type responses...")
    
    for idx, row in prove_df.iterrows():
        prompt = f"""
    You are evaluating a math reasoning dataset.

    Instruction: {row['instruction']}

    Response: {row['response'][:3000]}    

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
    monotone_check(df)
    llm_judge(df)
    
    print(f"\nColumns in dataset: {df.columns.tolist()}")


    # on the last eval harness run wih full response LLM judge, it was revealed that 3 response had theatrics
    # when compare to set-limit.. It suggests that Adaption's internal evaluation process leaked into
    # generated completions. 