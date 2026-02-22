import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiFetch } from '../lib/api';
import { CoursePublic, AccessCheckResponse } from '../types';
import { Loading, ErrorState } from '../components/Layout';

const Library: React.FC = () => {
    const [loading, setLoading] = useState(true);
    const [courses, setCourses] = useState<CoursePublic[]>([]);
    const [error, setError] = useState<any>(null);

    useEffect(() => {
        const load = async () => {
            setLoading(true);

            // 1) fetch all published courses
            const allCoursesRes = await apiFetch<CoursePublic[]>(`/courses`, { skipRedirect: true });
            if (!(allCoursesRes.status === 200 && allCoursesRes.data)) {
                setError(allCoursesRes.error);
                setLoading(false);
                return;
            }

            // 2) filter by access
            const checks = await Promise.all(
                allCoursesRes.data.map(async (c) => {
                    const accessRes = await apiFetch<AccessCheckResponse>(`/access/courses/${c.id}`, { skipRedirect: true });
                    return { course: c, allowed: Boolean(accessRes.data?.allowed) };
                })
            );

            setCourses(checks.filter(x => x.allowed).map(x => x.course));
            setLoading(false);
        };

        load();
    }, []);

    if (loading) return <Loading />;
    if (error) return <ErrorState status={500} message={error} />;

    return (
        <div className="max-w-5xl mx-auto px-4 py-12">
            <div className="mb-8 flex items-center justify-between">
                <h1 className="text-3xl font-black text-white uppercase italic tracking-tighter">My Library</h1>
                <Link to="/" className="text-sm border border-white/20 px-4 py-2 rounded-lg text-gray-400 hover:text-white hover:border-white transition flex items-center gap-2">
                    Explore Protocols
                </Link>
            </div>

            {courses.length === 0 ? (
                <div className="bg-[#111] border border-white/5 p-12 rounded-3xl text-center mt-12">
                    <h2 className="text-xl font-bold text-gray-500 mb-4">No Active Access</h2>
                    <p className="text-sm text-gray-600" dir="rtl">
                        עדיין אין לך קורסים פתוחים. כנס לעמוד הראשי ורכוש גישה לפרוטוקול.
                    </p>
                    <Link
                        to="/"
                        className="inline-block mt-6 bg-white text-black px-8 py-3 rounded-xl font-black uppercase tracking-widest hover:bg-red-500 hover:text-white transition"
                    >
                        Browse Courses
                    </Link>
                </div>
            ) : (
                <div className="grid gap-4">
                    {courses.map(c => (
                        <Link
                            key={c.id}
                            to={`/courses/${c.id}`}
                            className="bg-[#111] p-6 rounded-xl border border-white/5 hover:border-red-500/30 transition flex justify-between items-center group"
                        >
                            <span className="font-bold text-lg group-hover:text-red-500 transition" dir="rtl">{c.titleHe}</span>
                            <span className="text-gray-600">→</span>
                        </Link>
                    ))}
                </div>
            )}
        </div>
    );
};

export default Library;
