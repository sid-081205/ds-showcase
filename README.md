# audire (name tbd)

![home page placeholder](./assets/homepage.png)

## what makes this special?

most music apps just tell you what you listened to. we tell you what it felt like. by linking your spotify account, we pull your data through a sophisticated pipeline that combines official apis with deep metadata scraping and insights from curated kaggle datasets.

### audio dna extraction
we don't just look at genres. our backend uses musicbrainz and acousticbrainz integration to perform "dna extraction" on your tracks. we analyze:
- danceability: how movement-friendly is your library?
- mood profile: are you in a "chaotic good" phase or a "deep melancholy" streak?
- energy levels: mapping your hype cycles throughout the week.

### deep song analysis
through custom web scraping and api enrichment, we retrieve high-level acoustic features that spotify's basic interface hides. we've integrated extensive kaggle music datasets to provide deeper context and benchmarks for your listening patterns. you'll see beautiful, neo-brutalist charts (radar, area, and bar charts) that visualize your "audio dna" in real-time.

![mood analysis placeholder](./assets/analysis.png)

### active friend comparison
music is social. our compare feature allows you to link up with friends to see how your "musical dna" matches. 
- are you the "energy peak" of the group? 
- who has the most eccentric taste? 
- get a "match score" based on overlapping genres and mood profiles.

### predictive ai (the future vibe)
we use a supervised machine learning algorithm—trained using web-scraped data and massive kaggle datasets—to predict what you'll be obsessed with next. by analyzing your historical energy shifts and mood transitions, the system identifies evolving patterns in your taste before you even realize they're changing.

---

## under the hood

### the tech stack
- frontend: react (vite) + tailwind css + lucide icons (neo-brutalist design system)
- backend: python flask api handling oauth2 authentication
- database: sqlite for local, lightning-fast caching of your listening history
- analysis engine: a background python worker that processes isrc data to fetch mbids and acoustic features

### getting started

1. clone the repo and install dependencies for both the frontend (npm) and backend (pip).
2. setup your environment: add your spotipy_client_id, spotipy_client_secret, and spotipy_redirect_uri to a .env file.
3. run the backend: python3 "spotify data collection/spotify_collector.py"
4. start the frontend: npm run dev
5. analyze: head to localhost:5173, link your account, and let the extraction begin!

---

*built for serious music nerds.*
