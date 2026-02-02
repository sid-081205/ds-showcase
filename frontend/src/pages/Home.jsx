import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Play, TrendingUp, ArrowRight, Sparkles } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';

const Home = () => {
    const [isLoggedIn, setIsLoggedIn] = React.useState(false);
    const [isAnalyzing, setIsAnalyzing] = React.useState(false);
    const [analyzerProgress, setAnalyzerProgress] = React.useState(0);
    const [analyzerStatus, setAnalyzerStatus] = React.useState('');
    const [currentTrack, setCurrentTrack] = React.useState('');
    const [totalTracks, setTotalTracks] = React.useState(0);
    const [analyzedTracks, setAnalyzedTracks] = React.useState(0);
    const [outputLines, setOutputLines] = React.useState([]);
    const navigate = useNavigate();

    React.useEffect(() => {
        const checkUser = async () => {
            try {
                const response = await fetch('http://127.0.0.1:8888/status');
                const data = await response.json();
                setIsLoggedIn(!!data.user_info);
            } catch (error) {
                console.error("Failed to fetch status:", error);
            }
        };
        checkUser();
    }, []);

    // Poll analyzer status when analyzing
    React.useEffect(() => {
        if (!isAnalyzing) return;

        const interval = setInterval(async () => {
            try {
                const response = await fetch('http://127.0.0.1:8888/analyzer-status');
                const data = await response.json();

                setAnalyzerProgress(data.progress);
                setAnalyzerStatus(data.status);
                setCurrentTrack(data.current_track);
                setTotalTracks(data.total);
                setAnalyzedTracks(data.analyzed);
                setOutputLines(data.output_lines || []);

                if (!data.is_running && data.progress === 100) {
                    setIsAnalyzing(false);
                    // Show completion message for 2 seconds then navigate
                    setTimeout(() => {
                        navigate('/mood-analysis');
                    }, 2000);
                }
            } catch (error) {
                console.error("Failed to fetch analyzer status:", error);
            }
        }, 500); // Poll every 500ms for smooth updates

        return () => clearInterval(interval);
    }, [isAnalyzing, navigate]);

    const handleLinkSpotify = async () => {
        try {
            const res = await fetch('http://127.0.0.1:8888/login');
            const data = await res.json();
            if (data.url) window.location.href = data.url;
        } catch (e) {
            console.error("Login failed", e);
            alert("Make sure the backend is running!");
        }
    };

    const handleAnalyzeData = async () => {
        try {
            setIsAnalyzing(true);
            setAnalyzerProgress(0);
            setAnalyzerStatus('Starting analysis...');

            const response = await fetch('http://127.0.0.1:8888/analyze', {
                method: 'POST'
            });

            if (!response.ok) {
                const error = await response.json();
                alert(error.error || 'Failed to start analysis');
                setIsAnalyzing(false);
            }
        } catch (error) {
            console.error("Failed to start analysis:", error);
            alert("Make sure the backend is running!");
            setIsAnalyzing(false);
        }
    };

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
                        {!isLoggedIn ? (
                            <button
                                onClick={handleLinkSpotify}
                                className="inline-flex items-center justify-center gap-2 bg-white text-black border-2 border-black shadow-neo hover:translate-x-[-2px] hover:translate-y-[-2px] hover:shadow-neo-hover transition-all px-8 py-4 font-bold text-lg uppercase cursor-pointer"
                            >
                                <TrendingUp className="w-6 h-6" />
                                Link Spotify
                            </button>
                        ) : (
                            <button
                                onClick={handleAnalyzeData}
                                disabled={isAnalyzing}
                                className="inline-flex items-center justify-center gap-2 bg-white text-black border-2 border-black shadow-neo hover:translate-x-[-2px] hover:translate-y-[-2px] hover:shadow-neo-hover transition-all px-8 py-4 font-bold text-lg uppercase cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <Sparkles className="w-6 h-6" />
                                {isAnalyzing ? 'Analyzing...' : 'Analyze My Data'}
                            </button>
                        )}
                    </div>
                </div>
            </section>

            {/* Analysis Progress Section */}
            {isLoggedIn && (
                <Card className="bg-white">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-3 text-3xl">
                            <Play className="w-8 h-8 fill-black" />
                            Analysis Progress
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {/* Progress Bar */}
                        <div className="space-y-2">
                            <div className="flex justify-between items-center mb-2">
                                <span className="font-bold text-lg">
                                    {analyzerProgress === 100 ? 'Complete!' : analyzerStatus || 'Ready to analyze'}
                                </span>
                                <span className="font-black text-2xl">
                                    {analyzerProgress}%
                                </span>
                            </div>

                            {/* Progress Bar */}
                            <div className="w-full h-8 bg-gray-200 border-2 border-black shadow-neo overflow-hidden">
                                <div
                                    className="h-full bg-primary transition-all duration-300 ease-out flex items-center justify-center"
                                    style={{ width: `${analyzerProgress}%` }}
                                >
                                    {analyzerProgress > 10 && (
                                        <span className="font-bold text-sm px-2">
                                            {analyzedTracks > 0 && `${analyzedTracks}/${totalTracks} tracks`}
                                        </span>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Current Track Info */}
                        {currentTrack && isAnalyzing && (
                            <div className="bg-secondary border-2 border-black p-4 shadow-neo">
                                <p className="font-bold text-sm uppercase mb-1">Currently Analyzing:</p>
                                <p className="text-lg font-black">{currentTrack}</p>
                            </div>
                        )}

                        {/* Completion Message */}
                        {analyzerProgress === 100 && !isAnalyzing && (
                            <div className="bg-accent border-2 border-black p-6 shadow-neo text-center animate-in fade-in slide-in-from-bottom-4">
                                <p className="text-2xl font-black mb-4">🎉 Analysis Complete!</p>
                                <p className="font-bold mb-4">Redirecting to your mood analysis...</p>
                                <button
                                    onClick={() => navigate('/mood-analysis')}
                                    className="inline-flex items-center justify-center gap-2 bg-white text-black border-2 border-black shadow-neo hover:translate-x-[-2px] hover:translate-y-[-2px] hover:shadow-neo-hover transition-all px-6 py-3 font-bold uppercase"
                                >
                                    View Analysis Now
                                    <ArrowRight className="w-5 h-5" />
                                </button>
                            </div>
                        )}

                        {/* Analyzer Output */}
                        {outputLines.length > 0 && (
                            <div className="border-2 border-black p-4 bg-gray-50 font-mono text-sm max-h-48 overflow-y-auto">
                                <p className="font-bold text-sm mb-2 font-sans">Analyzer Output:</p>
                                <div className="space-y-1">
                                    {outputLines.map((line, index) => (
                                        <p key={index} className="text-xs leading-relaxed">
                                            {line}
                                        </p>
                                    ))}
                                </div>
                            </div>
                        )}
                    </CardContent>
                </Card>
            )}
        </div>
    );
};

export default Home;
