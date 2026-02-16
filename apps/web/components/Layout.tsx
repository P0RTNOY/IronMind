
import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

export const Navbar: React.FC = () => {
  const { isAuthorized, isAdmin, logout } = useAuth();
  const location = useLocation();
  const isMockMode = typeof window !== 'undefined' && localStorage.getItem('mockMode') === '1';

  const isActive = (path: string) => location.pathname === path;

  return (
    <nav className="sticky top-0 z-50 bg-black/80 backdrop-blur-md border-b border-white/10 px-4 py-3">
      <div className="max-w-7xl mx-auto flex justify-between items-center">
        <div className="flex items-center gap-8">
          <Link to="/" className="text-xl font-bold tracking-tighter text-white uppercase italic">
            Iron <span className="text-red-500">Mind</span>
          </Link>
          <div className="hidden md:flex gap-6 text-sm font-medium">
            <Link to="/" className={isActive('/') ? 'text-white' : 'text-gray-400 hover:text-white transition'}>Courses</Link>
            <Link to="/search" className={isActive('/search') ? 'text-white' : 'text-gray-400 hover:text-white transition'}>Search</Link>
            {isAuthorized && (
              <>
                <Link to="/me" className={isActive('/me') ? 'text-white' : 'text-gray-400 hover:text-white transition'}>Profile</Link>
                <Link to="/access" className={isActive('/access') ? 'text-white' : 'text-gray-400 hover:text-white transition'}>Access</Link>
              </>
            )}
            {isAdmin && (
              <Link to="/admin" className={isActive('/admin') ? 'text-red-500' : 'text-red-400 hover:text-red-300 transition'}>Admin</Link>
            )}
          </div>
        </div>

        <div className="flex items-center gap-4">
          {isMockMode && (
            <div className="hidden sm:block px-2 py-0.5 rounded bg-yellow-500/10 border border-yellow-500/20 text-[8px] font-black text-yellow-500 tracking-widest uppercase">
              Mock Mode
            </div>
          )}
          {!isAuthorized ? (
            <Link to="/login" className="bg-white text-black px-4 py-1.5 rounded-full text-xs font-bold hover:bg-gray-200 transition">
              LOGIN
            </Link>
          ) : (
            <button onClick={logout} className="text-xs text-gray-400 hover:text-white uppercase tracking-widest font-bold">
              LOGOUT
            </button>
          )}
        </div>
      </div>
    </nav>
  );
};

export const Loading: React.FC = () => (
  <div className="flex flex-col items-center justify-center min-h-[60vh]">
    <div className="w-10 h-10 border-4 border-red-500/30 border-t-red-500 rounded-full animate-spin"></div>
    <p className="mt-4 text-gray-500 text-sm animate-pulse">Engaging Systems...</p>
  </div>
);

export const ErrorState: React.FC<{ status: number; message?: any }> = ({ status, message }) => {
  const toggleMock = () => {
    localStorage.setItem('mockMode', '1');
    localStorage.setItem('debugUid', 'mock-user');
    window.location.reload();
  };

  const getFriendlyMessage = () => {
    if (status === 0) return message || "Strategic communication failure. The backend server could not be reached.";
    if (status === 401) return "Session unauthorized. Please authenticate via the Command Center.";
    if (status === 403) return "Access restricted. Clearance level insufficient.";
    if (status === 404) return "Resource not found in database.";
    return typeof message === 'string' ? message : "An unexpected tactical error occurred.";
  };

  return (
    <div className="bg-[#0a0a0a] border border-red-500/30 p-8 rounded-3xl text-center my-12 max-w-2xl mx-auto shadow-[0_0_50px_rgba(239,68,68,0.1)]">
      <div className="mb-6 inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-500/10 border border-red-500/20">
        <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      </div>

      <h2 className="text-3xl font-black text-white uppercase italic tracking-tighter mb-4">
        Signal <span className="text-red-500">Lost</span>
      </h2>

      <div className="bg-black/50 rounded-xl p-6 border border-white/5 text-left mb-8">
        <p className="text-gray-400 text-sm font-medium leading-relaxed font-mono">
          <span className="text-red-500 font-bold mr-2">STATUS_{status || '000'}:</span>
          {getFriendlyMessage()}
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <button onClick={() => window.location.reload()} className="bg-white text-black px-6 py-3 rounded-xl font-black uppercase tracking-widest hover:bg-gray-200 transition text-xs">
          Retry Link
        </button>
        <button onClick={toggleMock} className="bg-red-500 text-white px-6 py-3 rounded-xl font-black uppercase tracking-widest hover:bg-red-600 transition text-xs">
          Activate Mock Protocol
        </button>
      </div>

      {status === 0 && (
        <p className="mt-8 text-[10px] text-gray-600 leading-tight">
          Backend unreachable at {localStorage.getItem('apiBaseUrl') || 'http://localhost:8080'}. Activate Mock Mode to preview the interface with sample data.
        </p>
      )}
    </div>
  );
};
