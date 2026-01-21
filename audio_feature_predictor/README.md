# Audio Feature Predictor

Predict Spotify audio features using Last.fm tags, bypassing the restriction of Spotify closing its audio features API.

## Principle

```
[Training Data: 50k songs]          [New Songs]
Tags + Audio Features   →    Tags only
        ↓                        ↓
   Train Model (TF-IDF + RF) →   Predict Audio Features
```

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Train Model
```bash
# Train using your Music Info.csv
python train_model.py "path/to/Music Info.csv"
```

Output:
- `model_bundle.pkl` - Trained model
- `model_bundle_features.json` - Feature information

### 3. Get Last.fm API Key
1. Go to https://www.last.fm/api/account/create
2. Register an application to get an API Key

### 4. Scrape Tags for New Songs
```bash
# Scrape songs for Taylor Swift and Linkin Park
python lastfm_scraper.py YOUR_API_KEY

# Or scrape a single song
python lastfm_scraper.py YOUR_API_KEY "Taylor Swift" "Anti-Hero"
```

### 5. Predict + Analyze
```bash
python predict_analyze.py demo
```

## Code Structure

```
audio_feature_predictor/
├── train_model.py      # Training pipeline
├── lastfm_scraper.py   # Last.fm scraper
├── predict_analyze.py  # Prediction + Sentiment Analysis
├── requirements.txt
└── README.md
```

## Use as Module

```python
from train_model import load_and_preprocess, create_features, train_model
from lastfm_scraper import LastFMScraper
from predict_analyze import load_model, predict_features, analyze_playlist_mood

# Load model
model, vectorizer, features = load_model('model_bundle.pkl')

# Predict single song
tags = "rock, alternative, 90s, melancholic"
predicted = predict_features(model, vectorizer, tags, features)
print(predicted)
# {'valence': 0.32, 'energy': 0.67, 'danceability': 0.45, ...}

# Analyze playlist
df = pd.read_csv('my_playlist_with_tags.csv')
df = predict_batch(model, vectorizer, df, features)
mood = analyze_playlist_mood(df)
print_analysis(mood)
```

## Mood Quadrants

Based on Valence (Mood Positivity) + Energy:

```
        High Energy
            │
  Angry/    │    Happy/
  Intense   │    Energetic
            │
 ───────────┼─────────── High Valence
            │
  Sad/      │    Peaceful/
  Melancholic│   Content
            │
        Low Energy
```

## Limitations

1. **Tag Coverage**: Last.fm tags for niche/new songs might be sparse.
2. **Prediction Accuracy**: Some features (like acousticness) correlate weakly with tags.
3. **Subjectivity**: Tags are user-generated and may contain noise.
4. **Language**: Search is in English, so it might not work for non-English songs, especially for Japanese artists.

## Recommendations

- Focus mainly on **valence, energy, danceability**.
- Use for **relative comparison** (e.g., comparing albums) rather than absolute values.
- Set a tag count threshold to filter low-confidence results.
