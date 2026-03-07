import React from 'react';
import { useNavigate } from 'react-router-dom';
import { routes } from '../lib/routes';

export const DebugBanner: React.FC = () => {
    const isDev = import.meta.env.DEV;
    const uid = localStorage.getItem('debugUid');
    const isAdmin = localStorage.getItem('debugAdmin') === '1';
    const navigate = useNavigate();

    // Must be in dev mode with an active mock session to display
    if (!isDev || !uid) return null;

    const clearDebugSession = () => {
        localStorage.removeItem('debugUid');
        localStorage.removeItem('debugAdmin');
        navigate(routes.home(), { replace: true });
        // Optional forced reload applied safely for dev environments ensuring strict context cleanup
        window.location.reload();
    };

    return (
        <div className="fixed bottom-0 left-0 right-0 z-50 bg-[#111] border-t border-red-500/30 p-2 shadow-[0_-4px_20px_rgba(239,68,68,0.1)]">
            <div className="max-w-7xl mx-auto flex items-center justify-between px-4">
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                        <span className="animate-pulse w-2 h-2 rounded-full bg-red-500"></span>
                        <span className="text-[10px] font-black tracking-widest text-red-500 uppercase">Dev Session Active</span>
                    </div>

                    <div className="h-4 border-r border-white/20"></div>

                    <div className="flex flex-col">
                        <span className="text-[9px] text-gray-500 uppercase tracking-widest">Mock UID</span>
                        <span className="text-xs font-mono text-white">{uid}</span>
                    </div>

                    <div className="h-4 border-r border-white/20"></div>

                    <div className="flex flex-col">
                        <span className="text-[9px] text-gray-500 uppercase tracking-widest">Clearance</span>
                        <span className={`text-xs font-bold uppercase tracking-widest ${isAdmin ? 'text-red-400' : 'text-gray-400'}`}>
                            {isAdmin ? 'ADMIN' : 'USER'}
                        </span>
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    {isAdmin && (
                        <button
                            onClick={() => navigate(routes.admin())}
                            className="bg-transparent text-gray-400 hover:text-white border border-white/10 hover:border-white/30 px-3 py-1.5 rounded text-[10px] font-bold uppercase tracking-widest transition-colors"
                        >
                            Go Admin
                        </button>
                    )}
                    <button
                        onClick={clearDebugSession}
                        className="bg-red-500/10 text-red-500 hover:bg-red-500 hover:text-white border border-red-500/20 hover:border-red-500 px-3 py-1.5 rounded text-[10px] font-bold uppercase tracking-widest transition-colors"
                    >
                        Clear Session
                    </button>
                </div>
            </div>
        </div>
    );
};
