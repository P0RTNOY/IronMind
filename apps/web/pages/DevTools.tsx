import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { routes } from '../lib/routes';
import { apiFetch } from '../lib/api';
import { toast } from '../components/toast';

const DevTools: React.FC = () => {
    const isDev = import.meta.env.DEV;
    const { user, loginDev, logout } = useAuth();
    const navigate = useNavigate();

    const [overrideUid, setOverrideUid] = useState(localStorage.getItem('debugUid') || '');
    const [overrideAdmin, setOverrideAdmin] = useState(localStorage.getItem('debugAdmin') === '1');
    const [accessCourseId, setAccessCourseId] = useState('');
    const [introspectionResult, setIntrospectionResult] = useState<string | null>(null);

    if (!isDev) return null;

    const handleApplySession = () => {
        if (!overrideUid) {
            toast.error("You must provide a mock UID.");
            return;
        }

        // Native override writes matching DevAuth structural behavior natively
        localStorage.setItem('debugUid', overrideUid);
        localStorage.setItem('debugAdmin', overrideAdmin ? '1' : '0');

        // Navigate gracefully to purge URL-states before reloading
        navigate(routes.home());
        window.location.reload();
    };

    const handleClearSession = () => {
        logout();
        navigate(routes.home());
    };

    const handleIntrospect = async (endpoint: string) => {
        try {
            setIntrospectionResult("Fetching...");
            const { data, status } = await apiFetch(endpoint, { skipRedirect: true });
            setIntrospectionResult(JSON.stringify({ status, data }, null, 2));
        } catch (e: any) {
            setIntrospectionResult(`Error evaluating endpoint:\n${e.message}`);
        }
    };

    const handleAccessCheck = async () => {
        if (!accessCourseId) {
            toast.error("Submit the explicit string ID of the Course");
            return;
        }

        try {
            setIntrospectionResult(`Checking Access for Course: ${accessCourseId}...`);
            const { status } = await apiFetch(`/access/courses/${accessCourseId}`, { skipRedirect: true });

            if (status === 200) {
                setIntrospectionResult(`Status 200: ACCESS GRANTED for ${accessCourseId}`);
                toast.success("Course content is unlocked for this UID.");
            } else if (status === 403 || status === 401) {
                setIntrospectionResult(`Status ${status}: ACCESS DENIED for ${accessCourseId}`);
                toast.error("Course relies upon explicit stripe-payment matrices.");
            } else {
                setIntrospectionResult(`Unexpected Status: ${status}`);
            }
        } catch (e: any) {
            setIntrospectionResult(`Error during evaluation:\n${e.message}`);
        }
    };

    return (
        <div className="min-h-screen bg-[#0a0a0a] text-white p-8 max-w-6xl mx-auto space-y-8 pb-32">

            <div className="flex items-center gap-4 border-b border-red-500/20 pb-4">
                <div className="w-12 h-12 bg-red-500/10 rounded flex items-center justify-center text-red-500 text-2xl border border-red-500/30">
                    ⚡
                </div>
                <div>
                    <h1 className="text-3xl font-black italic uppercase tracking-tighter">Developer <span className="text-red-500">Toolkit</span></h1>
                    <p className="text-sm text-gray-400">Non-Production Environmental Analysis & Deterministic Test Overrides</p>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Panel 1: Session Overview */}
                <div className="bg-[#111] border border-white/5 rounded-2xl p-6">
                    <h2 className="text-sm font-bold uppercase tracking-widest text-gray-400 mb-6 flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-blue-500"></span> Session Context
                    </h2>

                    <div className="space-y-4">
                        <div className="grid grid-cols-2 gap-4 text-sm">
                            <div className="bg-black p-4 rounded-xl border border-white/5">
                                <span className="block text-[10px] text-gray-500 uppercase tracking-widest mb-1">localStorage.debugUid</span>
                                <span className="font-mono text-white">{localStorage.getItem('debugUid') || 'null'}</span>
                            </div>
                            <div className="bg-black p-4 rounded-xl border border-white/5">
                                <span className="block text-[10px] text-gray-500 uppercase tracking-widest mb-1">localStorage.debugAdmin</span>
                                <span className="font-mono text-white">{localStorage.getItem('debugAdmin') || 'null'}</span>
                            </div>
                            <div className="bg-black p-4 rounded-xl border border-white/5">
                                <span className="block text-[10px] text-gray-500 uppercase tracking-widest mb-1">useAuth() user.uid</span>
                                <span className="font-mono text-blue-400">{user?.uid || 'null'}</span>
                            </div>
                            <div className="bg-black p-4 rounded-xl border border-white/5">
                                <span className="block text-[10px] text-gray-500 uppercase tracking-widest mb-1">useAuth() user.is_admin</span>
                                <span className={`font-mono ${user?.is_admin ? 'text-red-400' : 'text-blue-400'}`}>{user ? String(user.is_admin) : 'null'}</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Panel 2: Manual Override */}
                <div className="bg-[#111] border border-white/5 rounded-2xl p-6">
                    <h2 className="text-sm font-bold uppercase tracking-widest text-gray-400 mb-6 flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-red-500"></span> Session Overrides
                    </h2>

                    <div className="space-y-4">
                        <div>
                            <label className="block text-[10px] text-gray-500 uppercase tracking-widest mb-2">Target Mock UID</label>
                            <input
                                type="text"
                                value={overrideUid}
                                onChange={(e) => setOverrideUid(e.target.value)}
                                className="w-full bg-black border border-white/10 rounded-lg px-4 py-3 text-sm focus:border-red-500 outline-none"
                                placeholder="e.g., mock-user-123"
                            />
                        </div>

                        <label className="flex items-center gap-3 cursor-pointer p-3 bg-black border border-white/5 rounded-lg hover:border-white/20 transition">
                            <input
                                type="checkbox"
                                checked={overrideAdmin}
                                onChange={(e) => setOverrideAdmin(e.target.checked)}
                                className="w-4 h-4 accent-red-500"
                            />
                            <span className="text-sm font-bold uppercase tracking-wider text-gray-300">Grant Admin Privilege</span>
                        </label>

                        <div className="grid grid-cols-2 gap-3 pt-4 border-t border-white/5">
                            <button
                                onClick={handleClearSession}
                                className="bg-white/5 text-gray-400 px-4 py-3 rounded-xl font-bold uppercase tracking-widest hover:bg-red-500/10 hover:text-red-500 transition text-xs border border-transparent hover:border-red-500/30"
                            >
                                Clear Context
                            </button>
                            <button
                                onClick={handleApplySession}
                                className="bg-red-500 text-white px-4 py-3 rounded-xl font-black uppercase tracking-widest hover:bg-red-600 transition text-xs"
                            >
                                Apply Block
                            </button>
                        </div>
                    </div>
                </div>

                {/* Panel 3: Diagnostics */}
                <div className="bg-[#111] border border-white/5 rounded-2xl p-6">
                    <h2 className="text-sm font-bold uppercase tracking-widest text-gray-400 mb-6 flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-purple-500"></span> Introspection Checks
                    </h2>

                    <div className="space-y-6">
                        <div className="grid grid-cols-2 gap-3">
                            <button onClick={() => handleIntrospect('/healthz')} className="bg-black border border-white/10 hover:border-purple-500 text-gray-300 hover:text-white px-4 py-3 rounded-lg text-xs font-bold uppercase tracking-wider transition">
                                ping /healthz
                            </button>
                            <button onClick={() => handleIntrospect('/access/me')} className="bg-black border border-white/10 hover:border-purple-500 text-gray-300 hover:text-white px-4 py-3 rounded-lg text-xs font-bold uppercase tracking-wider transition">
                                ping /access/me
                            </button>
                        </div>

                        <div className="flex gap-2">
                            <input
                                type="text"
                                value={accessCourseId}
                                onChange={(e) => setAccessCourseId(e.target.value)}
                                className="flex-1 bg-black border border-white/10 rounded-lg px-3 py-2 text-sm focus:border-purple-500 outline-none"
                                placeholder="Course ID (e.g., course_demo_one_time)"
                            />
                            <button onClick={handleAccessCheck} className="bg-white/10 hover:bg-purple-500 text-white px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-wider transition">
                                Check
                            </button>
                        </div>

                        {introspectionResult && (
                            <div className="mt-4 bg-black border border-purple-500/30 rounded-lg p-4 max-h-48 overflow-y-auto">
                                <pre className="text-[10px] text-purple-200 font-mono whitespace-pre-wrap">{introspectionResult}</pre>
                            </div>
                        )}
                    </div>
                </div>

                {/* Panel 4: Quick Matrix Paths */}
                <div className="bg-[#111] border border-white/5 rounded-2xl p-6">
                    <h2 className="text-sm font-bold uppercase tracking-widest text-gray-400 mb-6 flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-green-500"></span> Deterministic Traversal Matrix
                    </h2>

                    <div className="grid grid-cols-1 gap-3">
                        <Link to={routes.admin()} className="bg-black border border-white/5 hover:border-green-500 p-4 rounded-xl flex justify-between items-center group transition">
                            <span className="text-sm font-bold text-gray-300 group-hover:text-white">Admin Dashboard</span>
                            <span className="text-[10px] text-gray-600 font-mono">/admin</span>
                        </Link>
                        <Link to="/library" className="bg-black border border-white/5 hover:border-green-500 p-4 rounded-xl flex justify-between items-center group transition">
                            <span className="text-sm font-bold text-gray-300 group-hover:text-white">User Library</span>
                            <span className="text-[10px] text-gray-600 font-mono">/library</span>
                        </Link>
                        <Link to="/courses/course_demo_one_time" className="bg-black border border-white/5 hover:border-green-500 p-4 rounded-xl flex justify-between items-center group transition">
                            <span className="text-sm font-bold text-gray-300 group-hover:text-white">Demo Course Detail</span>
                            <span className="text-[10px] text-gray-600 font-mono">.../course_demo_one_time</span>
                        </Link>
                        <Link to="/lessons/lesson_demo_course_demo_one_time_1" className="bg-black border border-white/5 hover:border-green-500 p-4 rounded-xl flex justify-between items-center group transition">
                            <span className="text-sm font-bold text-gray-300 group-hover:text-white">Demo Lesson Player</span>
                            <span className="text-[10px] text-gray-600 font-mono">.../course_demo_one_time_1</span>
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DevTools;
