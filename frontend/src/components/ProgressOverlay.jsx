import React, { useState, useEffect } from 'react';

const ProgressOverlay = () => {
    const [status, setStatus] = useState({ is_running: false, progress: 0, current_track: "", status: "" });

    useEffect(() => {
        const checkStatus = async () => {
            try {
                const response = await fetch('http://127.0.0.1:8888/status');
                const data = await response.json();
                setStatus(data);
            } catch (error) {
                console.error("Failed to fetch status:", error);
            }
        };

        const interval = setInterval(checkStatus, 1000);
        return () => clearInterval(interval);
    }, []);

    if (!status.is_running && status.progress !== 100) return null;

    // If complete, we might want to hide it after a few seconds or when the user navigates
    // For now, let's keep it until 100% and then hide it if it's not running
    if (!status.is_running && status.progress === 100) {
        // Auto-hide complete status after 3 seconds
        setTimeout(() => setStatus(prev => ({ ...prev, progress: 0 })), 3000);
        if (status.progress === 100 && !status.is_running) return null;
    }

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-white/80 backdrop-blur-sm animate-in fade-in duration-300">
            <div className="w-full max-w-md p-8 bg-primary border-4 border-black shadow-neo transform -rotate-1">
                <h2 className="text-4xl font-black uppercase tracking-tighter mb-4 italic">
                    DNA EXTRACTION IN PROGRESS
                </h2>

                <div className="mb-6 space-y-2">
                    <div className="flex justify-between font-bold uppercase text-sm">
                        <span>{status.status}</span>
                        <span>{status.progress}%</span>
                    </div>
                    <div className="h-8 w-full bg-white border-3 border-black relative overflow-hidden">
                        <div
                            className="h-full bg-accent transition-all duration-500 ease-out border-r-3 border-black"
                            style={{ width: `${status.progress}%` }}
                        >
                            {/* Animated stripes for the progress bar */}
                            <div className="absolute inset-0 opacity-20 pointer-events-none"
                                style={{
                                    backgroundImage: 'linear-gradient(45deg, black 25%, transparent 25%, transparent 50%, black 50%, black 75%, transparent 75%, transparent)',
                                    backgroundSize: '20px 20px'
                                }}
                            />
                        </div>
                    </div>
                </div>

                {status.current_track && (
                    <p className="font-bold text-center border-2 border-black bg-white p-2 text-sm truncate">
                        ANALYZING: {status.current_track}
                    </p>
                )}

                <p className="mt-4 text-xs font-black text-center uppercase tracking-widest animate-pulse">
                    Respecting Rate Limits... Please Hold
                </p>
            </div>
        </div>
    );
};

export default ProgressOverlay;
