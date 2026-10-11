import type { RefObject, ReactNode } from "react";
import type { ViewId } from "../../domain/types.ts";
import { useAuth } from "../auth/AuthGate";
import { NavIcon } from "./NavIcon";
import styles from "./shell.module.css";

type NavEntry = { id: ViewId; label: string; sub?: boolean; meta?: string };

const primary: NavEntry[] = [
  { id: "dashboard", label: "Dashboard" },
  { id: "content-studio", label: "Content Studio" },
  { id: "drafts", label: "Borradores" },
  { id: "calendar", label: "Calendario" },
  { id: "history", label: "Historial" },
];

const upcoming: NavEntry[] = [
  { id: "library", label: "Library" },
  { id: "analytics", label: "Analytics" },
  { id: "brands", label: "Brands & Stores" },
  { id: "settings", label: "Settings" },
];

export function Sidebar({
  view,
  onNavigate,
  draftCount,
  switcher,
  open,
  sidebarRef,
  id,
}: {
  view: ViewId;
  onNavigate: (view: ViewId) => void;
  draftCount: number;
  switcher: ReactNode;
  open: boolean;
  sidebarRef: RefObject<HTMLElement | null>;
  id: string;
}) {
  const auth = useAuth();
  const displayName = auth ? auth.username.charAt(0).toUpperCase() + auth.username.slice(1) : "Gabriela";

  function renderItem(entry: NavEntry, meta?: string) {
    return (
      <li key={entry.id}>
        <button
          type="button"
          className={`${styles.navItem} ${entry.sub ? styles.navSub : ""}`}
          aria-current={view === entry.id ? "page" : undefined}
          onClick={() => onNavigate(entry.id)}
        >
          <span className={styles.navLabel}>
            <NavIcon id={entry.id} />
            {entry.label}
          </span>
          {meta && <span className={styles.navMeta}>{meta}</span>}
        </button>
      </li>
    );
  }

  return (
    <aside ref={sidebarRef} id={id} className={`${styles.sidebar} ${open ? styles.sidebarOpen : ""}`} aria-label="Barra lateral">
      <p className={styles.wordmark}>estudio<span>.</span></p>
      {switcher}
      <nav className={styles.nav} aria-label="Navegación principal">
        <div className={styles.navGroup}>
          <p className={styles.sectionLabel}>Trabajo editorial</p>
          <ul>{primary.map((entry) => renderItem(entry, entry.id === "drafts" ? String(draftCount) : undefined))}</ul>
        </div>
        <div className={styles.navGroup}>
          <p className={styles.sectionLabel}>Próximamente</p>
          <ul>{upcoming.map((entry) => renderItem(entry))}</ul>
        </div>
      </nav>
      <div className={styles.sidebarFoot}>
        <strong>{displayName}</strong>
        Content manager · espacio local
        {auth && <button type="button" className={styles.logout} onClick={auth.logout}>Cerrar sesión</button>}
      </div>
    </aside>
  );
}
