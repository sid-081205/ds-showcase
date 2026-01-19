# Audio Feature Predictor

用 Last.fm tags 预测 Spotify audio features，绕过 Spotify 关闭 audio features API 的限制。

## 原理

```
[训练数据: 50k首歌]          [新歌]
Tags + Audio Features   →    Tags only
        ↓                        ↓
   训练模型 (TF-IDF + RF)    →   预测 Audio Features
```

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 训练模型
```bash
# 用你的 Music Info.csv 训练
python train_model.py "path/to/Music Info.csv"
```

输出:
- `model_bundle.pkl` - 训练好的模型
- `model_bundle_features.json` - 特征信息

### 3. 获取 Last.fm API Key
1. 去 https://www.last.fm/api/account/create
2. 注册一个应用，拿到 API Key

### 4. 爬取新歌的 tags
```bash
# 爬 Taylor Swift 和 Linkin Park 的歌
python lastfm_scraper.py YOUR_API_KEY

# 或者爬单曲
python lastfm_scraper.py YOUR_API_KEY "Taylor Swift" "Anti-Hero"
```

### 5. 预测 + 分析
```bash
python predict_analyze.py demo
```

## 代码结构

```
audio_feature_predictor/
├── train_model.py      # 训练 pipeline
├── lastfm_scraper.py   # Last.fm 爬虫
├── predict_analyze.py  # 预测 + 情绪分析
├── requirements.txt
└── README.md
```

## 作为模块使用

```python
from train_model import load_and_preprocess, create_features, train_model
from lastfm_scraper import LastFMScraper
from predict_analyze import load_model, predict_features, analyze_playlist_mood

# 加载模型
model, vectorizer, features = load_model('model_bundle.pkl')

# 预测单曲
tags = "rock, alternative, 90s, melancholic"
predicted = predict_features(model, vectorizer, tags, features)
print(predicted)
# {'valence': 0.32, 'energy': 0.67, 'danceability': 0.45, ...}

# 分析 playlist
df = pd.read_csv('my_playlist_with_tags.csv')
df = predict_batch(model, vectorizer, df, features)
mood = analyze_playlist_mood(df)
print_analysis(mood)
```

## Mood 四象限

基于 Valence (情绪正负) + Energy (能量高低):

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

## 局限性

1. **Tag 覆盖率**: 冷门歌/新歌的 Last.fm tags 可能很稀疏
2. **预测精度**: 某些 features (如 acousticness) 和 tags 相关性不强
3. **主观性**: Tags 是用户打的，有噪音

## 建议

- 主要关注 **valence, energy, danceability** 这三个 features
- 用于**相对比较**（比如专辑间对比）而不是绝对值
- 设置 tag count 阈值过滤低置信度结果
