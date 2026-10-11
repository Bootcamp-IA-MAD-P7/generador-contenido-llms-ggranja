import { useState } from "react";
import type { BrandTheme, EditorialStatus, LocalDraft } from "../../domain/types.ts";
import { Kicker, SyntheticNotice } from "../ui/Kicker";
import { DraftStatusMark } from "../ui/EditorialStatus";
import { PostArt } from "../ui/PostArt";
import styles from "./drafts.module.css";

type Filter = "all" | EditorialStatus;

const filterOptions: { id: Filter; label: string }[] = [
  { id: "all", label: "Todos" },
  { id: "draft", label: "Borrador" },
  { id: "review", label: "En revisión" },
  { id: "approved", label: "Aprobado" },
];

export function DraftsView({
  welcomeName,
  contextName,
  handle,
  theme,
  drafts,
  onOpenDraft,
}: {
  welcomeName: string;
  contextName: string;
  handle: string;
  theme: BrandTheme;
  drafts: LocalDraft[];
  onOpenDraft: (draft: LocalDraft) => void;
}) {
  const [filter, setFilter] = useState<Filter>("all");
  const visible = filter === "all" ? drafts : drafts.filter((draft) => draft.status === filter);

  return (
    <section aria-labelledby="view-title">
      <header className={styles.head}>
        <Kicker>Borradores</Kicker>
        <p className={styles.welcome}>Te damos la bienvenida, {welcomeName}</p>
        <h1 id="view-title" className={styles.title}>{contextName}</h1>
        <p className={styles.lede}>Revisa los ejemplos por estado editorial y abre cualquiera en Content Studio.</p>
        <SyntheticNotice>Contenido local sintético · sin persistencia</SyntheticNotice>
      </header>

      <div className={styles.filters} role="group" aria-label="Filtrar borradores por estado">
        {filterOptions.map((option) => (
          <button
            key={option.id}
            type="button"
            className={styles.filter}
            aria-pressed={filter === option.id}
            onClick={() => setFilter(option.id)}
          >
            {option.label}
          </button>
        ))}
      </div>

      {visible.length > 0 ? (
        <ul className={styles.list}>
          {visible.map((draft) => (
            <li className={styles.entry} key={draft.id}>
              <PostArt theme={theme} headline={draft.title} handle={handle} platform={draft.platform} format={draft.format} />
              <div className={styles.entryTop}>
                <DraftStatusMark status={draft.status} />
                <span className={styles.entryMeta}>{draft.updatedAt} · ejemplo</span>
              </div>
              <h2 className={styles.entryTitle}>{draft.title}</h2>
              <p className={styles.entryMeta}>{draft.platform} · {draft.format}</p>
              <p className={styles.excerpt}>{draft.copy.replace(/\s+/g, " ").slice(0, 150)}</p>
              <button type="button" className={styles.open} onClick={() => onOpenDraft(draft)}>
                Abrir en Content Studio <span aria-hidden="true">→</span>
              </button>
            </li>
          ))}
        </ul>
      ) : (
        <div className={styles.empty} role="status">
          <strong>{drafts.length === 0 ? "Todavía no hay borradores" : "No hay borradores con este estado"}</strong>
          {drafts.length === 0
            ? "Cuando prepares contenido para este contexto, aparecerá aquí."
            : "Prueba otro filtro o prepara un borrador nuevo desde Content Studio."}
        </div>
      )}
      <p className={styles.boundary}>La lista es de ejemplo y no guarda cambios. Los estados no representan aprobaciones fuera del prototipo.</p>
    </section>
  );
}
