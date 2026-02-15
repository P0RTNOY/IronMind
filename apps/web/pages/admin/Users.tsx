import React, { useState, useEffect } from 'react';
import { apiFetch } from '../../lib/api';
import { AdminUsersListResponse, AdminUserRow, AdminUserDetailResponse, Entitlement, CourseAdmin } from '../../types';
import { Loading, ErrorState } from '../../components/Layout';

const AdminUsers: React.FC = () => {
    const [users, setUsers] = useState<AdminUserRow[]>([]);
    const [nextCursor, setNextCursor] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedUserUid, setSelectedUserUid] = useState<string | null>(null);

    useEffect(() => {
        fetchUsers();
    }, []);

    const fetchUsers = async (cursor?: string) => {
        setLoading(true);
        const query = cursor ? `?cursor=${encodeURIComponent(cursor)}` : '';
        const { data, status, error } = await apiFetch<AdminUsersListResponse>(`/admin/users${query}`);

        if (status === 200 && data) {
            if (cursor) {
                setUsers(prev => [...prev, ...data.users]);
            } else {
                setUsers(data.users);
            }
            setNextCursor(data.nextCursor || null);
        } else {
            setError(error?.detail || 'Failed to load users');
        }
        setLoading(false);
    };

    const handleLoadMore = () => {
        if (nextCursor) fetchUsers(nextCursor);
    };

    const closeModal = () => setSelectedUserUid(null);

    return (
        <div>
            <div className="flex justify-between items-end mb-8">
                <h1 className="text-4xl font-black uppercase italic tracking-tighter">
                    Users <span className="text-red-500">Manager</span>
                </h1>
                <button
                    onClick={() => fetchUsers()}
                    className="text-xs font-bold uppercase tracking-widest text-gray-500 hover:text-white"
                >
                    Refresh
                </button>
            </div>

            {error && <ErrorState status={500} message={error} />}

            <div className="bg-[#111] border border-white/5 rounded-2xl overflow-hidden">
                <table className="w-full text-left">
                    <thead className="bg-white/5 text-[10px] font-black uppercase tracking-widest text-gray-500">
                        <tr>
                            <th className="px-6 py-4">User</th>
                            <th className="px-6 py-4">Status</th>
                            <th className="px-6 py-4">Entitlements</th>
                            <th className="px-6 py-4 text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                        {users.map(user => (
                            <tr key={user.uid} className="hover:bg-white/[0.02] transition group">
                                <td className="px-6 py-4">
                                    <div className="font-bold text-white">{user.name || 'Anonymous'}</div>
                                    <div className="text-xs text-gray-500 font-mono">{user.email || user.uid}</div>
                                    <div className="text-[10px] text-gray-600 mt-1">
                                        Last seen: {user.lastSeenAt ? new Date(user.lastSeenAt).toLocaleDateString() : 'Never'}
                                    </div>
                                </td>
                                <td className="px-6 py-4">
                                    {user.membershipActive ? (
                                        <span className="bg-green-500/10 text-green-500 px-2 py-1 rounded text-[10px] font-bold border border-green-500/20">
                                            MEMBER
                                        </span>
                                    ) : (
                                        <span className="text-gray-500 text-[10px] font-bold">FREE</span>
                                    )}
                                </td>
                                <td className="px-6 py-4">
                                    <div className="flex gap-1 flex-wrap">
                                        {user.entitledCourseIds.slice(0, 3).map(id => (
                                            <span key={id} className="bg-white/10 px-1.5 py-0.5 rounded text-[10px] text-gray-300">
                                                {id.slice(0, 8)}...
                                            </span>
                                        ))}
                                        {user.entitledCourseIds.length > 3 && (
                                            <span className="text-[10px] text-gray-500 self-center">
                                                +{user.entitledCourseIds.length - 3} more
                                            </span>
                                        )}
                                        {user.entitledCourseIds.length === 0 && (
                                            <span className="text-[10px] text-gray-600 italic">None</span>
                                        )}
                                    </div>
                                </td>
                                <td className="px-6 py-4 text-right">
                                    <button
                                        onClick={() => setSelectedUserUid(user.uid)}
                                        className="text-[10px] font-bold uppercase bg-white text-black px-3 py-1.5 rounded hover:bg-gray-200 transition"
                                    >
                                        Manage
                                    </button>
                                </td>
                            </tr>
                        ))}
                        {users.length === 0 && !loading && (
                            <tr>
                                <td colSpan={4} className="px-6 py-8 text-center text-gray-500 italic">No users found.</td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>

            {nextCursor && (
                <div className="mt-8 text-center">
                    <button
                        onClick={handleLoadMore}
                        disabled={loading}
                        className="px-6 py-3 bg-[#111] border border-white/10 rounded-full text-xs font-bold uppercase tracking-widest hover:border-white/30 transition disabled:opacity-50"
                    >
                        {loading ? 'Loading...' : 'Load More users'}
                    </button>
                </div>
            )}

            {selectedUserUid && (
                <UserModal
                    uid={selectedUserUid}
                    onClose={closeModal}
                    onUpdate={() => {
                        // quick refresh list item? simplest is just re-fetch valid
                        fetchUsers();
                    }}
                />
            )}
        </div>
    );
};

// --- Modal Subcomponent ---

const UserModal: React.FC<{ uid: string, onClose: () => void, onUpdate: () => void }> = ({ uid, onClose, onUpdate }) => {
    const [data, setData] = useState<AdminUserDetailResponse | null>(null);
    const [courses, setCourses] = useState<CourseAdmin[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedCourseId, setSelectedCourseId] = useState('');
    const [granting, setGranting] = useState(false);

    useEffect(() => {
        loadDetails();
    }, [uid]);

    const loadDetails = async () => {
        setLoading(true);
        // Parallel fetch: user details + all courses (for dropdown)
        const [userRes, coursesRes] = await Promise.all([
            apiFetch<AdminUserDetailResponse>(`/admin/users/${uid}`),
            apiFetch<CourseAdmin[]>('/admin/courses')
        ]);

        if (userRes.data) setData(userRes.data);
        if (coursesRes.data) setCourses(coursesRes.data);
        setLoading(false);
    };

    const handleGrant = async () => {
        if (!selectedCourseId) return;
        setGranting(true);
        const { status, error } = await apiFetch(`/admin/users/${uid}/entitlements`, {
            method: 'POST',
            body: JSON.stringify({ courseId: selectedCourseId })
        });

        if (status === 200) {
            await loadDetails(); // refresh local modal state
            onUpdate(); // refresh parent list
            setSelectedCourseId('');
        } else {
            alert(`Failed: ${error?.detail}`);
        }
        setGranting(false);
    };

    const handleRevoke = async (entId: string) => {
        if (!confirm("Are you sure you want to revoke this access?")) return;
        const { status } = await apiFetch(`/admin/entitlements/${entId}`, { method: 'DELETE' });
        if (status === 204) {
            await loadDetails();
            onUpdate();
        }
    };

    if (!data && loading) return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
            <div className="text-white">Loading...</div>
        </div>
    );

    if (!data) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
            <div className="bg-[#0a0a0a] border border-white/10 w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-2xl shadow-2xl">
                <div className="p-6 border-b border-white/10 flex justify-between items-center sticky top-0 bg-[#0a0a0a] z-10">
                    <div>
                        <h2 className="text-xl font-bold">{data.profile.name || 'User Details'}</h2>
                        <div className="text-xs text-gray-500 font-mono mt-1">{uid}</div>
                    </div>
                    <button onClick={onClose} className="text-gray-400 hover:text-white transition text-2xl">×</button>
                </div>

                <div className="p-6 space-y-8">

                    {/* Entitlements Section */}
                    <div>
                        <h3 className="text-sm font-black uppercase tracking-widest text-gray-500 mb-4">Active Entitlements</h3>

                        {/* Grant New */}
                        <div className="flex gap-2 mb-6 p-4 bg-white/5 rounded-xl">
                            <select
                                className="flex-1 bg-black border border-white/20 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-red-500"
                                value={selectedCourseId}
                                onChange={e => setSelectedCourseId(e.target.value)}
                            >
                                <option value="">Select Protocol to Grant...</option>
                                {courses.map(c => (
                                    <option key={c.id} value={c.id}>{c.titleHe} ({c.id})</option>
                                ))}
                            </select>
                            <button
                                onClick={handleGrant}
                                disabled={!selectedCourseId || granting}
                                className="bg-white text-black px-4 py-2 rounded font-bold text-xs uppercase hover:bg-gray-200 disabled:opacity-50"
                            >
                                {granting ? 'Granting...' : 'Grant Access'}
                            </button>
                        </div>

                        <div className="space-y-2">
                            {data.entitlements.length === 0 && <div className="text-gray-500 italic text-sm">No entitlements found.</div>}
                            {data.entitlements.map(ent => (
                                <div key={ent.id} className="flex justify-between items-center p-3 border border-white/5 rounded hover:bg-white/5 transition">
                                    <div>
                                        <div className="font-bold text-sm">
                                            {ent.kind === 'membership' ? 'MEMBERSHIP' : (
                                                courses.find(c => c.id === ent.courseId)?.titleHe || ent.courseId
                                            )}
                                        </div>
                                        <div className="text-[10px] text-gray-500 font-mono flex gap-2">
                                            <span>{ent.status.toUpperCase()}</span>
                                            <span>•</span>
                                            <span>Src: {ent.source}</span>
                                            <span>•</span>
                                            <span>Expires: {ent.expiresAt ? new Date(ent.expiresAt).toLocaleDateString() : 'Never'}</span>
                                        </div>
                                    </div>
                                    {ent.status === 'active' && (
                                        <button
                                            onClick={() => handleRevoke(ent.id)}
                                            className="text-[10px] text-red-500 hover:text-red-400 font-bold uppercase border border-red-500/20 px-2 py-1 rounded hover:bg-red-500/10"
                                        >
                                            Revoke
                                        </button>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Raw JSON Debug (Optional, helpful for dev) */}
                    {/* <pre className="text-[10px] text-gray-600 whitespace-pre-wrap">{JSON.stringify(data, null, 2)}</pre> */}
                </div>
            </div>
        </div>
    );
};

export default AdminUsers;
