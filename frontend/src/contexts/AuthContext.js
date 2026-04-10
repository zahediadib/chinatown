import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem('ct_user');
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        setUser(parsed);
        axios.get(`${API}/auth/me`, {
          headers: { Authorization: `Bearer ${parsed.token}` },
        }).then(res => {
          const updated = { ...parsed, active_room: res.data.active_room };
          setUser(updated);
          localStorage.setItem('ct_user', JSON.stringify(updated));
        }).catch(() => {
          localStorage.removeItem('ct_user');
          setUser(null);
        }).finally(() => setLoading(false));
      } catch {
        localStorage.removeItem('ct_user');
        setLoading(false);
      }
    } else {
      setLoading(false);
    }
  }, []);

  const login = useCallback(async (username, password) => {
    const { data } = await axios.post(`${API}/auth/login`, { username, password });
    const meRes = await axios.get(`${API}/auth/me`, { headers: { Authorization: `Bearer ${data.token}` } });
    const userData = { ...data, active_room: meRes.data.active_room };
    localStorage.setItem('ct_user', JSON.stringify(userData));
    setUser(userData);
    return userData;
  }, []);

  const register = useCallback(async (username, password) => {
    const { data } = await axios.post(`${API}/auth/register`, { username, password });
    const userData = { ...data, active_room: null };
    localStorage.setItem('ct_user', JSON.stringify(userData));
    setUser(userData);
    return userData;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('ct_user');
    setUser(null);
  }, []);

  const updateUser = useCallback((updates) => {
    setUser(prev => {
      const next = { ...prev, ...updates };
      localStorage.setItem('ct_user', JSON.stringify(next));
      return next;
    });
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, updateUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
