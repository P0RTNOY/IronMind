import React, { useEffect, useState } from 'react';
import { apiFetch } from '../../lib/api';
import { LessonAdmin, CourseAdmin } from '../../types';
import { Loading, ErrorState } from '../../components/Layout';

const AdminLessons: React.FC = () => {
    const [lessons, setLessons] = useState<LessonAdmin[]>([]);
    const [courses, setCourses] = useState<CourseAdmin[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedCourse, setSelectedCourse] = useState<string>('');
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingLesson, setEditingLesson] = useState<LessonAdmin | null>(null);

    useEffect(() => {
        loadInitialData();
    }, []);

    useEffect(() => {
        if (selectedCourse) {
            fetchLessons(selectedCourse);
        } else {
            setLessons([]);
        }
    }, [selectedCourse]);

    const loadInitialData = async () => {
        setLoading(true);
        const { data } = await apiFetch<CourseAdmin[]>('/admin/courses');
        if (data) {
            setCourses(data);
            if (data.length > 0) setSelectedCourse(data[0].id);
        }
        setLoading(false);
    };

    const fetchLessons = async (courseId: string) => {
        const { data } = await apiFetch<LessonAdmin[]>(`/admin/courses/${courseId}/lessons`);
        if (data) setLessons(data.sort((a, b) => a.orderIndex - b.orderIndex));
    };

    const handleSave = async (lesson: Partial<LessonAdmin>) => {
        const isEdit = !!editingLesson;
        const url = isEdit ? `/admin/lessons/${editingLesson.id}` : '/admin/lessons';
        const method = isEdit ? 'PUT' : 'POST';

        const payload = { ...lesson, courseId: selectedCourse };

        const { data, status, error } = await apiFetch<LessonAdmin>(url, {
            method,
            body: JSON.stringify(payload)
        });

        if (status >= 200 && status < 300 && data) {
            setIsModalOpen(false);
            setEditingLesson(null);
            fetchLessons(selectedCourse);
        } else {
            alert(`Failed to save: ${JSON.stringify(error)}`);
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm('Are you sure?')) return;
        const { status } = await apiFetch(`/admin/lessons/${id}`, { method: 'DELETE' });
        if (status === 204) fetchLessons(selectedCourse);
    };

    if (loading) return <Loading />;

    return (
        <div>
            <div className="flex justify-between items-center mb-8">
                <h2 className="text-3xl font-black italic">LESSONS</h2>
                <div className="flex gap-4">
                    <select
                        value={selectedCourse}
                        onChange={e => setSelectedCourse(e.target.value)}
                        className="bg-[#111] border border-white/20 rounded p-2 text-white font-bold uppercase text-sm"
                    >
                        {courses.map(c => <option key={c.id} value={c.id}>{c.titleHe}</option>)}
                    </select>
                    <button
                        onClick={() => { setEditingLesson(null); setIsModalOpen(true); }}
                        className="bg-white text-black px-4 py-2 rounded font-bold uppercase hover:bg-gray-200 transition"
                    >
                        + New Lesson
                    </button>
                </div>
            </div>

            <div className="space-y-2">
                {lessons.map(lesson => (
                    <div key={lesson.id} className="bg-[#111] border border-white/5 p-4 rounded flex justify-between items-center group hover:bg-white/[0.02]">
                        <div className="flex gap-4 items-center">
                            <div className="font-mono text-gray-500 font-bold w-8 text-center">{lesson.orderIndex}</div>
                            <div dir="rtl">
                                <div className="font-bold">{lesson.titleHe}</div>
                                <div className="text-xs text-gray-500">{lesson.movementCategory} • {lesson.vimeoVideoId || "NO VIDEO"}</div>
                            </div>
                        </div>

                        <div className="flex gap-2">
                            <button onClick={() => { setEditingLesson(lesson); setIsModalOpen(true); }} className="text-xs font-bold uppercase text-gray-400 hover:text-white px-2">Edit</button>
                            <button onClick={() => handleDelete(lesson.id)} className="text-xs font-bold uppercase text-red-500 hover:text-red-400 px-2">Delete</button>
                        </div>
                    </div>
                ))}
                {lessons.length === 0 && <div className="text-gray-500 text-center py-12 italic">No lessons in this course</div>}
            </div>

            {isModalOpen && (
                <LessonModal
                    lesson={editingLesson}
                    onClose={() => setIsModalOpen(false)}
                    onSave={handleSave}
                />
            )}
        </div>
    );
};

const LessonModal: React.FC<{
    lesson: LessonAdmin | null,
    onClose: () => void,
    onSave: (l: Partial<LessonAdmin>) => void
}> = ({ lesson, onClose, onSave }) => {
    const [formData, setFormData] = useState<Partial<LessonAdmin>>({
        titleHe: '',
        descriptionHe: '',
        movementCategory: 'Metcon',
        tags: [],
        vimeoVideoId: '',
        orderIndex: 0,
        published: true
    });
    const [previewVideoId, setPreviewVideoId] = useState<string | null>(null);
    const [verifying, setVerifying] = useState(false);
    const [verifyError, setVerifyError] = useState<string | null>(null);

    useEffect(() => {
        if (lesson) setFormData(lesson);
    }, [lesson]);

    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'Escape') {
                setPreviewVideoId(null);
            }
        };
        if (previewVideoId) {
            window.addEventListener('keydown', handleKeyDown);
        }
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [previewVideoId]);

    const handleVerifyVideo = async () => {
        if (!lesson?.id || !formData.vimeoVideoId) return;
        setVerifying(true);
        setVerifyError(null);
        try {
            const { data, error, status } = await apiFetch(`/admin/vimeo/lessons/${lesson.id}/verify`, {
                method: 'POST'
            });
            if (error) {
                if (status === 501 && error.error === 'vimeo_verify_disabled') {
                    setVerifyError('Verification disabled (set VIMEO_VERIFY_ENABLED=true)');
                } else {
                    setVerifyError(error.detail || error.message || 'Verification failed');
                }
            } else if (data) {
                // Instantly update UI with new verification stats
                setFormData(prev => ({
                    ...prev,
                    vimeoVerifyOk: data.ok,
                    vimeoVerifyCheckedAt: data.checked_at,
                    vimeoVerifyMissingDomains: data.missing_domains,
                    vimeoVerifyAllowedDomains: data.allowed_domains,
                    vimeoVerifyEmbedMode: data.embed_mode
                }));
                // Also trigger an upstream save so parent list refreshes next time it's opened
                onSave({
                    ...formData,
                    vimeoVerifyOk: data.ok,
                    vimeoVerifyCheckedAt: data.checked_at,
                    vimeoVerifyMissingDomains: data.missing_domains
                });
            }
        } catch (err: any) {
            setVerifyError(err.message || 'Unknown error during verification');
        } finally {
            setVerifying(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
            <div className="bg-[#111] border border-white/10 rounded-2xl w-full max-w-lg p-8">
                <h2 className="text-2xl font-black italic mb-6">{lesson ? 'EDIT LESSON' : 'NEW LESSON'}</h2>

                <div className="space-y-4">
                    <div className="grid grid-cols-4 gap-4">
                        <div className="col-span-3">
                            <label className="block text-xs font-bold uppercase text-gray-400 mb-1">Title (HE)</label>
                            <input dir="rtl" value={formData.titleHe} onChange={e => setFormData(p => ({ ...p, titleHe: e.target.value }))} className="w-full bg-black border border-white/20 rounded p-2 text-white" />
                        </div>
                        <div>
                            <label className="block text-xs font-bold uppercase text-gray-400 mb-1">Index</label>
                            <input type="number" value={formData.orderIndex} onChange={e => setFormData(p => ({ ...p, orderIndex: parseInt(e.target.value) }))} className="w-full bg-black border border-white/20 rounded p-2 text-white text-center" />
                        </div>
                    </div>

                    <div>
                        <label className="block text-xs font-bold uppercase text-gray-400 mb-1">Description (HE)</label>
                        <textarea dir="rtl" value={formData.descriptionHe} onChange={e => setFormData(p => ({ ...p, descriptionHe: e.target.value }))} className="w-full bg-black border border-white/20 rounded p-2 text-white" />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-xs font-bold uppercase text-gray-400 mb-1">Vimeo ID</label>
                            <input value={formData.vimeoVideoId || ''} onChange={e => setFormData(p => ({ ...p, vimeoVideoId: e.target.value }))} className="w-full bg-black border border-white/20 rounded p-2 text-white" />
                            {formData.vimeoVideoId && (
                                <div className="mt-2 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded">
                                    <div className="flex items-center gap-2 text-yellow-500 mb-2">
                                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" /><path d="M12 9v4" /><path d="M12 17h.01" /></svg>
                                        <span className="text-sm font-medium">Vimeo Privacy Check</span>
                                    </div>
                                    <p className="text-xs text-gray-400 mb-3">
                                        Verify this video has "Specific domains" embedding enabled in Vimeo.
                                    </p>
                                    <button
                                        type="button"
                                        onClick={() => setPreviewVideoId(formData.vimeoVideoId as string)}
                                        className="text-xs bg-black/50 hover:bg-black border border-white/20 px-3 py-1.5 rounded transition-colors text-white"
                                    >
                                        Test Embed Preview
                                    </button>
                                </div>
                            )}
                        </div>
                        <div>
                            <label className="block text-xs font-bold uppercase text-gray-400 mb-1">Category</label>
                            <input value={formData.movementCategory} onChange={e => setFormData(p => ({ ...p, movementCategory: e.target.value }))} className="w-full bg-black border border-white/20 rounded p-2 text-white" />
                        </div>
                    </div>

                    <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
                        <button onClick={onClose} className="px-5 py-2 text-sm font-bold uppercase text-gray-400 hover:text-white">Cancel</button>
                        <button onClick={() => onSave(formData)} className="bg-white text-black px-6 py-2 rounded font-bold uppercase hover:bg-gray-200">Save Lesson</button>
                    </div>
                </div>
            </div>

            {previewVideoId && (
                <div className="fixed inset-0 bg-black/90 flex items-center justify-center z-[60] p-8" onClick={() => setPreviewVideoId(null)}>
                    <div className="w-full max-w-4xl relative" onClick={e => e.stopPropagation()}>
                        <button onClick={() => setPreviewVideoId(null)} className="absolute -top-10 right-0 text-white font-bold uppercase">Close</button>
                        <iframe
                            src={`https://player.vimeo.com/video/${previewVideoId}`}
                            className="w-full aspect-video rounded border border-white/20 shadow-2xl"
                            allowFullScreen
                        />
                    </div>
                </div>
            )}
        </div>
    );
};

export default AdminLessons;
