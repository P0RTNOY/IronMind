import React, { Suspense, lazy } from 'react';
import { HashRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Navbar, Loading } from './components/Layout';
import AdminLayout from './components/AdminLayout';
import { ToastProvider } from './components/ToastProvider';
import { useAuth } from './hooks/useAuth';

// Auth Guard Component
const RequireAuth: React.FC<{ children: JSX.Element }> = ({ children }) => {
  const { isAuthorized, loading } = useAuth();

  if (loading) return <Loading />;

  if (!isAuthorized) {
    const target = import.meta.env.DEV ? "/auth-debug" : "/login";
    return <Navigate to={target} replace />;
  }

  return children;
};

const Home = lazy(() => import('./pages/Home'));
const Login = lazy(() => import('./pages/Login'));
const Success = lazy(() => import('./pages/Success'));
const Cancel = lazy(() => import('./pages/Cancel'));
const CourseDetail = lazy(() => import('./pages/CourseDetail'));
const Search = lazy(() => import('./pages/Search'));
const Me = lazy(() => import('./pages/Me'));
const Access = lazy(() => import('./pages/Access'));
const DevAuth = lazy(() => import('./pages/DevAuth'));
const LessonPlayer = lazy(() => import('./pages/LessonPlayer'));
const Library = lazy(() => import('./pages/Library'));

// Admin Pages
const AdminDashboard = lazy(() => import('./pages/Admin'));
const AdminCourses = lazy(() => import('./pages/admin/Courses'));
const AdminLessons = lazy(() => import('./pages/admin/Lessons'));
const AdminPlans = lazy(() => import('./pages/admin/Plans'));
const AdminUsers = lazy(() => import('./pages/admin/Users'));

const App: React.FC = () => {
  const { loading } = useAuth();

  if (loading) return <Loading />;

  return (
    <ToastProvider>
      <Router>
        <div className="min-h-screen bg-[#0a0a0a] text-white flex flex-col font-sans selection:bg-red-500 selection:text-white">
          <Navbar />
          <main className="flex-grow">
            <Suspense fallback={<Loading />}>
              <Routes>
                {/* Public Routes */}
                <Route path="/" element={<Home />} />
                <Route path="/login" element={<Login />} />
                {/* Legacy /program preserved for now, mapping new /courses/:id */}
                <Route path="/program/:id" element={<CourseDetail />} />
                <Route path="/courses/:id" element={<CourseDetail />} />
                <Route path="/lessons/:id" element={<LessonPlayer />} />
                <Route path="/search" element={<Search />} />
                <Route path="/auth-debug" element={<DevAuth />} />
                <Route path="/success" element={<Success />} />
                <Route path="/cancel" element={<Cancel />} />

                {/* Protected Routes */}
                <Route path="/me" element={<RequireAuth><Me /></RequireAuth>} />
                <Route path="/access" element={<RequireAuth><Access /></RequireAuth>} />
                <Route path="/library" element={<RequireAuth><Library /></RequireAuth>} />

                {/* Admin Routes */}
                <Route path="/admin" element={<RequireAuth><AdminLayout><AdminDashboard /></AdminLayout></RequireAuth>} />
                <Route path="/admin/dashboard" element={<RequireAuth><AdminLayout><AdminDashboard /></AdminLayout></RequireAuth>} />
                <Route path="/admin/courses" element={<RequireAuth><AdminLayout><AdminCourses /></AdminLayout></RequireAuth>} />
                <Route path="/admin/lessons" element={<RequireAuth><AdminLayout><AdminLessons /></AdminLayout></RequireAuth>} />
                <Route path="/admin/plans" element={<RequireAuth><AdminLayout><AdminPlans /></AdminLayout></RequireAuth>} />
                <Route path="/admin/users" element={<RequireAuth><AdminLayout><AdminUsers /></AdminLayout></RequireAuth>} />

                {/* Fallback */}
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </Suspense>
          </main>

          <footer className="py-12 px-4 border-t border-white/5 mt-20">
            <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
              <div className="text-[10px] font-black tracking-widest text-gray-700 uppercase">
                IRON MIND / STRATEGIC LEARNING SYSTEMS / © 2024
              </div>
              <div className="flex gap-8 text-[10px] font-black tracking-widest text-gray-700 uppercase">
                <span className="hover:text-gray-400 cursor-pointer transition">Protocols</span>
                <span className="hover:text-gray-400 cursor-pointer transition">Systems</span>
                <span className="hover:text-gray-400 cursor-pointer transition">Security</span>
              </div>
            </div>
          </footer>
        </div>
      </Router>
    </ToastProvider>
  );
};

export default App;
