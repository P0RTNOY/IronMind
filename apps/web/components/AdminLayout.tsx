import React, { useEffect } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { Loading } from './Layout';

const AdminLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const { logout, isAdmin, loading } = useAuth();
    const navigate = useNavigate();

    useEffect(() => {
        if (!loading && !isAdmin) {
            navigate('/');
        }
    }, [loading, isAdmin, navigate]);

    if (loading) return <Loading />;

    // Double check to prevent flash of content
    if (!isAdmin) return null;

    return (
        <div className="min-h-screen bg-black text-white flex">
            {/* Sidebar */}
            <aside className="w-64 border-r border-white/10 flex flex-col fixed h-full bg-black z-10">
                <div className="p-8 border-b border-white/10">
                    <h1 className="text-2xl font-black italic uppercase">IronMind<span className="text-red-500">.Admin</span></h1>
                </div>

                <nav className="flex-1 p-4 space-y-1">
                    <NavItem to="/admin/dashboard" label="Overview" />
                    <NavItem to="/admin/courses" label="Courses" />
                    <NavItem to="/admin/lessons" label="Lessons" />
                    <NavItem to="/admin/plans" label="Plans" />
                    <NavItem to="/admin/users" label="Users" />
                    <NavItem to="/admin/activity" label="Activity" />
                </nav>

                <div className="p-4 border-t border-white/10">
                    <button onClick={logout} className="w-full text-left px-4 py-2 text-xs font-bold text-red-500 hover:bg-white/5 rounded uppercase tracking-widest">
                        Logout
                    </button>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 ml-64 p-8">
                {children}
            </main>
        </div>
    );
};

const NavItem: React.FC<{ to: string, label: string }> = ({ to, label }) => (
    <NavLink
        to={to}
        className={({ isActive }) =>
            `block px-4 py-3 rounded text-sm font-bold uppercase tracking-wider transition ${isActive
                ? 'bg-white text-black'
                : 'text-gray-400 hover:text-white hover:bg-white/5'
            }`
        }
    >
        {label}
    </NavLink>
);

export default AdminLayout;
