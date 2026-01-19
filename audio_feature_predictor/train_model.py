"""
Audio Feature Predictor - Training Pipeline
Uses Last.fm tags to predict Spotify audio features
"""

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score, mean_absolute_error
import pickle
import json

# ============================================
# 1. Load and preprocess data
# ============================================

def load_and_preprocess(csv_path):
    """Load the Music Info CSV and preprocess tags"""
    df = pd.read_csv(csv_path)
    
    # Check for required columns
    required_cols = ['tags', 'valence', 'energy', 'danceability']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    
    # Drop rows with missing tags or target values
    df = df.dropna(subset=['tags', 'valence', 'energy', 'danceability'])
    
    # Clean tags: ensure string format
    df['tags'] = df['tags'].astype(str)
    
    # Filter out rows with empty or minimal tags
    df = df[df['tags'].str.len() > 3]
    
    print(f"Loaded {len(df)} rows with valid tags")
    return df


def analyze_tags(df):
    """Analyze tag distribution"""
    # Split all tags and count
    all_tags = []
    for tags in df['tags']:
        all_tags.extend([t.strip() for t in tags.split(',')])
    
    tag_counts = pd.Series(all_tags).value_counts()
    
    print(f"\nTotal unique tags: {len(tag_counts)}")
    print(f"\nTop 30 tags:")
    print(tag_counts.head(30))
    
    return tag_counts


# ============================================
# 2. Feature engineering
# ============================================

def create_features(df, vectorizer=None, max_features=300):
    """Convert tags to TF-IDF features"""
    
    # 预处理：标准化 tags 格式
    # 1. 去掉逗号后的空格
    # 2. 统一用下划线替换空格和连字符
    def normalize_tags(tags_str):
        if pd.isna(tags_str):
            return ""
        tags = [t.strip().lower().replace(' ', '_').replace('-', '_') 
                for t in str(tags_str).split(',')]
        return ','.join(tags)
    
    normalized_tags = df['tags'].apply(normalize_tags)
    
    if vectorizer is None:
        vectorizer = TfidfVectorizer(
            max_features=max_features,
            token_pattern=r'[^,]+',  # Split by comma
            strip_accents='unicode',
            lowercase=True
        )
        X = vectorizer.fit_transform(normalized_tags)
        return X, vectorizer
    else:
        X = vectorizer.transform(normalized_tags)
        return X


# ============================================
# 3. Model training
# ============================================

def train_model(X, y, model_type='rf'):
    """Train a multi-output regression model"""
    
    if model_type == 'rf':
        base_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=15,
            min_samples_leaf=5,
            n_jobs=-1,
            random_state=42
        )
    elif model_type == 'gbm':
        base_model = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=5,
            random_state=42
        )
    elif model_type == 'ridge':
        base_model = Ridge(alpha=1.0)
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    # MultiOutputRegressor for multiple targets
    model = MultiOutputRegressor(base_model)
    model.fit(X, y)
    
    return model


def evaluate_model(model, X_test, y_test, feature_names):
    """Evaluate model performance"""
    y_pred = model.predict(X_test)
    
    results = {}
    for i, feature in enumerate(feature_names):
        r2 = r2_score(y_test.iloc[:, i], y_pred[:, i])
        mae = mean_absolute_error(y_test.iloc[:, i], y_pred[:, i])
        results[feature] = {'r2': r2, 'mae': mae}
        print(f"{feature:15} | R²: {r2:.4f} | MAE: {mae:.4f}")
    
    # Overall R²
    overall_r2 = r2_score(y_test, y_pred)
    print(f"\nOverall R²: {overall_r2:.4f}")
    
    return results


# ============================================
# 4. Save/Load model
# ============================================

def save_model(model, vectorizer, filepath='model_bundle.pkl'):
    """Save model and vectorizer"""
    bundle = {
        'model': model,
        'vectorizer': vectorizer
    }
    with open(filepath, 'wb') as f:
        pickle.dump(bundle, f)
    print(f"Model saved to {filepath}")


def load_model(filepath='model_bundle.pkl'):
    """Load model and vectorizer"""
    with open(filepath, 'rb') as f:
        bundle = pickle.load(f)
    return bundle['model'], bundle['vectorizer']


# ============================================
# 5. Main training pipeline
# ============================================

def main(csv_path, output_path='model_bundle.pkl'):
    # Load data
    print("=" * 50)
    print("Loading data...")
    df = load_and_preprocess(csv_path)
    
    # Analyze tags
    print("=" * 50)
    print("Analyzing tags...")
    tag_counts = analyze_tags(df)
    
    # Define target features
    target_features = ['valence', 'energy', 'danceability']
    
    # Add more features if available
    optional_features = ['speechiness', 'instrumentalness', 'liveness']
    for f in optional_features:
        if f in df.columns:
            target_features.append(f)
    
    print(f"\nTarget features: {target_features}")
    
    # Create features
    print("=" * 50)
    print("Creating TF-IDF features...")
    X, vectorizer = create_features(df, max_features=300)
    y = df[target_features]
    
    print(f"Feature matrix shape: {X.shape}")
    
    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Train model
    print("=" * 50)
    print("Training Random Forest model...")
    model = train_model(X_train, y_train, model_type='rf')
    
    # Evaluate
    print("=" * 50)
    print("Evaluation on test set:")
    results = evaluate_model(model, X_test, y_test, target_features)
    
    # Save model
    print("=" * 50)
    save_model(model, vectorizer, output_path)
    
    # Save feature names for reference
    feature_names_path = output_path.replace('.pkl', '_features.json')
    with open(feature_names_path, 'w') as f:
        json.dump({
            'target_features': target_features,
            'tfidf_features': vectorizer.get_feature_names_out().tolist()
        }, f, indent=2)
    print(f"Feature names saved to {feature_names_path}")
    
    return model, vectorizer, results


if __name__ == "__main__":
    # 从 config.py 读取 CSV 路径
    try:
        from config import MUSIC_INFO_CSV
        csv_path = MUSIC_INFO_CSV
    except ImportError:
        csv_path = "Music Info.csv"
    
    print(f"📂 使用数据文件: {csv_path}")
    main(csv_path)
