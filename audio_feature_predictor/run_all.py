"""
一键运行全部流程
"""

print("="*50)
print("Step 1/3: 训练模型...")
print("="*50)
from train_model import main as train
train("merged_data.csv")

print("\n" + "="*50)
print("Step 2/3: 爬取 Last.fm tags...")
print("="*50)
from config import LASTFM_API_KEY
from lastfm_scraper import fetch_taylor_swift_discography, fetch_linkin_park_discography
fetch_taylor_swift_discography(LASTFM_API_KEY)
fetch_linkin_park_discography(LASTFM_API_KEY)

print("\n" + "="*50)
print("Step 3/3: 分析结果...")
print("="*50)
from predict_analyze import demo_linkin_park_analysis, demo_taylor_swift_analysis
demo_linkin_park_analysis()
demo_taylor_swift_analysis()

print("\n" + "🎉"*20)
print("完成！")
