
import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiFetch } from '../lib/api';
import { AccessMeResponse, AccessCheckResponse } from '../types';
import { Loading, ErrorState } from '../components/Layout';

const Access: React.FC = () => {
  const [access, setAccess] = useState<AccessMeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<{ status: number, data: any } | null>(null);

  // Course access checker
  const [checkCourseId, setCheckCourseId] = useState('');
  const [checkResult, setCheckResult] = useState<{ allowed: boolean, courseId: string } | null>(null);
  const [checking, setChecking] = useState(false);

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

  const handleCheckAccess = async () => {
    if (!checkCourseId.trim()) return;
    setChecking(true);
    setCheckResult(null);
    const { data, status } = await apiFetch<AccessCheckResponse>(
      `/access/courses/${checkCourseId.trim()}`,
      { skipRedirect: true }
    );
    if (status === 200 && data?.allowed) {
      setCheckResult({ allowed: true, courseId: checkCourseId.trim() });
    } else {
      setCheckResult({ allowed: false, courseId: checkCourseId.trim() });
    }
    setChecking(false);
  };

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

      <div className="bg-[#111] border border-white/5 rounded-3xl p-10 mb-12">
        <h3 className="text-sm font-black text-gray-600 uppercase tracking-widest mb-8">Entitled Mission IDs</h3>
        {access.entitledCourseIds.length === 0 ? (
          <p className="text-gray-500 italic">No one-time purchase entitlements found.</p>
        ) : (
          <div className="flex flex-wrap gap-3">
            {access.entitledCourseIds.map(id => (
              <Link key={id} to={`/courses/${id}`} className="bg-red-500/10 border border-red-500/20 text-red-500 px-4 py-2 rounded-lg font-mono text-xs font-bold hover:bg-red-500/20 transition">
                {id}
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* Course Access Checker */}
      <div className="bg-[#111] border border-white/5 rounded-3xl p-10">
        <h3 className="text-sm font-black text-gray-600 uppercase tracking-widest mb-6">Course Access Checker</h3>
        <div className="flex gap-4 items-center mb-6">
          <input
            type="text"
            value={checkCourseId}
            onChange={e => setCheckCourseId(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleCheckAccess()}
            placeholder="Enter Course ID..."
            className="flex-1 bg-black border border-white/20 rounded-lg px-4 py-3 text-white font-mono text-sm placeholder:text-gray-600"
          />
          <button
            onClick={handleCheckAccess}
            disabled={checking || !checkCourseId.trim()}
            className="bg-white text-black px-6 py-3 rounded-lg font-bold uppercase text-sm hover:bg-gray-200 transition disabled:opacity-50"
          >
            {checking ? 'Checking...' : 'Check'}
          </button>
        </div>
        {checkResult && (
          <div className={`p-4 rounded-xl border ${checkResult.allowed ? 'border-green-500/30 bg-green-500/5' : 'border-red-500/30 bg-red-500/5'}`}>
            <p className={`font-bold text-lg ${checkResult.allowed ? 'text-green-500' : 'text-red-500'}`}>
              {checkResult.allowed ? '✅ Access Granted' : '❌ Access Denied'}
            </p>
            <p className="text-gray-500 text-sm mt-1">Course: <code className="text-gray-400">{checkResult.courseId}</code></p>
            {checkResult.allowed && (
              <Link to={`/courses/${checkResult.courseId}`} className="text-blue-400 text-sm mt-2 inline-block hover:text-blue-300 transition">
                → View Course
              </Link>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Access;
