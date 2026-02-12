
import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { apiFetch } from '../lib/api';

const DevAuth: React.FC = () => {
  const { uid, isAdmin, login, logout } = useAuth();
  const [inputUid, setInputUid] = useState(uid || '');
  const [inputAdmin, setInputAdmin] = useState(isAdmin);
  const [inputBaseUrl, setInputBaseUrl] = useState('');
  const [mockMode, setMockMode] = useState(false);
  const [testStatus, setTestStatus] = useState<{ loading: boolean; success?: boolean; message?: string } | null>(null);

  useEffect(() => {
    setInputUid(uid || '');
    setInputAdmin(isAdmin);
    // Use the Env URL as the default placeholder value
    // @ts-ignore
    const envUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';
    setInputBaseUrl(localStorage.getItem('apiBaseUrl') || envUrl);
    setMockMode(localStorage.getItem('mockMode') === '1');
  }, [uid, isAdmin]);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    localStorage.setItem('apiBaseUrl', inputBaseUrl.trim());
    localStorage.setItem('mockMode', mockMode ? '1' : '0');
    login(inputUid, inputAdmin);
  };

  const handleClear = () => {
    localStorage.removeItem('apiBaseUrl');
    localStorage.removeItem('mockMode');
    logout();
  };

  const testConnection = async () => {
    setTestStatus({ loading: true });
    const oldUrl = localStorage.getItem('apiBaseUrl');
    localStorage.setItem('apiBaseUrl', inputBaseUrl.trim());

    const { status, error } = await apiFetch('/health');

    if (status === 200) {
      setTestStatus({ loading: false, success: true, message: 'Link established.' });
    } else {
      setTestStatus({ loading: false, success: false, message: error || `Status ${status}` });
    }

    if (oldUrl) localStorage.setItem('apiBaseUrl', oldUrl);
    else localStorage.removeItem('apiBaseUrl');
  };

  return (
    <div className="max-w-md mx-auto px-4 py-20">
      <div className="bg-[#111] border border-white/10 p-10 rounded-3xl shadow-2xl relative">
        <h1 className="text-3xl font-black uppercase italic tracking-tighter mb-8 text-red-500">Dev <span className="text-white">Override</span></h1>

        <form onSubmit={handleSave} className="space-y-6">
          <div className="flex items-center justify-between p-4 bg-yellow-500/5 border border-yellow-500/20 rounded-xl">
            <span className="text-xs font-bold text-yellow-500 tracking-widest uppercase">Mock Protocol</span>
            <button
              type="button"
              onClick={() => setMockMode(!mockMode)}
              className={`w-10 h-5 rounded-full relative transition-colors ${mockMode ? 'bg-yellow-500' : 'bg-gray-800'}`}
            >
              <div className={`absolute top-0.5 w-4 h-4 bg-white rounded-full transition-all ${mockMode ? 'left-5.5' : 'left-0.5'}`}></div>
            </button>
          </div>

          <div>
            <div className="flex justify-between items-end mb-2">
              <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest">API BASE URL</label>
              <button type="button" onClick={testConnection} className="text-[10px] text-red-500 font-bold uppercase disabled:opacity-50">
                {testStatus?.loading ? 'Pinging...' : 'Test Link'}
              </button>
            </div>
            <input
              type="text"
              value={inputBaseUrl}
              onChange={(e) => setInputBaseUrl(e.target.value)}
              placeholder="https://proteins-arms-recommendation-mods.trycloudflare.com"
              className="w-full bg-black border border-white/10 rounded-xl px-4 py-3 text-white focus:border-red-500 outline-none transition font-mono text-xs"
            />
          </div>

          <div>
            <label className="block text-[10px] font-black text-gray-500 uppercase tracking-widest mb-2">DEBUG UID</label>
            <input
              type="text"
              value={inputUid}
              onChange={(e) => setInputUid(e.target.value)}
              className="w-full bg-black border border-white/10 rounded-xl px-4 py-3 text-white focus:border-red-500 outline-none transition font-mono text-sm"
              required
            />
          </div>

          <div className="flex items-center justify-between p-4 bg-black/40 border border-white/5 rounded-xl">
            <span className="text-sm font-bold text-gray-400">ADMIN CLEARANCE</span>
            <button
              type="button"
              onClick={() => setInputAdmin(!inputAdmin)}
              className={`w-12 h-6 rounded-full relative transition-colors ${inputAdmin ? 'bg-red-500' : 'bg-gray-800'}`}
            >
              <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-all ${inputAdmin ? 'left-7' : 'left-1'}`}></div>
            </button>
          </div>

          <div className="pt-6 space-y-3">
            <button type="submit" className="w-full bg-white text-black py-4 rounded-xl font-black uppercase tracking-widest hover:bg-red-500 hover:text-white transition-all">
              Commit Tactical Context
            </button>
            <button type="button" onClick={handleClear} className="w-full bg-transparent text-gray-600 py-2 font-bold uppercase text-[10px] hover:text-white transition">
              Factory Reset
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default DevAuth;
