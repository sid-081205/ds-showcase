import { Outlet, Link, useLocation } from 'react-router-dom';
import { cn } from '@/lib/utils';
import ProgressOverlay from './ProgressOverlay';
import { useState, useEffect } from 'react';

export default function Layout() {
    const location = useLocation();
    const [user, setUser] = useState(null);

    useEffect(() => {
        const checkUser = async () => {
            try {
                const response = await fetch('http://127.0.0.1:8888/status');
                const data = await response.json();
                if (data.user_info) {
                    setUser(data.user_info);
                } else {
                    setUser(null);
                }
            } catch (error) {
                console.error("Failed to fetch user status:", error);
            }
        };

        checkUser();
        const interval = setInterval(checkUser, 5000);
        return () => clearInterval(interval);
    }, []);

    const handleLogout = async () => {
        if (confirm("Are you sure you want to log out? This will unlink Spotify and clear all local data.")) {
            try {
                await fetch('http://127.0.0.1:8888/logout', { method: 'POST' });
                setUser(null);
                window.location.reload();
            } catch (error) {
                console.error("Logout failed:", error);
            }
        }
    };

    return (
        <div className="min-h-screen flex flex-col font-sans bg-background" style={{ backgroundImage: 'radial-gradient(#000 1px, transparent 1px)', backgroundSize: '40px 40px' }}>
            <ProgressOverlay />
            <nav className="sticky top-0 z-50 bg-white border-b-[3px] border-black p-6 flex justify-between items-center shadow-sm">
                <div className="flex items-center gap-8">
                    <div className="text-xl font-bold bg-black text-white px-4 py-2 transform -rotate-2 rounded-sm">
                        SPOTIFY MOOD
                    </div>
                    <div className="flex gap-8">
                        <NavLink to="/" current={location.pathname}>HOME</NavLink>
                        <NavLink to="/mood-analysis" current={location.pathname}>MOOD ANALYSIS</NavLink>
                        <NavLink to="/compare" current={location.pathname}>COMPARE</NavLink>
                    </div>
                </div>

                <div className="flex items-center gap-4">
                    {user ? (
                        <div className="flex items-center gap-3">
                            <div className="text-right">
                                <p className="text-[10px] font-black uppercase tracking-widest text-muted-foreground leading-none mb-1">LOGGED IN AS</p>
                                <p className="text-sm font-bold uppercase">{user.display_name}</p>
                            </div>
                            {user.image && (
                                <img src={user.image} alt={user.display_name} className="w-8 h-8 rounded-full border-2 border-black" />
                            )}
                            <button
                                onClick={handleLogout}
                                className="neo-brutal bg-red-400 text-black px-3 py-1 text-xs font-black uppercase hover:bg-red-500 transition-colors"
                            >
                                Logout
                            </button>
                        </div>
                    ) : (
                        <p className="text-xs font-bold uppercase tracking-widest text-muted-foreground italic">
                            NOT CONNECTED
                        </p>
                    )}
                </div>
            </nav>

            <main className="flex-1 container mx-auto py-12 px-4 animate-in fade-in duration-500">
                <Outlet />
            </main>

            <footer className="bg-black text-white p-8 text-center font-medium tracking-widest border-t-[3px] border-black">
                &copy; 2025 SPOTIFY MOOD REVIEW.
            </footer>
        </div>
    );
}

function NavLink({ to, children, current }) {
    const isActive = current === to;
    return (
        <Link
            to={to}
            className={cn(
                "font-medium relative hover:text-primary transition-colors",
                isActive && "after:content-[''] after:absolute after:w-full after:h-[3px] after:bg-black after:bottom-[-4px] after:left-0"
            )}
        >
            {children}
        </Link>
    );
}
