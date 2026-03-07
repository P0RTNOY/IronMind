import React from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { routes } from '../lib/routes';

const NotFound: React.FC = () => {
    const [searchParams] = useSearchParams();
    const reason = searchParams.get('reason');
    const navigate = useNavigate();

    return (
        <div className="max-w-4xl mx-auto px-4 py-24 text-center">
            <h1 className="text-4xl md:text-5xl font-black text-red-500 tracking-tighter uppercase italic mb-6">
                Signal Lost
            </h1>
            <p className="text-gray-400 mb-2">The requested protocol or resource could not be found.</p>
            {reason === 'lesson_missing' && (
                <p className="text-gray-500 text-sm mb-8 bg-black/50 inline-block px-4 py-2 rounded-lg border border-white/5">
                    Reason: We couldn't locate that specific lesson. It may have been removed or unpublished.
                </p>
            )}
            {!reason && (
                <div className="h-4 mb-8"></div>
            )}

            <div className="flex gap-4 justify-center">
                <button
                    onClick={() => navigate(-1)}
                    className="px-6 py-3 rounded-xl font-black uppercase text-xs tracking-widest border border-white/20 text-white hover:bg-white/10 transition"
                >
                    Go Back
                </button>
                <button
                    onClick={() => navigate(routes.home(), { replace: true })}
                    className="px-6 py-3 rounded-xl font-black uppercase text-xs tracking-widest bg-red-500 text-white hover:bg-red-600 transition"
                >
                    Back Home
                </button>
            </div>
        </div>
    );
};

export default NotFound;
