import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { apiFetch, fetchLessonPlayback } from '../lib/api';
import { LessonPublic } from '../types';
import { Loading, ErrorState } from '../components/Layout';

type PlaybackResponse = { provider: string; embedUrl: string; expiresIn: null };

const LessonPlayer: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();

    const [lesson, setLesson] = useState<LessonPublic | null>(null);
    const [embedUrl, setEmbedUrl] = useState<string | null>(null);
    const [status, setStatus] = useState<'loading' | 'ready' | 'locked' | 'notfound' | 'error'>('loading');
    const [error, setError] = useState<any>(null);

    useEffect(() => {
        const load = async () => {
            if (!id) return;

            setStatus('loading');

            // 1) Public lesson metadata
            const lessonRes = await apiFetch<LessonPublic>(`/lessons/${id}`, { skipRedirect: true });
            if (lessonRes.status === 404) {
                setStatus('notfound');
                return;
            }
            if (!(lessonRes.status === 200 && lessonRes.data)) {
                setStatus('error');
                setError(lessonRes.error);
                return;
            }
            setLesson(lessonRes.data);

            // 2) Gated playback
            const playbackRes = await apiFetch<PlaybackResponse>(`/content/lessons/${id}/playback`, { skipRedirect: true });

            if (playbackRes.status === 200 && playbackRes.data?.embedUrl) {
                setEmbedUrl(playbackRes.data.embedUrl);
                setStatus('ready');
                return;
            }

            if (playbackRes.status === 401) {
                // In dev you may have /auth-debug, in prod /login
                const target = import.meta.env.DEV ? '/auth-debug' : '/login';
                navigate(target, { replace: true });
                return;
            }

            if (playbackRes.status === 403) {
                setStatus('locked');
                return;
            }

            if (playbackRes.status === 404) {
                setStatus('notfound');
                return;
            }

            setStatus('error');
            setError(playbackRes.error);
        };

        load();
    }, [id]);

    if (status === 'loading') return <Loading />;
    if (status === 'notfound') return <ErrorState status={404} />;
    if (status === 'error') return <ErrorState status={500} message={error} />;
    if (!lesson) return <ErrorState status={404} />;

    if (status === 'locked') {
        return (
            <div className="max-w-5xl mx-auto px-4 py-12">
                <div className="mb-8">
                    <Link to={`/courses/${lesson.courseId}`} className="text-sm text-gray-500 hover:text-white transition flex items-center gap-2">
                        <span>←</span> Back to Course
                    </Link>
                </div>

                <div className="bg-[#111] border border-red-500/20 p-12 rounded-3xl text-center">
                    <h1 className="text-2xl font-black text-red-500 uppercase italic tracking-widest mb-4">Access Blocked</h1>
                    <p className="text-gray-500 mb-6" dir="rtl">
                        אין לך הרשאה לשיעור הזה. צריך לרכוש גישה לפרוטוקול כדי לצפות.
                    </p>
                    <Link
                        to={`/courses/${lesson.courseId}`}
                        className="inline-block bg-white text-black px-8 py-3 rounded-xl font-black uppercase tracking-widest hover:bg-red-500 hover:text-white transition"
                    >
                        Go to Purchase
                    </Link>
                </div>
            </div>
        );
    }

    // status === 'ready'
    return (
        <div className="max-w-6xl mx-auto px-4 py-12">
            <div className="mb-8 flex justify-between items-center">
                <Link to={`/courses/${lesson.courseId}`} className="text-sm text-gray-500 hover:text-white transition flex items-center gap-2">
                    <span>←</span> Back to Course
                </Link>
                <span className="text-[10px] text-gray-600 font-mono uppercase tracking-widest">Secure Playback</span>
            </div>

            <div className="bg-[#111] border border-white/5 rounded-3xl overflow-hidden">
                <div className="p-8 text-right" dir="rtl">
                    <h1 className="text-2xl md:text-3xl font-black tracking-tighter text-white uppercase italic">{lesson.titleHe}</h1>
                    <p className="text-gray-500 mt-2">{lesson.descriptionHe}</p>
                </div>

                <div className="px-6 pb-8">
                    <div className="w-full aspect-video rounded-2xl overflow-hidden border border-white/10 bg-black">
                        <iframe
                            src={embedUrl || ''}
                            className="w-full h-full"
                            allow="autoplay; fullscreen; picture-in-picture"
                            allowFullScreen
                            title={lesson.titleHe}
                        />
                    </div>
                </div>
            </div>
        </div>
    );
};

export default LessonPlayer;
