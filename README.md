# 🎵 Spotify Mood & DNA Review

Welcome to **Spotify Mood & DNA Review**, a deep dive into your musical soul. This isn't just another "wrapped" clone—it's a high-precision analysis tool designed to help you understand the *why* behind your listening habits, compare your vibe with your inner circle, and even peek into your musical future using machine learning.

![Home Page Placeholder](./assets/homepage.png)

## 🚀 What makes this special?

Most music apps just tell you what you listened to. We tell you what it *felt* like. By linking your Spotify account, we pull your data through a sophisticated pipeline that combines official APIs with deep metadata scraping.

### 🧬 Audio DNA Extraction
We don't just look at genres. Our backend uses **MusicBrainz** and **AcousticBrainz** integration to perform "DNA Extraction" on your tracks. We analyze:
- **Danceability**: How movement-friendly is your library?
- **Mood Profile**: Are you in a "Chaotic Good" phase or a "Deep Melancholy" streak?
- **Energy Levels**: Mapping your hype cycles throughout the week.

### 📊 Deep Song Analysis
Through custom web scraping and API enrichment, we retrieve high-level acoustic features that Spotify's basic interface hides. You'll see beautiful, neo-brutalist charts (Radar, Area, and Bar charts) that visualize your "Audio DNA" in real-time.

![Mood Analysis Placeholder](./assets/analysis.png)

### 👯‍♂️ Active Friend Comparison
Music is social. Our **Compare** feature allows you to link up with friends to see how your "Musical DNA" matches. 
- Are you the "Energy Peak" of the group? 
- Who has the most eccentric taste? 
- Get a "Match Score" based on overlapping genres and mood profiles.

### 🔮 Predictive AI (The Future Vibe)
We use a **Supervised Machine Learning algorithm** (trained on thousands of acoustic profiles) to predict what you'll be obsessed with next. By analyzing your historical energy shifts and mood transitions, the system identifies evolving patterns in your taste before you even realize they're changing.

---

## 🛠️ Under the Hood

### The Tech Stack
- **Frontend**: React (Vite) + Tailwind CSS + Lucide Icons (Neo-brutalist Design System).
- **Backend**: Python Flask API handling OAuth2 authentication.
- **Database**: SQLite for local, lightning-fast caching of your listening history.
- **Analysis Engine**: A background Python worker that processes ISRC data to fetch MBIDs and acoustic features.

### Getting Started

1. **Clone the repo** and install dependencies for both the frontend (npm) and backend (pip).
2. **Setup your environment**: Add your `SPOTIPY_CLIENT_ID`, `SPOTIPY_CLIENT_SECRET`, and `SPOTIPY_REDIRECT_URI` to a `.env` file.
3. **Run the Backend**: `python3 "spotify data collection/spotify_collector.py"`
4. **Start the Frontend**: `npm run dev`
5. **Analyze**: Head to `localhost:5173`, link your account, and let the extraction begin!

---

*Built with ❤️ for serious music nerds.*
