
import { useState, useEffect } from 'react';
import { apiFetch } from '../lib/api';
import { AccessMeResponse } from '../types';

export function useAuth() {
  const [uid, setUid] = useState<string | null>(null);
  const [isAdmin, setIsAdmin] = useState<boolean>(false);
  const [accessData, setAccessData] = useState<AccessMeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [isAuthorized, setIsAuthorized] = useState(false);

  useEffect(() => {
    const storedUid = localStorage.getItem('debugUid');
    const storedAdmin = localStorage.getItem('debugAdmin');
    
    setUid(storedUid);
    setIsAdmin(storedAdmin === '1');
    
    const fetchAccess = async () => {
      if (!storedUid) {
        setLoading(false);
        setIsAuthorized(false);
        return;
      }

      const { data, status } = await apiFetch<AccessMeResponse>('/access/me');
      if (status === 200 && data) {
        setAccessData(data);
        setIsAdmin(data.isAdmin);
        setIsAuthorized(true);
      } else if (status === 401) {
        setIsAuthorized(false);
      }
      setLoading(false);
    };

    fetchAccess();
  }, []);

  const login = (uid: string, admin: boolean) => {
    localStorage.setItem('debugUid', uid);
    localStorage.setItem('debugAdmin', admin ? '1' : '0');
    window.location.reload();
  };

  const logout = () => {
    localStorage.removeItem('debugUid');
    localStorage.removeItem('debugAdmin');
    window.location.reload();
  };

  return { uid, isAdmin, accessData, loading, isAuthorized, login, logout };
}
