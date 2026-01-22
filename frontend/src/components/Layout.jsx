import { Outlet, Link, useLocation } from 'react-router-dom';
import { cn } from '@/lib/utils';
import ProgressOverlay from './ProgressOverlay';

export default function Layout() {
    const location = useLocation();

    return (
        <div className="min-h-screen flex flex-col font-sans bg-background" style={{ backgroundImage: 'radial-gradient(#000 1px, transparent 1px)', backgroundSize: '40px 40px' }}>
            <ProgressOverlay />
            <nav className="sticky top-0 z-50 bg-white border-b-[3px] border-black p-6 flex justify-between items-center shadow-sm">
                <div className="text-xl font-bold bg-black text-white px-4 py-2 transform -rotate-2 rounded-sm">
                    SPOTIFY MOOD
                </div>
                <div className="flex gap-8">
                    <NavLink to="/" current={location.pathname}>HOME</NavLink>
                    <NavLink to="/mood-analysis" current={location.pathname}>MOOD ANALYSIS</NavLink>
                    <NavLink to="/compare" current={location.pathname}>COMPARE</NavLink>
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
