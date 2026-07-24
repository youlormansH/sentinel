"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import * as api from "@/lib/api";
import { clearTokens, getAccessToken, setTokens } from "@/lib/token-store";
import type { User } from "@/lib/types";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string, mfaCode?: string) => Promise<{ mfaRequired: boolean }>;
  register: (email: string, fullName: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const refreshUser = useCallback(async () => {
    if (!getAccessToken()) {
      setUser(null);
      return;
    }
    try {
      const me = await api.fetchMe();
      setUser(me);
    } catch {
      setUser(null);
    }
  }, []);

  useEffect(() => {
    refreshUser().finally(() => setLoading(false));
  }, [refreshUser]);

  const login = useCallback(
    async (email: string, password: string, mfaCode?: string) => {
      const result = await api.login(email, password, mfaCode);
      if (result.mfa_required) {
        return { mfaRequired: true };
      }
      setTokens(result.access_token, result.refresh_token);
      await refreshUser();
      return { mfaRequired: false };
    },
    [refreshUser]
  );

  const register = useCallback(async (email: string, fullName: string, password: string) => {
    await api.register(email, fullName, password);
  }, []);

  const logout = useCallback(async () => {
    try {
      await api.logout();
    } finally {
      clearTokens();
      setUser(null);
      router.push("/login");
    }
  }, [router]);

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
