import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiFetch } from '../lib/api';

const Login: React.FC = () => {
    const navigate = useNavigate();
    const [email, setEmail] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const [info, setInfo] = useState<string | null>(null);

    const handleMagicLink = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setInfo(null);

        // Placeholder for Phase 3
        try {
            await apiFetch('/auth/request', {
                method: 'POST',
                body: JSON.stringify({ email })
            });
            setInfo(import.meta.env.DEV
                ? 'Magic link sent! CHECK DOCKER LOGS for the link.'
                : 'Magic link sent! Check your email.');
        } catch (err: any) {
            setError('Failed to send magic link. ' + err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col items-center justify-center min-h-[80vh] px-4">
            <div className="bg-[#111] border border-white/10 p-8 rounded-2xl shadow-2xl max-w-md w-full text-center">
                <h1 className="text-3xl font-black text-white uppercase italic tracking-tighter mb-2">
                    Iron <span className="text-red-500">Mind</span>
                </h1>
                <p className="text-gray-400 text-sm mb-8">
                    Access the Command Center
                </p>

                {info && (
                    <div className="bg-green-500/10 border border-green-500/20 text-green-500 p-3 rounded-lg mb-6 text-xs text-left">
                        {info}
                    </div>
                )}

                {error && (
                    <div className="bg-red-500/10 border border-red-500/20 text-red-500 p-3 rounded-lg mb-6 text-xs text-left">
                        {error}
                    </div>
                )}

                <form onSubmit={handleMagicLink} className="space-y-4">
                    <input
                        type="email"
                        placeholder="name@example.com"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-white/30 transition-colors"
                        required
                    />
                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-white text-black py-4 rounded-xl font-bold uppercase tracking-widest hover:bg-gray-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {loading ? 'Sending...' : 'Send Magic Link'}
                    </button>
                </form>

                {import.meta.env.DEV && (
                    <div className="mt-8 pt-8 border-t border-white/5">
                        <p className="text-gray-600 text-[10px] uppercase tracking-widest mb-4">Development Access</p>
                        <button
                            onClick={() => navigate('/auth-debug')}
                            className="text-gray-500 hover:text-white text-xs underline"
                        >
                            Use Dev Auth (Mock User)
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Login;
