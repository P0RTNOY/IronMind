
import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { apiFetch, fetchCourse, fetchCourseLessons, fetchCoursePlans, checkCourseAccess, fetchPlanDownload } from '../lib/api';
import { CoursePublic, LessonPublic, PlanPublic } from '../types';
import { Loading, ErrorState } from '../components/Layout';
import { toast } from '../components/toast';
import { useNavigate } from 'react-router-dom';

const CourseDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [course, setCourse] = useState<CoursePublic | null>(null);
  const [lessons, setLessons] = useState<LessonPublic[]>([]);
  const [plans, setPlans] = useState<PlanPublic[]>([]);
  const [hasAccess, setHasAccess] = useState<boolean>(false);
  const [loading, setLoading] = useState(true);
  const [contentLoading, setContentLoading] = useState(true);
  const [accessLoading, setAccessLoading] = useState(true);
  const [error, setError] = useState<{ status: number, data: any } | null>(null);

  useEffect(() => {
    const loadData = async () => {
      if (!id) return;
      setLoading(true);
      setContentLoading(true);
      setAccessLoading(true);

      // 1. Fetch public course details
      const courseReq = await fetchCourse(id);
      if (courseReq.status === 200 && courseReq.data) {
        setCourse(courseReq.data);
      } else {
        setError({ status: courseReq.status, data: courseReq.error });
        setLoading(false);
        return;
      }
      setLoading(false); // Render structural page immediately

      // 2. Fetch public content in parallel
      Promise.all([fetchCourseLessons(id), fetchCoursePlans(id)]).then(([lessonsReq, plansReq]) => {
        if (lessonsReq.status === 200 && lessonsReq.data) setLessons(lessonsReq.data);
        if (plansReq.status === 200 && plansReq.data) setPlans(plansReq.data);
        setContentLoading(false);
      });

      // 3. Check access
      checkAccessStatus(id);
    };

    loadData();
  }, [id]);

  const checkAccessStatus = async (courseId: string) => {
    setAccessLoading(true);
    const accessReq = await checkCourseAccess(courseId);
    setHasAccess(Boolean(accessReq.data?.allowed));
    setAccessLoading(false);
  };

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
                    const res = await apiFetch<{ url: string, intentId?: string }>('/checkout/session', {
                      method: 'POST',
                      body: JSON.stringify({
                        type: course.type,
                        courseId: course.id
                      })
                    });

                    if (res.status === 200 && res.data?.url) {
                      // Save context for deterministic success/cancel routing
                      localStorage.setItem('ironmind_checkout', JSON.stringify({
                        courseId: course.id,
                        scope: course.type === 'one_time' ? 'course' : 'membership',
                        intentId: res.data.intentId || null,
                        startedAt: Date.now()
                      }));
                      window.location.href = res.data.url;
                    } else {
                      toast.error('Failed to initiate checkout: ' + (res.error?.detail || 'Unknown error'));
                    }
                  } catch (e) {
                    toast.error('System error initiating checkout');
                  }
                }}
                className="bg-white text-black px-10 py-4 rounded-xl font-black uppercase tracking-widest hover:bg-red-500 hover:text-white transition-all duration-500 shadow-xl shadow-white/5 active:scale-95"
              >
                Purchase Access
              </button>
              <button
                onClick={() => checkAccessStatus(course.id)}
                disabled={accessLoading}
                className="block mx-auto mt-6 text-xs text-gray-500 hover:text-white uppercase tracking-widest transition-colors flex items-center justify-center gap-2"
              >
                {accessLoading ? (
                  <>
                    <svg className="animate-spin h-3 w-3 text-red-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                    Checking access...
                  </>
                ) : (
                  "Already purchased? Refresh access"
                )}
              </button>
            </div>
          </div>
        )}

        <div className="space-y-4">
          {contentLoading ? (
            <div className="text-gray-500 text-sm">Loading lessons…</div>
          ) : lessons.length === 0 ? (
            <div className="text-gray-500 text-sm">No lessons published yet.</div>
          ) : (
            lessons.map((lesson, idx) => {
              const locked = !hasAccess || !lesson.hasVideo || accessLoading;
              return (
                <button
                  key={lesson.id}
                  type="button"
                  disabled={locked}
                  onClick={() => navigate(`/lessons/${lesson.id}`)}
                  className={`w-full text-left bg-[#111] p-6 rounded-2xl flex items-center justify-between border border-white/5 transition-all
                    ${locked ? 'opacity-60 cursor-not-allowed' : 'hover:border-white/20 cursor-pointer'}`}
                >
                  <div className="flex items-center gap-8 text-right" dir="rtl">
                    <span className="text-3xl font-black text-white/10 italic">{String(idx + 1).padStart(2, '0')}</span>
                    <div>
                      <h4 className="font-bold text-white">{lesson.titleHe}</h4>
                      <p className="text-xs text-gray-500">{lesson.descriptionHe}</p>
                    </div>
                  </div>
                  <span className="text-xl">{locked ? '🔒' : '▶'}</span>
                </button>
              );
            })
          )}
        </div>

        <div className="mt-10">
          <div className="flex justify-between items-center border-b border-white/5 pb-4 mb-6">
            <h2 className="text-sm font-black text-gray-600 uppercase tracking-[0.2em]">Plans</h2>
          </div>

          {contentLoading ? (
            <div className="text-gray-500 text-sm">Loading plans…</div>
          ) : plans.length === 0 ? (
            <div className="text-gray-500 text-sm">No plans published yet.</div>
          ) : (
            <div className="space-y-4">
              {plans.map((plan) => {
                const locked = !hasAccess || !plan.hasPdf || accessLoading;
                return (
                  <div key={plan.id} className="bg-[#111] p-6 rounded-2xl border border-white/5 flex items-center justify-between">
                    <div className="text-right" dir="rtl">
                      <h4 className="font-bold text-white">{plan.titleHe}</h4>
                      <p className="text-xs text-gray-500">{plan.descriptionHe}</p>
                    </div>
                    <button
                      type="button"
                      disabled={locked}
                      onClick={async () => {
                        const res = await fetchPlanDownload(plan.id);
                        if (res.status === 200 && res.data?.url) {
                          window.open(res.data.url, "_blank");
                          return;
                        }
                        if (res.status === 401) {
                          window.location.hash = '#/login';
                          return;
                        }
                        if (res.status === 403) {
                          toast.info("Locked: you don't have access to this plan.");
                          return;
                        }
                        toast.error(res.error?.detail || "Download failed");
                      }}
                      className={`px-4 py-2 rounded-xl text-xs font-black uppercase tracking-widest transition
                        ${locked ? 'bg-white/5 text-gray-500 cursor-not-allowed' : 'bg-white text-black hover:bg-red-500 hover:text-white'}`}
                    >
                      {locked ? "Locked" : "Download PDF"}
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CourseDetail;
