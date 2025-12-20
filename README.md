# audire

**discover your music story through data**

audire is a full-stack web application that analyzes your spotify listening history to reveal insights about your mood, energy, and musical journey. create parties with friends to see how your music tastes connect and interact.

## features

- **spotify integration** - seamless oauth authentication with spotify
- **mood tracking** - visualize how your musical mood has evolved over 6 months
- **audio analysis** - deep dive into the energy, danceability, valence, and other audio features of your favorite tracks
- **professional visualizations** - interactive charts using recharts (radar, line, bar, scatter)
- **party mode** - create parties to compare music tastes with friends
- **multi-user insights** - see compatibility scores and shared artists between party members
- **anytime wrapped** - get spotify wrapped-style insights whenever you want

## tech stack

### frontend
- react 18
- vite
- react router
- recharts (data visualization)
- axios
- jetbrains mono font
- spotify green theme (#1db954)

### backend
- node.js with express
- sqlite3 database
- spotify web api
- spotify audio features api

## project structure

```
audire/
├── frontend/           # react + vite frontend
│   ├── src/
│   │   ├── pages/
│   │   │   ├── home.jsx
│   │   │   ├── insights.jsx
│   │   │   ├── parties.jsx
│   │   │   └── callback.jsx
│   │   ├── app.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
│
└── backend/            # express backend
    ├── server.js       # main server with all routes
    ├── database.js     # sqlite database setup
    ├── spotify.js      # spotify api integration
    ├── .env            # spotify credentials (already configured)
    └── package.json
```

## setup & installation

### 1. spotify credentials (already configured)

your spotify app credentials are already set in `backend/.env`:
- client id: dcac6de719364cdfbca0403b1c0b7e98
- client secret: 57fc216ffd474f72ae7a213e8c9f7fce
- redirect uri: http://127.0.0.1:5173/callback

### 2. start the backend

```bash
cd backend
npm start
```

the backend will run on http://localhost:3001

### 3. start the frontend (in a new terminal)

```bash
cd frontend
npm run dev
```

the frontend will run on http://127.0.0.1:5173

### 4. open the app

navigate to http://127.0.0.1:5173 in your browser

## how to use

### 1. connect spotify
- click the "connect spotify" button in the top right
- authorize audire to access your spotify data
- you'll be redirected back to the app

### 2. view insights
- navigate to "extracting insights" to see:
  - your music statistics (tracks, artists, playlists)
  - mood progression over 6 months
  - your music vibe profile (radar chart)
  - top genres
  - energy vs happiness scatter plot
  - top artists

### 3. create parties
- navigate to "creating parties"
- click "+ create party"
- give your party a name
- share the party with friends
- once friends join and connect their spotify accounts, view combined insights:
  - group compatibility score
  - vibe comparison between members
  - mood alignment over time
  - shared artists

## api endpoints

### authentication
- `GET /auth/login` - initiate spotify oauth flow
- `POST /auth/callback` - handle oauth callback and exchange code for tokens

### user data
- `GET /api/user/:userId` - get user profile
- `GET /api/insights/:userId` - get user's music insights and visualizations

### parties
- `POST /api/parties` - create a new party
- `GET /api/parties/user/:userId` - get all parties for a user
- `POST /api/parties/:partyId/join` - join a party
- `GET /api/parties/:partyId/insights` - get combined insights for party members

## database schema

### users
- stores user profile and spotify tokens

### tracks
- stores track information (name, artist, album, popularity)

### audio_features
- stores spotify audio features (danceability, energy, valence, etc.)

### artists
- stores artist information and genres

### playlists
- stores user playlists

### parties
- stores party information

### party_members
- links users to parties

### user_tracks
- links users to their listened tracks

### user_artists
- links users to their favorite artists

## spotify audio features explained

- **danceability** - how suitable a track is for dancing (0.0 to 1.0)
- **energy** - intensity and activity measure (0.0 to 1.0)
- **valence** - musical positiveness/happiness (0.0 to 1.0)
- **speechiness** - presence of spoken words (0.0 to 1.0)
- **acousticness** - confidence the track is acoustic (0.0 to 1.0)
- **instrumentalness** - predicts if track has no vocals (0.0 to 1.0)

## design philosophy

- **aesthetic minimalism** - clean spotify-inspired design
- **small caps typography** - jetbrains mono for a unique, technical feel
- **data-driven insights** - meaningful visualizations that tell a story
- **social discovery** - connect through music with friends

## future enhancements

- time range selection (short/medium/long term)
- playlist analysis and recommendations
- export insights as images
- party invites via link sharing
- real-time party updates
- more correlation metrics
- genre evolution over time
- mood-based playlist generation

## troubleshooting

### oauth redirect issues
- make sure the frontend is running on exactly http://127.0.0.1:5173
- if using localhost instead, update the redirect uri in spotify dashboard

### no insights showing
- wait a few seconds after first login for data to be fetched
- click the "refresh" button on the insights page
- check backend console for any errors

### database issues
- delete `backend/audire.db` and restart the backend to reset the database

## license

mit

---

**built with ♫ for music lovers**
