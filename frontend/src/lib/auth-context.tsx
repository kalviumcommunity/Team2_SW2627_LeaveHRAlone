"use client";

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import {
  api,
  AuthToken,
  clearAuth,
  getStoredUser,
  storeAuth,
  User,
} from "./api";

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
}

interface RegisterData {
  name: string;
  email: string;
  password: string;
  role: string;
  region: string;
  country: string;
  department?: string;
  employment_type: string;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Restore user from localStorage on mount
    const storedUser = getStoredUser();
    if (storedUser) {
      setUser(storedUser);
    }
    setIsLoading(false);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const auth: AuthToken = await api.login(email, password);
    storeAuth(auth);
    setUser(auth.user);
  }, []);

  const register = useCallback(async (data: RegisterData) => {
    const auth: AuthToken = await api.register(data);
    storeAuth(auth);
    setUser(auth.user);
  }, []);

  const logout = useCallback(() => {
    clearAuth();
    setUser(null);
    // Attempt server-side logout (fire & forget)
    api.logout().catch(() => {});
  }, []);

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within <AuthProvider>");
  return ctx;
}
