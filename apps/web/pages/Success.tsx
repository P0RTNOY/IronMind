import React, { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { apiFetch } from '../lib/api';
import { Loading } from '../components/Layout';

interface CheckoutSessionVerification {
    courseId: string | null;
    paymentStatus: string;
}

interface IntentVerification {
    id: string;
    status: string;
    scope: string;
    courseId?: string;
}

const Success: React.FC = () => {
    const [searchParams] = useSearchParams();
    const sessionId = searchParams.get('session_id'); // From provider if present
    const [loading, setLoading] = useState(true);
    const [polling, setPolling] = useState(false);
    const [courseId, setCourseId] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    // 1. Recover Context
    useEffect(() => {
        const recoverAndVerify = async () => {
            // Read fallback context
            let localContext: any = null;
            try {
                const stored = localStorage.getItem('ironmind_checkout');
                if (stored) {
                    const parsed = JSON.parse(stored);
                    // Only use if started less than 30 mins ago
                    if (Date.now() - parsed.startedAt < 30 * 60 * 1000) {
                        localContext = parsed;
                    } else {
                        localStorage.removeItem('ironmind_checkout');
                    }
                }
            } catch (e) {
                // Ignore parse errors
            }

            // Restore basic info for UI
            if (localContext?.courseId) {
                setCourseId(localContext.courseId);
            }

            // If we have an explicit session ID in URL from provider, verify that directly (Stripe behavior)
            if (sessionId) {
                const { data, status } = await apiFetch<CheckoutSessionVerification>(`/checkout/session/${sessionId}`);
                if (status === 200 && data) {
                    if (data.paymentStatus === 'paid') {
                        setCourseId(data.courseId);
                        if (data.courseId) {
                            setPolling(true);
                        }
                    } else {
                        setError(`Payment status: ${data.paymentStatus}`);
                    }
                } else {
                    setError('Failed to verify purchase.');
                }
                setLoading(false);
                return;
            }

            // Otherwise, we rely on our intentId from localStorage (PayPlus behavior)
            if (localContext?.intentId) {
                setPolling(true);
                setLoading(false);
                return;
            }

            // If we have neither, we can't do much
            if (!localContext) {
                setError('No checkout session found. If you just completed a payment, check your library shortly.');
            } else {
                // We have a local context but no intent ID. Just poll the access route directly.
                setPolling(true);
            }
            setLoading(false);
        };

        recoverAndVerify();
    }, [sessionId]);

    // 2. Poll for Success
    useEffect(() => {
        if (!polling) return;

        let pollCount = 0;
        const maxPolls = 15; // 22.5 seconds max
        let timerId: NodeJS.Timeout;

        const checkCompletion = async () => {
            pollCount++;
            let localContext: any = null;
            try {
                const stored = localStorage.getItem('ironmind_checkout');
                if (stored) localContext = JSON.parse(stored);
            } catch (e) { }

            // A. If we know the intent ID, poll the intent status first
            if (localContext?.intentId) {
                const { data, status } = await apiFetch<IntentVerification>(`/payments/intents/${localContext.intentId}`);
                if (status === 200 && data) {
                    if (data.status === 'failed') {
                        setPolling(false);
                        setError('Your payment failed or was declined.');
                        localStorage.removeItem('ironmind_checkout');
                        return;
                    }
                    if (data.status === 'succeeded') {
                        // Immediately clear the storage, drop directly to checking access
                        localStorage.removeItem('ironmind_checkout');
                        // No return here, let it fall through to step B to verify access
                    } else {
                        return scheduleNext(); // Still pending
                    }
                } else if (status === 404) {
                    // Unexpected
                    return scheduleNext();
                } else if (status === 401) {
                    setPolling(false);
                    setError("Your session expired. Please log in to view your content.");
                    return;
                }
            }

            // B. Check final access (Content unlocked)
            if (courseId) {
                const { data, status } = await apiFetch<{ allowed: boolean }>(`/access/courses/${courseId}`);
                if (status === 200 && data?.allowed) {
                    setPolling(false);
                    localStorage.removeItem('ironmind_checkout');
                    return; // Access granted!
                }
            } else if (localContext?.scope === 'membership') {
                const { data, status } = await apiFetch<any>(`/access/me`);
                if (status === 200 && data?.tier !== 'free') {
                    setPolling(false);
                    localStorage.removeItem('ironmind_checkout');
                    return;
                }
            }

            scheduleNext();
        };

        const scheduleNext = () => {
            if (pollCount >= maxPolls) {
                setPolling(false);
                // We don't set an error; we just drop them into the "Still Processing" state
                return;
            }
            timerId = setTimeout(checkCompletion, 1500);
        }

        checkCompletion();

        return () => clearTimeout(timerId);
    }, [polling, courseId]);

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
                        <div className={`w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-6 ${polling ? 'bg-zinc-500/10 text-zinc-400' : 'bg-green-500/10 text-green-500'}`}>
                            {polling ? (
                                <svg className="w-8 h-8 animate-spin" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                            ) : (
                                <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                </svg>
                            )}
                        </div>
                        <h1 className="text-3xl font-black text-white italic uppercase tracking-tighter mb-2">
                            {polling ? 'Waiting for Confirmation' : (
                                <>Access <span className="text-green-500">Granted</span></>
                            )}
                        </h1>
                        <p className="text-gray-400 text-sm mb-8">
                            {polling
                                ? 'Payment confirmed! Checking your account access (this may take a few seconds)...'
                                : 'Your payment is complete and your access is ready.'
                            }
                        </p>

                        <div className="space-y-3">
                            {courseId && !polling && (
                                <Link
                                    to={`/courses/${courseId}`}
                                    className="block w-full bg-white text-black py-4 rounded-xl font-bold uppercase tracking-widest hover:bg-gray-200 transition-colors shadow-lg shadow-white/10"
                                >
                                    Go to course
                                </Link>
                            )}

                            <Link
                                to="/library"
                                className={`block w-full border border-white/20 text-white py-4 rounded-xl font-bold uppercase tracking-widest hover:bg-white/5 transition-colors ${!courseId || polling ? 'bg-white/5' : ''}`}
                            >
                                {polling ? 'Go to Library Instead' : 'Go to My Library'}
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
