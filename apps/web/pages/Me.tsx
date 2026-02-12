
import React, { useEffect, useState } from 'react';
import { apiFetch } from '../lib/api';
import { UserContext } from '../types';
import { Loading, ErrorState } from '../components/Layout';

const Me: React.FC = () => {
  const [me, setMe] = useState<UserContext | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<{status: number, data: any} | null>(null);

  useEffect(() => {
    const fetchMe = async () => {
      const { data, error, status } = await apiFetch<UserContext>('/me');
      if (status === 200 && data) {
        setMe(data);
      } else {
        setError({ status, data: error });
      }
      setLoading(false);
    };
    fetchMe();
  }, []);

  if (loading) return <Loading />;
  if (error) return <ErrorState status={error.status} message={error.data} />;
  if (!me) return <ErrorState status={401} />;

  return (
    <div className="max-w-2xl mx-auto px-4 py-20">
      <div className="bg-[#111] border border-white/5 rounded-3xl p-10 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-32 h-32 bg-red-500/10 blur-3xl rounded-full"></div>
        <div className="flex items-center gap-6 mb-10">
          <div className="w-20 h-20 bg-red-500 rounded-full flex items-center justify-center text-3xl font-black italic">
            {me.name?.[0] || 'U'}
          </div>
          <div>
            <h1 className="text-3xl font-bold tracking-tighter">{me.name || 'Anonymous Operative'}</h1>
            <p className="text-gray-500">{me.email || 'No email associated'}</p>
          </div>
        </div>

        <div className="space-y-6">
          <div className="flex justify-between border-b border-white/5 pb-4">
            <span className="text-gray-600 font-bold uppercase text-xs">UID</span>
            <code className="text-red-400 font-mono text-xs">{me.uid}</code>
          </div>
          <div className="flex justify-between border-b border-white/5 pb-4">
            <span className="text-gray-600 font-bold uppercase text-xs">Security Clearance</span>
            <span className={`text-xs font-bold uppercase px-2 py-1 rounded ${me.is_admin ? 'bg-red-500 text-white' : 'bg-white/10 text-gray-400'}`}>
              {me.is_admin ? 'Admin Override' : 'Standard User'}
            </span>
          </div>
        </div>

        <div className="mt-12 bg-black/40 p-6 rounded-xl border border-white/5">
          <h4 className="text-[10px] font-black text-gray-700 uppercase tracking-widest mb-4">Raw Metadata</h4>
          <pre className="text-[10px] text-gray-600 font-mono overflow-auto leading-relaxed">
            {JSON.stringify(me, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  );
};

export default Me;
