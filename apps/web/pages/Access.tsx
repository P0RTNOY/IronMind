
import React, { useEffect, useState } from 'react';
import { apiFetch } from '../lib/api';
import { AccessMeResponse } from '../types';
import { Loading, ErrorState } from '../components/Layout';

const Access: React.FC = () => {
  const [access, setAccess] = useState<AccessMeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<{status: number, data: any} | null>(null);

  useEffect(() => {
    const fetchAccess = async () => {
      const { data, error, status } = await apiFetch<AccessMeResponse>('/access/me');
      if (status === 200 && data) {
        setAccess(data);
      } else {
        setError({ status, data: error });
      }
      setLoading(false);
    };
    fetchAccess();
  }, []);

  if (loading) return <Loading />;
  if (error) return <ErrorState status={error.status} message={error.data} />;
  if (!access) return <ErrorState status={401} />;

  return (
    <div className="max-w-4xl mx-auto px-4 py-20">
      <h1 className="text-4xl font-black uppercase italic tracking-tighter mb-12">Access <span className="text-red-500">Inventory</span></h1>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        <div className="bg-[#111] p-8 rounded-2xl border border-white/5">
          <p className="text-[10px] font-black text-gray-600 uppercase tracking-widest mb-2">Membership</p>
          <p className={`text-2xl font-bold ${access.membershipActive ? 'text-green-500' : 'text-red-500'}`}>
            {access.membershipActive ? 'ACTIVE' : 'INACTIVE'}
          </p>
        </div>
        <div className="bg-[#111] p-8 rounded-2xl border border-white/5">
          <p className="text-[10px] font-black text-gray-600 uppercase tracking-widest mb-2">Clearance</p>
          <p className="text-2xl font-bold">{access.isAdmin ? 'ADMIN' : 'STANDARD'}</p>
        </div>
        <div className="bg-[#111] p-8 rounded-2xl border border-white/5">
          <p className="text-[10px] font-black text-gray-600 uppercase tracking-widest mb-2">Expires</p>
          <p className="text-2xl font-bold font-mono text-gray-400">
            {access.membershipExpiresAt ? new Date(access.membershipExpiresAt).toLocaleDateString() : 'PERPETUAL'}
          </p>
        </div>
      </div>

      <div className="bg-[#111] border border-white/5 rounded-3xl p-10">
        <h3 className="text-sm font-black text-gray-600 uppercase tracking-widest mb-8">Entitled Mission IDs</h3>
        {access.entitledCourseIds.length === 0 ? (
          <p className="text-gray-500 italic">No one-time purchase entitlements found.</p>
        ) : (
          <div className="flex flex-wrap gap-3">
            {access.entitledCourseIds.map(id => (
              <span key={id} className="bg-red-500/10 border border-red-500/20 text-red-500 px-4 py-2 rounded-lg font-mono text-xs font-bold">
                {id}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Access;
