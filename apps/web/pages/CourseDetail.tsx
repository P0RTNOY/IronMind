
import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { apiFetch } from '../lib/api';
import { CoursePublic, AccessCheckResponse } from '../types';
import { Loading, ErrorState } from '../components/Layout';

const CourseDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [course, setCourse] = useState<CoursePublic | null>(null);
  const [hasAccess, setHasAccess] = useState<boolean>(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<{ status: number, data: any } | null>(null);

  useEffect(() => {
    const loadData = async () => {
      if (!id) return;

      // 1. Fetch public course details
      const courseReq = await apiFetch<CoursePublic>(`/courses/${id}`);
      if (courseReq.status === 200 && courseReq.data) {
        setCourse(courseReq.data);
      } else {
        setError({ status: courseReq.status, data: courseReq.error });
        setLoading(false);
        return;
      }

      // 2. Check access (skip redirect so guests can view the page)
      const accessReq = await apiFetch<AccessCheckResponse>(`/access/courses/${id}`, {
        skipRedirect: true
      });
      if (accessReq.status === 200 && accessReq.data?.allowed) {
        setHasAccess(true);
      } else {
        setHasAccess(false);
      }

      setLoading(false);
    };

    loadData();
  }, [id]);

  if (loading) return <Loading />;
  if (error) return <ErrorState status={error.status} message={error.data} />;
  if (!course) return <ErrorState status={404} />;

  return (
    <div className="max-w-5xl mx-auto px-4 py-12">
      <div className="mb-8">
        <Link to="/" className="text-sm text-gray-500 hover:text-white transition flex items-center gap-2">
          <span>←</span> Back to Missions
        </Link>
      </div>

      <div className="bg-[#111] rounded-3xl overflow-hidden border border-white/5 mb-12 shadow-2xl">
        <div className="h-80 w-full relative">
          <img
            src={course.coverImageUrl || `https://picsum.photos/seed/${course.id}/1200/600`}
            className="w-full h-full object-cover opacity-40 grayscale"
            alt={course.titleHe}
          />
          <div className="absolute inset-0 bg-gradient-to-t from-[#111] via-[#111]/20 to-transparent"></div>
          <div className="absolute bottom-10 left-10 right-10 text-right" dir="rtl">
            <div className="bg-red-500 text-white text-[10px] font-black px-4 py-1.5 rounded-full w-fit mb-4 tracking-widest uppercase shadow-lg shadow-red-500/20">
              {course.type === 'subscription' ? 'System Subscription' : 'Single Access Protocol'}
            </div>
            <h1 className="text-4xl md:text-6xl font-black tracking-tighter mb-4 text-white uppercase italic">{course.titleHe}</h1>
          </div>
        </div>

        <div className="p-10 text-right" dir="rtl">
          <div className="bg-white/5 h-px w-24 mb-8"></div>
          <p className="text-gray-400 text-lg leading-relaxed whitespace-pre-wrap max-w-3xl ml-auto">
            {course.descriptionHe}
          </p>
        </div>
      </div>

      <div className="space-y-6">
        <div className="flex justify-between items-center border-b border-white/5 pb-4 mb-8">
          <h2 className="text-sm font-black text-gray-600 uppercase tracking-[0.2em]">Operational Modules</h2>
          <span className="text-[10px] text-gray-500 font-mono uppercase tracking-widest">Protocol Version 2.5.0</span>
        </div>

        {hasAccess ? (
          <div className="bg-green-500/10 border border-green-500/20 p-6 rounded-2xl mb-8 flex items-center gap-4">
            <div className="w-10 h-10 rounded-full bg-green-500/20 flex items-center justify-center text-green-500">✓</div>
            <div>
              <p className="text-green-500 font-black uppercase text-xs tracking-widest">Clearance Active</p>
              <p className="text-gray-400 text-sm">Full protocol access confirmed. Modules decrypted.</p>
            </div>
          </div>
        ) : (
          <div className="bg-red-500/5 border border-red-500/20 p-10 rounded-3xl text-center mb-12 relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-64 h-64 bg-red-500/5 blur-[100px] pointer-events-none group-hover:bg-red-500/10 transition-all duration-700"></div>
            <div className="relative z-10">
              <p className="text-red-500 text-2xl font-black uppercase italic tracking-tighter mb-2">Access Blocked</p>
              <p className="text-gray-500 mb-8 max-w-md mx-auto text-sm">This protocol requires authorized clearance. Acquire the mission access to unlock restricted instructional content.</p>
              <button
                onClick={async () => {
                  try {
                    const res = await apiFetch<{ url: string }>('/checkout/session', {
                      method: 'POST',
                      body: JSON.stringify({
                        type: course.type,
                        courseId: course.id
                      })
                    });

                    if (res.status === 200 && res.data?.url) {
                      window.location.href = res.data.url;
                    } else {
                      alert('Failed to initiate checkout: ' + (res.error?.detail || 'Unknown error'));
                    }
                  } catch (e) {
                    alert('System error initiating checkout');
                  }
                }}
                className="bg-white text-black px-10 py-4 rounded-xl font-black uppercase tracking-widest hover:bg-red-500 hover:text-white transition-all duration-500 shadow-xl shadow-white/5 active:scale-95"
              >
                Purchase Access
              </button>
            </div>
          </div>
        )}

        <div className={`space-y-4 ${!hasAccess ? 'opacity-40 grayscale pointer-events-none' : ''}`}>
          {[
            { title: 'יסודות ומבנה', desc: 'הכרת המבנה הבסיסי של הפרוטוקול', time: '12:45' },
            { title: 'טכניקות מתקדמות', desc: 'שיפור ביצועים תחת לחץ', time: '08:20' },
            { title: 'סיכום ויישום', desc: 'אינטגרציה של כלל הידע שנרכש', time: '15:10' }
          ].map((item, n) => (
            <div key={n} className="bg-[#111] p-6 rounded-2xl flex items-center justify-between border border-white/5 group hover:border-white/20 transition-all cursor-pointer">
              <div className="flex items-center gap-8 text-right" dir="rtl">
                <span className="text-3xl font-black text-white/10 italic group-hover:text-red-500/20 transition-colors">{(n + 1).toString().padStart(2, '0')}</span>
                <div>
                  <h4 className="font-bold text-white group-hover:text-red-500 transition-colors">{item.title}</h4>
                  <p className="text-xs text-gray-500">{item.desc}</p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <span className="text-[10px] font-mono text-gray-600">{item.time}</span>
                <span className="text-xl">{hasAccess ? '▶' : '🔒'}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default CourseDetail;
