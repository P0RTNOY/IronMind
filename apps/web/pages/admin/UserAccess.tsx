import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { apiFetch } from '../../lib/api';
import { AdminUserDetailResponse, CourseAdmin } from '../../types';
import { Loading, ErrorState } from '../../components/Layout';
import { toast } from '../../components/toast';

interface ActivityEvent {
    id: string;
    type: string;
    uid: string;
    createdAt?: string;
    courseId?: string;
    lessonId?: string;
    planId?: string;
}

const EVENT_COLORS: Record<string, string> = {
    access_check: 'text-blue-400',
    content_download: 'text-green-400',
    content_playback: 'text-purple-400',
    checkout_started: 'text-yellow-400',
};

const UserAccess: React.FC = () => {
    const { uid } = useParams<{ uid: string }>();
    const [data, setData] = useState<AdminUserDetailResponse | null>(null);
    const [courses, setCourses] = useState<CourseAdmin[]>([]);
    const [activity, setActivity] = useState<ActivityEvent[]>([]);
    const [loading, setLoading] = useState(true);
    const [activityLoading, setActivityLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Grant form state
    const [selectedCourseId, setSelectedCourseId] = useState('');
    const [granting, setGranting] = useState(false);

    // Membership state
    const [membershipExpiryInput, setMembershipExpiryInput] = useState('');
    const [membershipSaving, setMembershipSaving] = useState(false);

    useEffect(() => {
        if (uid) {
            loadAll();
            loadActivity();
        }
    }, [uid]);

    const loadAll = async () => {
        setLoading(true);
        const [userRes, coursesRes] = await Promise.all([
            apiFetch<AdminUserDetailResponse>(`/admin/users/${uid}`),
            apiFetch<CourseAdmin[]>('/admin/courses')
        ]);

        if (userRes.status === 200 && userRes.data) {
            setData(userRes.data);
            setError(null);
        } else {
            setError(userRes.error?.detail || 'Failed to load user data');
        }

        if (coursesRes.status === 200 && coursesRes.data) {
            setCourses(coursesRes.data);
        }
        setLoading(false);
    };

    const loadActivity = async () => {
        setActivityLoading(true);
        // Fetch more to ensure we get some for this user
        const { data, status } = await apiFetch<ActivityEvent[]>('/admin/activity?limit=50');
        if (status === 200 && data) {
            // Filter client-side for this user and take top 10
            const userEvents = data.filter(e => e.uid === uid).slice(0, 10);
            setActivity(userEvents);
        }
        setActivityLoading(false);
    };

    const handleGrant = async () => {
        if (!selectedCourseId || !uid) return;
        setGranting(true);

        const { status, error: grantError } = await apiFetch(`/admin/users/${uid}/entitlements`, {
            method: 'POST',
            body: JSON.stringify({ courseId: selectedCourseId })
        });

        if (status === 200) {
            toast.success(`Granted course ${selectedCourseId} successfully`);
            setSelectedCourseId('');
            await loadAll(); // Refetch user detail to sync state
        } else {
            toast.error(`Grant failed: ${grantError?.detail || 'Unknown error'}`);
        }
        setGranting(false);
    };

    const handleRevoke = async (entId: string) => {
        if (!confirm("Are you sure you want to revoke this access?")) return;

        const { status, error: revokeError } = await apiFetch(`/admin/entitlements/${entId}`, {
            method: 'DELETE'
        });

        if (status === 204) {
            toast.success("Access revoked successfully");
            await loadAll(); // Refetch user detail to sync state
        } else {
            toast.error(`Revoke failed: ${revokeError?.detail || 'Unknown error'}`);
        }
    };

    const handleActivateMembership = async () => {
        setMembershipSaving(true);
        const { status, error: err } = await apiFetch(`/admin/users/${uid}/membership/activate`, {
            method: 'POST',
            body: JSON.stringify({})
        });
        if (status === 200) {
            toast.success("Membership activated");
            await loadAll();
        } else {
            toast.error(`Activation failed: ${err?.detail || 'Unknown error'}`);
        }
        setMembershipSaving(false);
    };

    const handleDeactivateMembership = async () => {
        if (!confirm("Are you sure you want to deactivate this membership? This will clear any expiry date.")) return;
        setMembershipSaving(true);
        const { status, error: err } = await apiFetch(`/admin/users/${uid}/membership/deactivate`, {
            method: 'POST'
        });
        if (status === 200) {
            toast.success("Membership deactivated");
            await loadAll();
        } else {
            toast.error(`Deactivation failed: ${err?.detail || 'Unknown error'}`);
        }
        setMembershipSaving(false);
    };

    const handleSetMembershipExpiry = async () => {
        setMembershipSaving(true);
        let expiresAt = null;
        if (membershipExpiryInput) {
            expiresAt = `${membershipExpiryInput}T23:59:59.999Z`;
        }
        const { status, error: err } = await apiFetch(`/admin/users/${uid}/membership/set-expiry`, {
            method: 'POST',
            body: JSON.stringify({ expiresAt })
        });
        if (status === 200) {
            toast.success("Membership expiry updated");
            setMembershipExpiryInput('');
            await loadAll();
        } else {
            toast.error(`Update failed: ${err?.detail || 'Unknown error'}`);
        }
        setMembershipSaving(false);
    };

    if (loading && !data) return <Loading />;
    if (error) return <ErrorState status={500} message={error} />;
    if (!data) return <ErrorState status={404} message="User not found" />;

    const profile = data.profile;

    return (
        <div className="max-w-5xl mx-auto pb-20">
            {/* Header */}
            <div className="mb-8 border-b border-white/10 pb-6">
                <div className="flex justify-between items-start mb-4">
                    <div>
                        <Link to="/admin/users" className="text-red-500 hover:text-red-400 text-xs font-bold uppercase tracking-widest flex items-center gap-2 mb-4">
                            ← Back to Users
                        </Link>
                        <h1 className="text-4xl font-black uppercase italic tracking-tighter">
                            User <span className="text-red-500">Access Console</span>
                        </h1>
                        <div className="flex items-center gap-4 mt-2">
                            <span className="text-sm font-bold">{profile.name || 'No Name'}</span>
                            <span className="text-sm text-gray-500 font-mono">{profile.email || 'No Email'}</span>
                            <span className="text-xs text-gray-600 font-mono">UID: {profile.uid}</span>
                        </div>
                    </div>
                    <div className="flex gap-3">
                        <a href="/#/admin/activity" className="px-4 py-2 border border-white/10 rounded-lg text-xs font-bold uppercase tracking-widest text-gray-400 hover:text-white hover:border-white/30 transition">
                            Global Activity
                        </a>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

                {/* Main Content (Left Col) */}
                <div className="lg:col-span-2 space-y-8">

                    {/* Membership Card */}
                    <div className="bg-[#111] border border-white/5 rounded-2xl p-6">
                        <div className="flex justify-between items-start mb-6">
                            <h2 className="text-lg font-black uppercase tracking-widest">Membership</h2>
                            {profile.membershipActive ? (
                                <span className="bg-green-500/10 text-green-500 px-3 py-1 rounded text-xs font-bold border border-green-500/20">
                                    ACTIVE
                                </span>
                            ) : (
                                <span className="bg-white/5 text-gray-500 px-3 py-1 rounded text-xs font-bold">
                                    INACTIVE
                                </span>
                            )}
                        </div>

                        <div className="grid grid-cols-2 gap-4 mb-6">
                            <div className="bg-black/50 p-4 rounded-xl border border-white/5">
                                <div className="text-[10px] text-gray-500 uppercase font-black tracking-widest mb-1">Expires At</div>
                                <div className="font-mono text-sm text-gray-300">
                                    {profile.membershipExpiresAt ? new Date(profile.membershipExpiresAt).toLocaleDateString() : 'Never / None'}
                                </div>
                            </div>
                            <div className="bg-black/50 p-4 rounded-xl border border-white/5">
                                <div className="text-[10px] text-gray-500 uppercase font-black tracking-widest mb-1">Status</div>
                                <div className="font-bold text-sm text-gray-300">
                                    {profile.membershipActive ? 'Premium Member' : 'Free Tier'}
                                </div>
                            </div>
                        </div>

                        <div className="flex flex-col gap-3 pt-4 border-t border-white/5">
                            <div className="flex flex-wrap gap-3">
                                {profile.membershipActive ? (
                                    <button
                                        onClick={handleDeactivateMembership}
                                        disabled={membershipSaving}
                                        className="bg-red-500/10 text-red-500 hover:bg-red-500 hover:text-white px-4 py-2 rounded font-bold text-xs uppercase tracking-widest transition border border-red-500/20 hover:border-red-500 disabled:opacity-50"
                                    >
                                        {membershipSaving ? '...' : 'Deactivate'}
                                    </button>
                                ) : (
                                    <button
                                        onClick={handleActivateMembership}
                                        disabled={membershipSaving}
                                        className="bg-green-500/10 text-green-500 hover:bg-green-500 hover:text-white px-4 py-2 rounded font-bold text-xs uppercase tracking-widest transition border border-green-500/20 hover:border-green-500 disabled:opacity-50"
                                    >
                                        {membershipSaving ? '...' : 'Activate'}
                                    </button>
                                )}
                            </div>

                            <div className="flex gap-2 items-center mt-2 bg-white/[0.02] p-3 rounded-lg border border-white/5">
                                <input
                                    type="date"
                                    className="bg-black border border-white/20 rounded px-3 py-1.5 text-xs text-white focus:outline-none focus:border-red-500"
                                    value={membershipExpiryInput}
                                    onChange={e => setMembershipExpiryInput(e.target.value)}
                                />
                                <button
                                    onClick={handleSetMembershipExpiry}
                                    disabled={membershipSaving}
                                    className="bg-white/10 text-white hover:bg-white/20 px-4 py-1.5 rounded font-bold text-[10px] uppercase tracking-widest transition disabled:opacity-50"
                                >
                                    {membershipSaving ? '...' : 'Set Expiry'}
                                </button>
                                <span className="text-[10px] text-gray-500 italic ml-2">
                                    Leave blank to clear
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* Course Entitlements Card */}
                    <div className="bg-[#111] border border-white/5 rounded-2xl p-6">
                        <h2 className="text-lg font-black uppercase tracking-widest mb-6">Course Access</h2>

                        {/* Grant UI */}
                        <div className="flex gap-2 mb-8 p-4 bg-white/[0.02] border border-white/5 rounded-xl">
                            <select
                                className="flex-1 bg-black border border-white/20 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-red-500"
                                value={selectedCourseId}
                                onChange={e => setSelectedCourseId(e.target.value)}
                            >
                                <option value="">Select Plan / Protocol to Grant...</option>
                                {courses.map(c => (
                                    <option key={c.id} value={c.id}>{c.titleHe} ({c.id})</option>
                                ))}
                            </select>
                            <button
                                onClick={handleGrant}
                                disabled={!selectedCourseId || granting}
                                className="bg-white text-black px-6 py-2 rounded font-black text-xs uppercase tracking-widest hover:bg-gray-200 disabled:opacity-50 transition"
                            >
                                {granting ? '...' : 'Grant'}
                            </button>
                        </div>

                        {/* Entitlements List */}
                        <div className="space-y-3">
                            {data.entitlements.length === 0 && (
                                <div className="text-center p-8 bg-black/40 rounded-xl border border-white/5 border-dashed">
                                    <span className="text-gray-500 italic text-sm">No entitlements found</span>
                                </div>
                            )}
                            {data.entitlements.map(ent => {
                                const isInactive = ent.status === 'inactive';
                                const courseName = ent.kind === 'course'
                                    ? (courses.find(c => c.id === ent.courseId)?.titleHe || ent.courseId)
                                    : 'MEMBERSHIP';

                                return (
                                    <div key={ent.id} className={`flex justify-between items-center p-4 border border-white/5 rounded-xl transition ${isInactive ? 'opacity-50 bg-black/50' : 'bg-black/80 hover:bg-white/5'}`}>
                                        <div>
                                            <div className="flex items-center gap-3 mb-1">
                                                <div className={`font-bold text-sm ${isInactive ? 'text-gray-500 line-through' : 'text-white'}`}>
                                                    {courseName}
                                                </div>
                                                {isInactive ? (
                                                    <span className="px-2 py-0.5 bg-white/10 text-gray-400 rounded text-[9px] font-black tracking-widest uppercase">
                                                        Inactive
                                                    </span>
                                                ) : (
                                                    <span className="px-2 py-0.5 bg-green-500/20 text-green-500 border border-green-500/20 rounded text-[9px] font-black tracking-widest uppercase">
                                                        Active
                                                    </span>
                                                )}
                                            </div>
                                            <div className="text-[10px] text-gray-500 font-mono flex gap-3">
                                                <span><span className="text-gray-600">ID:</span> {ent.id.slice(0, 18)}...</span>
                                                <span><span className="text-gray-600">Src:</span> {ent.source}</span>
                                                {ent.expiresAt && <span><span className="text-gray-600">Exp:</span> {new Date(ent.expiresAt).toLocaleDateString()}</span>}
                                            </div>
                                        </div>

                                        {!isInactive && (
                                            <button
                                                onClick={() => handleRevoke(ent.id)}
                                                className="text-[10px] text-red-500 hover:text-red-400 font-bold uppercase border border-red-500/20 px-3 py-1.5 rounded hover:bg-red-500/10 transition"
                                            >
                                                Revoke
                                            </button>
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                </div>

                {/* Right Col: Context / Activity */}
                <div className="space-y-8">
                    <div className="bg-[#111] border border-white/5 rounded-2xl p-6">
                        <h3 className="text-sm font-black uppercase tracking-widest text-gray-500 mb-6 flex justify-between items-center">
                            Recent Activity
                            {activityLoading && <span className="text-[10px] animate-pulse">Loading...</span>}
                        </h3>

                        <div className="space-y-4">
                            {!activityLoading && activity.length === 0 && (
                                <div className="text-xs text-gray-600 italic text-center py-4">
                                    No recent events for this user.
                                </div>
                            )}
                            {activity.map(evt => (
                                <div key={evt.id} className="border-b border-white/5 pb-3 last:border-0 last:pb-0">
                                    <div className="flex justify-between items-start mb-1">
                                        <span className={`text-[10px] font-black uppercase tracking-widest ${EVENT_COLORS[evt.type] || 'text-gray-400'}`}>
                                            {evt.type.replace('_', ' ')}
                                        </span>
                                        <span className="text-[10px] text-gray-600 font-mono">
                                            {evt.createdAt ? new Date(evt.createdAt).toLocaleDateString() : '—'}
                                        </span>
                                    </div>
                                    <div className="text-xs text-gray-400 font-mono">
                                        {evt.courseId && <span className="mr-2 border border-white/10 px-1 rounded">C: {evt.courseId.slice(0, 8)}</span>}
                                        {evt.lessonId && <span className="mr-2 border border-white/10 px-1 rounded">L: {evt.lessonId.slice(0, 8)}</span>}
                                        {evt.planId && <span className="mr-2 border border-white/10 px-1 rounded">P: {evt.planId.slice(0, 8)}</span>}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Placeholder for future Payments / Subscriptions overview */}
                    <div className="bg-[#111] border border-white/5 rounded-2xl p-6 opacity-50">
                        <h3 className="text-sm font-black uppercase tracking-widest text-gray-500 mb-4">
                            Payments Context
                        </h3>
                        <div className="text-xs text-gray-500 italic">
                            Subscription & Payment data will appear here once the PayPlus integration is complete.
                        </div>
                    </div>
                </div>

            </div>
        </div>
    );
};

export default UserAccess;
