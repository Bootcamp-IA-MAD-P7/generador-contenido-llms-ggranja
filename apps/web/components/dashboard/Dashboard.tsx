import type { BrandTheme, DashboardFixture } from "../../domain/types.ts";
import { Kicker, SyntheticNotice } from "../ui/Kicker";
import { PostArt } from "../ui/PostArt";
import styles from "./dashboard.module.css";

export function Dashboard({
  welcomeName,
  contextName,
  kind,
  summary,
  handle,
  theme,
  fixture,
  onCreate,
}: {
  welcomeName: string;
  contextName: string;
  kind: string;
  summary: string;
  handle: string;
  theme: BrandTheme;
  fixture: DashboardFixture;
  onCreate: () => void;
}) {
  const ledger = [
    { label: "Borradores", value: fixture.drafts, note: "En preparación" },
    { label: "Pendientes de revisión", value: fixture.review, note: "Esperan decisión humana" },
    { label: "Aprobados", value: fixture.approved, note: "Aprobación explícita" },
  ];

  return (
    <div aria-labelledby="view-title" role="region">
      <header className={styles.masthead}>
        <div>
          <span className={styles.brandRule} aria-hidden="true" />
          <Kicker>{kind}</Kicker>
          <p className={styles.welcome}>Te damos la bienvenida, {welcomeName}</p>
          <h1 id="view-title" className={styles.title}>{contextName}</h1>
          <p className={styles.lede}>{summary}</p>
        </div>
        <button type="button" className={styles.create} onClick={onCreate}>
          Crear contenido <span aria-hidden="true">→</span>
        </button>
      </header>

      <section aria-label="Resumen editorial">
        <dl className={styles.ledger}>
          {ledger.map((item) => (
            <div className={styles.ledgerItem} key={item.label}>
              <dt className={styles.ledgerLabel}>{item.label}</dt>
              <dd>
                <span className={styles.ledgerValue}>{item.value}</span>
                <span className={styles.ledgerNote}>{item.note}</span>
              </dd>
            </div>
          ))}
        </dl>
        <p className={styles.boundary}>
          Cifras sintéticas del estado interno del flujo editorial. No son métricas de redes sociales ni rendimiento, y no hay cuentas conectadas.
        </p>
      </section>

      <div className={styles.columns}>
        <section aria-labelledby="upcoming-title">
          <div className={styles.heading}>
            <h2 id="upcoming-title">Próximos contenidos</h2>
            <SyntheticNotice>Calendario de ejemplo · sin publicación automática</SyntheticNotice>
          </div>
          {fixture.upcoming.length > 0 ? (
            <ul>
              {fixture.upcoming.map((item) => (
                <li className={styles.upcomingItem} key={item.id}>
                  <PostArt theme={theme} headline={item.title} handle={handle} platform={item.platform} format={item.format} />
                  <div>
                    <time className={styles.date}>{item.date}</time>
                    <p className={styles.upcomingTitle}>{item.title}</p>
                    <p className={styles.upcomingMeta}>{item.platform} · {item.format} · {item.campaign}</p>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <div className={styles.empty}>
              <strong>No hay próximos contenidos</strong>
              Este contexto sintético todavía no tiene elementos en el calendario de ejemplo.
            </div>
          )}
        </section>

        <section aria-labelledby="activity-title">
          <div className={styles.heading}>
            <h2 id="activity-title">Actividad reciente</h2>
          </div>
          {fixture.activity.length > 0 ? (
            <ol className={styles.activity}>
              {fixture.activity.map((entry) => (
                <li key={entry.id}>
                  <strong>{entry.text}</strong>
                  <span>{entry.time} · actividad sintética</span>
                </li>
              ))}
            </ol>
          ) : (
            <div className={styles.empty}>
              <strong>Sin actividad reciente</strong>
              Este contexto sintético aún no registra cambios de ejemplo.
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
