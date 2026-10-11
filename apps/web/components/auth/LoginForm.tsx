"use client";

import { useEffect, useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { getSession, login, LoginError } from "../../domain/auth.ts";
import styles from "./auth.module.css";

export function LoginForm() {
  const router = useRouter();
  const expired = useSearchParams().get("expirada") === "1";
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  useEffect(() => {
    if (getSession()) router.replace("/studio");
  }, [router]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!username.trim() || !password) {
      setError("Escribe tu usuario y tu contraseña.");
      return;
    }
    setPending(true);
    setError("");
    try {
      await login(username, password);
      router.replace("/studio");
    } catch (cause) {
      setError(cause instanceof LoginError ? cause.message : "No se pudo iniciar sesión. Inténtalo de nuevo.");
      setPending(false);
    }
  }

  return (
    <main className={styles.page}>
      <section className={styles.card} aria-labelledby="login-title">
        <p className={styles.wordmark}>estudio.</p>
        <h1 id="login-title" className={styles.title}>Inicia sesión</h1>
        <p className={styles.lede}>Entra para preparar, revisar y planificar tu contenido.</p>

        {expired && <p className={styles.notice} role="status">Tu sesión ha caducado. Vuelve a entrar para continuar.</p>}

        <form onSubmit={submit} noValidate className={styles.form}>
          <div className={styles.field}>
            <label htmlFor="login-user">Usuario</label>
            <input id="login-user" name="username" autoComplete="username" autoCapitalize="none" value={username} onChange={(event) => setUsername(event.target.value)} aria-invalid={Boolean(error)} aria-describedby={error ? "login-error" : undefined} />
          </div>
          <div className={styles.field}>
            <label htmlFor="login-password">Contraseña</label>
            <input id="login-password" name="password" type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} aria-invalid={Boolean(error)} aria-describedby={error ? "login-error" : undefined} />
          </div>
          {error && <p id="login-error" className={styles.error} role="alert">{error}</p>}
          <button type="submit" className={styles.submit} disabled={pending}>{pending ? "Entrando…" : "Entrar"}</button>
        </form>

        <p className={styles.back}><Link href="/">Volver al inicio</Link></p>
      </section>
    </main>
  );
}
