"""
Spotify 歌单导入工具
输入歌单链接 → 获取歌曲列表 → 爬 Last.fm tags → 预测情绪
"""

import requests
import base64
import re
import pandas as pd
from pathlib import Path


class SpotifyClient:
    """Spotify API 客户端"""
    
    AUTH_URL = "https://accounts.spotify.com/api/token"
    API_BASE = "https://api.spotify.com/v1"
    
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None
        self._authenticate()
    
    def _authenticate(self):
        """获取 access token (Client Credentials Flow)"""
        auth_str = f"{self.client_id}:{self.client_secret}"
        auth_b64 = base64.b64encode(auth_str.encode()).decode()
        
        response = requests.post(
            self.AUTH_URL,
            headers={"Authorization": f"Basic {auth_b64}"},
            data={"grant_type": "client_credentials"}
        )
        
        if response.status_code != 200:
            raise Exception(f"Spotify auth failed: {response.text}")
        
        self.token = response.json()["access_token"]
        print("✅ Spotify 认证成功")
    
    def _get(self, endpoint, params=None):
        """发送 GET 请求"""
        response = requests.get(
            f"{self.API_BASE}/{endpoint}",
            headers={"Authorization": f"Bearer {self.token}"},
            params=params
        )
        
        if response.status_code != 200:
            raise Exception(f"API error: {response.status_code} - {response.text}")
        
        return response.json()
    
    def get_playlist(self, playlist_id):
        """获取歌单信息和曲目"""
        # 获取歌单基本信息
        playlist = self._get(f"playlists/{playlist_id}")
        
        name = playlist["name"]
        description = playlist.get("description", "")
        total_tracks = playlist["tracks"]["total"]
        
        print(f"\n📀 歌单: {name}")
        print(f"   曲目数: {total_tracks}")
        
        # 获取所有曲目（分页处理）
        tracks = []
        offset = 0
        limit = 100
        
        while offset < total_tracks:
            result = self._get(
                f"playlists/{playlist_id}/tracks",
                params={"offset": offset, "limit": limit}
            )
            
            for item in result["items"]:
                track = item.get("track")
                if track is None:
                    continue
                
                # 提取艺术家名（可能有多个）
                artists = ", ".join([a["name"] for a in track["artists"]])
                
                tracks.append({
                    "track_id": track["id"],
                    "name": track["name"],
                    "artist": artists,
                    "album": track["album"]["name"],
                    "duration_ms": track["duration_ms"],
                    "popularity": track["popularity"],
                })
            
            offset += limit
            print(f"   已获取 {min(offset, total_tracks)}/{total_tracks} 首...")
        
        return {
            "name": name,
            "description": description,
            "tracks": pd.DataFrame(tracks)
        }
    
    @staticmethod
    def extract_playlist_id(url_or_id):
        """从 URL 或 URI 中提取 playlist ID"""
        # 支持的格式:
        # - https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M
        # - spotify:playlist:37i9dQZF1DXcBWIGoYBM5M
        # - 37i9dQZF1DXcBWIGoYBM5M
        
        patterns = [
            r'playlist[/:]([a-zA-Z0-9]+)',  # URL or URI
            r'^([a-zA-Z0-9]{22})$',          # Raw ID
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url_or_id)
            if match:
                return match.group(1)
        
        return url_or_id  # 假设就是 ID


def import_playlist(playlist_url, client_id, client_secret, 
                    lastfm_api_key=None, output_path=None):
    """
    导入 Spotify 歌单并获取 Last.fm tags
    
    Args:
        playlist_url: Spotify 歌单链接或 ID
        client_id: Spotify Client ID
        client_secret: Spotify Client Secret
        lastfm_api_key: Last.fm API Key (可选，用于获取 tags)
        output_path: 输出 CSV 路径 (可选)
    
    Returns:
        DataFrame with tracks and tags
    """
    # 连接 Spotify
    spotify = SpotifyClient(client_id, client_secret)
    
    # 提取 playlist ID
    playlist_id = SpotifyClient.extract_playlist_id(playlist_url)
    print(f"Playlist ID: {playlist_id}")
    
    # 获取歌单
    playlist = spotify.get_playlist(playlist_id)
    df = playlist["tracks"]
    
    # 获取 Last.fm tags（如果提供了 API key）
    if lastfm_api_key:
        print("\n正在获取 Last.fm tags...")
        from lastfm_scraper import LastFMScraper
        
        scraper = LastFMScraper(lastfm_api_key)
        
        tags_list = []
        for idx, row in df.iterrows():
            # 只用第一个艺术家（多艺术家时）
            artist = row["artist"].split(",")[0].strip()
            track = row["name"]
            
            tags_str = scraper.get_tags_string(artist, track)
            tags_list.append(tags_str)
            
            if (idx + 1) % 20 == 0:
                print(f"   已处理 {idx + 1}/{len(df)} 首...")
        
        scraper.close()
        df["tags"] = tags_list
        
        # 统计
        has_tags = df["tags"].str.len() > 0
        print(f"\n✅ Tags 获取完成")
        print(f"   有 tags: {has_tags.sum()}/{len(df)}")
    
    # 保存
    if output_path is None:
        # 用歌单名作为文件名
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', playlist["name"])
        output_path = f"playlist_{safe_name}.csv"
    
    df.to_csv(output_path, index=False)
    print(f"\n💾 已保存到: {output_path}")
    
    return df, playlist["name"]


def analyze_spotify_playlist(playlist_url, model_path="model_bundle.pkl"):
    """
    一键分析 Spotify 歌单情绪
    
    需要先在 config.py 配置好各种密钥
    """
    from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, LASTFM_API_KEY
    import pickle
    
    # 导入歌单
    df, playlist_name = import_playlist(
        playlist_url,
        SPOTIFY_CLIENT_ID,
        SPOTIFY_CLIENT_SECRET,
        LASTFM_API_KEY
    )
    
    # 加载模型
    with open(model_path, "rb") as f:
        bundle = pickle.load(f)
    model = bundle["model"]
    vectorizer = bundle["vectorizer"]
    
    # 预测
    # 标准化 tags 格式
    def normalize_tags(tags_str):
        if pd.isna(tags_str) or tags_str == "":
            return ""
        tags = [t.strip().lower().replace(' ', '_').replace('-', '_') 
                for t in str(tags_str).split(',')]
        return ','.join(tags)
    
    df["tags"] = df["tags"].fillna("").apply(normalize_tags)
    X = vectorizer.transform(df["tags"])
    
    target_features = ["valence", "energy", "danceability"]
    preds = model.predict(X)
    
    for i, feat in enumerate(target_features):
        df[f"pred_{feat}"] = preds[:, i]
    
    # 分析
    print("\n" + "=" * 60)
    print(f"🎵 歌单分析: {playlist_name}")
    print("=" * 60)
    
    print(f"\n📊 整体情绪:")
    for feat in target_features:
        col = f"pred_{feat}"
        print(f"   {feat.capitalize():15} {df[col].mean():.3f} (±{df[col].std():.3f})")
    
    # 情绪象限
    avg_valence = df["pred_valence"].mean()
    avg_energy = df["pred_energy"].mean()
    
    if avg_valence >= 0.5 and avg_energy >= 0.5:
        mood = "😄 Happy/Energetic - 积极、有能量"
    elif avg_valence >= 0.5 and avg_energy < 0.5:
        mood = "😌 Peaceful/Content - 平静、舒适"
    elif avg_valence < 0.5 and avg_energy >= 0.5:
        mood = "😤 Angry/Intense - 激烈、有张力"
    else:
        mood = "😢 Sad/Melancholic - 忧郁、沉思"
    
    print(f"\n🎭 整体氛围: {mood}")
    
    # 最 happy / 最 sad 的歌
    print(f"\n🌟 最积极的 3 首:")
    top_happy = df.nlargest(3, "pred_valence")[["name", "artist", "pred_valence"]]
    for _, row in top_happy.iterrows():
        print(f"   • {row['name']} - {row['artist']} (valence: {row['pred_valence']:.3f})")
    
    print(f"\n💧 最忧郁的 3 首:")
    top_sad = df.nsmallest(3, "pred_valence")[["name", "artist", "pred_valence"]]
    for _, row in top_sad.iterrows():
        print(f"   • {row['name']} - {row['artist']} (valence: {row['pred_valence']:.3f})")
    
    return df


# ============================================
# Main
# ============================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("""
╔══════════════════════════════════════════════════════════╗
║          Spotify 歌单导入工具                              ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  使用前先在 config.py 添加:                               ║
║                                                          ║
║    SPOTIFY_CLIENT_ID = "你的 Client ID"                   ║
║    SPOTIFY_CLIENT_SECRET = "你的 Client Secret"           ║
║                                                          ║
║  使用方法:                                                ║
║    python spotify_import.py <歌单链接>                    ║
║                                                          ║
║  示例:                                                    ║
║    python spotify_import.py https://open.spotify.com/... ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
        """)
        sys.exit(0)
    
    playlist_url = sys.argv[1]
    
    try:
        analyze_spotify_playlist(playlist_url)
    except ImportError as e:
        if "SPOTIFY" in str(e):
            print("❌ 请在 config.py 中配置 SPOTIFY_CLIENT_ID 和 SPOTIFY_CLIENT_SECRET")
        else:
            raise
