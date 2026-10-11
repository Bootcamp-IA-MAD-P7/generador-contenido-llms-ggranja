import { Suspense } from "react";
import type { Metadata } from "next";
import { LoginForm } from "../../components/auth/LoginForm";

export const metadata: Metadata = { title: "Iniciar sesión · Estudio" };

export default function LoginPage() {
  return (
    <Suspense fallback={null}>
      <LoginForm />
    </Suspense>
  );
}
