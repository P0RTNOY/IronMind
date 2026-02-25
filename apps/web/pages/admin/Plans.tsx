import React, { useEffect, useState } from 'react';
import { apiFetch } from '../../lib/api';
import { PlanAdmin, CourseAdmin } from '../../types';
import { Loading, ErrorState } from '../../components/Layout';
import { useUpload } from '../../hooks/useUpload';

const AdminPlans: React.FC = () => {
    const [plans, setPlans] = useState<PlanAdmin[]>([]);
    const [courses, setCourses] = useState<CourseAdmin[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedCourse, setSelectedCourse] = useState<string>('');
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingPlan, setEditingPlan] = useState<PlanAdmin | null>(null);

    useEffect(() => {
        loadInitialData();
    }, []);

    useEffect(() => {
        if (selectedCourse) {
            fetchPlans(selectedCourse);
        } else {
            setPlans([]);
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

    const fetchPlans = async (courseId: string) => {
        const { data } = await apiFetch<PlanAdmin[]>(`/admin/courses/${courseId}/plans`);
        if (data) setPlans(data);
    };

    const handleSave = async (plan: Partial<PlanAdmin>) => {
        const isEdit = !!editingPlan;
        const url = isEdit ? `/admin/plans/${editingPlan.id}` : '/admin/plans';
        const method = isEdit ? 'PUT' : 'POST';

        const payload = { ...plan, courseId: selectedCourse };

        const { data, status, error } = await apiFetch<PlanAdmin>(url, {
            method,
            body: JSON.stringify(payload)
        });

        if (status >= 200 && status < 300 && data) {
            setIsModalOpen(false);
            setEditingPlan(null);
            fetchPlans(selectedCourse);
        } else {
            alert(`Failed to save: ${JSON.stringify(error)}`);
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm('Are you sure?')) return;
        const { status } = await apiFetch(`/admin/plans/${id}`, { method: 'DELETE' });
        if (status === 204) fetchPlans(selectedCourse);
    };

    const togglePublish = async (planId: string, currentPublished: boolean) => {
        const action = currentPublished ? 'unpublish' : 'publish';
        const { status, data } = await apiFetch<PlanAdmin>(
            `/admin/plans/${planId}/${action}`, { method: 'POST' }
        );
        if (status === 200 && data) {
            setPlans(prev => prev.map(p => p.id === planId ? data : p));
        }
    };

    if (loading) return <Loading />;

    if (courses.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[50vh] text-center">
                <h2 className="text-3xl font-black italic mb-4">NO PROTOCOLS FOUND</h2>
                <p className="text-gray-400 mb-8 max-w-md">
                    You must create at least one Protocol (Course) before you can manage Plans.
                    Plans are strictly associated with a specific Protocol.
                </p>
                <a href="#/admin/courses" className="bg-red-500 text-white px-8 py-3 rounded-full font-bold uppercase hover:bg-red-600 transition">
                    Go to Protocols
                </a>
            </div>
        );
    }

    return (
        <div>
            <div className="flex justify-between items-center mb-8">
                <h2 className="text-3xl font-black italic">PLANS (PDFs)</h2>
                <div className="flex gap-4">
                    <select
                        value={selectedCourse}
                        onChange={e => setSelectedCourse(e.target.value)}
                        className="bg-[#111] border border-white/20 rounded p-2 text-white font-bold uppercase text-sm"
                    >
                        {courses.map(c => <option key={c.id} value={c.id}>{c.titleHe}</option>)}
                    </select>
                    <button
                        onClick={() => { setEditingPlan(null); setIsModalOpen(true); }}
                        disabled={!selectedCourse}
                        className="bg-white text-black px-4 py-2 rounded font-bold uppercase hover:bg-gray-200 transition disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        + New Plan
                    </button>
                </div>
            </div>

            <div className="space-y-2">
                {plans.map(plan => (
                    <div key={plan.id} className="bg-[#111] border border-white/5 p-4 rounded flex justify-between items-center group hover:bg-white/[0.02]">
                        <div className="flex gap-4 items-center">
                            <div className="w-10 h-10 bg-red-500/10 text-red-500 rounded flex items-center justify-center font-bold text-xs">PDF</div>
                            <div dir="rtl">
                                <div className="font-bold">{plan.titleHe}</div>
                                <div className="text-xs text-gray-500">{plan.pdfPath || "NO PDF"} • {plan.published ? 'PUBLISHED' : 'DRAFT'}</div>
                            </div>
                        </div>

                        <div className="flex gap-2">
                            <a href={`/#/courses/${selectedCourse}`} target="_blank" rel="noopener noreferrer" className="text-xs font-bold uppercase text-blue-400 hover:text-blue-300 px-2" title="View course as user">↗</a>
                            <button
                                onClick={() => togglePublish(plan.id, plan.published)}
                                className={`text-xs font-bold uppercase px-2 ${plan.published ? 'text-yellow-500 hover:text-yellow-400' : 'text-green-500 hover:text-green-400'}`}
                            >
                                {plan.published ? 'Unpublish' : 'Publish'}
                            </button>
                            <button onClick={() => { setEditingPlan(plan); setIsModalOpen(true); }} className="text-xs font-bold uppercase text-gray-400 hover:text-white px-2">Edit</button>
                            <button onClick={() => handleDelete(plan.id)} className="text-xs font-bold uppercase text-red-500 hover:text-red-400 px-2">Delete</button>
                        </div>
                    </div>
                ))}
                {plans.length === 0 && <div className="text-gray-500 text-center py-12 italic">No plans in this course</div>}
            </div>

            {isModalOpen && (
                <PlanModal
                    plan={editingPlan}
                    onClose={() => setIsModalOpen(false)}
                    onSave={handleSave}
                />
            )}
        </div>
    );
};

const PlanModal: React.FC<{
    plan: PlanAdmin | null,
    onClose: () => void,
    onSave: (p: Partial<PlanAdmin>) => void
}> = ({ plan, onClose, onSave }) => {
    const { uploadFile, uploading, error: uploadError } = useUpload();
    const [formData, setFormData] = useState<Partial<PlanAdmin>>({
        titleHe: '',
        descriptionHe: '',
        tags: [],
        pdfPath: '',
        published: true
    });

    useEffect(() => {
        if (plan) setFormData(plan);
    }, [plan]);

    const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            const res = await uploadFile(e.target.files[0], 'plan_pdf');
            if (res) {
                setFormData(prev => ({
                    ...prev,
                    pdfPath: res.objectPath
                }));
            }
        }
    };

    return (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
            <div className="bg-[#111] border border-white/10 rounded-2xl w-full max-w-lg p-8">
                <h2 className="text-2xl font-black italic mb-6">{plan ? 'EDIT PLAN' : 'NEW PLAN'}</h2>

                <div className="space-y-4">
                    <div>
                        <label className="block text-xs font-bold uppercase text-gray-400 mb-1">Title (HE)</label>
                        <input dir="rtl" value={formData.titleHe} onChange={e => setFormData(p => ({ ...p, titleHe: e.target.value }))} className="w-full bg-black border border-white/20 rounded p-2 text-white" />
                    </div>

                    <div>
                        <label className="block text-xs font-bold uppercase text-gray-400 mb-1">Description (HE)</label>
                        <textarea dir="rtl" value={formData.descriptionHe} onChange={e => setFormData(p => ({ ...p, descriptionHe: e.target.value }))} className="w-full bg-black border border-white/20 rounded p-2 text-white" />
                    </div>

                    <div>
                        <label className="block text-xs font-bold uppercase text-gray-400 mb-1">PDF File</label>
                        <div className="flex items-center gap-4">
                            {formData.pdfPath && <span className="text-xs text-green-500 font-mono">PDF LINKED</span>}
                            <input type="file" accept="application/pdf" onChange={handleFileChange} className="text-sm text-gray-500" />
                        </div>
                        {uploading && <span className="text-xs text-yellow-500 animate-pulse">UPLOADING...</span>}
                        {uploadError && <p className="text-red-500 text-xs mt-1">{uploadError}</p>}
                    </div>

                    <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
                        <button onClick={onClose} className="px-5 py-2 text-sm font-bold uppercase text-gray-400 hover:text-white">Cancel</button>
                        <button onClick={() => onSave(formData)} disabled={uploading} className="bg-white text-black px-6 py-2 rounded font-bold uppercase hover:bg-gray-200 disabled:opacity-50">Save Plan</button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AdminPlans;
