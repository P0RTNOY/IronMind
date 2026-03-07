import React, { Suspense, lazy } from 'react';
import { HashRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Navbar, Loading } from './components/Layout';
import AdminLayout from './components/AdminLayout';
import { ToastProvider } from './components/ToastProvider';
import { useAuth } from './hooks/useAuth';
import { routes } from './lib/routes';

// Auth Guard Component
const RequireAuth: React.FC<{ children: JSX.Element }> = ({ children }) => {
  const { isAuthorized, loading } = useAuth();

  if (loading) return <Loading />;

  if (!isAuthorized) {
    const currentHash = window.location.hash;
    const target = import.meta.env.DEV ? routes.devAuth(currentHash) : routes.login(currentHash);

    return <Navigate to={target.replace('#', '')} replace />;
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
const NotFound = lazy(() => import('./pages/NotFound'));
const DevTools = lazy(() => import('./pages/DevTools'));

import { useParams } from 'react-router-dom';

const ProgramRedirect = () => {
  const { id } = useParams();
  if (!id) return <Navigate to="/" replace />;
  return <Navigate to={`/courses/${id}`} replace />;
};

// Admin Pages
const AdminDashboard = lazy(() => import('./pages/Admin'));
const AdminCourses = lazy(() => import('./pages/admin/Courses'));
const AdminLessons = lazy(() => import('./pages/admin/Lessons'));
const AdminPlans = lazy(() => import('./pages/admin/Plans'));
const AdminUsers = lazy(() => import('./pages/admin/Users'));
const AdminUserAccess = lazy(() => import('./pages/admin/UserAccess'));
const AdminActivity = lazy(() => import('./pages/admin/Activity'));
const AdminPayments = lazy(() => import('./pages/admin/Payments'));

import { DebugBanner } from './components/DebugBanner';

const App: React.FC = () => {
  const { loading } = useAuth();

  if (loading) return <Loading />;

  return (
    <ToastProvider>
      <Router>
        <div className="min-h-screen bg-[#0a0a0a] text-white flex flex-col font-sans selection:bg-red-500 selection:text-white">
          <DebugBanner />
          <Navbar />
          <main className="flex-grow">
            <Suspense fallback={<Loading />}>
              <Routes>
                {/* Public Routes */}
                <Route path="/" element={<Home />} />
                <Route path="/login" element={<Login />} />

                {/* Canonical route and legacy redirect mapping */}
                <Route path="/courses/:id" element={<CourseDetail />} />
                <Route path="/program/:id" element={<ProgramRedirect />} />

                <Route path="/lessons/:id" element={<LessonPlayer />} />
                <Route path="/search" element={<Search />} />
                <Route path="/auth-debug" element={<DevAuth />} />
                <Route path="/success" element={<Success />} />
                <Route path="/cancel" element={<Cancel />} />

                {/* DEV Override Panels */}
                {import.meta.env.DEV && <Route path="/dev-tools" element={<DevTools />} />}

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
                <Route path="/admin/users/:uid/access" element={<RequireAuth><AdminLayout><AdminUserAccess /></AdminLayout></RequireAuth>} />
                <Route path="/admin/activity" element={<RequireAuth><AdminLayout><AdminActivity /></AdminLayout></RequireAuth>} />
                <Route path="/admin/payments" element={<RequireAuth><AdminLayout><AdminPayments /></AdminLayout></RequireAuth>} />

                {/* Fallback */}
                <Route path="/not-found" element={<NotFound />} />
                <Route path="*" element={<NotFound />} />
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
