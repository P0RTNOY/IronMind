import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

const Cancel: React.FC = () => {
    const [courseId, setCourseId] = useState<string | null>(null);

    useEffect(() => {
        try {
            const stored = localStorage.getItem('ironmind_checkout');
            if (stored) {
                const parsed = JSON.parse(stored);
                if (parsed.courseId) {
                    setCourseId(parsed.courseId);
                }
            }
        } catch (e) {
            // ignore
        } finally {
            // Always clean up on cancel so we don't accidentally use it later
            localStorage.removeItem('ironmind_checkout');
        }
    }, []);

    return (
        <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
            <div className="bg-[#111] border border-white/10 p-8 rounded-2xl shadow-2xl max-w-md w-full">
                <div className="w-16 h-16 bg-yellow-500/10 rounded-full flex items-center justify-center mx-auto mb-6 text-yellow-500">
                    <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                </div>
                <h1 className="text-2xl font-bold text-white mb-2 tracking-tight">Purchase Cancelled</h1>
                <p className="text-gray-400 text-sm mb-8">
                    The transaction was not completed. No charges were made.
                </p>

                <div className="space-y-3">
                    {courseId ? (
                        <>
                            <Link
                                to={`/courses/${courseId}`}
                                className="block w-full bg-white text-black py-4 rounded-xl font-bold uppercase tracking-widest hover:bg-gray-200 transition-colors shadow-lg shadow-white/10"
                            >
                                Try Again
                            </Link>
                            <Link
                                to="/"
                                className="block w-full text-gray-400 py-3 rounded-xl font-bold uppercase tracking-widest hover:text-white transition-colors"
                            >
                                Return to Courses
                            </Link>
                        </>
                    ) : (
                        <Link
                            to="/"
                            className="block w-full bg-white text-black py-4 rounded-xl font-bold uppercase tracking-widest hover:bg-gray-200 transition-colors shadow-lg shadow-white/10"
                        >
                            Return to Courses
                        </Link>
                    )}
                </div>
            </div>
        </div>
    );
};

export default Cancel;
