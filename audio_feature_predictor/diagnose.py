"""
Diagnostic Script: Check why energy prediction didn't change
"""

import pandas as pd
import numpy as np
import pickle
import json

print("=" * 60)
print("🔍 Diagnosis: Energy Prediction Issue")
print("=" * 60)

# 1. Load model and vectorizer
print("\n[1] Loading model...")
with open('model_bundle.pkl', 'rb') as f:
    bundle = pickle.load(f)
model = bundle['model']
vectorizer = bundle['vectorizer']

# 2. View vectorizer learned vocabulary
print("\n[2] TF-IDF Vectorizer Vocabulary:")
vocab = vectorizer.get_feature_names_out()
# Check for leading spaces
has_leading_space = any(v.startswith(' ') for v in vocab)
print(f"    Vocabulary Size: {len(vocab)}")
print(f"    Has Leading Space: {'⚠️ Yes (This is a bug!)' if has_leading_space else '✓ No'}")
print(f"    First 30 words: {list(vocab[:30])}")

# 3. Check if energy related words are in vocabulary
energy_related = ['energetic', 'chill', 'chillout', 'mellow', 'ambient', 
                  'upbeat', 'calm', 'relaxing', 'intense', 'aggressive',
                  'soft', 'hard', 'heavy', 'light', 'loud', 'quiet']

print("\n[3] Energy Related Vocabulary Check:")
for word in energy_related:
    in_vocab = word in vocab
    print(f"    {word:15} {'✓ In Vocabulary' if in_vocab else '✗ Not In Vocabulary'}")

# 4. Load Last.fm scraped data, check token match rate
print("\n[4] Checking Last.fm Tags Match Rate...")

def check_tag_coverage(csv_path):
    try:
        df = pd.read_csv(csv_path)
        if 'tags' not in df.columns:
            print(f"    {csv_path}: No 'tags' column")
            return
        
        all_tags = []
        for tags_str in df['tags'].dropna():
            # Split by comma
            tags = [t.strip().lower() for t in str(tags_str).split(',')]
            all_tags.extend(tags)
        
        unique_tags = set(all_tags)
        matched = unique_tags & set(vocab)
        unmatched = unique_tags - set(vocab)
        
        print(f"\n    📄 {csv_path}:")
        print(f"       Total Tags: {len(all_tags)}")
        print(f"       Unique Tags: {len(unique_tags)}")
        print(f"       Matched Vocabulary: {len(matched)} ({100*len(matched)/max(len(unique_tags),1):.1f}%)")
        print(f"       Unmatched: {len(unmatched)}")
        
        if unmatched:
            print(f"       Unmatched Tags (Top 20): {list(unmatched)[:20]}")
        
        return matched, unmatched
        
    except FileNotFoundError:
        print(f"    {csv_path}: File not found")
        return None, None

# Check a few files
for f in ['taylor_swift_tags.csv', 'linkin_park_tags.csv', 
          'playlist_Hurry Up Tomorrow.csv', 'playlist_Tsunami Sea.csv']:
    check_tag_coverage(f)

# 5. Test vectorizer transformation on new tags
print("\n[5] Test Vectorizer Transformation:")

test_cases = [
    "rock, alternative_rock, nu_metal",  # Should match
    "pop, synthpop, rnb",                 # Partial match
    "j_pop, doujin, vocaloid",            # Might not match
]

for tags_str in test_cases:
    X = vectorizer.transform([tags_str])
    non_zero = X.nnz  # Number of non-zero elements
    print(f"    '{tags_str[:40]}...'")
    print(f"       Non-zero Features: {non_zero}")

# 6. Check model prediction distribution for energy
print("\n[6] Model Prediction Test:")

# Test with some extreme tags
extreme_cases = {
    "ambient, chillout, relaxing, calm, soft": "Should be low energy",
    "metal, heavy_metal, hard_rock, aggressive, intense": "Should be high energy",
    "pop, dance, electronic, energetic, upbeat": "Should be high energy",
    "acoustic, folk, singer_songwriter, mellow": "Should be low energy",
    "": "Empty tags (baseline)",
}

for tags_str, expected in extreme_cases.items():
    X = vectorizer.transform([tags_str])
    pred = model.predict(X)[0]
    # Assuming energy is the second feature (index 1)
    print(f"\n    Tags: '{tags_str[:50]}...'")
    print(f"    Expected: {expected}")
    print(f"    Predicted: valence={pred[0]:.3f}, energy={pred[1]:.3f}, danceability={pred[2]:.3f}")

# 7. Load training data, check relationship between energy and tags
print("\n[7] Training Data Energy vs Tags Relationship:")
try:
    df_train = pd.read_csv('merged_data.csv')
    
    # Find average energy for songs containing specific tag
    def avg_energy_for_tag(tag):
        mask = df_train['tags'].str.contains(tag, case=False, na=False)
        if mask.sum() > 0:
            return df_train.loc[mask, 'energy'].mean(), mask.sum()
        return None, 0
    
    print("\n    Average Energy for Tags:")
    check_tags = ['metal', 'ambient', 'chill', 'rock', 'electronic', 
                  'acoustic', 'pop', 'dance', 'hip_hop', 'classical']
    
    for tag in check_tags:
        avg, count = avg_energy_for_tag(tag)
        if avg:
            print(f"    {tag:15} → energy={avg:.3f} (n={count})")

except FileNotFoundError:
    print(" merged_data.csv not found")

print("\n" + "=" * 60)
print("Diagnosis Complete")
print("=" * 60)
