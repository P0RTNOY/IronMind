
import React, { useEffect, useState } from 'react';
import { apiFetch } from '../lib/api';
import { CoursePublic } from '../types';
import { Loading, ErrorState } from '../components/Layout';
import { Link } from 'react-router-dom';

const Home: React.FC = () => {
  const [courses, setCourses] = useState<CoursePublic[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<{status: number, data: any} | null>(null);

  useEffect(() => {
    const fetchCourses = async () => {
      const { data, error, status } = await apiFetch<CoursePublic[]>('/courses');
      if (status === 200 && data) {
        setCourses(data);
      } else {
        setError({ status, data: error });
      }
      setLoading(false);
    };
    fetchCourses();
  }, []);

  if (loading) return <Loading />;
  if (error) return <ErrorState status={error.status} message={error.data} />;

  return (
    <div className="max-w-7xl mx-auto px-4 py-12">
      <header className="mb-12">
        <h1 className="text-4xl md:text-6xl font-black tracking-tighter uppercase mb-4 italic">Available <span className="text-red-500">Missions</span></h1>
        <p className="text-gray-400 max-w-2xl text-lg">Master your body and mind with our elite selection of training protocols.</p>
      </header>

      {courses.length === 0 ? (
        <div className="py-20 text-center border border-dashed border-white/10 rounded-3xl">
          <p className="text-gray-500">No courses currently available. Stand by for deployment.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {courses.map((course) => (
            <Link 
              key={course.id} 
              to={`/courses/${course.id}`}
              className="group relative bg-[#111] border border-white/5 rounded-2xl overflow-hidden hover:border-red-500/50 transition-all duration-500 flex flex-col"
            >
              <div className="aspect-[16/9] w-full bg-gray-900 relative">
                <img 
                  src={course.coverImageUrl || `https://picsum.photos/seed/${course.id}/600/400`} 
                  alt={course.titleHe}
                  className="w-full h-full object-cover grayscale group-hover:grayscale-0 transition-all duration-700 opacity-60 group-hover:opacity-100"
                />
                <div className="absolute top-4 left-4 bg-black/80 backdrop-blur px-3 py-1 rounded-full text-[10px] font-bold tracking-widest text-red-500 border border-red-500/30">
                  {course.type === 'subscription' ? 'SUBSCRIPTION' : 'ONE-TIME'}
                </div>
              </div>
              <div className="p-6">
                <h3 className="text-xl font-bold mb-3 group-hover:text-red-500 transition-colors" dir="rtl">{course.titleHe}</h3>
                <p className="text-gray-500 text-sm line-clamp-2 leading-relaxed" dir="rtl">{course.descriptionHe}</p>
                <div className="mt-6 flex items-center justify-between">
                  <span className="text-[10px] text-gray-600 font-mono tracking-tighter">{course.id}</span>
                  <span className="text-red-500 group-hover:translate-x-1 transition-transform">→</span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
};

export default Home;
