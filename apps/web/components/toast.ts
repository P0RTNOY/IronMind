type ToastType = 'success' | 'error' | 'info';

type Toast = {
    id: string;
    type: ToastType;
    message: string;
};

// Global event target for dispatching toasts
const toastTarget = new EventTarget();

export function dispatchToast(type: ToastType, message: string) {
    const event = new CustomEvent('toast', { detail: { type, message } });
    toastTarget.dispatchEvent(event);
}

export const toast = {
    success: (message: string) => dispatchToast('success', message),
    error: (message: string) => dispatchToast('error', message),
    info: (message: string) => dispatchToast('info', message),
};

export function subscribeToasts(callback: (toast: Omit<Toast, 'id'>) => void) {
    const handler = (e: Event) => {
        const customEvent = e as CustomEvent;
        callback(customEvent.detail);
    };
    toastTarget.addEventListener('toast', handler);
    return () => toastTarget.removeEventListener('toast', handler);
}
