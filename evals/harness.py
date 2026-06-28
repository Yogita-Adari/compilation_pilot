#eval runs on any file , automatically everytime

import json
import pandas as pd
import sys
import os
from dotenv import load_dotenv
import anthropic

from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / ".env"


load_dotenv(env_path)

# manually read the file
with open('.env', 'r') as f:
    print(f.read())

def load_dataset(filepath):
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
    
    # normalize column names
    if 'ENHANCED PROMPT' in df.columns:
        df = df.rename(columns={
            'ENHANCED PROMPT': 'instruction',
            'ENHANCED COMPLETION': 'response'
        })
    elif 'prompt' in df.columns:
        df = df.rename(columns={
            'prompt': 'instruction',
            'completion': 'response'
        })
    
    # check required columns exist
    required = ['instruction', 'response']
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    return df

def basic_checks(df):
    print("basic checks=")
    
    print(f"\nShape: {df.shape}")
    
    print(f"\nMissing values:")
    print(df[['instruction', 'response']].isnull().sum())
    
    print(f"\nDuplicate instructions: {df.duplicated(subset=['instruction']).sum()}")
    print(f"Unique instructions: {df['instruction'].nunique()}")
    
    print(f"\nLength summary:")
    print(f"  Instruction avg: {df['instruction'].str.len().mean():.0f} chars")
    print(f"  Response avg: {df['response'].str.len().mean():.0f} chars")
    
    # check thought column if exists
    if 'thought' in df.columns:
        print(f"  Thought avg: {df['thought'].str.len().mean():.0f} chars")
    
    print(f"\nLength collapse (response under 500 chars): {len(df[df['response'].str.len() < 500])}")


def phrase_checks(df):
    print("\noverclaims and theatrics")
    
    overclaiming = ['we have proved', 'we proved', 'this proves', 'qed']
    theatrical = ['i made an error', 'i was wrong', 'let me correct',
                  'wait that is wrong', 'i initially thought', 
                  'at first i believed', 'i incorrectly']
    
    # only check prove type instructions for overclaiming
    prove_mask = df['instruction'].str.lower().str.contains('prove')
    
    print("\nOverclaiming in response (prove-type only):")
    for p in overclaiming:
        count = df[prove_mask]['response'].str.lower().str.contains(p).sum()
        print(f"   '{p}': {count}")
    
    print("\nOverclaiming in thought (prove-type only):")
    if 'thought' in df.columns:
        for p in overclaiming:
            count = df[prove_mask]['thought'].str.lower().str.contains(p).sum()
            print(f"   '{p}': {count}")
    else:
        print("   No thought column found")

    print("\nTheatrical in response:")
    for t in theatrical:
        count = df['response'].str.lower().str.contains(t).sum()
        print(f"   '{t}': {count}")
    
    print("\nTheatrical in thought:")
    if 'thought' in df.columns:
        for t in theatrical:
            count = df['thought'].str.lower().str.contains(t).sum()
            print(f"   '{t}': {count}")
    else:
        print("   No thought column found")

def llm_judge(df):
    
    key = os.getenv("ANTHROPIC_API_KEY")
    
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    print("\n LLM JUDGE ")
    
    # only check prove type instructions
    prove_mask = df['instruction'].str.lower().str.contains('prove')
    prove_df = df[prove_mask]

    all_df = df
    
    print(f"Checking {len(prove_df)} prove-type responses...")
    
    for idx, row in prove_df.iterrows():
        prompt = f"""
You are evaluating a math reasoning dataset.

Instruction: {row['instruction']}

Response (first 1000 chars): {row['response'][:1000]}

Answer these two questions with YES or NO only, then one line explanation:
1. Does this response claim to prove something that is mathematically unsolved or impossible?
2. Is there any circular reasoning (using the conclusion as a premise)?
3. Is there any theatrical self-correction - where an error is announced before any evidence show it is wrong?

Format:
OVERCLAIMING: YES/NO - reason
CIRCULAR: YES/NO - reason
THEATRICAL SELF-EVALUATION: YES/NO - reason
"""
        
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=200,
            temperature =0,
            messages=[{"role": "user", "content": prompt}]
        )
        
        result = response.content[0].text
        print(f"\nRow {idx} - {row['instruction'][:50]}...")
        print(result)





# test it
if __name__ == "__main__":
    filepath = sys.argv[1] if len(sys.argv) > 1 else "Data/math_logic_samples.jsonl"
    df = load_dataset(filepath)
    basic_checks(df)
    phrase_checks(df)
    llm_judge(df)
    print(f"Loaded: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")



