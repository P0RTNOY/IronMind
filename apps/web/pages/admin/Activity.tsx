import React, { useEffect, useState } from 'react';
import { apiFetch } from '../../lib/api';
import { Loading } from '../../components/Layout';

interface ActivityEvent {
    id: string;
    type: string;
    uid: string;
    courseId?: string;
    lessonId?: string;
    planId?: string;
    createdAt?: string;
}

function timeAgo(dateStr?: string): string {
    if (!dateStr) return '—';
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMin = Math.floor(diffMs / 60000);
    if (diffMin < 1) return 'just now';
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffHr = Math.floor(diffMin / 60);
    if (diffHr < 24) return `${diffHr}h ago`;
    const diffDays = Math.floor(diffHr / 24);
    return `${diffDays}d ago`;
}

const EVENT_COLORS: Record<string, string> = {
    access_check: 'text-blue-400',
    content_download: 'text-green-400',
    content_playback: 'text-purple-400',
    checkout_started: 'text-yellow-400',
};

const AdminActivity: React.FC = () => {
    const [events, setEvents] = useState<ActivityEvent[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const load = async () => {
            const { data, status } = await apiFetch<ActivityEvent[]>('/admin/activity?limit=50');
            if (status === 200 && data) {
                setEvents(data);
            }
            setLoading(false);
        };
        load();
    }, []);

    if (loading) return <Loading />;

    return (
        <div className="max-w-5xl mx-auto">
            <h1 className="text-3xl font-black uppercase italic tracking-tighter mb-8">
                Recent <span className="text-red-500">Activity</span>
            </h1>

            {events.length === 0 ? (
                <div className="bg-[#111] border border-white/5 p-12 rounded-xl text-center">
                    <p className="text-gray-500">No activity events recorded yet.</p>
                </div>
            ) : (
                <div className="bg-[#111] border border-white/5 rounded-xl overflow-hidden">
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="border-b border-white/10 text-left">
                                <th className="px-4 py-3 text-[10px] font-black text-gray-600 uppercase tracking-widest">Time</th>
                                <th className="px-4 py-3 text-[10px] font-black text-gray-600 uppercase tracking-widest">Type</th>
                                <th className="px-4 py-3 text-[10px] font-black text-gray-600 uppercase tracking-widest">User</th>
                                <th className="px-4 py-3 text-[10px] font-black text-gray-600 uppercase tracking-widest">Resource</th>
                            </tr>
                        </thead>
                        <tbody>
                            {events.map(e => (
                                <tr key={e.id} className="border-b border-white/5 hover:bg-white/[0.02] transition">
                                    <td className="px-4 py-3 text-gray-500 font-mono text-xs">{timeAgo(e.createdAt)}</td>
                                    <td className={`px-4 py-3 font-bold text-xs uppercase ${EVENT_COLORS[e.type] || 'text-gray-400'}`}>
                                        {e.type}
                                    </td>
                                    <td className="px-4 py-3 font-mono text-xs text-gray-400">{e.uid}</td>
                                    <td className="px-4 py-3 font-mono text-xs text-gray-500">
                                        {e.courseId && (
                                            <a href={`/#/courses/${e.courseId}`} className="text-blue-400 hover:text-blue-300 mr-2">{e.courseId}</a>
                                        )}
                                        {e.lessonId && (
                                            <a href={`/#/lessons/${e.lessonId}`} className="text-purple-400 hover:text-purple-300 mr-2">{e.lessonId}</a>
                                        )}
                                        {e.planId && (
                                            <span className="text-green-400">{e.planId}</span>
                                        )}
                                        {!e.courseId && !e.lessonId && !e.planId && '—'}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
};

export default AdminActivity;
