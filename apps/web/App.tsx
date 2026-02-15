import React, { Suspense, lazy } from 'react';
import { HashRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Navbar, Loading } from './components/Layout';
import AdminLayout from './components/AdminLayout';
import { useAuth } from './hooks/useAuth';

// Lazy load pages for performance
const Home = lazy(() => import('./pages/Home'));
const CourseDetail = lazy(() => import('./pages/CourseDetail'));
const Search = lazy(() => import('./pages/Search'));
const Me = lazy(() => import('./pages/Me'));
const Access = lazy(() => import('./pages/Access'));
const DevAuth = lazy(() => import('./pages/DevAuth'));

// Admin Pages
const AdminDashboard = lazy(() => import('./pages/Admin'));
const AdminCourses = lazy(() => import('./pages/admin/Courses'));
const AdminLessons = lazy(() => import('./pages/admin/Lessons'));
const AdminPlans = lazy(() => import('./pages/admin/Plans'));
const AdminUsers = lazy(() => import('./pages/admin/Users'));

const App: React.FC = () => {
  const { loading, isAuthorized } = useAuth();

  if (loading) return <Loading />;

  return (
    <Router>
      <div className="min-h-screen bg-[#0a0a0a] text-white flex flex-col font-sans selection:bg-red-500 selection:text-white">
        <Navbar />
        <main className="flex-grow">
          <Suspense fallback={<Loading />}>
            <Routes>
              {/* Public Routes */}
              <Route path="/" element={<Home />} />
              <Route path="/program/:id" element={<CourseDetail />} />
              <Route path="/search" element={<Search />} />
              <Route path="/auth-debug" element={<DevAuth />} />

              {/* Protected Routes */}
              <Route
                path="/me"
                element={isAuthorized ? <Me /> : <Navigate to="/auth-debug" replace />}
              />
              <Route
                path="/access"
                element={isAuthorized ? <Access /> : <Navigate to="/auth-debug" replace />}
              />

              {/* Admin Routes */}
              <Route
                path="/admin"
                element={isAuthorized ? <AdminLayout><AdminDashboard /></AdminLayout> : <Navigate to="/auth-debug" replace />}
              />
              <Route
                path="/admin/dashboard"
                element={isAuthorized ? <AdminLayout><AdminDashboard /></AdminLayout> : <Navigate to="/auth-debug" replace />}
              />
              <Route
                path="/admin/courses"
                element={isAuthorized ? <AdminLayout><AdminCourses /></AdminLayout> : <Navigate to="/auth-debug" replace />}
              />
              <Route
                path="/admin/lessons"
                element={isAuthorized ? <AdminLayout><AdminLessons /></AdminLayout> : <Navigate to="/auth-debug" replace />}
              />
              <Route
                path="/admin/plans"
                element={isAuthorized ? <AdminLayout><AdminPlans /></AdminLayout> : <Navigate to="/auth-debug" replace />}
              />
              <Route
                path="/admin/users"
                element={isAuthorized ? <AdminLayout><AdminUsers /></AdminLayout> : <Navigate to="/auth-debug" replace />}
              />

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
  );
};

export default App;
