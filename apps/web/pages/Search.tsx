
import React, { useState, useEffect } from 'react';
import { apiFetch } from '../lib/api';
import { SearchResult } from '../types';
import { Loading } from '../components/Layout';
import { toast } from '../components/toast';
import { Link } from 'react-router-dom';

const Search: React.FC = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      if (query.trim()) handleSearch();
      else setResults(null);
    }, 400);
    return () => clearTimeout(timer);
  }, [query]);

  const handleSearch = async () => {
    setLoading(true);
    const { data } = await apiFetch<SearchResult>(`/search?q=${encodeURIComponent(query)}`);
    if (data) setResults(data);
    setLoading(false);
  };

  const downloadPlan = async (planId: string) => {
    const res = await apiFetch<{ url: string }>(`/content/plans/${planId}/download`, { skipRedirect: true });
    if (res.status === 200 && res.data?.url) {
      window.open(res.data.url, "_blank");
      return;
    }
    if (res.status === 401) {
      window.location.hash = '#/login';
      return;
    }
    if (res.status === 403) {
      toast.info("Locked: you don't have access to this plan. Acquire the mission access.");
      return;
    }
    toast.error(res.error?.detail || "Download failed");
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-16">
      <div className="relative group">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search Protocols, Lessons, or Plans..."
          className="w-full bg-[#111] border border-white/10 rounded-2xl px-8 py-6 text-xl md:text-2xl font-bold tracking-tighter focus:outline-none focus:border-red-500/50 transition-all placeholder:text-gray-700"
        />
        <div className="absolute right-6 top-1/2 -translate-y-1/2 text-gray-600 group-focus-within:text-red-500">
          <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
        </div>
      </div>

      <div className="mt-12">
        {loading && <Loading />}
        {!loading && results && (
          <div className="space-y-12">
            {/* Courses Section */}
            {results.courses.length > 0 && (
              <section>
                <h3 className="text-sm font-black text-gray-600 uppercase tracking-widest mb-6 flex items-center gap-4">
                  <span>Courses</span>
                  <div className="h-px bg-white/5 flex-grow"></div>
                </h3>
                <div className="grid gap-4">
                  {results.courses.map(c => (
                    <Link key={c.id} to={`/courses/${c.id}`} className="bg-[#111] p-6 rounded-xl border border-white/5 hover:border-red-500/30 transition flex justify-between items-center group">
                      <span className="font-bold text-lg group-hover:text-red-500 transition" dir="rtl">{c.titleHe}</span>
                      <span className="text-gray-600">→</span>
                    </Link>
                  ))}
                </div>
              </section>
            )}

            {/* Lessons Section */}
            {results.lessons.length > 0 && (
              <section>
                <h3 className="text-sm font-black text-gray-600 uppercase tracking-widest mb-6 flex items-center gap-4">
                  <span>Lessons</span>
                  <div className="h-px bg-white/5 flex-grow"></div>
                </h3>
                <div className="grid gap-4">
                  {results.lessons.map(l => (
                    <Link
                      key={l.id}
                      to={`/lessons/${l.id}`}
                      className="bg-[#111] p-6 rounded-xl border border-white/5 hover:border-red-500/30 transition flex flex-col gap-1 group"
                    >
                      <div className="flex justify-between items-start">
                        <span className="font-bold text-white group-hover:text-red-500 transition" dir="rtl">{l.titleHe}</span>
                        <span className="bg-white/5 px-2 py-1 rounded text-[10px] text-gray-500">{l.movementCategory}</span>
                      </div>
                      <p className="text-sm text-gray-500" dir="rtl">{l.descriptionHe}</p>
                      <div className="mt-2 text-[10px] text-gray-600 flex justify-end">
                        <span>{l.hasVideo ? '▶ View Lesson' : 'No Video'}</span>
                      </div>
                    </Link>
                  ))}
                </div>
              </section>
            )}

            {/* Plans Section */}
            {results.plans.length > 0 && (
              <section>
                <h3 className="text-sm font-black text-gray-600 uppercase tracking-widest mb-6 flex items-center gap-4">
                  <span>Plans</span>
                  <div className="h-px bg-white/5 flex-grow"></div>
                </h3>
                <div className="grid gap-4">
                  {results.plans.map(p => (
                    <div key={p.id} className="bg-[#111] p-6 rounded-xl border border-white/5 flex justify-between items-center">
                      <span className="font-bold text-white" dir="rtl">{p.titleHe}</span>

                      {p.hasPdf ? (
                        <button
                          onClick={() => downloadPlan(p.id)}
                          className="text-xs font-black uppercase tracking-widest bg-white text-black px-4 py-2 rounded-lg hover:bg-red-500 hover:text-white transition shadow-lg shadow-white/5"
                        >
                          Download PDF
                        </button>
                      ) : (
                        <span className="text-gray-600 text-xs font-black uppercase tracking-widest">NO PDF</span>
                      )}
                    </div>
                  ))}
                </div>
              </section>
            )}

            {results.courses.length === 0 && results.lessons.length === 0 && results.plans.length === 0 && (
              <div className="text-center py-20 bg-white/5 rounded-3xl border border-white/5">
                <p className="text-gray-500 font-bold">No data matches your search query.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Search;
