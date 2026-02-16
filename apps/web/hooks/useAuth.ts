import { useState, useEffect } from "react";
import { UserContext } from "../types";
import { apiFetch } from "../lib/api";

export function useAuth() {
    const [user, setUser] = useState<UserContext | null>(null);
    const [loading, setLoading] = useState(true);

    const checkAuth = async () => {
        // 1. Dev Auth (localStorage) - Synchronous Check
        // This allows instant load for dev environment
        const debugUid = localStorage.getItem("debugUid");
        if (debugUid) {
            setUser({
                uid: debugUid,
                is_admin: localStorage.getItem("debugAdmin") === "1",
                email: "dev@local",
                name: "Dev User"
            });
            setLoading(false);
            return;
        }

        // 2. Production Auth (Cookie Session)
        // We call the API. If 401, we are not logged in.
        try {
            const { data, status } = await apiFetch<{ uid: string; email: string; isAdmin: boolean }>('/auth/session', {
                skipRedirect: true
            });

            if (status === 200 && data) {
                setUser({
                    uid: data.uid,
                    email: data.email,
                    is_admin: data.isAdmin,
                    name: data.email.split('@')[0],
                });
            } else {
                setUser(null);
            }
        } catch (e) {
            setUser(null);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        checkAuth();
    }, []);

    const loginDev = (uid: string, admin: boolean) => {
        localStorage.setItem('debugUid', uid);
        localStorage.setItem('debugAdmin', admin ? '1' : '0');
        window.location.reload();
    };

    const logout = async () => {
        if (localStorage.getItem('debugUid')) {
            localStorage.removeItem('debugUid');
            localStorage.removeItem('debugAdmin');
            window.location.reload();
            return;
        }

        // Prod Logout
        try {
            await apiFetch('/auth/logout', { method: 'POST' });
            window.location.href = '/';
        } catch (e) {
            console.error("Logout failed", e);
            // Force reload anyway
            window.location.href = '/';
        }
    };

    return { user, loading, loginDev, logout };
}
