"""
数据合并 + 歌单比较工具
"""

import pandas as pd
import numpy as np
from pathlib import Path


# ============================================
# 1. 合并两个 CSV
# ============================================

def merge_datasets(csv_with_tags, csv_with_features, output_path="merged_data.csv"):
    """
    合并两个数据集：
    - csv_with_tags: 有 Last.fm tags 的那个 (Music Info.csv)
    - csv_with_features: 有完整 audio features 的那个 (你的另一个 spotify csv)
    
    合并逻辑：
    1. 用 artist + track_name 做 key
    2. 优先保留有 tags 的数据
    3. 补充没有 tags 但有 audio features 的数据
    """
    
    print("Loading datasets...")
    df_tags = pd.read_csv(csv_with_tags)
    df_features = pd.read_csv(csv_with_features)
    
    print(f"  Tags dataset: {len(df_tags)} rows")
    print(f"  Features dataset: {len(df_features)} rows")
    
    # 标准化列名（处理可能的命名差异）
    def normalize_columns(df):
        df.columns = df.columns.str.lower().str.strip()
        # 常见的列名变体
        rename_map = {
            'track_name': 'name',
            'artist_name': 'artist',
            'artists': 'artist',
        }
        for old, new in rename_map.items():
            if old in df.columns and new not in df.columns:
                df = df.rename(columns={old: new})
        return df
    
    df_tags = normalize_columns(df_tags)
    df_features = normalize_columns(df_features)
    
    # 创建合并 key
    def create_key(df):
        # 清理 artist 和 name，去除大小写和空格差异
        artist = df['artist'].astype(str).str.lower().str.strip()
        name = df['name'].astype(str).str.lower().str.strip()
        return artist + "|||" + name
    
    df_tags['_merge_key'] = create_key(df_tags)
    df_features['_merge_key'] = create_key(df_features)
    
    # 找出 df_features 中有但 df_tags 中没有的歌
    existing_keys = set(df_tags['_merge_key'])
    new_songs = df_features[~df_features['_merge_key'].isin(existing_keys)]
    
    print(f"\n  Songs only in features dataset: {len(new_songs)}")
    print(f"  Songs with tags: {len(df_tags)}")
    
    # 合并
    # 对于 new_songs，tags 列设为空（之后按需爬取）
    if 'tags' not in new_songs.columns:
        new_songs = new_songs.copy()
        new_songs['tags'] = ''
    
    # 确保两个 df 有相同的列
    common_cols = list(set(df_tags.columns) & set(new_songs.columns))
    
    merged = pd.concat([
        df_tags[common_cols],
        new_songs[common_cols]
    ], ignore_index=True)
    
    # 删除临时列
    if '_merge_key' in merged.columns:
        merged = merged.drop(columns=['_merge_key'])
    
    # 保存
    merged.to_csv(output_path, index=False)
    print(f"\n✅ Merged dataset saved to {output_path}")
    print(f"   Total rows: {len(merged)}")
    
    # 统计
    has_tags = merged['tags'].notna() & (merged['tags'] != '')
    print(f"   With tags: {has_tags.sum()}")
    print(f"   Without tags (need scraping): {(~has_tags).sum()}")
    
    return merged


# ============================================
# 2. 歌单比较
# ============================================

def load_playlist(source, model_bundle_path='model_bundle.pkl'):
    """
    加载歌单，支持多种输入格式：
    - CSV 文件路径
    - DataFrame
    - List of dicts [{'artist': '...', 'track': '...'}, ...]
    """
    if isinstance(source, str) and source.endswith('.csv'):
        df = pd.read_csv(source)
    elif isinstance(source, pd.DataFrame):
        df = source.copy()
    elif isinstance(source, list):
        df = pd.DataFrame(source)
    else:
        raise ValueError(f"Unsupported source type: {type(source)}")
    
    return df


def compare_playlists(playlist1, playlist2, name1="Playlist 1", name2="Playlist 2", 
                      model_bundle_path='model_bundle.pkl'):
    """
    比较两个歌单的情绪特征
    
    Args:
        playlist1, playlist2: CSV路径 / DataFrame / dict list
        name1, name2: 歌单名称（用于显示）
    
    Returns:
        比较结果 dict
    """
    import pickle
    
    # 加载模型
    with open(model_bundle_path, 'rb') as f:
        bundle = pickle.load(f)
    model = bundle['model']
    vectorizer = bundle['vectorizer']
    
    # 加载歌单
    df1 = load_playlist(playlist1)
    df2 = load_playlist(playlist2)
    
    # 目标特征
    target_features = ['valence', 'energy', 'danceability']
    
    def get_features(df):
        """获取或预测 audio features"""
        results = {}
        
        # 检查是否已有 audio features
        has_features = all(f in df.columns for f in target_features)
        has_tags = 'tags' in df.columns
        
        if has_features:
            # 直接用现有的
            for f in target_features:
                results[f] = df[f].mean()
            results['source'] = 'actual'
        elif has_tags:
            # 用 tags 预测
            # 标准化 tags 格式
            def normalize_tags(tags_str):
                if pd.isna(tags_str) or tags_str == "":
                    return ""
                tags = [t.strip().lower().replace(' ', '_').replace('-', '_') 
                        for t in str(tags_str).split(',')]
                return ','.join(tags)
            
            df['tags'] = df['tags'].fillna('').apply(normalize_tags)
            X = vectorizer.transform(df['tags'])
            preds = model.predict(X)
            for i, f in enumerate(target_features):
                results[f] = preds[:, i].mean()
            results['source'] = 'predicted'
        else:
            raise ValueError("DataFrame needs either audio features or tags column")
        
        return results
    
    feat1 = get_features(df1)
    feat2 = get_features(df2)
    
    # 计算差异
    comparison = {
        'playlist1': {'name': name1, 'tracks': len(df1), **feat1},
        'playlist2': {'name': name2, 'tracks': len(df2), **feat2},
        'difference': {}
    }
    
    for f in target_features:
        diff = feat1[f] - feat2[f]
        comparison['difference'][f] = diff
    
    # 情绪解读
    val_diff = comparison['difference']['valence']
    energy_diff = comparison['difference']['energy']
    
    interpretations = []
    
    if abs(val_diff) > 0.1:
        if val_diff > 0:
            interpretations.append(f"{name1} 比 {name2} 更积极/快乐 (valence +{val_diff:.2f})")
        else:
            interpretations.append(f"{name1} 比 {name2} 更消极/忧郁 (valence {val_diff:.2f})")
    
    if abs(energy_diff) > 0.1:
        if energy_diff > 0:
            interpretations.append(f"{name1} 比 {name2} 更有能量 (energy +{energy_diff:.2f})")
        else:
            interpretations.append(f"{name1} 比 {name2} 更平静/舒缓 (energy {energy_diff:.2f})")
    
    if not interpretations:
        interpretations.append("两个歌单情绪特征相似")
    
    comparison['interpretation'] = interpretations
    
    return comparison


def print_comparison(comparison):
    """打印比较结果"""
    p1 = comparison['playlist1']
    p2 = comparison['playlist2']
    
    print("\n" + "=" * 60)
    print("🎵 歌单情绪比较")
    print("=" * 60)
    
    print(f"\n📀 {p1['name']} ({p1['tracks']} tracks)")
    print(f"   Valence:      {p1['valence']:.3f}")
    print(f"   Energy:       {p1['energy']:.3f}")
    print(f"   Danceability: {p1['danceability']:.3f}")
    print(f"   [数据来源: {p1['source']}]")
    
    print(f"\n📀 {p2['name']} ({p2['tracks']} tracks)")
    print(f"   Valence:      {p2['valence']:.3f}")
    print(f"   Energy:       {p2['energy']:.3f}")
    print(f"   Danceability: {p2['danceability']:.3f}")
    print(f"   [数据来源: {p2['source']}]")
    
    print("\n" + "-" * 60)
    print("📊 差异分析:")
    for interp in comparison['interpretation']:
        print(f"   • {interp}")
    
    # 可视化（ASCII art）
    print("\n" + "-" * 60)
    print("📈 Valence-Energy 四象限:")
    print("""
                    High Energy
                         │
           Angry/        │        Happy/
           Intense       │        Energetic
                         │
    ─────────────────────┼───────────────────── High Valence
                         │
           Sad/          │        Peaceful/
           Melancholic   │        Content
                         │
                    Low Energy
    """)
    
    def get_quadrant(v, e):
        if v >= 0.5 and e >= 0.5:
            return "Happy/Energetic (右上)"
        elif v >= 0.5 and e < 0.5:
            return "Peaceful/Content (右下)"
        elif v < 0.5 and e >= 0.5:
            return "Angry/Intense (左上)"
        else:
            return "Sad/Melancholic (左下)"
    
    q1 = get_quadrant(p1['valence'], p1['energy'])
    q2 = get_quadrant(p2['valence'], p2['energy'])
    
    print(f"   {p1['name']}: {q1}")
    print(f"   {p2['name']}: {q2}")


# ============================================
# 3. 按需爬取缺失的 tags
# ============================================

def fill_missing_tags(df, api_key, output_path=None):
    """
    为没有 tags 的歌曲爬取 Last.fm tags
    """
    from lastfm_scraper import LastFMScraper
    
    # 找出缺失 tags 的行
    missing_mask = df['tags'].isna() | (df['tags'] == '')
    missing_count = missing_mask.sum()
    
    if missing_count == 0:
        print("✅ 所有歌曲都有 tags，无需爬取")
        return df
    
    print(f"需要爬取 {missing_count} 首歌的 tags...")
    
    scraper = LastFMScraper(api_key)
    
    # 爬取
    for idx in df[missing_mask].index:
        artist = df.loc[idx, 'artist']
        track = df.loc[idx, 'name']
        
        tags_str = scraper.get_tags_string(artist, track)
        df.loc[idx, 'tags'] = tags_str
        
        if (idx + 1) % 50 == 0:
            print(f"  已处理 {idx + 1} 首...")
    
    scraper.close()
    
    # 保存
    if output_path:
        df.to_csv(output_path, index=False)
        print(f"✅ 已保存到 {output_path}")
    
    return df


# ============================================
# Main
# ============================================

if __name__ == "__main__":
    import sys
    
    print("""
╔══════════════════════════════════════════════════════════╗
║           歌单情绪分析工具 - 使用指南                      ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  1. 合并数据集:                                           ║
║     python playlist_tools.py merge data1.csv data2.csv   ║
║                                                          ║
║  2. 比较两个歌单:                                         ║
║     python playlist_tools.py compare p1.csv p2.csv       ║
║                                                          ║
║  3. 为缺失 tags 的歌曲爬取:                               ║
║     python playlist_tools.py fill data.csv               ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    if len(sys.argv) < 2:
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == "merge" and len(sys.argv) >= 4:
        merge_datasets(sys.argv[2], sys.argv[3])
    
    elif cmd == "compare" and len(sys.argv) >= 4:
        result = compare_playlists(
            sys.argv[2], sys.argv[3],
            name1=Path(sys.argv[2]).stem,
            name2=Path(sys.argv[3]).stem
        )
        print_comparison(result)
    
    elif cmd == "fill" and len(sys.argv) >= 3:
        from config import LASTFM_API_KEY
        df = pd.read_csv(sys.argv[2])
        fill_missing_tags(df, LASTFM_API_KEY, sys.argv[2])
    
    else:
        print("参数错误，请查看上面的使用指南")
