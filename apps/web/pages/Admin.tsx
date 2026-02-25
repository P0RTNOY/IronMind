
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
  const [growthData, setGrowthData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<{ status: number, data: any } | null>(null);

  useEffect(() => {
    if (!authLoading && !isAdmin) {
      navigate('/');
      return;
    }

    const loadAdminData = async () => {
      setLoading(true);
      const [metricsReq, growthReq] = await Promise.all([
        apiFetch<MetricsOverview>('/admin/metrics/overview'),
        apiFetch<any[]>('/admin/analytics/growth?days=30')
      ]);

      if (metricsReq.status === 200 && metricsReq.data) {
        setMetrics(metricsReq.data);
      } else {
        setError({ status: metricsReq.status, data: metricsReq.error });
      }

      if (growthReq.status === 200 && growthReq.data) {
        setGrowthData(growthReq.data);
      }

      setLoading(false);
    };

    if (isAdmin) loadAdminData();
  }, [isAdmin, authLoading, navigate]);


  if (authLoading || loading) return <Loading />;
  if (error) return <ErrorState status={error.status} message={error.data} />;

  return (
    <div className="max-w-7xl mx-auto px-4 py-12">
      <div className="flex items-center justify-between mb-12">
        <h1 className="text-5xl font-black uppercase italic tracking-tighter flex items-center gap-4">
          Command <span className="text-red-500 underline decoration-4">Center</span>
        </h1>
        {import.meta.env.DEV && (
          <button
            onClick={async () => {
              const { data, status, error } = await apiFetch<any>('/admin/dev/seed', { method: 'POST' });
              if (status === 200 && data) {
                const created = data.created?.length || 0;
                const skipped = data.skipped?.length || 0;
                const updated = data.updated?.length || 0;
                alert(`Seed complete: ${created} created, ${updated} updated, ${skipped} skipped`);
                navigate('/admin/courses');
              } else {
                alert(`Seed failed: ${JSON.stringify(error)}`);
              }
            }}
            className="bg-yellow-500 text-black px-4 py-2 rounded font-bold uppercase text-sm hover:bg-yellow-400 transition"
          >
            🌱 Seed Demo Data
          </button>
        )}
      </div>

      {metrics && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4 mb-12">
          <MetricCard label="Total Users" value={metrics.users_total} />
          {Object.entries(metrics).map(([key, val]) => {
            if (key === 'users_total') return null;
            return (
              <div key={key} className="bg-[#111] border border-white/5 p-6 rounded-xl hover:border-white/10 transition">
                <p className="text-[9px] font-black text-gray-500 uppercase tracking-widest mb-1 truncate">{key.replace(/_/g, ' ')}</p>
                <p className="text-2xl font-black italic text-white">{val}</p>
              </div>
            );
          })}
        </div>
      )}

      <div className="mb-12">
        <AnalyticsChart data={growthData} />
      </div>
    </div>
  );
};

const MetricCard: React.FC<{ label: string, value: number }> = ({ label, value }) => (
  <div className="bg-[#111] border border-white/5 p-6 rounded-xl">
    <p className="text-[9px] font-black text-gray-600 uppercase tracking-widest mb-1 truncate">{label}</p>
    <p className="text-2xl font-black italic">{value}</p>
  </div>
);

import { AnalyticsChart } from '../components/AnalyticsChart';
export default Admin;
