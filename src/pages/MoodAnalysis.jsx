import React from "react"
import {
    moodData,
    genreData,
    audioFeatures,
    listeningHours,
    topTracks,
    monthlyStats,
    moodScoreHistory,
    listeningSummary
} from "@/lib/data"
import {
    BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
    PieChart, Pie,
    RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
    AreaChart, Area,
    LineChart, Line
} from 'recharts'
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Music, Clock, Disc, TrendingUp, Headphones, Zap, Heart, BarChart3 } from "lucide-react"

// Neo-brutalist tooltip component
const NeoTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
        return (
            <div className="bg-white border-3 border-black shadow-neo p-3 font-bold">
                <p className="text-sm underline decoration-2 mb-1">{label}</p>
                {payload.map((entry, index) => (
                    <p key={index} style={{ color: entry.color || entry.fill }} className="text-sm">
                        {entry.name}: {entry.value}
                    </p>
                ))}
            </div>
        );
    }
    return null;
};

// Custom external label for donut chart
const renderCustomizedLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent, name, value }) => {
    const RADIAN = Math.PI / 180;
    const radius = outerRadius + 30; // Position outside the donut
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);

    return (
        <text
            x={x}
            y={y}
            fill="black"
            textAnchor={x > cx ? 'start' : 'end'}
            dominantBaseline="central"
            className="font-black text-sm"
        >
            {`${name} ${(percent * 100).toFixed(0)}%`}
        </text>
    );
};

export default function MoodAnalysis() {
    const { currentMood, trends, topArtists } = moodData;

    return (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Header */}
            <div>
                <h1 className="text-5xl font-black uppercase tracking-tighter mb-2">
                    MOOD ANALYSIS
                </h1>
                <p className="text-xl font-medium text-muted-foreground">
                    Deep dive into your listening soul.
                </p>
            </div>

            {/* Stats Cards Row */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Card className="bg-primary neo-brutal">
                    <CardContent className="p-4 flex flex-col items-center justify-center text-center">
                        <Clock className="w-8 h-8 mb-2" />
                        <p className="text-3xl font-black">{Math.round(listeningSummary.totalMinutes / 60)}h</p>
                        <p className="text-sm font-bold uppercase">Total Listened</p>
                    </CardContent>
                </Card>
                <Card className="bg-secondary neo-brutal">
                    <CardContent className="p-4 flex flex-col items-center justify-center text-center">
                        <Music className="w-8 h-8 mb-2" />
                        <p className="text-3xl font-black">{listeningSummary.totalTracks.toLocaleString()}</p>
                        <p className="text-sm font-bold uppercase">Tracks Played</p>
                    </CardContent>
                </Card>
                <Card className="bg-accent neo-brutal">
                    <CardContent className="p-4 flex flex-col items-center justify-center text-center">
                        <Disc className="w-8 h-8 mb-2" />
                        <p className="text-3xl font-black">{listeningSummary.uniqueArtists}</p>
                        <p className="text-sm font-bold uppercase">Artists</p>
                    </CardContent>
                </Card>
                <Card className="bg-white neo-brutal">
                    <CardContent className="p-4 flex flex-col items-center justify-center text-center">
                        <Zap className="w-8 h-8 mb-2" />
                        <p className="text-3xl font-black">{listeningSummary.longestStreak}</p>
                        <p className="text-sm font-bold uppercase">Day Streak</p>
                    </CardContent>
                </Card>
            </div>

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Current Vibe Card */}
                <Card className="bg-primary neo-brutal">
                    <CardHeader className="border-b-3 border-black">
                        <CardTitle className="flex items-center gap-2 text-2xl">
                            <Heart className="w-6 h-6" />
                            YOUR CURRENT VIBE
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="p-6">
                        <div className="text-6xl font-black uppercase mb-4 tracking-tighter">
                            {currentMood}
                        </div>
                        <div className="space-y-3">
                            <p className="font-bold text-lg uppercase tracking-wide">Top Artists This Week:</p>
                            <div className="flex flex-wrap gap-2">
                                {topArtists.map((artist, i) => (
                                    <span
                                        key={i}
                                        className="bg-black text-white px-3 py-1 font-bold text-sm transform"
                                        style={{ transform: `rotate(${(i % 2 === 0 ? 1 : -1) * 2}deg)` }}
                                    >
                                        {artist}
                                    </span>
                                ))}
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Genre Distribution Donut Chart */}
                <Card className="bg-white neo-brutal">
                    <CardHeader className="border-b-3 border-black">
                        <CardTitle className="flex items-center gap-2 text-2xl">
                            <Disc className="w-6 h-6" />
                            GENRE BREAKDOWN
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="p-6">
                        <div className="h-[280px]">
                            <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                    <Pie
                                        data={genreData}
                                        cx="50%"
                                        cy="50%"
                                        labelLine={{
                                            stroke: 'black',
                                            strokeWidth: 2,
                                        }}
                                        label={renderCustomizedLabel}
                                        outerRadius={100}
                                        innerRadius={50}
                                        dataKey="value"
                                        stroke="black"
                                        strokeWidth={3}
                                    >
                                        {genreData.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={entry.color} />
                                        ))}
                                    </Pie>
                                    <Tooltip content={<NeoTooltip />} />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                    </CardContent>
                </Card>

                {/* Audio Features Radar Chart */}
                <Card className="bg-secondary neo-brutal">
                    <CardHeader className="border-b-3 border-black">
                        <CardTitle className="flex items-center gap-2 text-2xl">
                            <BarChart3 className="w-6 h-6" />
                            AUDIO DNA
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="h-[350px] p-6">
                        <ResponsiveContainer width="100%" height="100%">
                            <RadarChart data={audioFeatures}>
                                <PolarGrid
                                    stroke="black"
                                    strokeWidth={2}
                                    gridType="polygon"
                                />
                                <PolarAngleAxis
                                    dataKey="feature"
                                    tick={{ fill: 'black', fontWeight: 'bold', fontSize: 12 }}
                                />
                                <PolarRadiusAxis
                                    angle={30}
                                    domain={[0, 100]}
                                    tick={false}
                                    axisLine={false}
                                />
                                <Radar
                                    name="Audio Features"
                                    dataKey="value"
                                    stroke="black"
                                    strokeWidth={4}
                                    fill="hsl(84, 100%, 73%)"
                                    fillOpacity={0.8}
                                />
                                <Tooltip content={<NeoTooltip />} />
                            </RadarChart>
                        </ResponsiveContainer>
                    </CardContent>
                </Card>

                {/* Listening Hours Bar Chart */}
                <Card className="bg-accent neo-brutal">
                    <CardHeader className="border-b-3 border-black">
                        <CardTitle className="flex items-center gap-2 text-2xl">
                            <Headphones className="w-6 h-6" />
                            PEAK LISTENING HOURS
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="h-[350px] p-4">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={listeningHours}>
                                <XAxis
                                    dataKey="time"
                                    axisLine={{ stroke: 'black', strokeWidth: 3 }}
                                    tickLine={{ stroke: 'black', strokeWidth: 2 }}
                                    tick={{ fill: 'black', fontWeight: 'bold', fontSize: 12 }}
                                />
                                <YAxis
                                    axisLine={{ stroke: 'black', strokeWidth: 3 }}
                                    tickLine={{ stroke: 'black', strokeWidth: 2 }}
                                    tick={{ fill: 'black', fontWeight: 'bold' }}
                                    label={{ value: 'Hours', angle: -90, position: 'insideLeft', fontWeight: 'bold' }}
                                />
                                <Tooltip content={<NeoTooltip />} />
                                <Bar dataKey="hours" name="Hours" radius={[4, 4, 0, 0]}>
                                    {listeningHours.map((entry, index) => (
                                        <Cell
                                            key={`cell-${index}`}
                                            fill={entry.hours > 2 ? "hsl(359, 100%, 80%)" : "hsl(84, 100%, 73%)"}
                                            stroke="black"
                                            strokeWidth={3}
                                        />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </CardContent>
                </Card>
            </div>

            {/* Full Width Charts */}
            <div className="space-y-8">
                {/* Mood Score History Area Chart */}
                <Card className="bg-white neo-brutal">
                    <CardHeader className="border-b-3 border-black">
                        <CardTitle className="flex items-center gap-2 text-2xl">
                            <TrendingUp className="w-6 h-6" />
                            MOOD & ENERGY TREND
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="h-[300px] p-6">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={moodScoreHistory}>
                                <defs>
                                    <pattern id="stripes" patternUnits="userSpaceOnUse" width="4" height="4">
                                        <path d="M-1,1 l2,-2 M0,4 l4,-4 M3,5 l2,-2" stroke="black" strokeWidth="0.5" />
                                    </pattern>
                                </defs>
                                <XAxis
                                    dataKey="week"
                                    axisLine={{ stroke: 'black', strokeWidth: 3 }}
                                    tickLine={{ stroke: 'black', strokeWidth: 2 }}
                                    tick={{ fill: 'black', fontWeight: 'bold' }}
                                />
                                <YAxis
                                    domain={[0, 100]}
                                    axisLine={{ stroke: 'black', strokeWidth: 3 }}
                                    tickLine={{ stroke: 'black', strokeWidth: 2 }}
                                    tick={{ fill: 'black', fontWeight: 'bold' }}
                                />
                                <Tooltip content={<NeoTooltip />} />
                                <Area
                                    type="monotone"
                                    dataKey="mood"
                                    name="Mood Score"
                                    stroke="black"
                                    strokeWidth={3}
                                    fill="hsl(84, 100%, 73%)"
                                />
                                <Area
                                    type="monotone"
                                    dataKey="energy"
                                    name="Energy"
                                    stroke="black"
                                    strokeWidth={3}
                                    fill="hsl(359, 100%, 80%)"
                                    fillOpacity={0.6}
                                />
                            </AreaChart>
                        </ResponsiveContainer>
                    </CardContent>
                </Card>

                {/* Monthly Listening Stats */}
                <Card className="bg-primary neo-brutal">
                    <CardHeader className="border-b-3 border-black">
                        <CardTitle className="flex items-center gap-2 text-2xl">
                            <BarChart3 className="w-6 h-6" />
                            MONTHLY LISTENING TIME
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="h-[300px] p-6">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={monthlyStats}>
                                <XAxis
                                    dataKey="month"
                                    axisLine={{ stroke: 'black', strokeWidth: 3 }}
                                    tickLine={{ stroke: 'black', strokeWidth: 2 }}
                                    tick={{ fill: 'black', fontWeight: 'bold', fontSize: 11 }}
                                />
                                <YAxis
                                    axisLine={{ stroke: 'black', strokeWidth: 3 }}
                                    tickLine={{ stroke: 'black', strokeWidth: 2 }}
                                    tick={{ fill: 'black', fontWeight: 'bold' }}
                                    tickFormatter={(value) => `${Math.round(value / 60)}h`}
                                />
                                <Tooltip
                                    content={<NeoTooltip />}
                                    formatter={(value) => [`${Math.round(value / 60)} hours`, 'Listening Time']}
                                />
                                <Bar dataKey="minutes" name="Minutes" radius={[4, 4, 0, 0]}>
                                    {monthlyStats.map((entry, index) => (
                                        <Cell
                                            key={`cell-${index}`}
                                            fill={index === 6 ? "hsl(359, 100%, 80%)" : "white"}
                                            stroke="black"
                                            strokeWidth={3}
                                        />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </CardContent>
                </Card>

                {/* Top Tracks Table */}
                <Card className="bg-white neo-brutal">
                    <CardHeader className="border-b-3 border-black">
                        <CardTitle className="flex items-center gap-2 text-2xl">
                            <Music className="w-6 h-6" />
                            TOP TRACKS
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="p-0">
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead>
                                    <tr className="border-b-3 border-black bg-black text-white">
                                        <th className="p-4 text-left font-black uppercase">#</th>
                                        <th className="p-4 text-left font-black uppercase">Track</th>
                                        <th className="p-4 text-left font-black uppercase">Artist</th>
                                        <th className="p-4 text-left font-black uppercase">Plays</th>
                                        <th className="p-4 text-left font-black uppercase">Duration</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {topTracks.map((track, index) => (
                                        <tr
                                            key={track.rank}
                                            className={`border-b-2 border-black transition-all hover:bg-primary/30 cursor-pointer ${index % 2 === 0 ? 'bg-gray-50' : 'bg-white'}`}
                                        >
                                            <td className="p-4">
                                                <span className="w-8 h-8 flex items-center justify-center bg-black text-white font-black rounded-full text-sm">
                                                    {track.rank}
                                                </span>
                                            </td>
                                            <td className="p-4 font-bold">{track.name}</td>
                                            <td className="p-4 font-medium">{track.artist}</td>
                                            <td className="p-4">
                                                <span className="bg-accent border-2 border-black px-2 py-1 font-bold">
                                                    {track.plays}
                                                </span>
                                            </td>
                                            <td className="p-4 font-mono font-bold">{track.duration}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </CardContent>
                </Card>

                {/* Weekly Mood Trends (Original Chart) */}
                <Card className="bg-accent neo-brutal">
                    <CardHeader className="border-b-3 border-black">
                        <CardTitle className="flex items-center gap-2 text-2xl">
                            <TrendingUp className="w-6 h-6" />
                            WEEKLY MOOD BREAKDOWN
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="h-[350px] p-6">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={trends}>
                                <XAxis
                                    dataKey="name"
                                    axisLine={{ stroke: 'black', strokeWidth: 3 }}
                                    tickLine={{ stroke: 'black', strokeWidth: 2 }}
                                    tick={{ fill: 'black', fontWeight: 'bold' }}
                                />
                                <YAxis
                                    axisLine={{ stroke: 'black', strokeWidth: 3 }}
                                    tickLine={{ stroke: 'black', strokeWidth: 2 }}
                                    tick={{ fill: 'black', fontWeight: 'bold' }}
                                />
                                <Tooltip content={<NeoTooltip />} />
                                <Bar dataKey="energy" name="Energy" fill="hsl(84, 100%, 73%)" stroke="black" strokeWidth={2} radius={[4, 4, 0, 0]} />
                                <Bar dataKey="happiness" name="Happiness" fill="hsl(359, 100%, 80%)" stroke="black" strokeWidth={2} radius={[4, 4, 0, 0]} />
                                <Bar dataKey="sadness" name="Sadness" fill="hsl(210, 40%, 80%)" stroke="black" strokeWidth={2} radius={[4, 4, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}
