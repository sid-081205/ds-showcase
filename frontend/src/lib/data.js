export const moodData = {
    user: "User",
    currentMood: "Energetic",
    trends: [
        { name: "Mon", energy: 80, happiness: 60, sadness: 10 },
        { name: "Tue", energy: 90, happiness: 70, sadness: 5 },
        { name: "Wed", energy: 60, happiness: 50, sadness: 40 },
        { name: "Thu", energy: 100, happiness: 90, sadness: 0 },
        { name: "Fri", energy: 70, happiness: 80, sadness: 10 },
        { name: "Sat", energy: 95, happiness: 85, sadness: 5 },
        { name: "Sun", energy: 65, happiness: 75, sadness: 15 },
    ],
    topArtists: ["The Weeknd", "Dua Lipa", "Kendrick Lamar", "Tame Impala"]
};

export const friendsData = [
    { name: "Alice", match: 85, topGenre: "Pop" },
    { name: "Bob", match: 40, topGenre: "Rock" },
    { name: "Charlie", match: 92, topGenre: "Hip Hop" },
    { name: "Diana", match: 65, topGenre: "Indie" }
];

// Genre distribution for pie chart
export const genreData = [
    { name: "Pop", value: 35, color: "hsl(84, 100%, 73%)" },
    { name: "Hip Hop", value: 25, color: "hsl(359, 100%, 80%)" },
    { name: "Indie", value: 20, color: "hsl(154, 91%, 75%)" },
    { name: "Electronic", value: 12, color: "hsl(45, 100%, 70%)" },
    { name: "Rock", value: 8, color: "hsl(280, 80%, 75%)" },
];

// Audio features for radar chart
export const audioFeatures = [
    { feature: "Danceability", value: 82, fullMark: 100 },
    { feature: "Energy", value: 75, fullMark: 100 },
    { feature: "Speechiness", value: 45, fullMark: 100 },
    { feature: "Acousticness", value: 30, fullMark: 100 },
    { feature: "Liveness", value: 55, fullMark: 100 },
    { feature: "Valence", value: 68, fullMark: 100 },
];

// Listening hours by time of day
export const listeningHours = [
    { time: "6AM", hours: 0.5 },
    { time: "9AM", hours: 1.2 },
    { time: "12PM", hours: 0.8 },
    { time: "3PM", hours: 1.5 },
    { time: "6PM", hours: 2.3 },
    { time: "9PM", hours: 3.1 },
    { time: "12AM", hours: 1.8 },
];

// Top tracks data
export const topTracks = [
    { rank: 1, name: "Blinding Lights", artist: "The Weeknd", plays: 156, duration: "3:20" },
    { rank: 2, name: "Levitating", artist: "Dua Lipa", plays: 132, duration: "3:23" },
    { rank: 3, name: "HUMBLE.", artist: "Kendrick Lamar", plays: 98, duration: "2:57" },
    { rank: 4, name: "The Less I Know The Better", artist: "Tame Impala", plays: 87, duration: "3:36" },
    { rank: 5, name: "Bad Guy", artist: "Billie Eilish", plays: 76, duration: "3:14" },
];

// Monthly listening stats
export const monthlyStats = [
    { month: "Jan", minutes: 2400 },
    { month: "Feb", minutes: 2100 },
    { month: "Mar", minutes: 2800 },
    { month: "Apr", minutes: 3200 },
    { month: "May", minutes: 2900 },
    { month: "Jun", minutes: 3500 },
    { month: "Jul", minutes: 4100 },
    { month: "Aug", minutes: 3800 },
    { month: "Sep", minutes: 3300 },
    { month: "Oct", minutes: 2700 },
    { month: "Nov", minutes: 3100 },
    { month: "Dec", minutes: 3600 },
];

// Mood score over time (area chart)
export const moodScoreHistory = [
    { week: "Week 1", mood: 65, energy: 70 },
    { week: "Week 2", mood: 72, energy: 68 },
    { week: "Week 3", mood: 58, energy: 55 },
    { week: "Week 4", mood: 80, energy: 85 },
    { week: "Week 5", mood: 75, energy: 78 },
    { week: "Week 6", mood: 88, energy: 92 },
];

// Listening stats summary
export const listeningSummary = {
    totalMinutes: 38500,
    totalTracks: 2847,
    uniqueArtists: 342,
    topGenre: "Pop",
    avgSessionLength: 45,
    longestStreak: 28,
};
