import React from 'react';
import { useNavigate } from 'react-router-dom';
import { routes } from '../lib/routes';

const AdminRequired: React.FC = () => {
    const navigate = useNavigate();
    const isDev = import.meta.env.DEV;

    return (
        <div className="flex flex-col items-center justify-center min-h-[80vh] px-4 text-center">
            <div className="bg-[#111] border border-red-500/20 p-12 rounded-3xl max-w-md w-full relative overflow-hidden">
                <div className="absolute top-0 left-0 w-full h-1 bg-red-500" />

                <div className="flex justify-center mb-6">
                    <div className="w-16 h-16 rounded-full bg-red-500/10 flex items-center justify-center text-red-500 text-3xl">
                        ⚠️
                    </div>
                </div>

                <h1 className="text-2xl font-black text-white uppercase italic tracking-tighter mb-4">
                    Admin Access Required
                </h1>

                <p className="text-gray-400 text-sm mb-8 leading-relaxed">
                    You are signed in, but your current session does not have the necessary administrative privileges to view this sector.
                </p>

                <div className="space-y-4">
                    <button
                        onClick={() => navigate(routes.home())}
                        className="w-full flex items-center justify-center gap-2 bg-white text-black py-3 rounded-xl font-bold uppercase tracking-widest hover:bg-gray-200 transition-colors"
                    >
                        <span>&larr;</span>
                        Go Home
                    </button>

                    {isDev && (
                        <div className="pt-6 mt-6 border-t border-white/5 space-y-4">
                            <p className="text-[10px] text-gray-600 font-mono uppercase tracking-widest text-center">
                                Dev Access Only
                            </p>
                            <button
                                onClick={() => navigate(routes.devAuth(window.location.hash))}
                                className="w-full flex items-center justify-center gap-2 bg-black border border-white/10 text-gray-300 py-3 rounded-xl font-bold uppercase tracking-widest hover:bg-white/5 hover:text-white transition-all text-xs"
                            >
                                <span>⚡</span>
                                Open Dev Auth
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default AdminRequired;
