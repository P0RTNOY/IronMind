import React, { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { apiFetch } from '../lib/api';
import { Loading } from '../components/Layout';

interface CheckoutSessionVerification {
    courseId: string | null;
    paymentStatus: string;
}

const Success: React.FC = () => {
    const [searchParams] = useSearchParams();
    const sessionId = searchParams.get('session_id');
    const [loading, setLoading] = useState(true);
    const [courseId, setCourseId] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const verifyPurchase = async () => {
            if (!sessionId) {
                setError('No session ID found.');
                setLoading(false);
                return;
            }

            const { data, status } = await apiFetch<CheckoutSessionVerification>(`/checkout/session/${sessionId}`);

            if (status === 200 && data) {
                if (data.paymentStatus === 'paid') {
                    setCourseId(data.courseId);
                } else {
                    setError(`Payment status: ${data.paymentStatus}`);
                }
            } else {
                setError('Failed to verify purchase.');
            }
            setLoading(false);
        };

        verifyPurchase();
    }, [sessionId]);

    if (loading) return <Loading />;

    return (
        <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
            <div className="bg-[#111] border border-green-500/20 p-8 rounded-2xl shadow-[0_0_50px_rgba(34,197,94,0.1)] max-w-md w-full">
                {error ? (
                    <>
                        <div className="w-16 h-16 bg-red-500/10 rounded-full flex items-center justify-center mx-auto mb-6 text-red-500">
                            <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </div>
                        <h1 className="text-2xl font-bold text-white mb-2">Verification Failed</h1>
                        <p className="text-gray-400 mb-6">{error}</p>
                        <Link to="/" className="text-white underline hover:text-gray-300">Return Home</Link>
                    </>
                ) : (
                    <>
                        <div className="w-16 h-16 bg-green-500/10 rounded-full flex items-center justify-center mx-auto mb-6 text-green-500">
                            <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                        </div>
                        <h1 className="text-3xl font-black text-white italic uppercase tracking-tighter mb-2">
                            Access <span className="text-green-500">Granted</span>
                        </h1>
                        <p className="text-gray-400 text-sm mb-8">
                            Payment confirmed. Access may take a few seconds.
                        </p>

                        <div className="space-y-3">
                            {courseId && (
                                <Link
                                    to={`/courses/${courseId}`}
                                    className="block w-full bg-white text-black py-4 rounded-xl font-bold uppercase tracking-widest hover:bg-gray-200 transition-colors shadow-lg shadow-white/10"
                                >
                                    Go to course
                                </Link>
                            )}

                            <Link
                                to="/library"
                                className={`block w-full border border-white/20 text-white py-4 rounded-xl font-bold uppercase tracking-widest hover:bg-white/5 transition-colors ${!courseId && 'bg-white/5'}`}
                            >
                                Go to My Library
                            </Link>

                            <Link
                                to="/"
                                className="block w-full text-gray-500 py-3 rounded-xl text-xs uppercase tracking-widest hover:text-white transition-colors mt-4"
                            >
                                Back to Home
                            </Link>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};

export default Success;
