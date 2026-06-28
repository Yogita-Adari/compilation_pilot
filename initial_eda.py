import json

import pandas as pd

data=[]

with open('Data/math_logic_samples.jsonl','r',encoding="utf-8") as f:
    for line in f:
        data.append(json.loads(line))

df = pd.DataFrame(data)     #all cols included in DF
print(df.columns.tolist())      #show all columns
print(df.shape)         #show shape - (r,c)

#checking if thought is empty or missing
print(df['thought'].isnull().sum())
print(df['thought'].str.len().describe())
# Thought is not missing, but the 25%: 16706 -> 25% thoughts are shorter than the 16,700 chars. 
#meaning avg thought: 25,168 Chars, and avg response: 11,867 chars. so thoughts = 2X (response) -> suggests extended reasoning not compressed traces.

#EDA_all columns
#missing values -- all cols
print(df.isnull().sum())
print(df.duplicated().sum()) #checks all but returned 0, when manually checked there were duplcate instr
print(df.duplicated(subset=['instruction']).sum())      #24 duplicate instructions appeared
print(df['instruction'].str.len().describe())           #no missing, very short chars, but consistent
print(df['response'].str.len().describe())              #no miss, inconsistency in max chars against mean which is 11867 chars
print(df['thought'].str.len().describe())               #no miss, mean is 25,168 and like earlier, 2X response len, also inconsistency observed.

# instruction: ~210 chars  (question)
# thought:     ~25,000 chars (reasoning)
# response:    ~11,867 chars (answer)

# ---- Overclaims, Theatrical reasoning, circular reasoning checks ----
phrase = ['we have proved', ' we proved', 'this proves', 'qed']
#prove_mask will only filter rows where instruction says "prove"
prove_mask = df['instruction'].str.lower().str.contains('prove')

print("OVERCLAIMING IN RESPONSE:")
for p in phrase:
    count = df[prove_mask]['response'].str.lower().str.contains(p).sum()
    print(f"   '{p}': {count}")

print("OVERCLAIMING IN THOUGHT:")
for p in phrase:
    count = df[prove_mask]['thought'].str.lower().str.contains(p).sum()
    print(f"   '{p}': {count}")

# this still doesn't tell me if X is actually provale or not, right now we will just narrow the search prove-type instructions
#Limitations : "prove pythagoras" + "we have proved" -> fine but still flags it. but we need to check if it says "we proved" for Riemann and SGD,
#we can use LLM in evals to catch this context, as hardcoding wouldnt scale organically
# OVERCLAIMING IN RESPONSE:
#    'we have proved': 3
#    ' we proved': 0
#    'this proves': 1
#    'qed': 0
# OVERCLAIMING IN THOUGHT: model's internal reasoning is careful, but overclaims in response while summarizing. This is hard to catch without checking 
# both the columns seperately
#    'we have proved': 0
#    ' we proved': 0
#    'this proves': 0 
#    'qed': 1

# THEATRICAL SELF-CORRECTIONS
theatrics = ['i made an error', 'i was wrong', 'let me correct', 
             'wait that is wrong', 'hold on', 'i incorrectly',
             'i initially thought', 'at first i believed','you are right', 'let me fix']

print("THEATRICAL IN RESPONSE:")
for t in theatrics:
    count = df['response'].str.lower().str.contains(t).sum()
    print(f"   '{t}': {count}")

print("\nTHEATRICAL IN THOUGHT:")
for t in theatrics:
    count = df['thought'].str.lower().str.contains(t).sum()
    print(f"   '{t}': {count}")
# no theatrics detected in response or thought however model could be using a seperate phrasing, we need to use LLM judge later to confirm this

print(df['thought'].str[:80].value_counts())        # check monotone -> we need to appears a lot in thought --> possible reasons: rigid system prompt/template
print(df['response'].str[:80].value_counts())       # responses are more varied than thought -- model might have had fewer constraints

