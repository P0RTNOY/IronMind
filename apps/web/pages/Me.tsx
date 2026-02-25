
import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiFetch } from '../lib/api';
import { AccessMeResponse } from '../types';
import { Loading, ErrorState } from '../components/Layout';

const Me: React.FC = () => {
  const [access, setAccess] = useState<AccessMeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<{ status: number, data: any } | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      const { data, error, status } = await apiFetch<AccessMeResponse>('/access/me');
      if (status === 200 && data) {
        setAccess(data);
      } else {
        setError({ status, data: error });
      }
      setLoading(false);
    };
    fetchData();
  }, []);

  if (loading) return <Loading />;
  if (error) return <ErrorState status={error.status} message={error.data} />;
  if (!access) return <ErrorState status={401} />;

  return (
    <div className="max-w-2xl mx-auto px-4 py-20">
      <div className="bg-[#111] border border-white/5 rounded-3xl p-10 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-32 h-32 bg-red-500/10 blur-3xl rounded-full"></div>
        <div className="flex items-center gap-6 mb-10">
          <div className="w-20 h-20 bg-red-500 rounded-full flex items-center justify-center text-3xl font-black italic">
            {access.email?.[0]?.toUpperCase() || 'U'}
          </div>
          <div>
            <h1 className="text-3xl font-bold tracking-tighter">{access.email?.split('@')[0] || 'Operative'}</h1>
            <p className="text-gray-500">{access.email || 'No email associated'}</p>
          </div>
        </div>

        <div className="space-y-6">
          <div className="flex justify-between border-b border-white/5 pb-4">
            <span className="text-gray-600 font-bold uppercase text-xs">UID</span>
            <code className="text-red-400 font-mono text-xs">{access.uid}</code>
          </div>
          <div className="flex justify-between border-b border-white/5 pb-4">
            <span className="text-gray-600 font-bold uppercase text-xs">Security Clearance</span>
            <span className={`text-xs font-bold uppercase px-2 py-1 rounded ${access.isAdmin ? 'bg-red-500 text-white' : 'bg-white/10 text-gray-400'}`}>
              {access.isAdmin ? 'Admin Override' : 'Standard User'}
            </span>
          </div>
          <div className="flex justify-between border-b border-white/5 pb-4">
            <span className="text-gray-600 font-bold uppercase text-xs">Membership</span>
            <span className={`text-xs font-bold uppercase px-2 py-1 rounded ${access.membershipActive ? 'bg-green-500/20 text-green-500' : 'bg-white/10 text-gray-400'}`}>
              {access.membershipActive ? 'Active' : 'Inactive'}
            </span>
          </div>
          {access.membershipExpiresAt && (
            <div className="flex justify-between border-b border-white/5 pb-4">
              <span className="text-gray-600 font-bold uppercase text-xs">Expires</span>
              <span className="text-gray-400 font-mono text-xs">
                {new Date(access.membershipExpiresAt).toLocaleDateString()}
              </span>
            </div>
          )}
          <div className="flex justify-between border-b border-white/5 pb-4">
            <span className="text-gray-600 font-bold uppercase text-xs mt-1">Entitled Courses</span>
            <div className="flex flex-wrap justify-end gap-2 max-w-[60%]">
              {access.entitledCourseIds.length > 0 ? (
                access.entitledCourseIds.map(id => (
                  <Link
                    key={id}
                    to={`/courses/${id}`}
                    className="text-xs font-mono text-white bg-white/10 hover:bg-white/20 px-2 py-1 rounded transition"
                  >
                    {id.length > 15 ? `${id.slice(0, 15)}...` : id}
                  </Link>
                ))
              ) : (
                <span className="text-gray-500 italic text-xs mt-1">None</span>
              )}
            </div>
          </div>
        </div>

        {/* CTA Buttons */}
        <div className="mt-10 flex gap-4">
          <Link
            to="/library"
            className="bg-white text-black px-6 py-3 rounded-xl font-black uppercase tracking-widest text-sm hover:bg-red-500 hover:text-white transition"
          >
            Go to Library
          </Link>
          <Link
            to="/"
            className="border border-white/20 px-6 py-3 rounded-xl font-black uppercase tracking-widest text-sm text-gray-400 hover:text-white hover:border-white transition"
          >
            Browse Courses
          </Link>
        </div>

        <details className="mt-12 bg-black/40 rounded-xl border border-white/5 group">
          <summary className="p-6 cursor-pointer text-[10px] font-black text-gray-700 uppercase tracking-widest hover:text-gray-400 transition list-none flex justify-between items-center">
            <span>Raw Metadata</span>
            <span className="text-gray-600 group-open:rotate-180 transition-transform">▼</span>
          </summary>
          <div className="px-6 pb-6 pt-0">
            <pre className="text-[10px] text-gray-600 font-mono overflow-auto leading-relaxed bg-black/50 p-4 rounded-lg border border-white/5">
              {JSON.stringify(access, null, 2)}
            </pre>
          </div>
        </details>
      </div>
    </div>
  );
};

export default Me;
