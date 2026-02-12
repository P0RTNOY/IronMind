
import React, { useEffect, useState } from 'react';
import { apiFetch } from '../lib/api';
import { MetricsOverview, CourseAdmin } from '../types';
import { Loading, ErrorState } from '../components/Layout';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

const Admin: React.FC = () => {
  const { isAdmin, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const [metrics, setMetrics] = useState<MetricsOverview | null>(null);
  const [courses, setCourses] = useState<CourseAdmin[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<{status: number, data: any} | null>(null);

  useEffect(() => {
    if (!authLoading && !isAdmin) {
      navigate('/');
      return;
    }

    const loadAdminData = async () => {
      setLoading(true);
      const metricsReq = await apiFetch<MetricsOverview>('/admin/metrics/overview');
      const coursesReq = await apiFetch<CourseAdmin[]>('/admin/courses');

      if (metricsReq.status === 200 && metricsReq.data) {
        setMetrics(metricsReq.data);
      }
      if (coursesReq.status === 200 && coursesReq.data) {
        setCourses(coursesReq.data);
      } else {
        setError({ status: coursesReq.status, data: coursesReq.error });
      }
      setLoading(false);
    };

    if (isAdmin) loadAdminData();
  }, [isAdmin, authLoading, navigate]);

  const togglePublish = async (courseId: string, currentPublished: boolean) => {
    const action = currentPublished ? 'unpublish' : 'publish';
    const { status, data } = await apiFetch<CourseAdmin>(`/admin/courses/${courseId}/${action}`, { method: 'POST' });
    if (status === 200 && data) {
      setCourses(prev => prev.map(c => c.id === courseId ? data : c));
    } else {
      alert(`Failed to ${action} course: ${JSON.stringify(data)}`);
    }
  };

  if (authLoading || loading) return <Loading />;
  if (error) return <ErrorState status={error.status} message={error.data} />;

  return (
    <div className="max-w-7xl mx-auto px-4 py-12">
      <h1 className="text-5xl font-black uppercase italic tracking-tighter mb-12 flex items-center gap-4">
        Command <span className="text-red-500 underline decoration-4">Center</span>
      </h1>

      {metrics && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4 mb-12">
          {Object.entries(metrics).map(([key, val]) => (
            <div key={key} className="bg-[#111] border border-white/5 p-6 rounded-xl">
              <p className="text-[9px] font-black text-gray-600 uppercase tracking-widest mb-1 truncate">{key.replace('_', ' ')}</p>
              <p className="text-2xl font-black italic">{val}</p>
            </div>
          ))}
        </div>
      )}

      <div className="flex justify-between items-end mb-8">
        <h2 className="text-2xl font-bold">Managed Protocols</h2>
        <button className="bg-red-500 text-white px-6 py-2 rounded-full font-bold text-sm hover:bg-red-600 transition">
          + New Protocol
        </button>
      </div>

      <div className="bg-[#111] border border-white/5 rounded-3xl overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-white/5 text-[10px] font-black uppercase tracking-widest text-gray-500">
            <tr>
              <th className="px-6 py-4">Title (HE)</th>
              <th className="px-6 py-4">Status</th>
              <th className="px-6 py-4">Type</th>
              <th className="px-6 py-4">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {courses.map(course => (
              <tr key={course.id} className="group hover:bg-white/[0.02] transition">
                <td className="px-6 py-6" dir="rtl">
                  <div className="font-bold">{course.titleHe}</div>
                  <div className="text-[10px] text-gray-600 font-mono mt-1 uppercase">{course.id}</div>
                </td>
                <td className="px-6 py-6">
                  <span className={`px-2 py-1 rounded text-[10px] font-bold ${course.published ? 'bg-green-500/10 text-green-500 border border-green-500/20' : 'bg-yellow-500/10 text-yellow-500 border border-yellow-500/20'}`}>
                    {course.published ? 'PUBLISHED' : 'DRAFT'}
                  </span>
                </td>
                <td className="px-6 py-6">
                  <span className="text-xs text-gray-400 font-medium uppercase tracking-tight">{course.type}</span>
                </td>
                <td className="px-6 py-6">
                  <div className="flex gap-4">
                    <button 
                      onClick={() => togglePublish(course.id, course.published)}
                      className="text-[10px] font-bold text-gray-400 hover:text-white transition uppercase border border-white/10 px-3 py-1.5 rounded"
                    >
                      {course.published ? 'UNPUBLISH' : 'PUBLISH'}
                    </button>
                    <button className="text-[10px] font-bold text-red-500 hover:text-red-400 transition uppercase">Edit</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Admin;
