/** Sign-in session for the local prototype. The token lives in sessionStorage for the tab only. */

export type Session = { token: string; username: string; expiresAt: number };

const STORAGE_KEY = "estudio.session";

function baseUrl(): string {
  return (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000").replace(/\/+$/, "");
}

/** Reads a stored session, ignoring anything malformed or expired. */
export function parseSession(raw: string | null, nowSeconds: number = Date.now() / 1000): Session | null {
  if (!raw) return null;
  try {
    const value = JSON.parse(raw) as Partial<Session>;
    if (typeof value.token !== "string" || typeof value.username !== "string" || typeof value.expiresAt !== "number") return null;
    return value.expiresAt > nowSeconds ? (value as Session) : null;
  } catch {
    return null;
  }
}

export function getSession(): Session | null {
  if (typeof window === "undefined") return null;
  try {
    return parseSession(window.sessionStorage.getItem(STORAGE_KEY));
  } catch {
    return null;
  }
}

export function clearSession(): void {
  try { window.sessionStorage.removeItem(STORAGE_KEY); } catch { /* storage unavailable */ }
}

export function authHeaders(): Record<string, string> {
  const session = getSession();
  return session ? { Authorization: `Bearer ${session.token}` } : {};
}

/** Called when the API answers 401: drops the session and tells the shell to go back to sign-in. */
export function handleUnauthorized(): void {
  clearSession();
  if (typeof window !== "undefined") window.dispatchEvent(new Event("auth:expired"));
}

export class LoginError extends Error {}

export async function login(username: string, password: string): Promise<Session> {
  let response: Response;
  try {
    response = await fetch(`${baseUrl()}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: username.trim(), password }),
      signal: AbortSignal.timeout(10000),
    });
  } catch {
    throw new LoginError("No se pudo conectar con la API. Comprueba que esté en marcha e inténtalo de nuevo.");
  }
  if (response.status === 401) throw new LoginError("Usuario o contraseña incorrectos.");
  if (response.status === 503) throw new LoginError("El acceso no está configurado en el servidor.");
  if (!response.ok) throw new LoginError("No se pudo iniciar sesión. Inténtalo de nuevo.");
  const body = (await response.json()) as { access_token: string; username: string; expires_at: number };
  const session: Session = { token: body.access_token, username: body.username, expiresAt: body.expires_at };
  try { window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(session)); } catch { /* storage unavailable */ }
  return session;
}
