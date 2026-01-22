import React from 'react';
import { Link } from 'react-router-dom';
import { Play, TrendingUp, Users } from 'lucide-react';
import { moodData } from '../lib/data';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import TrendsChart from '../components/TrendsChart';

const Home = () => {
    return (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Hero Section */}
            <section className="bg-primary border-3 border-black shadow-neo p-8 text-center relative overflow-hidden">
                <div className="relative z-10">
                    <h1 className="text-5xl md:text-7xl font-black mb-4 uppercase tracking-tighter">
                        Your Vibe Check
                    </h1>
                    <p className="text-xl md:text-2xl font-bold mb-8 italic">
                        "Your music taste is <span className="underline decoration-4 decoration-white">chaotic good</span> right now."
                    </p>
                    <div className="flex flex-col sm:flex-row gap-4 justify-center">
                        <button
                            onClick={async () => {
                                try {
                                    const res = await fetch('http://127.0.0.1:8888/login');
                                    const data = await res.json();
                                    if (data.url) window.location.href = data.url;
                                } catch (e) {
                                    console.error("Login failed", e);
                                    alert("Make sure the backend is running!");
                                }
                            }}
                            className="inline-flex items-center justify-center gap-2 bg-white text-black border-2 border-black shadow-neo hover:translate-x-[-2px] hover:translate-y-[-2px] hover:shadow-neo-hover transition-all px-8 py-4 font-bold text-lg uppercase cursor-pointer"
                        >
                            <TrendingUp className="w-6 h-6" />
                            Link Spotify
                        </button>
                        <Link to="/compare" className="inline-flex items-center justify-center gap-2 bg-accent text-black border-2 border-black shadow-neo hover:translate-x-[-2px] hover:translate-y-[-2px] hover:shadow-neo-hover transition-all px-8 py-4 font-bold text-lg uppercase">
                            <Users className="w-6 h-6" />
                            Compare with Friends
                        </Link>
                    </div>
                </div>
                {/* Decorative background elements can go here */}
            </section>

            {/* Current Mood Quick View */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <Card className="bg-secondary">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-3 text-3xl">
                            <Play className="w-8 h-8 fill-black" />
                            Current Mood
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-6xl font-black mb-2">{moodData.currentMood}</div>
                        <p className="font-bold text-lg">Based on your recent listening</p>
                    </CardContent>
                </Card>

                <Card className="bg-white">
                    <CardHeader>
                        <CardTitle className="text-3xl">Top Artists</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <ul className="space-y-3">
                            {moodData.topArtists.map((artist, i) => (
                                <li key={i} className="flex items-center gap-3 font-bold text-lg border-b-2 border-black last:border-0 pb-2 last:pb-0">
                                    <span className="w-8 h-8 flex items-center justify-center bg-black text-white rounded-full text-sm">
                                        {i + 1}
                                    </span>
                                    {artist}
                                </li>
                            ))}
                        </ul>
                    </CardContent>
                </Card>
            </div>

            {/* Weekly Trends Chart */}
            <TrendsChart data={moodData.trends} />
        </div>
    );
};

export default Home;
