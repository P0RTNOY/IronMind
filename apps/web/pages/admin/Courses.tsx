import React, { useEffect, useState } from 'react';
import { apiFetch } from '../../lib/api';
import { CourseAdmin } from '../../types';
import { Loading, ErrorState } from '../../components/Layout';
import { useUpload } from '../../hooks/useUpload';

const AdminCourses: React.FC = () => {
    const [courses, setCourses] = useState<CourseAdmin[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingCourse, setEditingCourse] = useState<CourseAdmin | null>(null);

    useEffect(() => {
        fetchCourses();
    }, []);

    const fetchCourses = async () => {
        setLoading(true);
        const { data, status, error } = await apiFetch<CourseAdmin[]>('/admin/courses');
        if (status === 200 && data) {
            setCourses(data);
        } else {
            setError(error?.detail || 'Failed to load courses');
        }
        setLoading(false);
    };

    const handleSave = async (course: Partial<CourseAdmin>) => {
        const isEdit = !!editingCourse;
        const url = isEdit ? `/admin/courses/${editingCourse.id}` : '/admin/courses';
        const method = isEdit ? 'PUT' : 'POST';

        const { data, status, error } = await apiFetch<CourseAdmin>(url, {
            method,
            body: JSON.stringify(course)
        });

        if (status >= 200 && status < 300 && data) {
            setIsModalOpen(false);
            setEditingCourse(null);
            fetchCourses();
        } else {
            alert(`Failed to save: ${JSON.stringify(error)}`);
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm('Are you sure you want to delete this course?')) return;
        const { status } = await apiFetch(`/admin/courses/${id}`, { method: 'DELETE' });
        if (status === 204) {
            fetchCourses();
        } else {
            alert('Failed to delete course');
        }
    };

    const togglePublish = async (courseId: string, currentPublished: boolean) => {
        const action = currentPublished ? 'unpublish' : 'publish';
        const { status, data } = await apiFetch<CourseAdmin>(`/admin/courses/${courseId}/${action}`, { method: 'POST' });
        if (status === 200 && data) {
            setCourses(prev => prev.map(c => c.id === courseId ? data : c));
        }
    };

    if (loading) return <Loading />;
    if (error) return <ErrorState status={500} message={error} />;

    return (
        <div>
            <div className="flex justify-between items-center mb-8">
                <h2 className="text-3xl font-black italic">COURSES</h2>
                <button
                    onClick={() => { setEditingCourse(null); setIsModalOpen(true); }}
                    className="bg-white text-black px-4 py-2 rounded font-bold uppercase hover:bg-gray-200 transition"
                >
                    + New Course
                </button>
            </div>

            <div className="grid gap-4">
                {courses.map(course => (
                    <div key={course.id} className="bg-[#111] border border-white/10 p-6 rounded-xl flex justify-between items-center group">
                        <div className="flex items-center gap-6">
                            {course.coverImageUrl ? (
                                <img src={course.coverImageUrl} alt={course.titleHe} className="w-16 h-16 object-cover rounded bg-white/5" />
                            ) : (
                                <div className="w-16 h-16 bg-white/5 rounded flex items-center justify-center text-xs text-gray-500">NO IMG</div>
                            )}
                            <div dir="rtl" className="text-right">
                                <h3 className="font-bold text-lg">{course.titleHe}</h3>
                                <div className="text-xs text-gray-500 font-mono uppercase">{course.id} • {course.type} • {course.published ? 'PUBLISHED' : 'DRAFT'}</div>
                            </div>
                        </div>

                        <div className="flex gap-3 opacity-100 sm:opacity-0 sm:group-hover:opacity-100 transition">
                            <button
                                onClick={() => togglePublish(course.id, course.published)}
                                className={`px-3 py-1 text-xs font-bold uppercase rounded border ${course.published ? 'text-yellow-500 border-yellow-500/50' : 'text-green-500 border-green-500/50'}`}
                            >
                                {course.published ? 'Unpublish' : 'Publish'}
                            </button>
                            <button
                                onClick={() => { setEditingCourse(course); setIsModalOpen(true); }}
                                className="px-3 py-1 text-xs font-bold uppercase rounded border border-white/20 hover:bg-white hover:text-black transition"
                            >
                                Edit
                            </button>
                            <button
                                onClick={() => handleDelete(course.id)}
                                className="px-3 py-1 text-xs font-bold uppercase rounded border border-red-500/50 text-red-500 hover:bg-red-500 hover:text-white transition"
                            >
                                Delete
                            </button>
                        </div>
                    </div>
                ))}
            </div>

            {isModalOpen && (
                <CourseModal
                    course={editingCourse}
                    onClose={() => setIsModalOpen(false)}
                    onSave={handleSave}
                />
            )}
        </div>
    );
};

const CourseModal: React.FC<{
    course: CourseAdmin | null,
    onClose: () => void,
    onSave: (c: Partial<CourseAdmin>) => void
}> = ({ course, onClose, onSave }) => {
    const { uploadFile, uploading, error: uploadError } = useUpload();

    const [formData, setFormData] = useState<Partial<CourseAdmin>>({
        titleHe: '',
        descriptionHe: '',
        type: 'one_time',
        published: false,
        coverImageUrl: '',
        coverImagePath: '',
        stripePriceIdOneTime: '',
        stripePriceIdSubscription: '',
        currency: 'usd',
        tags: []
    });

    useEffect(() => {
        if (course) {
            setFormData(course);
        }
    }, [course]);

    const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            const res = await uploadFile(e.target.files[0], 'cover');
            if (res) {
                setFormData(prev => ({
                    ...prev,
                    coverImageUrl: res.publicUrl,
                    coverImagePath: res.objectPath
                }));
            }
        }
    };

    return (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
            <div className="bg-[#111] border border-white/10 rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto p-8">
                <h2 className="text-2xl font-black italic mb-6">{course ? 'EDIT COURSE' : 'NEW COURSE'}</h2>

                <div className="space-y-6">
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-xs font-bold uppercase text-gray-400 mb-1">Type</label>
                            <select
                                value={formData.type}
                                onChange={e => setFormData(prev => ({ ...prev, type: e.target.value as any }))}
                                className="w-full bg-black border border-white/20 rounded p-2 text-white"
                            >
                                <option value="one_time">One Time Purchase</option>
                                <option value="subscription">Subscription</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-xs font-bold uppercase text-gray-400 mb-1">Currency</label>
                            <input
                                value={formData.currency}
                                onChange={e => setFormData(prev => ({ ...prev, currency: e.target.value }))}
                                className="w-full bg-black border border-white/20 rounded p-2 text-white"
                            />
                        </div>
                    </div>

                    <div>
                        <label className="block text-xs font-bold uppercase text-gray-400 mb-1">Title (Hebrew)</label>
                        <input
                            dir="rtl"
                            value={formData.titleHe}
                            onChange={e => setFormData(prev => ({ ...prev, titleHe: e.target.value }))}
                            className="w-full bg-black border border-white/20 rounded p-2 text-white"
                        />
                    </div>

                    <div>
                        <label className="block text-xs font-bold uppercase text-gray-400 mb-1">Description (Hebrew)</label>
                        <textarea
                            dir="rtl"
                            rows={3}
                            value={formData.descriptionHe}
                            onChange={e => setFormData(prev => ({ ...prev, descriptionHe: e.target.value }))}
                            className="w-full bg-black border border-white/20 rounded p-2 text-white"
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-xs font-bold uppercase text-gray-400 mb-1">Stripe Price ID (One Time)</label>
                            <input
                                value={formData.stripePriceIdOneTime || ''}
                                onChange={e => setFormData(prev => ({ ...prev, stripePriceIdOneTime: e.target.value }))}
                                className="w-full bg-black border border-white/20 rounded p-2 text-white font-mono text-xs"
                            />
                        </div>
                        <div>
                            <label className="block text-xs font-bold uppercase text-gray-400 mb-1">Stripe Price ID (Sub)</label>
                            <input
                                value={formData.stripePriceIdSubscription || ''}
                                onChange={e => setFormData(prev => ({ ...prev, stripePriceIdSubscription: e.target.value }))}
                                className="w-full bg-black border border-white/20 rounded p-2 text-white font-mono text-xs"
                            />
                        </div>
                    </div>

                    <div>
                        <label className="block text-xs font-bold uppercase text-gray-400 mb-1">Cover Image</label>
                        <div className="flex items-center gap-4">
                            {formData.coverImageUrl && (
                                <img src={formData.coverImageUrl} className="w-16 h-16 object-cover rounded bg-white/5" />
                            )}
                            <input type="file" accept="image/*" onChange={handleFileChange} />
                            {uploading && <span className="text-xs text-yellow-500 animate-pulse">UPLOADING...</span>}
                        </div>
                        {uploadError && <p className="text-red-500 text-xs mt-1">{uploadError}</p>}
                    </div>

                    <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
                        <button onClick={onClose} className="px-5 py-2 text-sm font-bold uppercase text-gray-400 hover:text-white">Cancel</button>
                        <button
                            onClick={() => onSave(formData)}
                            disabled={uploading}
                            className="bg-white text-black px-6 py-2 rounded font-bold uppercase hover:bg-gray-200 transition disabled:opacity-50"
                        >
                            Save Course
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AdminCourses;
