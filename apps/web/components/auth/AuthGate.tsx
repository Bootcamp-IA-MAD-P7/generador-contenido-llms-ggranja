"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { clearSession, getSession, type Session } from "../../domain/auth.ts";

type AuthValue = { username: string; logout: () => void };

const AuthContext = createContext<AuthValue | null>(null);

/** The signed-in user and sign-out action, or null outside a protected page. */
export function useAuth(): AuthValue | null {
  return useContext(AuthContext);
}

/** Renders its children only with a live session; otherwise sends the visitor to sign-in. */
export function AuthGate({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [session, setSession] = useState<Session | null>(null);
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    const current = getSession();
    if (!current) {
      router.replace("/login");
      return;
    }
    setSession(current);
    setChecked(true);
    const onExpired = () => router.replace("/login?expirada=1");
    window.addEventListener("auth:expired", onExpired);
    return () => window.removeEventListener("auth:expired", onExpired);
  }, [router]);

  const logout = useCallback(() => {
    clearSession();
    router.replace("/");
  }, [router]);

  const value = useMemo(() => (session ? { username: session.username, logout } : null), [session, logout]);

  if (!checked || !value) return <p role="status" style={{ padding: "2rem" }}>Comprobando tu sesión…</p>;
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
