import { useState } from "react";
import type { HistoryEntry, LocalDraft } from "../../domain/types.ts";
import { Kicker, SyntheticNotice } from "../ui/Kicker";
import { DraftStatusMark } from "../ui/EditorialStatus";
import styles from "./history.module.css";

type Filter = "all" | "draft" | "review" | "approved";

const filters: { id: Filter; label: string }[] = [
  { id: "all", label: "Todos" },
  { id: "draft", label: "Borradores" },
  { id: "review", label: "En revisión" },
  { id: "approved", label: "Aprobados" },
];

export function HistoryView({
  welcomeName,
  contextName,
  entries,
  drafts,
  onOpenDraft,
}: {
  welcomeName: string;
  contextName: string;
  entries: HistoryEntry[];
  drafts: LocalDraft[];
  onOpenDraft: (draft: LocalDraft) => void;
}) {
  const [filter, setFilter] = useState<Filter>("all");
  const visible = filter === "all" ? entries : entries.filter((entry) =>
    filter === "draft" ? entry.status === "draft" || entry.status === "changes-requested" : entry.status === filter,
  );

  return (
    <section aria-labelledby="view-title">
      <header className={styles.head}>
        <Kicker>Historial editorial</Kicker>
        <p className={styles.welcome}>Te damos la bienvenida, {welcomeName}</p>
        <h1 id="view-title" className={styles.title}>{contextName}</h1>
        <p className={styles.lede}>Actividad sintética del contexto seleccionado, sin conexiones externas.</p>
        <SyntheticNotice>Ejemplos sintéticos y actividad de esta sesión</SyntheticNotice>
      </header>

      <div className={styles.filters} role="group" aria-label="Filtrar actividad por estado">
        {filters.map((option) => (
          <button key={option.id} type="button" aria-pressed={filter === option.id} onClick={() => setFilter(option.id)}>
            {option.label}
          </button>
        ))}
      </div>

      {visible.length ? (
        <ol className={styles.list}>
          {visible.map((entry) => {
            const draft = drafts.find((item) => item.id === entry.draftId);
            return (
              <li key={entry.id} className={styles.entry}>
                <div className={styles.meta}>
                  <time>{entry.time}{entry.source === "session" ? " · esta sesión" : " · ejemplo"}</time>
                  {entry.status === "changes-requested" ? <span>Cambios solicitados</span> : <DraftStatusMark status={entry.status} />}
                </div>
                <p>{entry.text}</p>
                {draft && <button type="button" onClick={() => onOpenDraft(draft)}>Abrir “{draft.title}” en Content Studio →</button>}
              </li>
            );
          })}
        </ol>
      ) : (
        <div className={styles.empty} role="status">
          <strong>{entries.length ? "No hay actividad con este estado" : "Todavía no hay actividad"}</strong>
          <span>El historial muestra ejemplos del contexto seleccionado.</span>
        </div>
      )}
    </section>
  );
}
