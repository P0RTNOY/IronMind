import React from 'react';
import { Link } from 'react-router-dom';

const Cancel: React.FC = () => {
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
                <Link
                    to="/"
                    className="block w-full bg-white text-black py-4 rounded-xl font-bold uppercase tracking-widest hover:bg-gray-200 transition-colors"
                >
                    Return to Courses
                </Link>
            </div>
        </div>
    );
};

export default Cancel;
