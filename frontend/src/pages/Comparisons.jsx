import { useState, useEffect } from "react"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ArrowLeft, Music, Heart, TrendingUp, Users as UsersIcon } from "lucide-react"
import { useNavigate } from "react-router-dom"
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from 'recharts'

export default function Comparisons() {
    const [users, setUsers] = useState([])
    const [comparisonData, setComparisonData] = useState(null)
    const [loading, setLoading] = useState(true)
    const navigate = useNavigate()

    useEffect(() => {
        fetchComparison()
    }, [])

    const fetchComparison = async () => {
        try {
            // Get users
            const usersResponse = await fetch('http://127.0.0.1:8888/users')
            const usersData = await usersResponse.json()
            const completedUsers = (usersData.users || []).filter(u => u.analysis_status === 'completed')
            setUsers(completedUsers)

            if (completedUsers.length >= 2) {
                // Get comparison data
                const compResponse = await fetch('http://127.0.0.1:8888/comparison-data')
                const compData = await compResponse.json()
                setComparisonData(compData)
            }

            setLoading(false)
        } catch (error) {
            console.error('Error fetching comparison:', error)
            setLoading(false)
        }
    }

    const getCompatibilityColor = (score) => {
        if (score >= 80) return 'bg-green-400'
        if (score >= 60) return 'bg-blue-400'
        if (score >= 40) return 'bg-yellow-400'
        if (score >= 20) return 'bg-orange-400'
        return 'bg-red-400'
    }

    const getCompatibilityText = (score) => {
        if (score >= 80) return 'Perfect Match! 🎯'
        if (score >= 60) return 'Great Compatibility! 🌟'
        if (score >= 40) return 'Some Common Ground 🎵'
        if (score >= 20) return 'Different Tastes 🎭'
        return 'Opposite Preferences 🔄'
    }

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <p className="text-2xl font-black">Loading comparison...</p>
            </div>
        )
    }

    if (users.length < 2) {
        return (
            <div className="space-y-8">
                <Button
                    onClick={() => navigate('/compare')}
                    className="neo-brutal bg-white hover:bg-gray-100 font-bold"
                >
                    <ArrowLeft className="mr-2 h-4 w-4" />
                    Back to Compare
                </Button>

                <div className="bg-yellow-200 border-4 border-black p-12 text-center">
                    <h2 className="text-3xl font-black mb-4">Not Enough Users!</h2>
                    <p className="text-xl font-medium">
                        You need at least 2 analyzed users to see comparisons.
                    </p>
                    <p className="mt-4 font-bold">
                        Currently analyzed: {users.length}/2
                    </p>
                </div>
            </div>
        )
    }

    if (!comparisonData) {
        return (
            <div className="flex items-center justify-center h-64">
                <p className="text-2xl font-black">No comparison data available</p>
            </div>
        )
    }

    // Prepare mood radar data
    const moodRadarData = comparisonData.mood_profiles ? [
        {
            mood: 'Happy',
            user1: (comparisonData.mood_profiles.user1?.happy || 0) * 100,
            user2: (comparisonData.mood_profiles.user2?.happy || 0) * 100
        },
        {
            mood: 'Relaxed',
            user1: (comparisonData.mood_profiles.user1?.relaxed || 0) * 100,
            user2: (comparisonData.mood_profiles.user2?.relaxed || 0) * 100
        },
        {
            mood: 'Energetic',
            user1: (comparisonData.mood_profiles.user1?.danceability || 0) * 100,
            user2: (comparisonData.mood_profiles.user2?.danceability || 0) * 100
        },
        {
            mood: 'Aggressive',
            user1: (comparisonData.mood_profiles.user1?.aggressive || 0) * 100,
            user2: (comparisonData.mood_profiles.user2?.aggressive || 0) * 100
        },
        {
            mood: 'Sad',
            user1: (comparisonData.mood_profiles.user1?.sad || 0) * 100,
            user2: (comparisonData.mood_profiles.user2?.sad || 0) * 100
        }
    ] : []

    // Prepare overlap bar data
    const overlapData = [
        {
            name: 'Artists',
            percentage: comparisonData.taste_overlap?.artist_overlap || 0
        },
        {
            name: 'Genres',
            percentage: comparisonData.taste_overlap?.genre_overlap || 0
        }
    ]

    const user1 = comparisonData.users?.[0] || users[0]
    const user2 = comparisonData.users?.[1] || users[1]

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex justify-between items-start">
                <div>
                    <h1 className="text-4xl font-black uppercase mb-2">Music Taste Comparison</h1>
                    <p className="text-xl font-medium text-muted-foreground">
                        {user1.display_name} vs {user2.display_name}
                    </p>
                </div>

                <Button
                    onClick={() => navigate('/compare')}
                    className="neo-brutal bg-white hover:bg-gray-100 font-bold"
                >
                    <ArrowLeft className="mr-2 h-4 w-4" />
                    Back to Compare
                </Button>
            </div>

            {/* Compatibility Score - Hero Section */}
            <Card className={`neo-brutal ${getCompatibilityColor(comparisonData.compatibility_score)} border-4`}>
                <CardContent className="p-12 text-center">
                    <div className="flex items-center justify-center gap-8">
                        <div className="flex-1 text-center">
                            <p className="text-xl font-black mb-2">{user1.display_name}</p>
                            <div className="w-24 h-24 mx-auto rounded-full bg-black flex items-center justify-center">
                                <UsersIcon className="h-12 w-12 text-white" />
                            </div>
                        </div>

                        <div className="text-center">
                            <div className="text-8xl font-black mb-4">
                                {comparisonData.compatibility_score}%
                            </div>
                            <p className="text-3xl font-black uppercase">
                                {getCompatibilityText(comparisonData.compatibility_score)}
                            </p>
                            <p className="text-lg font-bold mt-4 opacity-70">
                                Compatibility Score
                            </p>
                        </div>

                        <div className="flex-1 text-center">
                            <p className="text-xl font-black mb-2">{user2.display_name}</p>
                            <div className="w-24 h-24 mx-auto rounded-full bg-black flex items-center justify-center">
                                <UsersIcon className="h-12 w-12 text-white" />
                            </div>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Card className="neo-brutal bg-primary">
                    <CardContent className="p-6 text-center">
                        <Heart className="h-12 w-12 mx-auto mb-4" />
                        <div className="text-4xl font-black mb-2">
                            {Math.round(comparisonData.mood_similarity)}%
                        </div>
                        <p className="font-bold">Mood Similarity</p>
                    </CardContent>
                </Card>

                <Card className="neo-brutal bg-secondary">
                    <CardContent className="p-6 text-center">
                        <Music className="h-12 w-12 mx-auto mb-4" />
                        <div className="text-4xl font-black mb-2">
                            {comparisonData.common_artists?.length || 0}
                        </div>
                        <p className="font-bold">Common Artists</p>
                    </CardContent>
                </Card>

                <Card className="neo-brutal bg-accent">
                    <CardContent className="p-6 text-center">
                        <TrendingUp className="h-12 w-12 mx-auto mb-4" />
                        <div className="text-4xl font-black mb-2">
                            {comparisonData.common_genres?.length || 0}
                        </div>
                        <p className="font-bold">Common Genres</p>
                    </CardContent>
                </Card>
            </div>

            {/* Mood Profile Comparison */}
            <Card className="neo-brutal bg-white">
                <CardHeader className="border-b-4 border-black">
                    <CardTitle className="text-2xl font-black uppercase">Mood Profile Comparison</CardTitle>
                </CardHeader>
                <CardContent className="p-8">
                    <ResponsiveContainer width="100%" height={400}>
                        <RadarChart data={moodRadarData}>
                            <PolarGrid stroke="#000" strokeWidth={2} />
                            <PolarAngleAxis
                                dataKey="mood"
                                tick={{ fill: '#000', fontWeight: 'bold', fontSize: 14 }}
                            />
                            <PolarRadiusAxis
                                angle={90}
                                domain={[0, 100]}
                                tick={{ fill: '#000', fontWeight: 'bold' }}
                            />
                            <Radar
                                name={user1.display_name}
                                dataKey="user1"
                                stroke="#FF6B6B"
                                fill="#FF6B6B"
                                fillOpacity={0.5}
                                strokeWidth={3}
                            />
                            <Radar
                                name={user2.display_name}
                                dataKey="user2"
                                stroke="#4ECDC4"
                                fill="#4ECDC4"
                                fillOpacity={0.5}
                                strokeWidth={3}
                            />
                            <Tooltip
                                contentStyle={{
                                    border: '3px solid black',
                                    borderRadius: 0,
                                    fontWeight: 'bold'
                                }}
                            />
                        </RadarChart>
                    </ResponsiveContainer>
                    <div className="flex justify-center gap-8 mt-4">
                        <div className="flex items-center gap-2">
                            <div className="w-6 h-6 bg-[#FF6B6B] border-2 border-black"></div>
                            <span className="font-bold">{user1.display_name}</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="w-6 h-6 bg-[#4ECDC4] border-2 border-black"></div>
                            <span className="font-bold">{user2.display_name}</span>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Taste Overlap */}
            <Card className="neo-brutal bg-white">
                <CardHeader className="border-b-4 border-black">
                    <CardTitle className="text-2xl font-black uppercase">Taste Overlap</CardTitle>
                </CardHeader>
                <CardContent className="p-8">
                    <ResponsiveContainer width="100%" height={200}>
                        <BarChart data={overlapData} layout="vertical">
                            <XAxis type="number" domain={[0, 100]} tick={{ fontWeight: 'bold' }} />
                            <YAxis type="category" dataKey="name" tick={{ fontWeight: 'bold' }} width={100} />
                            <Tooltip
                                contentStyle={{
                                    border: '3px solid black',
                                    borderRadius: 0,
                                    fontWeight: 'bold'
                                }}
                                formatter={(value) => `${Math.round(value)}%`}
                            />
                            <Bar dataKey="percentage" fill="#FFD93D" stroke="#000" strokeWidth={2}>
                                {overlapData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={index === 0 ? '#FF6B6B' : '#4ECDC4'} />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                    <div className="mt-6 grid grid-cols-2 gap-4 text-center">
                        <div className="bg-gray-100 border-2 border-black p-4">
                            <p className="text-3xl font-black">{comparisonData.taste_overlap?.common_artists_count || 0}</p>
                            <p className="font-bold">Common Artists</p>
                        </div>
                        <div className="bg-gray-100 border-2 border-black p-4">
                            <p className="text-3xl font-black">{comparisonData.taste_overlap?.common_genres_count || 0}</p>
                            <p className="font-bold">Common Genres</p>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Common Artists */}
            {comparisonData.common_artists && comparisonData.common_artists.length > 0 && (
                <Card className="neo-brutal bg-primary">
                    <CardHeader className="border-b-4 border-black">
                        <CardTitle className="text-2xl font-black uppercase">Common Artists</CardTitle>
                    </CardHeader>
                    <CardContent className="p-6">
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {comparisonData.common_artists.map((artist, index) => (
                                <div key={index} className="bg-white border-2 border-black p-4">
                                    <p className="font-black text-lg">{artist.name}</p>
                                    <div className="flex items-center gap-2 mt-2">
                                        <div className="flex-1 h-2 bg-gray-200 border border-black">
                                            <div
                                                className="h-full bg-black"
                                                style={{ width: `${artist.popularity}%` }}
                                            />
                                        </div>
                                        <span className="text-xs font-bold">{artist.popularity}</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Common Genres */}
            {comparisonData.common_genres && comparisonData.common_genres.length > 0 && (
                <Card className="neo-brutal bg-secondary">
                    <CardHeader className="border-b-4 border-black">
                        <CardTitle className="text-2xl font-black uppercase">Common Genres</CardTitle>
                    </CardHeader>
                    <CardContent className="p-6">
                        <div className="flex flex-wrap gap-3">
                            {comparisonData.common_genres.map((genre, index) => (
                                <div
                                    key={index}
                                    className="bg-white border-2 border-black px-4 py-2 font-bold uppercase text-sm hover:bg-black hover:text-white transition-colors cursor-default"
                                >
                                    {genre.name}
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Unique Preferences */}
            {comparisonData.unique_preferences && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <Card className="neo-brutal bg-accent">
                        <CardHeader className="border-b-4 border-black">
                            <CardTitle className="text-xl font-black">
                                Unique to {user1.display_name}
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="p-6 space-y-4">
                            {comparisonData.unique_preferences.user1_unique_artists?.length > 0 && (
                                <div>
                                    <p className="font-black mb-2">Artists:</p>
                                    <div className="flex flex-wrap gap-2">
                                        {comparisonData.unique_preferences.user1_unique_artists.slice(0, 5).map((artist, i) => (
                                            <span key={i} className="bg-white border border-black px-2 py-1 text-xs font-bold">
                                                {artist}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}
                            {comparisonData.unique_preferences.user1_unique_genres?.length > 0 && (
                                <div>
                                    <p className="font-black mb-2">Genres:</p>
                                    <div className="flex flex-wrap gap-2">
                                        {comparisonData.unique_preferences.user1_unique_genres.slice(0, 5).map((genre, i) => (
                                            <span key={i} className="bg-white border border-black px-2 py-1 text-xs font-bold">
                                                {genre}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </CardContent>
                    </Card>

                    <Card className="neo-brutal bg-accent">
                        <CardHeader className="border-b-4 border-black">
                            <CardTitle className="text-xl font-black">
                                Unique to {user2.display_name}
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="p-6 space-y-4">
                            {comparisonData.unique_preferences.user2_unique_artists?.length > 0 && (
                                <div>
                                    <p className="font-black mb-2">Artists:</p>
                                    <div className="flex flex-wrap gap-2">
                                        {comparisonData.unique_preferences.user2_unique_artists.slice(0, 5).map((artist, i) => (
                                            <span key={i} className="bg-white border border-black px-2 py-1 text-xs font-bold">
                                                {artist}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}
                            {comparisonData.unique_preferences.user2_unique_genres?.length > 0 && (
                                <div>
                                    <p className="font-black mb-2">Genres:</p>
                                    <div className="flex flex-wrap gap-2">
                                        {comparisonData.unique_preferences.user2_unique_genres.slice(0, 5).map((genre, i) => (
                                            <span key={i} className="bg-white border border-black px-2 py-1 text-xs font-bold">
                                                {genre}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </div>
            )}

            {/* Joint Recommendations */}
            {comparisonData.joint_recommendations && comparisonData.joint_recommendations.length > 0 && (
                <Card className="neo-brutal bg-white border-4 mt-8">
                    <CardHeader className="border-b-4 border-black bg-black text-white">
                        <CardTitle className="text-3xl font-black uppercase flex items-center gap-3">
                            <Music className="h-8 w-8" />
                            Recommended for You Both
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="p-8">
                        <p className="font-bold text-lg mb-8">
                            Based on your combined mood profiles and a PCA-based machine learning algorithm, we think you'd both vibe with these tracks:
                        </p>
                        <div className="space-y-4">
                            {comparisonData.joint_recommendations.map((track, index) => (
                                <div
                                    key={index}
                                    className="bg-accent border-4 border-black p-6 flex justify-between items-center hover:translate-x-[-4px] hover:translate-y-[-4px] hover:shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] transition-all cursor-default"
                                >
                                    <div>
                                        <p className="text-2xl font-black">{track.name}</p>
                                        <p className="text-lg font-bold opacity-70">{track.artist}</p>
                                    </div>
                                    <div className="text-right">
                                        <div className="inline-block bg-black text-white px-4 py-2 font-black text-xl mb-1">
                                            {track.match_score}%
                                        </div>
                                        <p className="text-xs font-bold uppercase tracking-widest">Match Score</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    )
}
