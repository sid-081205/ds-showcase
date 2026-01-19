"""
诊断脚本：检查为什么 energy 预测没有变化
"""

import pandas as pd
import numpy as np
import pickle
import json

print("=" * 60)
print("🔍 诊断：Energy 预测问题")
print("=" * 60)

# 1. 加载模型和 vectorizer
print("\n[1] 加载模型...")
with open('model_bundle.pkl', 'rb') as f:
    bundle = pickle.load(f)
model = bundle['model']
vectorizer = bundle['vectorizer']

# 2. 查看 vectorizer 学到的词汇
print("\n[2] TF-IDF Vectorizer 词汇表:")
vocab = vectorizer.get_feature_names_out()
# 检查是否有前导空格
has_leading_space = any(v.startswith(' ') for v in vocab)
print(f"    词汇表大小: {len(vocab)}")
print(f"    有前导空格: {'⚠️ 是 (这是bug!)' if has_leading_space else '✓ 否'}")
print(f"    前 30 个词: {list(vocab[:30])}")

# 3. 检查 energy 相关的词是否在词汇表里
energy_related = ['energetic', 'chill', 'chillout', 'mellow', 'ambient', 
                  'upbeat', 'calm', 'relaxing', 'intense', 'aggressive',
                  'soft', 'hard', 'heavy', 'light', 'loud', 'quiet']

print("\n[3] Energy 相关词汇检查:")
for word in energy_related:
    in_vocab = word in vocab
    print(f"    {word:15} {'✓ 在词汇表中' if in_vocab else '✗ 不在词汇表中'}")

# 4. 加载 Last.fm 爬取的数据，检查 token 匹配情况
print("\n[4] 检查 Last.fm tags 的匹配率...")

def check_tag_coverage(csv_path):
    try:
        df = pd.read_csv(csv_path)
        if 'tags' not in df.columns:
            print(f"    {csv_path}: 没有 tags 列")
            return
        
        all_tags = []
        for tags_str in df['tags'].dropna():
            # 按逗号分隔
            tags = [t.strip().lower() for t in str(tags_str).split(',')]
            all_tags.extend(tags)
        
        unique_tags = set(all_tags)
        matched = unique_tags & set(vocab)
        unmatched = unique_tags - set(vocab)
        
        print(f"\n    📄 {csv_path}:")
        print(f"       总 tags 数: {len(all_tags)}")
        print(f"       Unique tags: {len(unique_tags)}")
        print(f"       匹配词汇表: {len(matched)} ({100*len(matched)/max(len(unique_tags),1):.1f}%)")
        print(f"       未匹配: {len(unmatched)}")
        
        if unmatched:
            print(f"       未匹配的 tags (前20个): {list(unmatched)[:20]}")
        
        return matched, unmatched
        
    except FileNotFoundError:
        print(f"    {csv_path}: 文件不存在")
        return None, None

# 检查几个文件
for f in ['taylor_swift_tags.csv', 'linkin_park_tags.csv', 
          'playlist_Hurry Up Tomorrow.csv', 'playlist_Tsunami Sea.csv']:
    check_tag_coverage(f)

# 5. 测试 vectorizer 对新 tags 的转换
print("\n[5] 测试 Vectorizer 转换:")

test_cases = [
    "rock, alternative_rock, nu_metal",  # 应该匹配
    "pop, synthpop, rnb",                 # 部分匹配
    "j_pop, doujin, vocaloid",            # 可能不匹配
]

for tags_str in test_cases:
    X = vectorizer.transform([tags_str])
    non_zero = X.nnz  # 非零元素数量
    print(f"    '{tags_str[:40]}...'")
    print(f"       非零特征数: {non_zero}")

# 6. 检查模型对 energy 的预测分布
print("\n[6] 模型预测测试:")

# 用一些极端的 tags 测试
extreme_cases = {
    "ambient, chillout, relaxing, calm, soft": "应该低 energy",
    "metal, heavy_metal, hard_rock, aggressive, intense": "应该高 energy",
    "pop, dance, electronic, energetic, upbeat": "应该高 energy",
    "acoustic, folk, singer_songwriter, mellow": "应该低 energy",
    "": "空 tags (baseline)",
}

for tags_str, expected in extreme_cases.items():
    X = vectorizer.transform([tags_str])
    pred = model.predict(X)[0]
    # 假设 energy 是第二个特征 (index 1)
    print(f"\n    Tags: '{tags_str[:50]}...'")
    print(f"    预期: {expected}")
    print(f"    预测: valence={pred[0]:.3f}, energy={pred[1]:.3f}, danceability={pred[2]:.3f}")

# 7. 加载训练数据，检查 energy 和 tags 的实际关系
print("\n[7] 训练数据中 Energy 与 Tags 的关系:")
try:
    df_train = pd.read_csv('merged_data.csv')
    
    # 找出包含特定 tag 的歌曲的平均 energy
    def avg_energy_for_tag(tag):
        mask = df_train['tags'].str.contains(tag, case=False, na=False)
        if mask.sum() > 0:
            return df_train.loc[mask, 'energy'].mean(), mask.sum()
        return None, 0
    
    print("\n    各 tag 对应的平均 Energy:")
    check_tags = ['metal', 'ambient', 'chill', 'rock', 'electronic', 
                  'acoustic', 'pop', 'dance', 'hip_hop', 'classical']
    
    for tag in check_tags:
        avg, count = avg_energy_for_tag(tag)
        if avg:
            print(f"    {tag:15} → energy={avg:.3f} (n={count})")

except FileNotFoundError:
    print(" merged_data.csv 不存在")

print("\n" + "=" * 60)
print("诊断完成")
print("=" * 60)
