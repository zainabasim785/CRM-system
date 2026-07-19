"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { getCurrentUser, loginUser, registerUser } from "@/lib/api/auth";
import { AUTH_LOST_EVENT, getErrorMessage } from "@/lib/api/client";
import {
  clearAccessToken,
  getAccessToken,
  setAccessToken,
} from "@/lib/auth/token";
import type { LoginFormValues, RegisterFormValues } from "@/lib/validations";
import type { UserRead } from "@/types/api";

interface AuthContextValue {
  user: UserRead | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (values: LoginFormValues) => Promise<void>;
  register: (values: RegisterFormValues) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserRead | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    const token = getAccessToken();
    if (!token) {
      setUser(null);
      return;
    }
    try {
      const me = await getCurrentUser();
      setUser(me);
    } catch {
      clearAccessToken();
      setUser(null);
    }
  }, []);

  useEffect(() => {
    void (async () => {
      try {
        await refreshUser();
      } finally {
        setLoading(false);
      }
    })();
  }, [refreshUser]);

  useEffect(() => {
    const onAuthLost = () => setUser(null);
    window.addEventListener(AUTH_LOST_EVENT, onAuthLost);
    return () => window.removeEventListener(AUTH_LOST_EVENT, onAuthLost);
  }, []);

  const login = useCallback(async (values: LoginFormValues) => {
    const token = await loginUser(values);
    setAccessToken(token.access_token);
    const me = await getCurrentUser();
    setUser(me);
  }, []);

  const register = useCallback(async (values: RegisterFormValues) => {
    const result = await registerUser({
      email: values.email,
      password: values.password,
      full_name: values.full_name || undefined,
      phone: values.phone || undefined,
    });
    setAccessToken(result.access_token);
    setUser(result.user);
  }, []);

  const logout = useCallback(() => {
    clearAccessToken();
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({
      user,
      loading,
      isAuthenticated: Boolean(user),
      login,
      register,
      logout,
      refreshUser,
    }),
    [user, loading, login, register, logout, refreshUser]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

export { getErrorMessage };
