import React, { useState, useEffect } from 'react';
import { subscribeToasts } from './toast';

type ToastType = 'success' | 'error' | 'info';

interface ToastItem {
    id: string;
    type: ToastType;
    message: string;
}

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [toasts, setToasts] = useState<ToastItem[]>([]);

    useEffect(() => {
        const unsubscribe = subscribeToasts((newToast) => {
            const id = Math.random().toString(36).substring(2, 9);
            setToasts((prev) => [...prev, { id, ...newToast }]);

            // Auto-dismiss after 4s
            setTimeout(() => {
                setToasts((prev) => prev.filter((t) => t.id !== id));
            }, 4000);
        });

        return () => unsubscribe();
    }, []);

    const removeToast = (id: string) => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
    };

    return (
        <>
            {children}
            <div
                aria-live="polite"
                className="fixed bottom-4 left-1/2 -translate-x-1/2 z-50 flex flex-col gap-2 pointer-events-none"
            >
                {toasts.map((t) => {
                    const baseClasses = "pointer-events-auto flex items-center justify-between min-w-[300px] px-4 py-3 rounded-xl shadow-2xl border text-sm font-medium transition-all animate-in slide-in-from-bottom-5";
                    let colorClasses = "";

                    if (t.type === 'success') {
                        colorClasses = "bg-green-900/90 border-green-500/30 text-green-50";
                    } else if (t.type === 'error') {
                        colorClasses = "bg-red-900/90 border-red-500/30 text-red-50";
                    } else {
                        colorClasses = "bg-[#222]/90 border-white/10 text-white";
                    }

                    return (
                        <div key={t.id} className={`${baseClasses} ${colorClasses}`}>
                            <span dir="rtl">{t.message}</span>
                            <button
                                onClick={() => removeToast(t.id)}
                                className="ml-4 opacity-70 hover:opacity-100 transition p-1"
                                aria-label="Close"
                            >
                                ✕
                            </button>
                        </div>
                    );
                })}
            </div>
        </>
    );
};
