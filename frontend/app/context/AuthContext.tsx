"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { API_BASE, safeFetch } from "../utils/api";

export interface User {
  id: number;
  email: string;
  full_name: string;
  plan_tier: string;
  avatar_url?: string;
}

export type AuthModalMode = "login" | "signup" | "forgot" | "reset";

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (data: any) => void;
  logout: () => void;
  updateUser: (updated: Partial<User>) => void;
  openAuthModal: (mode?: AuthModalMode) => void;
  closeAuthModal: () => void;
  isAuthModalOpen: boolean;
  authModalMode: AuthModalMode;
  openProfileModal: () => void;
  closeProfileModal: () => void;
  isProfileModalOpen: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authModalMode, setAuthModalMode] = useState<AuthModalMode>("login");
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);

  useEffect(() => {
    const savedToken = localStorage.getItem("tradegod_token");
    const savedUser = localStorage.getItem("tradegod_user");
    
    if (savedToken && savedUser) {
      setToken(savedToken);
      try {
        setUser(JSON.parse(savedUser));
      } catch (e) {}
      
      safeFetch(`${API_BASE}/api/auth/me`)
        .then((res) => {
          if (res.ok) return res.json();
          throw new Error("Invalid token");
        })
        .then((data) => {
          if (data?.user) {
            setUser(data.user);
            localStorage.setItem("tradegod_user", JSON.stringify(data.user));
          }
        })
        .catch(() => {
          // Token invalid
          setToken(null);
          setUser(null);
          localStorage.removeItem("tradegod_token");
          localStorage.removeItem("tradegod_user");
          setIsAuthModalOpen(true);
        })
        .finally(() => setIsLoading(false));
    } else {
      setIsLoading(false);
      setIsAuthModalOpen(true);
    }
  }, []);

  const login = (authData: { token: string; user: User }) => {
    setToken(authData.token);
    setUser(authData.user);
    localStorage.setItem("tradegod_token", authData.token);
    localStorage.setItem("tradegod_user", JSON.stringify(authData.user));
    setIsAuthModalOpen(false);
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem("tradegod_token");
    localStorage.removeItem("tradegod_user");
    setIsProfileModalOpen(false);
    setAuthModalMode("login");
    setIsAuthModalOpen(true);
  };

  const updateUser = (updated: Partial<User>) => {
    if (user) {
      const newObj = { ...user, ...updated };
      setUser(newObj);
      localStorage.setItem("tradegod_user", JSON.stringify(newObj));
    }
  };

  const openAuthModal = (mode: AuthModalMode = "login") => {
    setAuthModalMode(mode);
    setIsAuthModalOpen(true);
  };

  const closeAuthModal = () => {
    if (token && user) {
      setIsAuthModalOpen(false);
    }
  };

  const openProfileModal = () => setIsProfileModalOpen(true);
  const closeProfileModal = () => setIsProfileModalOpen(false);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token && !!user,
        isLoading,
        login,
        logout,
        updateUser,
        openAuthModal,
        closeAuthModal,
        isAuthModalOpen,
        authModalMode,
        openProfileModal,
        closeProfileModal,
        isProfileModalOpen,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
